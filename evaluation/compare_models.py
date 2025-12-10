"""Evaluation framework for comparing RAG vs non-RAG performance."""

import json
import time
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Try LangChain first, fallback to original
try:
    from rag_pipeline.langchain_generator import LangChainCryptoGenerator as CryptoAnswerGenerator
    USING_LANGCHAIN = True
except ImportError:
    from rag_pipeline.answer_generator import CryptoAnswerGenerator
    USING_LANGCHAIN = False
from utils.logger import logger


@dataclass
class EvaluationMetric:
    """Single evaluation metric result."""
    query: str
    rag_answer: str
    no_rag_answer: str
    rag_time: float
    no_rag_time: float
    facts_used: int
    timestamp: str


class CryptoEvaluator:
    """Evaluates RAG vs non-RAG performance."""
    
    def __init__(self):
        self.generator = CryptoAnswerGenerator()
        self.test_queries = [
            "What is the current price of Bitcoin?",
            "Which cryptocurrency has increased the most in the last 24 hours?",
            "Compare Ethereum and Bitcoin market caps",
            "What is the trading volume of Solana?",
            "How has Cardano performed recently?",
            "Which are the top 3 cryptocurrencies by market cap?",
            "What is the price change of Polygon in the last day?",
            "Tell me about Chainlink's market position"
        ]
        logger.info("Crypto evaluator initialized")
    
    def run_evaluation(self, custom_queries: List[str] = None) -> List[EvaluationMetric]:
        """Run comprehensive evaluation."""
        queries = custom_queries or self.test_queries
        results = []
        
        logger.info(f"Starting evaluation with {len(queries)} queries")
        
        for i, query in enumerate(queries, 1):
            logger.info(f"Evaluating query {i}/{len(queries)}: {query}")
            
            try:
                # Get comparison results
                comparison = self.generator.compare_answers(query)
                
                # Create evaluation metric
                metric = EvaluationMetric(
                    query=query,
                    rag_answer=comparison["rag_answer"]["answer"],
                    no_rag_answer=comparison["no_rag_answer"]["answer"],
                    rag_time=comparison["performance"]["rag_total_time"],
                    no_rag_time=comparison["performance"]["no_rag_total_time"],
                    facts_used=comparison["performance"]["facts_retrieved"],
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(metric)
                
            except Exception as e:
                logger.error(f"Error evaluating query '{query}': {e}")
                continue
        
        logger.info(f"Evaluation completed. {len(results)} successful evaluations")
        return results 
   
    def analyze_results(self, results: List[EvaluationMetric]) -> Dict[str, Any]:
        """Analyze evaluation results and generate metrics."""
        if not results:
            return {"error": "No results to analyze"}
        
        # Performance metrics
        avg_rag_time = sum(r.rag_time for r in results) / len(results)
        avg_no_rag_time = sum(r.no_rag_time for r in results) / len(results)
        avg_facts_used = sum(r.facts_used for r in results) / len(results)
        
        # Speed comparison
        rag_faster_count = sum(1 for r in results if r.rag_time < r.no_rag_time)
        
        # Answer length analysis
        avg_rag_length = sum(len(r.rag_answer.split()) for r in results) / len(results)
        avg_no_rag_length = sum(len(r.no_rag_answer.split()) for r in results) / len(results)
        
        analysis = {
            "total_queries": len(results),
            "performance": {
                "avg_rag_time": avg_rag_time,
                "avg_no_rag_time": avg_no_rag_time,
                "time_difference": avg_rag_time - avg_no_rag_time,
                "rag_faster_percentage": (rag_faster_count / len(results)) * 100
            },
            "content": {
                "avg_facts_used": avg_facts_used,
                "avg_rag_answer_length": avg_rag_length,
                "avg_no_rag_answer_length": avg_no_rag_length,
                "length_difference": avg_rag_length - avg_no_rag_length
            },
            "queries_with_facts": sum(1 for r in results if r.facts_used > 0),
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    def save_results(self, results: List[EvaluationMetric], analysis: Dict[str, Any], 
                    filename: str = None) -> str:
        """Save evaluation results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_results_{timestamp}.json"
        
        from pathlib import Path
        eval_dir = Path("evaluation_results")
        eval_dir.mkdir(exist_ok=True)
        
        filepath = eval_dir / filename
        
        output_data = {
            "analysis": analysis,
            "detailed_results": [asdict(result) for result in results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Saved evaluation results to {filepath}")
        return str(filepath)
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Print evaluation summary."""
        print("\n" + "="*60)
        print("🧪 EVALUATION SUMMARY")
        print("="*60)
        
        perf = analysis["performance"]
        content = analysis["content"]
        
        print(f"📊 Total Queries Evaluated: {analysis['total_queries']}")
        print(f"📈 Queries with Retrieved Facts: {analysis['queries_with_facts']}")
        
        print(f"\n⏱️  PERFORMANCE METRICS:")
        print(f"   • Average RAG Time: {perf['avg_rag_time']:.3f}s")
        print(f"   • Average No-RAG Time: {perf['avg_no_rag_time']:.3f}s")
        print(f"   • Time Difference: {perf['time_difference']:+.3f}s")
        print(f"   • RAG Faster: {perf['rag_faster_percentage']:.1f}% of queries")
        
        print(f"\n📝 CONTENT METRICS:")
        print(f"   • Average Facts Used: {content['avg_facts_used']:.1f}")
        print(f"   • RAG Answer Length: {content['avg_rag_answer_length']:.1f} words")
        print(f"   • No-RAG Answer Length: {content['avg_no_rag_answer_length']:.1f} words")
        print(f"   • Length Difference: {content['length_difference']:+.1f} words")


def main():
    """Run evaluation and display results."""
    evaluator = CryptoEvaluator()
    
    print("🚀 Starting Crypto Knowledge System Evaluation")
    print("This will compare RAG-enhanced vs standard LLM responses")
    
    # Run evaluation
    results = evaluator.run_evaluation()
    
    if not results:
        print("❌ No evaluation results generated")
        return
    
    # Analyze results
    analysis = evaluator.analyze_results(results)
    
    # Print summary
    evaluator.print_summary(analysis)
    
    # Save results
    filepath = evaluator.save_results(results, analysis)
    print(f"\n💾 Detailed results saved to: {filepath}")
    
    # Show sample comparison
    if results:
        print(f"\n📋 SAMPLE COMPARISON:")
        print(f"Query: {results[0].query}")
        print(f"\n🤖 RAG Answer ({results[0].facts_used} facts, {results[0].rag_time:.2f}s):")
        print(f"   {results[0].rag_answer[:200]}...")
        print(f"\n🧠 No-RAG Answer ({results[0].no_rag_time:.2f}s):")
        print(f"   {results[0].no_rag_answer[:200]}...")


if __name__ == "__main__":
    main()