#!/bin/bash
# Merge final_merged_10k with synthetic_hindi datasets
# Usage: bash merge_datasets.sh

set -e

DATA_DIR="/Users/Subho/autonomous_laughter_prediction_essential/data"
OUTPUT_DIR="${DATA_DIR}/combined_multilingual"

echo "============================================================"
echo "MERGING MULTILINGUAL DATASETS"
echo "============================================================"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Paths
FINAL_10K="${DATA_DIR}/final_merged_10k"
SYNTHETIC_HINDI="${DATA_DIR}/synthetic_hindi"

# Check if synthetic_hindi exists and has files
if [ ! -d "${SYNTHETIC_HINDI}" ] || [ ! -f "${SYNTHETIC_HINDI}/train.jsonl" ]; then
    echo "WARNING: synthetic_hindi not ready yet (${SYNTHETIC_HINDI}/train.jsonl not found)"
    echo "Using final_merged_10k only..."
    
    # Just copy final_merged_10k
    cp -r "${FINAL_10K}" "${OUTPUT_DIR}"
    echo "Copied final_merged_10k to ${OUTPUT_DIR}"
else
    echo "Found synthetic_hindi: ${SYNTHETIC_HINDI}"
    
    # Count examples in each
    echo ""
    echo "Dataset sizes:"
    echo "  final_merged_10k:"
    wc -l "${FINAL_10K}"/*.jsonl 2>/dev/null || echo "    (not found)"
    echo "  synthetic_hindi:"
    wc -l "${SYNTHETIC_HINDI}"/*.jsonl 2>/dev/null || echo "    (not found)"
    
    # Merge train
    echo ""
    echo "Merging train..."
    cat "${FINAL_10K}/train.jsonl" "${SYNTHETIC_HINDI}/train.jsonl" > "${OUTPUT_DIR}/train.jsonl"
    
    # Merge valid
    echo "Merging valid..."
    cat "${FINAL_10K}/valid.jsonl" "${SYNTHETIC_HINDI}/valid.jsonl" > "${OUTPUT_DIR}/valid.jsonl"
    
    # Merge test
    echo "Merging test..."
    cat "${FINAL_10K}/test.jsonl" "${SYNTHETIC_HINDI}/test.jsonl" > "${OUTPUT_DIR}/test.jsonl"
fi

# Count final totals
echo ""
echo "============================================================"
echo "FINAL COMBINED DATASET"
echo "============================================================"
wc -l "${OUTPUT_DIR}"/*.jsonl

# Language distribution
echo ""
echo "Language distribution:"
python3 << 'EOF'
import json
from collections import Counter

data_dir = "/Users/Subho/autonomous_laughter_prediction_essential/data/combined_multilingual"
for split in ['train', 'valid', 'test']:
    path = f"{data_dir}/{split}.jsonl"
    try:
        with open(path) as f:
            lines = f.readlines()
        langs = Counter()
        for line in lines:
            ex = json.loads(line)
            langs[ex.get('language', 'unknown')] += 1
        print(f"  {split}: {dict(langs)}")
    except:
        pass
EOF

echo ""
echo "Output: ${OUTPUT_DIR}"
echo "============================================================"