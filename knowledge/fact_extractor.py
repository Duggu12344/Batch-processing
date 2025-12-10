"""Extract and convert cryptocurrency data into natural language facts."""

from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingestion.fetch_prices import CryptoData
from utils.logger import logger


@dataclass
class CryptoFact:
    """Structured fact about cryptocurrency data."""
    fact_id: str
    content: str
    crypto_id: str
    crypto_symbol: str
    fact_type: str  # price, change, volume, market_cap
    timestamp: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "crypto_id": self.crypto_id,
            "crypto_symbol": self.crypto_symbol,
            "fact_type": self.fact_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class CryptoFactExtractor:
    """Converts raw crypto data into natural language facts."""
    
    def __init__(self):
        logger.info("Crypto fact extractor initialized")
    
    def extract_facts(self, crypto_data: List[CryptoData]) -> List[CryptoFact]:
        """Extract multiple types of facts from crypto data."""
        facts = []
        
        for crypto in crypto_data:
            # Price facts
            facts.extend(self._extract_price_facts(crypto))
            # Change facts
            facts.extend(self._extract_change_facts(crypto))
            # Market facts
            facts.extend(self._extract_market_facts(crypto))
            # Volume facts
            facts.extend(self._extract_volume_facts(crypto))
        
        logger.info(f"Extracted {len(facts)} facts from {len(crypto_data)} cryptocurrencies")
        return facts
    
    def _extract_price_facts(self, crypto: CryptoData) -> List[CryptoFact]:
        """Extract price-related facts."""
        facts = []
        
        # Current price fact
        price_content = f"{crypto.name} ({crypto.symbol}) is currently trading at ${crypto.current_price:,.2f} USD."
        
        facts.append(CryptoFact(
            fact_id=f"{crypto.id}_price_{crypto.timestamp}",
            content=price_content,
            crypto_id=crypto.id,
            crypto_symbol=crypto.symbol,
            fact_type="price",
            timestamp=crypto.timestamp,
            metadata={
                "price": crypto.current_price,
                "currency": "USD",
                "source": crypto.source
            }
        ))
        
        return facts
    
    def _extract_change_facts(self, crypto: CryptoData) -> List[CryptoFact]:
        """Extract price change facts."""
        facts = []
        
        change_pct = crypto.price_change_percentage_24h
        change_abs = crypto.price_change_24h
        
        if change_pct != 0:
            direction = "increased" if change_pct > 0 else "decreased"
            change_content = f"{crypto.name} has {direction} by {abs(change_pct):.2f}% (${abs(change_abs):.2f}) in the last 24 hours."
            
            facts.append(CryptoFact(
                fact_id=f"{crypto.id}_change_{crypto.timestamp}",
                content=change_content,
                crypto_id=crypto.id,
                crypto_symbol=crypto.symbol,
                fact_type="change",
                timestamp=crypto.timestamp,
                metadata={
                    "change_percentage": change_pct,
                    "change_absolute": change_abs,
                    "direction": direction,
                    "timeframe": "24h"
                }
            ))
        
        return facts
    
    def _extract_market_facts(self, crypto: CryptoData) -> List[CryptoFact]:
        """Extract market cap and ranking facts."""
        facts = []
        
        if crypto.market_cap > 0:
            market_cap_billions = crypto.market_cap / 1_000_000_000
            
            market_content = f"{crypto.name} has a market capitalization of ${market_cap_billions:.2f} billion USD, ranking #{crypto.market_cap_rank} by market cap."
            
            facts.append(CryptoFact(
                fact_id=f"{crypto.id}_market_{crypto.timestamp}",
                content=market_content,
                crypto_id=crypto.id,
                crypto_symbol=crypto.symbol,
                fact_type="market_cap",
                timestamp=crypto.timestamp,
                metadata={
                    "market_cap": crypto.market_cap,
                    "market_cap_billions": market_cap_billions,
                    "rank": crypto.market_cap_rank
                }
            ))
        
        return facts
    
    def _extract_volume_facts(self, crypto: CryptoData) -> List[CryptoFact]:
        """Extract trading volume facts."""
        facts = []
        
        if crypto.volume_24h > 0:
            volume_millions = crypto.volume_24h / 1_000_000
            
            volume_content = f"{crypto.name} has a 24-hour trading volume of ${volume_millions:.2f} million USD."
            
            facts.append(CryptoFact(
                fact_id=f"{crypto.id}_volume_{crypto.timestamp}",
                content=volume_content,
                crypto_id=crypto.id,
                crypto_symbol=crypto.symbol,
                fact_type="volume",
                timestamp=crypto.timestamp,
                metadata={
                    "volume_24h": crypto.volume_24h,
                    "volume_millions": volume_millions,
                    "timeframe": "24h"
                }
            ))
        
        return facts
    
    def save_facts(self, facts: List[CryptoFact], filename: str = None) -> str:
        """Save facts to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_facts_{timestamp}.json"
        
        from pathlib import Path
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        facts_dict = {
            "timestamp": datetime.now().isoformat(),
            "count": len(facts),
            "facts": [fact.to_dict() for fact in facts]
        }
        
        with open(filepath, 'w') as f:
            json.dump(facts_dict, f, indent=2)
        
        logger.info(f"Saved {len(facts)} facts to {filepath}")
        return str(filepath)