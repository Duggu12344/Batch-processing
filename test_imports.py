"""Test script to verify all imports work correctly."""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test all module imports."""
    print("🧪 Testing module imports...")
    
    try:
        # Test utils
        from utils.config import Config
        from utils.logger import logger
        print("✅ Utils imports successful")
        
        # Test data ingestion
        from data_ingestion.fetch_prices import CoinGeckoFetcher, CryptoData
        print("✅ Data ingestion imports successful")
        
        # Test knowledge processing
        from knowledge.fact_extractor import CryptoFactExtractor, CryptoFact
        from knowledge.embed_store import CryptoVectorStore
        print("✅ Knowledge processing imports successful")
        
        # Test RAG pipeline
        from rag_pipeline.retriever import CryptoRetriever
        from rag_pipeline.answer_generator import CryptoAnswerGenerator
        print("✅ RAG pipeline imports successful")
        
        # Test evaluation
        from evaluation.compare_models import CryptoEvaluator
        print("✅ Evaluation imports successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ System ready to run!")
    else:
        print("\n❌ Fix import issues before proceeding")
        sys.exit(1)