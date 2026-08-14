#!/bin/bash

echo "🚀 CHUCKLENET GPU EXTRACTION - AUTOMATED EXECUTION"
echo "=================================================="
echo "⏰ Starting automated execution process..."
echo ""

# Step 1: Check requirements
echo "📋 CHECKING REQUIREMENTS..."
echo "✅ Checking Kaggle CLI..."
which python3 -m kaggle > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Kaggle CLI working"
else
    echo "❌ Kaggle CLI not found"
    exit 1
fi

echo "✅ Checking kernel availability..."
python3 -m kaggle kernels list --mine | grep "chucklenet-gpu-extraction" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ GPU extraction kernel found"
else
    echo "❌ GPU extraction kernel not found"
    exit 1
fi

# Step 2: Prepare execution environment
echo ""
echo "🔧 PREPARING EXECUTION ENVIRONMENT..."

# Ensure metadata file exists
cat > kernel-metadata.json << 'METADATA'
{
  "title": "ChuckleNet GPU Extraction - Automated Run",
  "code_file": "gpu_extraction_final.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": false,
  "enable_gpu": true,
  "dataset_sources": [],
  "competition_sources": [],
  "code_file_template": "notebook.ipynb",
  "kernel_sources": []
}
METADATA

echo "✅ Kernel metadata prepared"

# Step 3: Create execution script
echo ""
echo "🎯 CREATING EXECUTION SCRIPT..."

cat > execute_gpu_extraction.py << 'EXEC_SCRIPT'
import subprocess
import time
import webbrowser
import os

print("🚀 CHUCKLENET GPU EXTRACTION - AUTOMATED EXECUTION")
print("=" * 55)
print("")

# Kernel information
kernel_url = "https://www.kaggle.com/code/subhajitdas/chucklenet-gpu-extraction-11-4x-faster-than-cpu"
kernel_id = "subhajitdas/chucklenet-gpu-extraction-11-4x-faster-than-cpu"

print(f"🎯 Target Kernel: {kernel_url}")
print("")

# Option 1: Open browser for manual execution
print("📤 Option 1: Automated Browser Execution")
print("1. Opening kernel in browser...")
webbrowser.open(kernel_url)

print("2. Please manually:")
print("   - Click 'Copy and Edit'")
print("   - Enable T4 GPU in Settings")
print("   - Click 'Run All'")
print("   - Wait ~1.2 hours")
print("")

# Option 2: Try API-based execution
print("📤 Option 2: API-based Execution Attempt")
print("")

# Get authentication token
try:
    # Get Kaggle token
    result = subprocess.run([
        'python3', '-m', 'kaggle', 'config', 'view', '-g', 'token'
    ], capture_output=True, text=True)
    
    token = result.stdout.strip()
    if token:
        print("✅ Kaggle authentication available")
        
        # Try to trigger execution via API
        import requests
        
        execution_url = f"https://www.kaggle.com/api/v1/kernels/execute/{kernel_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        print("🔄 Attempting API execution...")
        response = requests.post(execution_url, json={}, headers=headers)
        
        if response.status_code == 200:
            print("✅ Execution triggered successfully!")
            result = response.json()
            print(f"📊 Result: {result}")
            
            # Monitor execution status
            print("📡 Monitoring execution status...")
            time.sleep(10)
            
        else:
            print(f"❌ API execution failed: {response.status_code}")
            print(f"📊 Response: {response.text}")
            
    else:
        print("❌ No Kaggle token found")
        
except Exception as e:
    print(f"❌ API execution error: {e}")

print("")
print("🎯 NEXT STEPS:")
print("1. Use Option 1 (browser) for guaranteed execution")
print("2. Monitor progress in the browser")
print("3. Download results when complete")
print("")
print("⚡ Expected execution time: ~1.2 hours")
print("🎉 Process will automatically extract 620 video frames!")

EXEC_SCRIPT

echo "✅ Execution script created"
echo ""

# Step 4: Run the automation
echo "🚀 STARTING AUTOMATED EXECUTION..."
echo "=================================================="

python3 execute_gpu_extraction.py

echo ""
echo "🎉 AUTOMATION COMPLETE!"
echo "📋 What happened:"
echo "✅ Browser opened with GPU extraction kernel"
echo "✅ Execution script prepared"
echo "✅ API execution attempted"
echo "🔄 Waiting for your manual browser actions..."
echo ""
echo "⏱️ Total time until completion: ~1.2 hours"
echo "📁 Output will be in: /kaggle/working/vtt_frames/"

