"""Vector embedding and storage for cryptocurrency facts."""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from knowledge.fact_extractor import CryptoFact
from utils.config import Config
from utils.logger import logger


class CryptoVectorStore:
    """Vector database for storing and retrieving crypto facts."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.VECTOR_DB_PATH
        self.collection_name = "crypto_facts"
        
        # Initialize embedding model
        logger.info("Loading sentence transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self._init_chromadb()
        
        logger.info("Vector store initialized")
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        # Create database directory
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Cryptocurrency facts and knowledge"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_facts(self, facts: List[CryptoFact]) -> int:
        """Add facts to the vector database."""
        if not facts:
            return 0
        
        # Prepare data for insertion
        documents = []
        metadatas = []
        ids = []
        
        for fact in facts:
            documents.append(fact.content)
            metadatas.append({
                "crypto_id": fact.crypto_id,
                "crypto_symbol": fact.crypto_symbol,
                "fact_type": fact.fact_type,
                "timestamp": fact.timestamp,
                **fact.metadata
            })
            ids.append(fact.fact_id)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} facts...")
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
        
        logger.info(f"Added {len(facts)} facts to vector database")
        return len(facts)
    
    def search_facts(self, query: str, n_results: int = 5, 
                    crypto_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for relevant facts using semantic similarity."""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Prepare where clause for filtering
        where_clause = {}
        if crypto_filter:
            where_clause["crypto_symbol"] = crypto_filter
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "id": results['ids'][0][i]
                })
        
        logger.info(f"Found {len(formatted_results)} relevant facts for query: {query}")
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count()
        
        # Get sample of metadata to understand data distribution
        if count > 0:
            sample = self.collection.get(limit=min(100, count))
            crypto_symbols = set()
            fact_types = set()
            
            for metadata in sample['metadatas']:
                crypto_symbols.add(metadata.get('crypto_symbol', 'unknown'))
                fact_types.add(metadata.get('fact_type', 'unknown'))
            
            return {
                "total_facts": count,
                "unique_cryptos": len(crypto_symbols),
                "crypto_symbols": list(crypto_symbols),
                "fact_types": list(fact_types)
            }
        
        return {"total_facts": 0}
    
    def clear_collection(self):
        """Clear all data from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Cryptocurrency facts and knowledge"}
        )
        logger.info("Collection cleared")


def main():
    """Test the vector store functionality."""
    from data_ingestion.fetch_prices import CoinGeckoFetcher
    from knowledge.fact_extractor import CryptoFactExtractor
    
    logger.info("Testing vector store functionality")
    
    # Fetch some data
    fetcher = CoinGeckoFetcher()
    crypto_data = fetcher.fetch_top_cryptocurrencies(limit=5)
    
    if not crypto_data:
        logger.error("No crypto data available for testing")
        return
    
    # Extract facts
    extractor = CryptoFactExtractor()
    facts = extractor.extract_facts(crypto_data)
    
    # Initialize vector store
    vector_store = CryptoVectorStore()
    
    # Add facts
    added_count = vector_store.add_facts(facts)
    print(f"✅ Added {added_count} facts to vector database")
    
    # Get stats
    stats = vector_store.get_collection_stats()
    print(f"📊 Database stats: {stats}")
    
    # Test search
    test_queries = [
        "What is the current price of Bitcoin?",
        "Which cryptocurrency has increased the most?",
        "Tell me about Ethereum's market cap"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = vector_store.search_facts(query, n_results=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content']}")
            print(f"     Distance: {result['distance']:.3f}")


if __name__ == "__main__":
    main()