#!/usr/bin/env python3
"""
Test script for Brand Jobs Automation Setup
Verifies all components are working correctly
"""

import requests
import json
import os
from datetime import datetime

def test_n8n_connection():
    """Test N8N web interface connection"""
    try:
        response = requests.get('http://localhost:5678', timeout=5)
        if response.status_code == 200:
            print("✅ N8N Web Interface: Accessible")
            return True
        else:
            print(f"❌ N8N Web Interface: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ N8N Web Interface: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Environment Configuration:")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file exists")
        
        with open('.env', 'r') as f:
            content = f.read()
            
        # Check for required variables
        required_vars = ['SERPAPI_KEY', 'GOOGLE_SHEET_ID']
        for var in required_vars:
            if f"{var}=" in content:
                if f"{var}=your_" in content or f"{var}=your_" in content:
                    print(f"⚠️  {var}: Needs to be updated")
                else:
                    print(f"✅ {var}: Configured")
            else:
                print(f"❌ {var}: Missing")
    else:
        print("❌ .env file not found")

def test_files():
    """Test required files exist"""
    print("\n📁 Required Files:")
    
    files_to_check = [
        'n8n/enhanced_brand_jobs_workflow.json',
        'sheet/jobs_sheet_template.csv',
        'sheet/companies.csv',
        'scripts/brand_jobs_daily.gs',
        'README_BRAND_JOBS_AUTOMATION.md'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")

def test_management_scripts():
    """Test management scripts"""
    print("\n🔧 Management Scripts:")
    
    scripts = [
        'start_n8n.sh',
        'monitor_brand_jobs.sh',
        'restart_n8n.sh',
        'stop_n8n.sh'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"✅ {script} (executable)")
            else:
                print(f"⚠️  {script} (not executable)")
        else:
            print(f"❌ {script}")

def test_workflow_json():
    """Test workflow JSON is valid"""
    print("\n📋 Workflow Validation:")
    
    try:
        with open('n8n/enhanced_brand_jobs_workflow.json', 'r') as f:
            workflow = json.load(f)
        
        # Check required fields
        required_fields = ['name', 'nodes', 'connections']
        for field in required_fields:
            if field in workflow:
                print(f"✅ Workflow has {field}")
            else:
                print(f"❌ Workflow missing {field}")
        
        # Count nodes
        node_count = len(workflow.get('nodes', []))
        print(f"✅ Workflow has {node_count} nodes")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
    except Exception as e:
        print(f"❌ Error reading workflow: {e}")

def main():
    """Run all tests"""
    print("🧪 Brand Jobs Automation - Setup Test")
    print("=" * 50)
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    n8n_ok = test_n8n_connection()
    test_environment()
    test_files()
    test_management_scripts()
    test_workflow_json()
    
    print("\n" + "=" * 50)
    if n8n_ok:
        print("🎉 Setup looks good! N8N is running.")
        print("\n📥 Next Steps:")
        print("1. Open http://localhost:5678")
        print("2. Login: admin / brandjobs2024")
        print("3. Import n8n/enhanced_brand_jobs_workflow.json")
        print("4. Configure Google Sheets credentials")
        print("5. Test and activate workflow")
    else:
        print("⚠️  N8N is not running. Start it with: ./start_n8n.sh")
    
    print("\n📚 Documentation: README_BRAND_JOBS_AUTOMATION.md")

if __name__ == "__main__":
    main()