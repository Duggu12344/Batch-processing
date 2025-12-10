"""Retrieval component for the RAG pipeline."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from knowledge.embed_store import CryptoVectorStore
except ImportError:
    # Fallback to simple vector store if sentence-transformers is not available
    from knowledge.embed_store_simple import SimpleCryptoVectorStore as CryptoVectorStore
from utils.logger import logger


@dataclass
class RetrievalResult:
    """Result from fact retrieval."""
    query: str
    facts: List[Dict[str, Any]]
    total_found: int
    retrieval_time: float


class CryptoRetriever:
    """Handles fact retrieval for crypto queries."""
    
    def __init__(self, vector_store: CryptoVectorStore = None):
        self.vector_store = vector_store or CryptoVectorStore()
        logger.info("Crypto retriever initialized")
    
    def retrieve_facts(self, query: str, max_facts: int = 5, 
                      crypto_filter: Optional[str] = None,
                      relevance_threshold: float = 0.8) -> RetrievalResult:
        """Retrieve relevant facts for a query."""
        import time
        
        start_time = time.time()
        
        # Search for facts
        raw_results = self.vector_store.search_facts(
            query=query,
            n_results=max_facts * 2,  # Get more to filter by relevance
            crypto_filter=crypto_filter
        )
        
        # Filter by relevance threshold
        filtered_facts = []
        for result in raw_results:
            # Lower distance = higher similarity
            similarity = 1 - (result.get('distance', 1.0))
            if similarity >= relevance_threshold:
                result['similarity'] = similarity
                filtered_facts.append(result)
        
        # Take top results
        filtered_facts = filtered_facts[:max_facts]
        
        retrieval_time = time.time() - start_time
        
        logger.info(f"Retrieved {len(filtered_facts)} relevant facts for query: '{query}'")
        
        return RetrievalResult(
            query=query,
            facts=filtered_facts,
            total_found=len(raw_results),
            retrieval_time=retrieval_time
        )
    
    def get_context_string(self, retrieval_result: RetrievalResult) -> str:
        """Convert retrieval results to context string for LLM."""
        if not retrieval_result.facts:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        context_parts.append(f"Based on the latest cryptocurrency data, here are the relevant facts:")
        
        for i, fact in enumerate(retrieval_result.facts, 1):
            content = fact['content']
            metadata = fact['metadata']
            timestamp = metadata.get('timestamp', 'unknown')
            
            context_parts.append(f"{i}. {content}")
            context_parts.append(f"   (Source: {metadata.get('crypto_symbol', 'N/A')}, Time: {timestamp[:19]})")
        
        return "\n".join(context_parts)
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine intent and extract crypto symbols."""
        query_lower = query.lower()
        
        # Common crypto symbols and names
        crypto_mapping = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH',
            'cardano': 'ADA', 'ada': 'ADA',
            'solana': 'SOL', 'sol': 'SOL',
            'polkadot': 'DOT', 'dot': 'DOT',
            'chainlink': 'LINK', 'link': 'LINK',
            'polygon': 'MATIC', 'matic': 'MATIC',
            'avalanche': 'AVAX', 'avax': 'AVAX'
        }
        
        # Intent keywords
        intent_keywords = {
            'price': ['price', 'cost', 'value', 'worth', 'trading'],
            'change': ['change', 'increase', 'decrease', 'up', 'down', 'gain', 'loss'],
            'market_cap': ['market cap', 'market capitalization', 'valuation'],
            'volume': ['volume', 'trading volume', 'liquidity'],
            'ranking': ['rank', 'ranking', 'position', 'top']
        }
        
        # Extract crypto symbols
        mentioned_cryptos = []
        for name, symbol in crypto_mapping.items():
            if name in query_lower:
                mentioned_cryptos.append(symbol)
        
        # Determine intent
        detected_intents = []
        for intent, keywords in intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_intents.append(intent)
        
        return {
            'cryptos': list(set(mentioned_cryptos)),
            'intents': detected_intents,
            'is_comparison': any(word in query_lower for word in ['compare', 'vs', 'versus', 'between']),
            'is_general': len(mentioned_cryptos) == 0
        }