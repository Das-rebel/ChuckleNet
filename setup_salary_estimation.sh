#!/bin/bash

# Setup Script for Brand Jobs with Salary Estimation
echo "🚀 Setting up Brand Jobs with Salary Estimation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python dependencies
check_python_deps() {
    print_status "Checking Python dependencies..."
    
    # Check if required packages are installed
    python3 -c "import requests, pandas, openai" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "Python dependencies already installed"
    else
        print_warning "Installing Python dependencies..."
        pip3 install requests pandas openai
        if [ $? -eq 0 ]; then
            print_success "Python dependencies installed"
        else
            print_error "Failed to install Python dependencies"
            exit 1
        fi
    fi
}

# Create enhanced Google Sheets template
create_enhanced_template() {
    print_status "Creating enhanced Google Sheets template..."
    
    if [ ! -d "sheet" ]; then
        mkdir -p sheet
    fi
    
    # The enhanced CSV template is already created
    if [ -f "sheet/enhanced_jobs_sheet_template.csv" ]; then
        print_success "Enhanced Google Sheets template ready"
        echo "📋 Enhanced template includes salary estimation fields:"
        echo "   - salary_estimation_method"
        echo "   - estimated_min_lpa"
        echo "   - estimated_max_lpa"
        echo "   - estimated_avg_lpa"
        echo "   - estimation_confidence"
        echo "   - estimation_reasoning"
        echo "   - estimation_error"
    else
        print_error "Enhanced template not found!"
        exit 1
    fi
}

# Create salary estimation test script
create_test_script() {
    print_status "Creating salary estimation test script..."
    
    cat > test_salary_estimation.py << 'EOF'
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
EOF

    chmod +x test_salary_estimation.py
    print_success "Salary estimation test script created"
}

# Create enhanced N8N workflow instructions
create_workflow_instructions() {
    print_status "Creating enhanced workflow instructions..."
    
    cat > ENHANCED_WORKFLOW_SETUP.md << 'EOF'
# Enhanced Brand Jobs Workflow with Salary Estimation

## 🎯 Features

### Salary Estimation Methods
1. **Explicit Salary Extraction** - From job descriptions
2. **Web Search Research** - Using SerpAPI to find salary data
3. **AI-Powered Estimation** - Using OpenAI GPT-4 for intelligent estimation
4. **Benchmark-Based Estimation** - Using industry and role benchmarks

### Enhanced Data Fields
- `salary_estimation_method` - How salary was determined
- `estimated_min_lpa` - Minimum estimated salary
- `estimated_max_lpa` - Maximum estimated salary
- `estimated_avg_lpa` - Average estimated salary
- `estimation_confidence` - Confidence level (1-10)
- `estimation_reasoning` - Explanation of estimation
- `estimation_error` - Error message if estimation failed

## 🚀 Setup Instructions

### 1. Update Environment Variables
Add to your `.env` file:
```bash
# Required for salary estimation
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here
GOOGLE_SHEET_ID=your_google_sheet_id_here
```

### 2. Import Enhanced Workflow
1. Open N8N at http://localhost:5678
2. Import `n8n/enhanced_brand_jobs_with_salary_estimation.json`
3. Configure Google Sheets credentials
4. Test the workflow

### 3. Update Google Sheet
1. Import `sheet/enhanced_jobs_sheet_template.csv` as "jobs" tab
2. The enhanced template includes all salary estimation fields

## 🔧 How It Works

### Workflow Process
1. **Daily Trigger** - Runs at 9:30 AM IST
2. **Job Search** - Searches for brand marketing roles
3. **Salary Extraction** - Extracts explicit salaries from job descriptions
4. **Web Research** - Searches for salary data using SerpAPI
5. **AI Estimation** - Uses OpenAI for intelligent salary estimation
6. **Benchmark Fallback** - Uses industry benchmarks if other methods fail
7. **Data Enhancement** - Adds all salary estimation fields to job data
8. **Google Sheets** - Saves enhanced data to sheet

### Salary Estimation Logic
1. **Priority 1**: Explicit salary in job description
2. **Priority 2**: Web search for company-specific salary data
3. **Priority 3**: Web search for role + location salary data
4. **Priority 4**: AI-powered estimation using job context
5. **Priority 5**: Benchmark-based estimation using industry data

## 📊 Expected Results

### Daily Output
- **Jobs Found**: 20-50 new jobs per day
- **Salary Estimated**: 80-90% of jobs will have salary estimates
- **Confidence Levels**: 5-10/10 for most estimates
- **Methods Used**: Mix of explicit, web search, and AI estimation

### Data Quality
- **High Confidence**: Explicit salaries and company-specific data
- **Medium Confidence**: Role + location research
- **Lower Confidence**: AI estimation and benchmarks
- **Transparency**: Full reasoning and confidence levels provided

## 🧪 Testing

### Test Salary Estimation
```bash
python3 test_salary_estimation.py
```

### Test Individual Components
```bash
# Test AI estimation service
python3 scripts/salary_estimation_service.py

# Test research enhancer
python3 scripts/salary_research_enhancer.py
```

## 🔍 Monitoring

### Check Estimation Quality
- Review `estimation_confidence` field in Google Sheets
- Monitor `estimation_reasoning` for quality insights
- Track `salary_estimation_method` distribution

### Optimize Performance
- Adjust confidence thresholds
- Add more salary data sources
- Refine AI prompts for better estimation

## 🚨 Troubleshooting

### Common Issues
1. **Low Estimation Confidence**
   - Check API key validity
   - Verify search queries are appropriate
   - Review benchmark data accuracy

2. **AI Estimation Failures**
   - Verify OpenAI API key
   - Check API usage limits
   - Review prompt effectiveness

3. **Web Search Failures**
   - Verify SerpAPI key
   - Check search query effectiveness
   - Review rate limiting

### Debug Mode
Enable detailed logging by modifying the N8N workflow to include more console.log statements.

## 📈 Next Steps

### Enhancements
1. **More Data Sources** - Add Glassdoor, AmbitionBox APIs
2. **Better AI Prompts** - Refine prompts for more accurate estimation
3. **Historical Analysis** - Track salary trends over time
4. **Company Analysis** - Build company-specific salary databases

### Integration
1. **Slack Notifications** - Send high-confidence estimates to Slack
2. **Email Alerts** - Notify about high-salary opportunities
3. **Dashboard** - Create salary analytics dashboard
4. **API Endpoints** - Expose salary data via REST API

---

**Happy Salary Hunting! 💰**
EOF

    print_success "Enhanced workflow instructions created"
}

# Main execution
main() {
    echo "🎯 Brand Jobs with Salary Estimation - Setup"
    echo "============================================="
    echo ""
    
    check_python_deps
    create_enhanced_template
    create_test_script
    create_workflow_instructions
    
    echo ""
    print_success "Enhanced setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update .env with OPENAI_API_KEY and SERPAPI_KEY"
    echo "2. Import enhanced workflow in N8N"
    echo "3. Update Google Sheet with enhanced template"
    echo "4. Test salary estimation: python3 test_salary_estimation.py"
    echo "5. Run complete automation"
    echo ""
    echo "🔧 Enhanced Features:"
    echo "• AI-powered salary estimation"
    echo "• Web-based salary research"
    echo "• Industry benchmark fallback"
    echo "• Confidence scoring and reasoning"
    echo "• Multiple estimation methods"
    echo ""
    echo "📚 Documentation: ENHANCED_WORKFLOW_SETUP.md"
}

# Run main function
main "$@"