#!/usr/bin/env python3
"""
Test Salary Estimation Features
"""

import os
import sys
sys.path.append('scripts')

from salary_estimation_service import SalaryEstimationService
from salary_research_enhancer import SalaryResearchEnhancer

def test_salary_estimation():
    """Test salary estimation service"""
    print("🧪 Testing Salary Estimation Service")
    print("=" * 50)
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    if not serpapi_key:
        print("❌ SERPAPI_KEY not set")
        return False
    
    # Initialize service
    service = SalaryEstimationService(openai_key, serpapi_key)
    
    # Test jobs
    test_jobs = [
        {
            "title": "Senior Brand Manager",
            "company": "Hindustan Unilever",
            "location": "Mumbai, India",
            "description": "Lead brand strategy and marketing initiatives"
        },
        {
            "title": "Head of Brand",
            "company": "Tech Startup",
            "location": "Bangalore, India",
            "description": "Build and scale brand presence"
        }
    ]
    
    print("Testing AI-powered salary estimation...")
    results = service.batch_estimate_salaries(test_jobs)
    
    for job in results:
        print(f"\n📊 {job['title']} @ {job['company']}")
        print(f"   Location: {job['location']}")
        if job.get('estimated_avg_lpa'):
            print(f"   Estimated: {job['estimated_min_lpa']}-{job['estimated_max_lpa']} LPA")
            print(f"   Average: {job['estimated_avg_lpa']} LPA")
            print(f"   Confidence: {job['estimation_confidence']}/10")
            print(f"   Method: {job['salary_estimation_method']}")
            print(f"   Reasoning: {job['estimation_reasoning']}")
        else:
            print(f"   ❌ Estimation failed: {job.get('estimation_error', 'Unknown error')}")
    
    return True

def test_research_enhancer():
    """Test salary research enhancer"""
    print("\n🔍 Testing Salary Research Enhancer")
    print("=" * 50)
    
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        print("❌ SERPAPI_KEY not set")
        return False
    
    # Initialize enhancer
    enhancer = SalaryResearchEnhancer(serpapi_key)
    
    # Test jobs
    test_jobs = [
        {
            "title": "Senior Brand Manager",
            "company": "Hindustan Unilever",
            "location": "Mumbai, India",
            "parsed_lpa": ""
        },
        {
            "title": "Head of Brand",
            "company": "Tech Startup",
            "location": "Bangalore, India",
            "parsed_lpa": ""
        }
    ]
    
    print("Testing web-based salary research...")
    enhanced_jobs = enhancer.enhance_job_salaries(test_jobs)
    
    for job in enhanced_jobs:
        print(f"\n📊 {job['title']} @ {job['company']}")
        print(f"   Location: {job['location']}")
        if job.get('estimated_avg_lpa'):
            print(f"   Estimated: {job['estimated_min_lpa']}-{job['estimated_max_lpa']} LPA")
            print(f"   Average: {job['estimated_avg_lpa']} LPA")
            print(f"   Confidence: {job['estimation_confidence']}/10")
            print(f"   Method: {job['salary_estimation_method']}")
            print(f"   Reasoning: {job['estimation_reasoning']}")
        else:
            print(f"   ❌ Research failed: {job.get('estimation_error', 'Unknown error')}")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Brand Jobs Salary Estimation - Test Suite")
    print("=" * 60)
    
    # Test AI estimation
    ai_success = test_salary_estimation()
    
    # Test research enhancer
    research_success = test_research_enhancer()
    
    print("\n" + "=" * 60)
    if ai_success and research_success:
        print("🎉 All salary estimation tests passed!")
        print("\n📋 Next Steps:")
        print("1. Update .env with your API keys")
        print("2. Import enhanced workflow in N8N")
        print("3. Test the complete automation")
    else:
        print("⚠️  Some tests failed. Check API keys and dependencies.")
    
    return ai_success and research_success

if __name__ == "__main__":
    main()
