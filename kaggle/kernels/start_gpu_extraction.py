#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

print("🚀 CHUCKLENET GPU EXTRACTION EXECUTION")
print("="*50)

# Check if we're in the right directory
current_dir = Path.cwd()
if "kernels" not in str(current_dir):
    # Navigate to kernels directory
    kernels_dir = current_dir / "kaggle" / "kernels"
    if kernels_dir.exists():
        os.chdir(kernels_dir)
        print(f"✅ Navigated to: {Path.cwd()}")
    else:
        print("❌ kernels directory not found")
        sys.exit(1)

# Check required files
required_files = ["gpu_extraction_final.ipynb"]
for file in required_files:
    if Path(file).exists():
        print(f"✅ {file} found")
    else:
        print(f"❌ {file} missing")

print("\n📋 EXECUTION PLAN:")
print("1. You'll need to manually execute the Kaggle kernel")
print("2. GPU extraction will run automatically once triggered")
print("3. Process will take ~1.2 hours (11.4x faster than CPU)")
print("4. Results will be saved to /kaggle/working/vtt_frames/")

print("\n🎯 IMMEDIATE NEXT STEPS:")
print("1. Go to: https://www.kaggle.com/code/subhajitdas/chucklenet-gpu-extraction-11-4x-faster-than-cpu")
print("2. Click 'Copy and Edit'")
print("3. Ensure T4 GPU is selected in Settings")
print("4. Run all cells")
print("5. Monitor progress (~1.2 hours)")
print("6. Download vtt_frames folder when complete")

print("\n⚡ READY TO EXECUTE!")
