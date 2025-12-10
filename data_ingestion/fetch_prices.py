"""Cryptocurrency price data fetcher using CoinGecko API."""

import requests
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.config import Config
from utils.logger import logger


@dataclass
class CryptoData:
    """Data class for cryptocurrency information."""
    id: str
    symbol: str
    name: str
    current_price: float
    market_cap: int
    market_cap_rank: int
    price_change_24h: float
    price_change_percentage_24h: float
    volume_24h: float
    timestamp: str
    source: str = "coingecko"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class CoinGeckoFetcher:
    """Fetches cryptocurrency data from CoinGecko API."""
    
    def __init__(self):
        self.base_url = Config.COINGECKO_BASE_URL
        self.api_key = Config.COINGECKO_API_KEY
        self.timeout = Config.REQUEST_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        self.retry_delay = Config.RETRY_DELAY
        
        # Setup session with headers
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"x-cg-demo-api-key": self.api_key})
        
        logger.info("CoinGecko fetcher initialized")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making request to {url}, attempt {attempt + 1}")
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        logger.error(f"Failed to fetch data after {self.max_retries} attempts")
        return None
    
    def fetch_top_cryptocurrencies(self, limit: int = None) -> List[CryptoData]:
        """Fetch top cryptocurrencies by market cap."""
        if limit is None:
            limit = Config.MAX_CRYPTO_COINS
            
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        
        logger.info(f"Fetching top {limit} cryptocurrencies")
        data = self._make_request("coins/markets", params)
        
        if not data:
            logger.error("Failed to fetch cryptocurrency data")
            return []
        
        crypto_list = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for coin in data:
            try:
                crypto_data = CryptoData(
                    id=coin["id"],
                    symbol=coin["symbol"].upper(),
                    name=coin["name"],
                    current_price=float(coin["current_price"] or 0),
                    market_cap=int(coin["market_cap"] or 0),
                    market_cap_rank=int(coin["market_cap_rank"] or 0),
                    price_change_24h=float(coin["price_change_24h"] or 0),
                    price_change_percentage_24h=float(coin["price_change_percentage_24h"] or 0),
                    volume_24h=float(coin["total_volume"] or 0),
                    timestamp=timestamp
                )
                crypto_list.append(crypto_data)
                
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"Error parsing coin data for {coin.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(crypto_list)} cryptocurrencies")
        return crypto_list
    
    def fetch_specific_coins(self, coin_ids: List[str]) -> List[CryptoData]:
        """Fetch data for specific cryptocurrency IDs."""
        if not coin_ids:
            return []
            
        params = {
            "ids": ",".join(coin_ids),
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        
        logger.info(f"Fetching data for coins: {coin_ids}")
        data = self._make_request("coins/markets", params)
        
        if not data:
            return []
        
        crypto_list = []
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for coin in data:
            try:
                crypto_data = CryptoData(
                    id=coin["id"],
                    symbol=coin["symbol"].upper(),
                    name=coin["name"],
                    current_price=float(coin["current_price"] or 0),
                    market_cap=int(coin["market_cap"] or 0),
                    market_cap_rank=int(coin["market_cap_rank"] or 0),
                    price_change_24h=float(coin["price_change_24h"] or 0),
                    price_change_percentage_24h=float(coin["price_change_percentage_24h"] or 0),
                    volume_24h=float(coin["total_volume"] or 0),
                    timestamp=timestamp
                )
                crypto_list.append(crypto_data)
                
            except (KeyError, TypeError, ValueError) as e:
                logger.warning(f"Error parsing coin data: {e}")
                continue
        
        return crypto_list
    
    def save_data(self, crypto_data: List[CryptoData], filename: str = None) -> str:
        """Save cryptocurrency data to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_data_{timestamp}.json"
        
        # Create data directory if it doesn't exist
        from pathlib import Path
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        filepath = data_dir / filename
        
        # Convert to serializable format
        data_dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(crypto_data),
            "data": [crypto.to_dict() for crypto in crypto_data]
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data_dict, f, indent=2)
            
            logger.info(f"Saved {len(crypto_data)} records to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise


def main():
    """Main function for testing the fetcher."""
    logger.info("Starting cryptocurrency data fetch")
    
    fetcher = CoinGeckoFetcher()
    
    # Fetch top cryptocurrencies
    crypto_data = fetcher.fetch_top_cryptocurrencies()
    
    if crypto_data:
        # Save data
        filepath = fetcher.save_data(crypto_data)
        
        # Display summary
        print(f"\n✅ Successfully fetched {len(crypto_data)} cryptocurrencies")
        print(f"📁 Data saved to: {filepath}")
        print("\n📊 Top 5 by Market Cap:")
        for i, crypto in enumerate(crypto_data[:5], 1):
            change_emoji = "📈" if crypto.price_change_percentage_24h > 0 else "📉"
            print(f"{i}. {crypto.name} ({crypto.symbol})")
            print(f"   💰 ${crypto.current_price:,.2f}")
            print(f"   {change_emoji} {crypto.price_change_percentage_24h:+.2f}% (24h)")
            print()
    else:
        print("❌ Failed to fetch cryptocurrency data")


if __name__ == "__main__":
    main()