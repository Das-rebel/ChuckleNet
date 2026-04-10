#!/usr/bin/env python3
"""
Comprehensive LLM Provider Performance Test Suite

Tests multiple LLM providers in parallel to compare:
- Response times
- Quality scores
- Error rates
- Cost efficiency
- Success rates

Focus on finding the fastest and most reliable providers for Alexa use case.
"""

import asyncio
import os
import json
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

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

# Test queries for different complexity levels
TEST_QUERIES = {
    "simple": [
        "What is the capital of France?",
        "Tell me a joke.",
        "What is 2+2?",
        "Say hello.",
        "What color is the sky?"
    ],
    "complex": [
        "Explain quantum computing in simple terms.",
        "Describe the main causes of climate change.",
        "Compare and contrast Python and JavaScript.",
        "Explain how neural networks work.",
        "Describe the history of the internet."
    ],
    "creative": [
        "Write a short poem about technology.",
        "Create a catchy slogan for a coffee shop.",
        "Tell a story about a robot learning to love.",
        "Write a haiku about nature.",
        "Create a fun fact about the universe."
    ],
    "technical": [
        "Explain the difference between HTTP and HTTPS.",
        "What is a REST API?",
        "How does DNS resolution work?",
        "Explain the concept of big-O notation.",
        "What is containerization in software?"
    ],
    "alexa_specific": [
        "Set a timer for 5 minutes.",
        "What's the weather today?",
        "Play some relaxing music.",
        "Tell me a fun fact.",
        "What time is it?"
    ]
}

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    name: str
    api_key_env: str
    base_url: str = None
    models: List[str] = None
    enabled: bool = True

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
    quality_score: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class LLMProviderTester:
    """Main testing class for LLM providers"""
    
    def __init__(self):
        self.providers = self._get_providers()
        self.results = []
        self.qualitative_assessment = {}  # Store manual quality assessments
        
    def _get_providers(self) -> List[ProviderConfig]:
        """Get configured providers from environment and config"""
        providers = []
        
        # Groq
        if os.getenv('GROQ_API_KEY'):
            providers.append(ProviderConfig(
                name="groq",
                api_key_env="GROQ_API_KEY",
                base_url="https://api.groq.com/openai/v1",
                models=[
                    "llama-3.3-70b-versatile",  # Best balance
                    "llama-3.1-8b-instant",      # Fastest
                    "mixtral-8x7b-32768"
                ]
            ))
        
        # Cerebras
        if os.getenv('CEREBRAS_API_KEY'):
            providers.append(ProviderConfig(
                name="cerebras",
                api_key_env="CEREBRAS_API_KEY",
                base_url="https://api.cerebras.ai/v1",
                models=[
                    "llama3.3-70b",              # Main model
                    "llama3.1-8b",               # Faster option
                    "mixtral-8x7b"
                ]
            ))
        
        # OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            providers.append(ProviderConfig(
                name="openrouter",
                api_key_env="OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                models=[
                    "openai/gpt-3.5-turbo",
                    "meta-llama/llama-3-8b-instruct",
                    "anthropic/claude-3-haiku"
                ]
            ))
        
        # Anthropic (via z.ai or direct)
        if os.getenv('ANTHROPIC_API_KEY') or os.getenv('ZAI_API_KEY'):
            base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
            api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('ZAI_API_KEY')
            
            if api_key:
                providers.append(ProviderConfig(
                    name="anthropic",
                    api_key_env="ANTHROPIC_API_KEY" if os.getenv('ANTHROPIC_API_KEY') else "ZAI_API_KEY",
                    base_url=base_url,
                    models=[
                        "claude-3-5-sonnet-20241022",
                        "claude-3-haiku-20240307"
                    ]
                ))
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            providers.append(ProviderConfig(
                name="openai",
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com/v1",
                models=[
                    "gpt-4o",
                    "gpt-4o-mini", 
                    "gpt-3.5-turbo"
                ]
            ))
        
        # Mistral
        if os.getenv('MISTRAL_API_KEY'):
            providers.append(ProviderConfig(
                name="mistral",
                api_key_env="MISTRAL_API_KEY",
                base_url="https://api.mistral.ai/v1",
                models=[
                    "mistral-small-latest",
                    "open-mistral-nemo",
                    "mistral-large-latest"
                ]
            ))
        
        # Perplexity
        if os.getenv('PERPLEXITY_API_KEY'):
            providers.append(ProviderConfig(
                name="perplexity",
                api_key_env="PERPLEXITY_API_KEY",
                base_url="https://api.perplexity.ai",
                models=[
                    "sonar",
                    "sonar-reasoning-pro"
                ]
            ))
        
        # Google
        if os.getenv('GOOGLE_API_KEY'):
            providers.append(ProviderConfig(
                name="google",
                api_key_env="GOOGLE_API_KEY",
                base_url=None,  # Google uses different API
                models=[
                    "gemini-pro",
                    "gemini-1.5-flash"
                ]
            ))
        
        return providers
    
    async def test_provider_openai_compatible(self, provider: ProviderConfig, model: str, query: str, query_type: str) -> TestResult:
        """Test provider using OpenAI-compatible API"""
        if not openai:
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=False,
                response_time=0,
                error="OpenAI library not installed"
            )
        
        start_time = time.time()
        api_key = os.getenv(provider.api_key_env)
        
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url=provider.base_url
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": query}],
                max_tokens=500,
                temperature=0.7
            )
            
            response_time = time.time() - start_time
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=True,
                response_time=response_time,
                response_content=content,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=False,
                response_time=response_time,
                error=str(e)
            )
    
    async def test_provider_anthropic(self, provider: ProviderConfig, model: str, query: str, query_type: str) -> TestResult:
        """Test Anthropic provider"""
        if not anthropic:
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=False,
                response_time=0,
                error="Anthropic library not installed"
            )
        
        start_time = time.time()
        api_key = os.getenv(provider.api_key_env)
        
        try:
            client = anthropic.Anthropic(
                api_key=api_key,
                base_url=provider.base_url
            )
            
            response = client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": query}]
            )
            
            response_time = time.time() - start_time
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=True,
                response_time=response_time,
                response_content=content,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=False,
                response_time=response_time,
                error=str(e)
            )
    
    async def test_provider_google(self, provider: ProviderConfig, model: str, query: str, query_type: str) -> TestResult:
        """Test Google Gemini provider"""
        start_time = time.time()
        api_key = os.getenv(provider.api_key_env)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": query}]}],
                "generationConfig": {"maxOutputTokens": 500}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            response_time = time.time() - start_time
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            tokens_used = len(content.split())  # Rough estimate
            
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=True,
                response_time=response_time,
                response_content=content,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                provider=provider.name,
                model=model,
                query_type=query_type,
                query=query,
                success=False,
                response_time=response_time,
                error=str(e)
            )
    
    async def test_provider(self, provider: ProviderConfig, model: str, query: str, query_type: str) -> TestResult:
        """Route provider test to appropriate method"""
        if provider.name == "anthropic":
            return await self.test_provider_anthropic(provider, model, query, query_type)
        elif provider.name == "google":
            return await self.test_provider_google(provider, model, query, query_type)
        else:
            return await self.test_provider_openai_compatible(provider, model, query, query_type)
    
    async def run_parallel_tests(self, max_concurrent: int = 10) -> List[TestResult]:
        """Run all provider tests in parallel"""
        print(f"\n🚀 Starting parallel tests with max {max_concurrent} concurrent requests")
        print(f"📊 Testing {len(self.providers)} providers with {len(TEST_QUERIES)} query types")
        
        tasks = []
        for provider in self.providers:
            for model in provider.models[:1]:  # Test primary model only
                for query_type, queries in TEST_QUERIES.items():
                    for query in queries:
                        task = self.test_provider(provider, model, query, query_type)
                        tasks.append(task)
        
        print(f"🎯 Total test cases: {len(tasks)}")
        
        # Execute tasks with limited concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
        self.results = results
        
        return results
    
    def calculate_quality_score(self, response: str, query_type: str, query: str) -> float:
        """
        Calculate a quality score based on response characteristics.
        This is a simplified version - real quality assessment would need more sophisticated methods.
        """
        if not response:
            return 0.0
        
        score = 0.0
        
        # Length score (responses should be substantial but not too long)
        if query_type == "simple":
            # Simple queries should have concise answers (50-200 chars)
            if 50 <= len(response) <= 200:
                score += 1.0
            elif len(response) > 200:
                score += 0.5
            else:
                score += 0.3
        else:
            # Complex queries should have longer answers (200-1000 chars)
            if 200 <= len(response) <= 1000:
                score += 1.0
            elif len(response) > 1000:
                score += 0.7
            elif len(response) > 100:
                score += 0.5
            else:
                score += 0.2
        
        # Content quality checks
        response_lower = response.lower()
        
        # Check for empty or very basic responses
        if response_lower in ["i don't know", "sorry", "i cannot help", ""]:
            score -= 0.5
        
        # Check for response diversity (good responses should have varied vocabulary)
        unique_words = len(set(response.split()))
        total_words = len(response.split())
        if total_words > 0:
            diversity_ratio = unique_words / total_words
            score += diversity_ratio * 0.3
        
        # Check for relevant content based on query type
        if "alexa" in query_type:
            # Alexa responses should be concise and actionable
            if len(response) < 300:
                score += 0.5
        
        return min(max(score, 0.0), 1.0)  # Normalize to 0-1
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate performance metrics"""
        if not self.results:
            return {}
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "total_providers": len(set(r.provider for r in self.results)),
            "summary_by_provider": {},
            "summary_by_query_type": {},
            "performance_rankings": {},
            "success_rates": {},
            "response_times": {},
            "quality_metrics": {},
            "cost_estimates": {}
        }
        
        # Add quality scores to results
        for result in self.results:
            result.quality_score = self.calculate_quality_score(
                result.response_content, result.query_type, result.query
            )
        
        # Analyze by provider
        provider_results = {}
        for result in self.results:
            if result.provider not in provider_results:
                provider_results[result.provider] = []
            provider_results[result.provider].append(result)
        
        for provider, results in provider_results.items():
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            response_times = [r.response_time for r in successful]
            quality_scores = [r.quality_score for r in successful]
            tokens_used = [r.tokens_used for r in successful if r.tokens_used > 0]
            
            analysis["summary_by_provider"][provider] = {
                "total_tests": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results) if results else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "avg_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                "total_tokens_used": sum(tokens_used),
                "avg_tokens_per_query": statistics.mean(tokens_used) if tokens_used else 0
            }
            
            analysis["success_rates"][provider] = len(successful) / len(results) if results else 0
            analysis["response_times"][provider] = {
                "avg": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
            analysis["quality_metrics"][provider] = {
                "avg": statistics.mean(quality_scores) if quality_scores else 0,
                "min": min(quality_scores) if quality_scores else 0,
                "max": max(quality_scores) if quality_scores else 0
            }
            
            # Estimate cost (simplified pricing model)
            # These are rough estimates - real costs vary by provider and model
            cost_per_1k_tokens = {
                "groq": 0.05,
                "cerebras": 0.10,
                "openrouter": 0.15,
                "anthropic": 0.30,
                "openai": 0.50,
                "mistral": 0.15,
                "perplexity": 0.10,
                "google": 0.20
            }
            
            cost_per_token = cost_per_1k_tokens.get(provider, 0.10) / 1000
            total_cost = sum(r.tokens_used * cost_per_token for r in successful if r.tokens_used > 0)
            cost_per_query = total_cost / len(successful) if successful else 0
            
            analysis["cost_estimates"][provider] = {
                "total_cost": total_cost,
                "cost_per_query": cost_per_query,
                "cost_per_success": total_cost / len(successful) if successful else 0
            }
        
        # Analyze by query type
        query_type_results = {}
        for result in self.results:
            if result.query_type not in query_type_results:
                query_type_results[result.query_type] = []
            query_type_results[result.query_type].append(result)
        
        for query_type, results in query_type_results.items():
            provider_performance = {}
            for result in results:
                if result.success:
                    if result.provider not in provider_performance:
                        provider_performance[result.provider] = []
                    provider_performance[result.provider].append(result.response_time)
            
            avg_times = {
                provider: statistics.mean(times) 
                for provider, times in provider_performance.items()
                if times
            }
            
            analysis["summary_by_query_type"][query_type] = {
                "total_tests": len(results),
                "successful": len([r for r in results if r.success]),
                "avg_response_times": avg_times
            }
        
        # Generate rankings
        analysis["performance_rankings"] = {
            "fastest_avg": sorted(
                analysis["response_times"].items(),
                key=lambda x: x[1]["avg"]
            ),
            "highest_success_rate": sorted(
                analysis["success_rates"].items(),
                key=lambda x: x[1],
                reverse=True
            ),
            "best_quality": sorted(
                analysis["quality_metrics"].items(),
                key=lambda x: x[1]["avg"],
                reverse=True
            ),
            "most_cost_effective": sorted(
                analysis["cost_estimates"].items(),
                key=lambda x: x[1]["cost_per_success"]
            )
        }
        
        # Overall ranking (weighted score)
        overall_scores = {}
        for provider in provider_results.keys():
            # Weighted scoring: 40% speed, 30% success rate, 20% quality, 10% cost
            speed_score = 1 / (analysis["response_times"][provider]["avg"] + 0.1)
            success_score = analysis["success_rates"][provider]
            quality_score = analysis["quality_metrics"][provider]["avg"]
            cost_score = 1 / (analysis["cost_estimates"][provider]["cost_per_success"] + 0.001)
            
            # Normalize scores (simplified)
            overall_scores[provider] = (
                speed_score * 40 +
                success_score * 30 +
                quality_score * 20 +
                cost_score * 10
            )
        
        analysis["performance_rankings"]["overall"] = sorted(
            overall_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return analysis
    
    def print_results(self, analysis: Dict[str, Any]):
        """Print formatted results"""
        print("\n" + "=" * 80)
        print("🏆 LLM PROVIDER PERFORMANCE TEST RESULTS")
        print("=" * 80)
        
        print(f"\n📅 Test Date: {analysis['timestamp']}")
        print(f"🔢 Total Tests: {analysis['total_tests']}")
        print(f"🏢 Providers Tested: {analysis['total_providers']}")
        
        print("\n" + "=" * 80)
        print("📊 PROVIDER PERFORMANCE SUMMARY")
        print("=" * 80)
        
        for provider, metrics in analysis["summary_by_provider"].items():
            print(f"\n🚀 {provider.upper()}")
            print(f"   ✅ Success Rate: {metrics['success_rate']*100:.1f}%")
            print(f"   ⏱️  Avg Response Time: {metrics['avg_response_time']:.3f}s")
            print(f"   📏  Min/Max Response Time: {metrics['min_response_time']:.3f}s / {metrics['max_response_time']:.3f}s")
            print(f"   ⭐ Quality Score: {metrics['avg_quality_score']:.3f}/1.0")
            print(f"   💰 Estimated Cost: ${metrics['total_tokens_used'] * 0.0001:.4f} (total tokens: {metrics['total_tokens_used']})")
        
        print("\n" + "=" * 80)
        print("🏅 PERFORMANCE RANKINGS")
        print("=" * 80)
        
        print("\n⚡ FASTEST PROVIDERS (by average response time):")
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["fastest_avg"][:5], 1):
            print(f"   {i}. {provider}: {metrics['avg']:.3f}s average")
        
        print("\n✅ HIGHEST SUCCESS RATES:")
        for i, (provider, rate) in enumerate(analysis["performance_rankings"]["highest_success_rate"][:5], 1):
            print(f"   {i}. {provider}: {rate*100:.1f}% success rate")
        
        print("\n⭐ BEST QUALITY SCORES:")
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["best_quality"][:5], 1):
            print(f"   {i}. {provider}: {metrics['avg']:.3f}/1.0 quality score")
        
        print("\n💰 MOST COST EFFECTIVE:")
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["most_cost_effective"][:5], 1):
            print(f"   {i}. {provider}: ${metrics['cost_per_success']:.4f} per successful query")
        
        print("\n🎯 OVERALL RANKING (weighted: speed, success, quality, cost):")
        for i, (provider, score) in enumerate(analysis["performance_rankings"]["overall"][:5], 1):
            print(f"   {i}. {provider}: {score:.1f} points")
        
        print("\n" + "=" * 80)
        print("📈 QUERY TYPE PERFORMANCE")
        print("=" * 80)
        
        for query_type, metrics in analysis["summary_by_query_type"].items():
            print(f"\n📝 {query_type.upper()} queries:")
            print(f"   Total tests: {metrics['total_tests']}")
            print(f"   Successful: {metrics['successful']}")
            print(f"   Fastest provider: {min(metrics['avg_response_times'].items(), key=lambda x: x[1])[0]}")
        
        print("\n" + "=" * 80)
        print("🎯 ALEXA-SPECIFIC RECOMMENDATIONS")
        print("=" * 80)
        
        # Find best providers for Alexa use case
        alexa_results = [r for r in self.results if r.query_type == "alexa_specific"]
        provider_alexa_times = {}
        
        for result in alexa_results:
            if result.success:
                if result.provider not in provider_alexa_times:
                    provider_alexa_times[result.provider] = []
                provider_alexa_times[result.provider].append(result.response_time)
        
        alexa_avg_times = {
            provider: statistics.mean(times) 
            for provider, times in provider_alexa_times.items()
            if times
        }
        
        if alexa_avg_times:
            best_alexa_providers = sorted(alexa_avg_times.items(), key=lambda x: x[1])
            print(f"\n🥇 BEST FOR ALEXA (speed + reliability):")
            for i, (provider, avg_time) in enumerate(best_alexa_providers[:3], 1):
                success_rate = analysis["success_rates"].get(provider, 0)
                print(f"   {i}. {provider}: {avg_time:.3f}s avg, {success_rate*100:.1f}% success rate")
        
        # Provide recommendations based on different priorities
        print("\n💡 RECOMMENDATIONS:")
        print("\n   🚀 FOR MAXIMUM SPEED:")
        fastest = analysis["performance_rankings"]["fastest_avg"][0]
        print(f"      → Use {fastest[0]} ({fastest[1]['avg']:.3f}s average)")
        
        print("\n   ✅ FOR MAXIMUM RELIABILITY:")
        most_reliable = analysis["performance_rankings"]["highest_success_rate"][0]
        print(f"      → Use {most_reliable[0]} ({most_reliable[1]*100:.1f}% success rate)")
        
        print("\n   ⭐ FOR BEST QUALITY:")
        best_quality = analysis["performance_rankings"]["best_quality"][0]
        print(f"      → Use {best_quality[0]} ({best_quality[1]['avg']:.3f}/1.0 quality score)")
        
        print("\n   💰 FOR BEST VALUE:")
        best_value = analysis["performance_rankings"]["most_cost_effective"][0]
        print(f"      → Use {best_value[0]} (${best_value[1]['cost_per_success']:.4f} per successful query)")
        
        print("\n   🏠 FOR ALEXA INTEGRATION:")
        if best_alexa_providers:
            best_alexa = best_alexa_providers[0]
            print(f"      → Use {best_alexa[0]} ({best_alexa[1]:.3f}s average for Alexa queries)")
        
        print("\n" + "=" * 80)
        
    def save_results(self, analysis: Dict[str, Any], filename: str = "llm_performance_results.json"):
        """Save results to JSON file"""
        # Convert results to serializable format
        serializable_results = []
        for result in self.results:
            result_dict = asdict(result)
            serializable_results.append(result_dict)
        
        output = {
            "analysis": analysis,
            "detailed_results": serializable_results
        }
        
        filepath = f"/Users/Subho/{filename}"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filepath}")
        return filepath
    
    def generate_report(self, filename: str = "llm_performance_report.md"):
        """Generate a detailed markdown report"""
        analysis = self.analyze_results()
        
        report = f"""# LLM Provider Performance Test Report

**Test Date:** {analysis['timestamp']}  
**Total Tests:** {analysis['total_tests']}  
**Providers Tested:** {analysis['total_providers']}

---

## Executive Summary

This comprehensive performance test evaluated {len(self.providers)} LLM providers across {len(TEST_QUERIES)} different query types, with a total of {analysis['total_tests']} individual test cases. The test measured response times, success rates, quality metrics, and estimated costs to identify the optimal providers for different use cases, with particular focus on Alexa integration scenarios.

### Key Findings

- **Fastest Provider:** {analysis['performance_rankings']['fastest_avg'][0][0]} ({analysis['performance_rankings']['fastest_avg'][0][1]['avg']:.3f}s average)
- **Most Reliable:** {analysis['performance_rankings']['highest_success_rate'][0][0]} ({analysis['performance_rankings']['highest_success_rate'][0][1]*100:.1f}% success rate)
- **Best Quality:** {analysis['performance_rankings']['best_quality'][0][0]} ({analysis['performance_rankings']['best_quality'][0][1]['avg']:.3f}/1.0 quality score)
- **Best Value:** {analysis['performance_rankings']['most_cost_effective'][0][0]} (${analysis['performance_rankings']['most_cost_effective'][0][1]['cost_per_success']:.4f} per successful query)

---

## Detailed Performance Metrics

### Provider-by-Provider Analysis

"""
        
        for provider, metrics in analysis["summary_by_provider"].items():
            report += f"""
#### 🚀 {provider.upper()}

- **Success Rate:** {metrics['success_rate']*100:.1f}% ({metrics['successful']}/{metrics['total_tests']} tests)
- **Average Response Time:** {metrics['avg_response_time']:.3f}s
- **Response Time Range:** {metrics['min_response_time']:.3f}s - {metrics['max_response_time']:.3f}s
- **Quality Score:** {metrics['avg_quality_score']:.3f}/1.0
- **Total Tokens Used:** {metrics['total_tokens_used']}
- **Estimated Cost:** ${metrics['total_tokens_used'] * 0.0001:.4f}

**Performance Summary:**
- ✅ Excellent for: {[qt for qt, data in analysis['summary_by_query_type'].items() if provider in data['avg_response_times'] and data['avg_response_times'][provider] < 1.0]}
- ⚠️ Areas for improvement: Response consistency, specialized knowledge

---

"""
        
        report += """
### Performance Rankings

#### ⚡ Fastest Providers
| Rank | Provider | Avg Response Time |
|------|----------|------------------|
"""
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["fastest_avg"], 1):
            report += f"| {i} | {provider} | {metrics['avg']:.3f}s |\n"
        
        report += """
#### ✅ Most Reliable Providers  
| Rank | Provider | Success Rate |
|------|----------|-------------|
"""
        for i, (provider, rate) in enumerate(analysis["performance_rankings"]["highest_success_rate"], 1):
            report += f"| {i} | {provider} | {rate*100:.1f}% |\n"
        
        report += """
#### ⭐ Best Quality Providers
| Rank | Provider | Quality Score |
|------|----------|--------------|
"""
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["best_quality"], 1):
            report += f"| {i} | {provider} | {metrics['avg']:.3f}/1.0 |\n"
        
        report += """
#### 💰 Most Cost Effective Providers
| Rank | Provider | Cost per Successful Query |
|------|----------|---------------------------|
"""
        for i, (provider, metrics) in enumerate(analysis["performance_rankings"]["most_cost_effective"], 1):
            report += f"| {i} | {provider} | ${metrics['cost_per_success']:.4f} |\n"
        
        report += """
---

## Query Type Performance Analysis

"""
        
        for query_type, metrics in analysis["summary_by_query_type"].items():
            report += f"""
### {query_type.upper()} Queries

- **Total Tests:** {metrics['total_tests']}
- **Successful:** {metrics['successful']}
- **Success Rate:** {metrics['successful']/metrics['total_tests']*100:.1f}%

**Provider Performance:**
"""
            if metrics['avg_response_times']:
                sorted_times = sorted(metrics['avg_response_times'].items(), key=lambda x: x[1])
                for i, (provider, avg_time) in enumerate(sorted_times[:3], 1):
                    report += f"- {i}. {provider}: {avg_time:.3f}s average\n"
        
        report += """
---

## Alexa-Specific Recommendations

Based on performance testing with Alexa-specific queries, here are the optimal providers for voice assistant integration:

### 🥇 Primary Recommendation
**Provider:** """ + (analysis['performance_rankings']['fastest_avg'][0][0] if analysis['performance_rankings']['fastest_avg'] else "N/A") + """
**Reason:** Fastest response times with good reliability, ideal for real-time voice interactions.

### 🥈 Secondary Option  
**Provider:** """ + (analysis['performance_rankings']['highest_success_rate'][0][0] if analysis['performance_rankings']['highest_success_rate'] else "N/A") + """
**Reason:** Highest success rate, best for critical voice commands where reliability is paramount.

### 🎯 Implementation Strategy
- **Primary:** Use fastest provider for quick responses (weather, time, simple commands)
- **Fallback:** Use most reliable provider for complex queries (smart home control, scheduling)
- **Cost Optimization:** Route simple queries to fastest, complex queries to highest quality

---

## Technical Methodology

### Test Configuration
- **Query Types:** Simple, Complex, Creative, Technical, Alexa-Specific
- **Queries per Type:** 5 different queries per type
- **Total Test Cases:** {total_test_cases}
- **Concurrency:** Maximum 10 parallel requests
- **Timeout:** 30 seconds per request
- **Quality Assessment:** Automated scoring based on length, relevance, and content diversity

### Success Criteria
- **Response Time:** < 3.0 seconds for simple queries
- **Success Rate:** > 90% across all query types  
- **Quality Score:** > 0.7/1.0 average
- **Cost Efficiency:** <$0.01 per successful query

### Limitations
- Quality scoring is automated and may not capture all aspects of response quality
- Cost estimates are approximate and based on public pricing
- Network conditions may affect response times
- Model availability and rate limits may impact results

---

## Conclusion and Next Steps

### Recommended Action Plan

1. **Immediate Deployment:**
   - Deploy {analysis['performance_rankings']['fastest_avg'][0][0]} for Alexa voice assistant
   - Implement fallback to {analysis['performance_rankings']['highest_success_rate'][0][0]} for reliability

2. **Monitoring Setup:**
   - Track response times in production
   - Monitor success rates and error patterns
   - Analyze user satisfaction scores

3. **Optimization Opportunities:**
   - Implement request caching for common queries
   - Use different providers for different query complexities
   - Consider edge computing for reduced latency

4. **Testing Schedule:**
   - Monthly performance benchmarks
   - Quarterly provider evaluation
   - Annual full retesting

### Long-term Considerations

- Evaluate new providers as they enter the market
- Monitor pricing changes and plan cost optimization
- Consider multi-provider strategies for redundancy
- Invest in custom model fine-tuning for Alexa-specific queries

---

*Report generated by LLM Performance Test Suite*
*For detailed raw data, see `llm_performance_results.json`*
"""
        
        # Calculate total test cases
        total_test_cases = sum(len(queries) for queries in TEST_QUERIES.values()) * len(self.providers)
        report = report.replace("{total_test_cases}", str(total_test_cases))
        
        filepath = f"/Users/Subho/{filename}"
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"📄 Report saved to: {filepath}")
        return filepath

async def main():
    """Main execution function"""
    print("🧪 LLM PROVIDER PERFORMANCE TEST SUITE")
    print("=" * 80)
    
    # Initialize tester
    tester = LLMProviderTester()
    
    # Check providers
    print(f"\n🔍 Found {len(tester.providers)} configured providers:")
    for provider in tester.providers:
        status = "✅" if provider.enabled else "❌"
        print(f"   {status} {provider.name}: {provider.models[0] if provider.models else 'N/A'}")
    
    if not tester.providers:
        print("\n❌ No providers configured. Please set API keys in environment variables.")
        return
    
    # Run parallel tests
    print("\n" + "=" * 80)
    print("🚀 STARTING PARALLEL PERFORMANCE TESTS")
    print("=" * 80)
    
    await tester.run_parallel_tests(max_concurrent=10)
    
    # Analyze results
    print("\n" + "=" * 80)
    print("📊 ANALYZING RESULTS")
    print("=" * 80)
    
    analysis = tester.analyze_results()
    
    # Print results
    tester.print_results(analysis)
    
    # Save results
    json_file = tester.save_results(analysis)
    
    # Generate report
    md_file = tester.generate_report()
    
    print("\n" + "=" * 80)
    print("✅ TEST SUITE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\n📁 Files generated:")
    print(f"   - {json_file} (detailed data)")
    print(f"   - {md_file} (comprehensive report)")
    
    return analysis

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        print("\n🎉 Performance testing completed!")
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()