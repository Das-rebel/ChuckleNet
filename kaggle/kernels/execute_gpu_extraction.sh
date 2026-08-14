#!/bin/bash
cd autonomous_laughter_prediction_essential/kaggle/kernels

echo "🚀 Setting up for GPU execution..."
echo "1. Creating kernel from gpu_extraction_final.ipynb"
echo "2. Enabling T4 GPU"
echo "3. Running extraction pipeline"

# Create metadata file
cat > kernel-metadata.json << 'METADATA'
{
  "title": "ChuckleNet GPU Execution",
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

echo "✅ Kernel metadata created"
echo "🎯 Next steps:"
echo "1. Go to: https://www.kaggle.com/code/subhajitdas/chucklenet-gpu-extraction-11-4x-faster-than-cpu"
echo "2. Click 'Copy and Edit'"
echo "3. Make sure T4 GPU is enabled"
echo "4. Run all cells"
echo "5. This will execute the 11.4x faster GPU extraction"
