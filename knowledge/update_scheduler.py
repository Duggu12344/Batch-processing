"""Automated scheduler for updating crypto knowledge base."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data_ingestion.fetch_prices import CoinGeckoFetcher
from knowledge.fact_extractor import CryptoFactExtractor
from knowledge.embed_store import CryptoVectorStore
from utils.config import Config
from utils.logger import logger


class CryptoKnowledgeScheduler:
    """Automated scheduler for crypto knowledge updates."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.fetcher = CoinGeckoFetcher()
        self.extractor = CryptoFactExtractor()
        self.vector_store = CryptoVectorStore()
        self.update_interval = Config.UPDATE_INTERVAL_MINUTES
        
        logger.info(f"Scheduler initialized with {self.update_interval} minute intervals")
    
    def update_knowledge_base(self):
        """Update the knowledge base with fresh crypto data."""
        try:
            logger.info("Starting scheduled knowledge base update")
            
            # Fetch fresh data
            crypto_data = self.fetcher.fetch_top_cryptocurrencies()
            
            if not crypto_data:
                logger.error("Failed to fetch crypto data during scheduled update")
                return
            
            # Extract facts
            facts = self.extractor.extract_facts(crypto_data)
            
            # Store in vector database
            added_count = self.vector_store.add_facts(facts)
            
            logger.info(f"Scheduled update completed: {added_count} facts added from {len(crypto_data)} cryptocurrencies")
            
        except Exception as e:
            logger.error(f"Error during scheduled update: {e}")
    
    def start(self):
        """Start the scheduler."""
        # Add the job
        self.scheduler.add_job(
            func=self.update_knowledge_base,
            trigger=IntervalTrigger(minutes=self.update_interval),
            id='crypto_update_job',
            name='Update Crypto Knowledge Base',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        
        # Ensure scheduler shuts down on exit
        atexit.register(lambda: self.scheduler.shutdown())
        
        logger.info(f"Scheduler started - updates every {self.update_interval} minutes")
        
        # Run initial update
        self.update_knowledge_base()
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status."""
        return {
            "running": self.scheduler.running,
            "jobs": len(self.scheduler.get_jobs()),
            "next_run": str(self.scheduler.get_jobs()[0].next_run_time) if self.scheduler.get_jobs() else None,
            "update_interval_minutes": self.update_interval
        }


def main():
    """Test the scheduler functionality."""
    scheduler = CryptoKnowledgeScheduler()
    
    print("🕐 Starting Crypto Knowledge Scheduler")
    print(f"📅 Updates every {scheduler.update_interval} minutes")
    
    try:
        scheduler.start()
        
        # Keep running
        import time
        while True:
            status = scheduler.get_status()
            print(f"⏰ Scheduler running: {status['running']}, Next update: {status['next_run']}")
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        scheduler.stop()
        print("✅ Scheduler stopped")


if __name__ == "__main__":
    main()