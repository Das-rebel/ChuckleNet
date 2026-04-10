#!/usr/bin/env python3
"""
Quick LLM Provider Performance Test - Optimized for Speed

Tests multiple LLM providers in parallel with minimal queries for rapid results.
Focus on finding fastest providers for Alexa use case.
"""

import asyncio
import os
import json
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Try to import required libraries
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import requests
except ImportError:
    requests = None

# Simplified test queries - 2 per type for quick results
TEST_QUERIES = {
    "simple": [
        "What is the capital of France?",
        "Tell me a joke."
    ],
    "alexa": [
        "What's the weather today?",
        "Set a timer for 5 minutes."
    ],
    "technical": [
        "Explain the difference between HTTP and HTTPS.",
        "What is a REST API?"
    ]
}

@dataclass
class TestResult:
    """Result of a single provider test"""
    provider: str
    model: str
    query_type: str
    query: str
    success: bool
    response_time: float
    response_content: str = None
    error: str = None
    tokens_used: int = 0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class QuickLLMTester:
    """Quick testing class for LLM providers"""
    
    def __init__(self):
        self.providers = self._get_providers()
        self.results = []
        
    def _get_providers(self) -> List[Dict[str, Any]]:
        """Get configured providers from environment"""
        providers = []
        
        # Groq
        if os.getenv('GROQ_API_KEY'):
            providers.append({
                "name": "groq",
                "api_key_env": "GROQ_API_KEY",
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.3-70b-versatile"]
            })
        
        # Cerebras
        if os.getenv('CEREBRAS_API_KEY'):
            providers.append({
                "name": "cerebras",
                "api_key_env": "CEREBRAS_API_KEY",
                "base_url": "https://api.cerebras.ai/v1",
                "models": ["llama-3.3-70b", "llama-3.1-8b", "qwen-3-235b-a22b-instruct-2507"]
            })
        
        # OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            providers.append({
                "name": "openrouter",
                "api_key_env": "OPENROUTER_API_KEY",
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["openai/gpt-3.5-turbo"]
            })
        
        # Anthropic (via z.ai)
        if os.getenv('ZAI_API_KEY'):
            providers.append({
                "name": "anthropic",
                "api_key_env": "ZAI_API_KEY",
                "base_url": os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com'),
                "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"]
            })
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            providers.append({
                "name": "openai",
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o-mini"]
            })
        
        # Mistral
        if os.getenv('MISTRAL_API_KEY'):
            providers.append({
                "name": "mistral",
                "api_key_env": "MISTRAL_API_KEY",
                "base_url": "https://api.mistral.ai/v1",
                "models": ["mistral-small-latest"]
            })
        
        return providers
    
    async def test_openai_provider(self, provider: Dict, model: str, query: str, query_type: str) -> TestResult:
        """Test OpenAI-compatible provider"""
        if not openai:
            return TestResult(provider["name"], model, query_type, query, False, 0, error="OpenAI library not installed")
        
        start_time = time.time()
        api_key = os.getenv(provider["api_key_env"])
        
        try:
            client = openai.OpenAI(api_key=api_key, base_url=provider["base_url"])
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": query}],
                max_tokens=200,
                temperature=0.7
            )
            
            return TestResult(
                provider=provider["name"],
                model=model,
                query_type=query_type,
                query=query,
                success=True,
                response_time=time.time() - start_time,
                response_content=response.choices[0].message.content,
                tokens_used=getattr(response.usage, 'total_tokens', 0)
            )
        except Exception as e:
            return TestResult(provider["name"], model, query_type, query, False, time.time() - start_time, error=str(e))
    
    async def test_anthropic_provider(self, provider: Dict, model: str, query: str, query_type: str) -> TestResult:
        """Test Anthropic provider"""
        if not anthropic:
            return TestResult(provider["name"], model, query_type, query, False, 0, error="Anthropic library not installed")
        
        start_time = time.time()
        api_key = os.getenv(provider["api_key_env"])
        
        try:
            client = anthropic.Anthropic(api_key=api_key, base_url=provider["base_url"])
            response = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": query}]
            )
            
            return TestResult(
                provider=provider["name"],
                model=model,
                query_type=query_type,
                query=query,
                success=True,
                response_time=time.time() - start_time,
                response_content=response.content[0].text,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )
        except Exception as e:
            return TestResult(provider["name"], model, query_type, query, False, time.time() - start_time, error=str(e))
    
    async def test_provider_with_fallback(self, provider: Dict, model: str, query: str, query_type: str) -> TestResult:
        """Test provider with model fallback"""
        # Try the requested model first
        result = await self.test_provider(provider, model, query, query_type)
        
        # If first model fails, try alternative models
        if not result.success and len(provider["models"]) > 1:
            for alt_model in provider["models"]:
                if alt_model != model:
                    print(f"   Trying fallback model {alt_model} for {provider['name']}...")
                    alt_result = await self.test_provider(provider, alt_model, query, query_type)
                    if alt_result.success:
                        alt_result.model = alt_model
                        print(f"   ✓ Fallback model {alt_model} worked!")
                        return alt_result
        
        return result
    
    async def test_provider(self, provider: Dict, model: str, query: str, query_type: str) -> TestResult:
        """Route to appropriate test method"""
        if provider["name"] == "anthropic":
            return await self.test_anthropic_provider(provider, model, query, query_type)
        else:
            return await self.test_openai_provider(provider, model, query, query_type)
    
    async def run_tests(self) -> List[TestResult]:
        """Run all tests in parallel"""
        print(f"🚀 Testing {len(self.providers)} providers...")
        
        tasks = []
        for provider in self.providers:
            # Only test the first model to speed things up
            primary_model = provider["models"][0]
            for query_type, queries in TEST_QUERIES.items():
                for query in queries:
                    # Use the version with fallback for better reliability
                    tasks.append(self.test_provider_with_fallback(provider, primary_model, query, query_type))
        
        print(f"📊 Total tests: {len(tasks)}")
        
        # Run with limited concurrency
        semaphore = asyncio.Semaphore(8)
        
        async def run_with_limit(task):
            async with semaphore:
                return await task
        
        self.results = await asyncio.gather(*[run_with_limit(task) for task in tasks])
        return self.results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results"""
        if not self.results:
            return {}
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "providers": {},
            "rankings": {}
        }
        
        # Group by provider
        for provider in [p["name"] for p in self.providers]:
            provider_results = [r for r in self.results if r.provider == provider]
            successful = [r for r in provider_results if r.success]
            failed = [r for r in provider_results if not r.success]
            
            times = [r.response_time for r in successful]
            alexa_times = [r.response_time for r in successful if r.query_type == "alexa"]
            
            analysis["providers"][provider] = {
                "total_tests": len(provider_results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(provider_results) if provider_results else 0,
                "avg_response_time": statistics.mean(times) if times else 0,
                "min_response_time": min(times) if times else 0,
                "max_response_time": max(times) if times else 0,
                "alexa_avg_time": statistics.mean(alexa_times) if alexa_times else 0,
                "total_tokens": sum(r.tokens_used for r in successful)
            }
        
        # Generate rankings
        success_rates = {k: v["success_rate"] for k, v in analysis["providers"].items()}
        avg_times = {k: v["avg_response_time"] for k, v in analysis["providers"].items()}
        alexa_times = {k: v["alexa_avg_time"] for k, v in analysis["providers"].items()}
        
        analysis["rankings"] = {
            "fastest": sorted(avg_times.items(), key=lambda x: x[1]),
            "most_reliable": sorted(success_rates.items(), key=lambda x: x[1], reverse=True),
            "best_for_alexa": sorted(alexa_times.items(), key=lambda x: x[1] if x[1] > 0 else float('inf'))
        }
        
        return analysis
    
    def print_results(self, analysis: Dict[str, Any]):
        """Print formatted results"""
        print("\n" + "=" * 70)
        print("🏆 QUICK LLM PROVIDER PERFORMANCE TEST RESULTS")
        print("=" * 70)
        
        print(f"\n📅 {analysis['timestamp']}")
        print(f"📊 Total Tests: {analysis['total_tests']}")
        
        print("\n" + "=" * 70)
        print("📊 PROVIDER PERFORMANCE")
        print("=" * 70)
        
        for provider, metrics in analysis["providers"].items():
            print(f"\n🚀 {provider.upper()}")
            print(f"   ✅ Success: {metrics['successful']}/{metrics['total_tests']} ({metrics['success_rate']*100:.0f}%)")
            print(f"   ⏱️  Avg Time: {metrics['avg_response_time']:.3f}s")
            print(f"   🏠 Alexa: {metrics['alexa_avg_time']:.3f}s" if metrics['alexa_avg_time'] > 0 else "   🏠 Alexa: N/A")
            print(f"   📏  Range: {metrics['min_response_time']:.3f}s - {metrics['max_response_time']:.3f}s")
        
        print("\n" + "=" * 70)
        print("🏅 RANKINGS")
        print("=" * 70)
        
        print("\n⚡ FASTEST OVERALL:")
        for i, (provider, time) in enumerate(analysis["rankings"]["fastest"], 1):
            if time > 0:
                print(f"   {i}. {provider}: {time:.3f}s")
        
        print("\n✅ MOST RELIABLE:")
        for i, (provider, rate) in enumerate(analysis["rankings"]["most_reliable"], 1):
            print(f"   {i}. {provider}: {rate*100:.0f}% success rate")
        
        print("\n🎯 BEST FOR ALEXA:")
        alexa_rankings = [x for x in analysis["rankings"]["best_for_alexa"] if x[1] > 0]
        for i, (provider, time) in enumerate(alexa_rankings, 1):
            print(f"   {i}. {provider}: {time:.3f}s")
        
        print("\n" + "=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        
        if analysis["rankings"]["fastest"] and analysis["rankings"]["fastest"][0][1] > 0:
            fastest_provider = analysis["rankings"]["fastest"][0][0]
            print(f"\n🚀 FOR SPEED: {fastest_provider}")
        
        if analysis["rankings"]["most_reliable"] and analysis["rankings"]["most_reliable"][0][1] > 0:
            reliable_provider = analysis["rankings"]["most_reliable"][0][0]
            print(f"✅ FOR RELIABILITY: {reliable_provider}")
        
        if alexa_rankings:
            best_alexa = alexa_rankings[0][0]
            print(f"🎯 FOR ALEXA: {best_alexa}")
        
        print("\n" + "=" * 70)
    
    def save_results(self, analysis: Dict[str, Any]):
        """Save results to JSON"""
        output = {
            "analysis": analysis,
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        filepath = "/Users/Subho/quick_llm_performance_results.json"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filepath}")

async def main():
    """Main execution"""
    print("⚡ QUICK LLM PROVIDER PERFORMANCE TEST")
    print("=" * 70)
    
    tester = QuickLLMTester()
    
    if not tester.providers:
        print("❌ No providers configured!")
        return
    
    print(f"🔍 Found {len(tester.providers)} providers")
    
    # Run tests
    print("\n🚀 Starting tests...")
    await tester.run_tests()
    
    # Analyze
    analysis = tester.analyze_results()
    
    # Print results
    tester.print_results(analysis)
    
    # Save results
    tester.save_results(analysis)
    
    print("\n✅ Quick test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()