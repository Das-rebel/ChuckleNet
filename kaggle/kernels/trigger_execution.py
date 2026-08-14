import subprocess
import webbrowser
import time
import os

print("🚀 CHUCKLENET GPU EXTRACTION - EXECUTION TRIGGER")
print("=" * 55)

# Get kernel information
result = subprocess.run([
    'python3', '-m', 'kaggle', 'kernels', 'list', '--mine'
], capture_output=True, text=True)

kernel_found = False
kernel_ref = ""
kernel_url = ""

# Find the GPU extraction kernel
for line in result.stdout.split('\n'):
    if 'chucklenet-gpu-extraction' in line and '11.4x' in line:
        kernel_ref = line.split()[0]
        kernel_url = f'https://www.kaggle.com/code/{kernel_ref}'
        kernel_found = True
        break

if kernel_found:
    print(f"✅ Kernel found: {kernel_ref}")
    print(f"🌐 URL: {kernel_url}")
    
    # Open the kernel for execution
    print("\n🌐 Opening browser for manual execution...")
    webbrowser.open(kernel_url)
    
    print("\n📋 EXECUTION CHECKLIST:")
    print("1. ✓ Browser opened with GPU extraction kernel")
    print("2. 🔄 Click 'Copy and Edit' (creates your execution instance)")
    print("3. 🔄 Go to Settings → Select 'T4 GPU' → Save")
    print("4. 🔄 Click 'Run All' (starts extraction)")
    print("5. ⏰ Wait ~1.2 hours for completion")
    
    print(f"\n⚠️ IMPORTANT - Please complete these steps NOW!")
    print("The kernel will NOT execute until you click 'Run All'")
    
    # Create status monitoring script
    with open('monitor_execution.sh', 'w') as f:
        f.write("""#!/bin/bash
echo "📊 Monitoring GPU extraction status..."
while true; do
    echo "⏰ Checking status - $(date)"
    result=$(python3 -m kaggle kernels list --mine | grep -E "(chucklenet.*gpu|extraction.*11.4x)" | head -1)
    if [[ "$result" == *" "* ]]; then
        echo "✅ Kernel found: $result"
    else
        echo "⏳ Still waiting for execution to start..."
    fi
    sleep 60
done
""")
    
    os.chmod('monitor_execution.sh', 0o755)
    print(f"\n📊 Created status monitor: ./monitor_execution.sh")
    
else:
    print("❌ GPU extraction kernel not found")
    print("⚠️ May need to recreate the kernel")

print("\n🎉 EXECUTION TRIGGER COMPLETE!")
print("Now go complete the manual steps in the browser!")
