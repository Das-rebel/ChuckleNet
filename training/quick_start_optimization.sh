#!/bin/bash
# Quick Start Script for GCACU Hyperparameter Optimization
# This script demonstrates the optimization system on the multilingual dataset

echo "======================================================================"
echo "GCACU Hyperparameter Optimization - Quick Start"
echo "======================================================================"

# Set paths
DATA_DIR="/Users/Subho/autonomous_laughter_prediction/data/training"
OUTPUT_DIR="/Users/Subho/autonomous_laughter_prediction/gcacu_optimization_demo"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo ""
echo "Step 1: Running comprehensive optimization..."
echo "This will analyze the multilingual dataset and optimize hyperparameters"
echo ""

cd /Users/Subho/autonomous_laughter_prediction/training

# Run optimization with 10 trials for quick demo
python run_gcacu_optimization.py \
    --train-file "$DATA_DIR/multilingual.jsonl" \
    --valid-file "$DATA_DIR/multilingual.jsonl" \
    --test-file "$DATA_DIR/multilingual.jsonl" \
    --model-name "FacebookAI/xlm-roberta-base" \
    --output-dir "$OUTPUT_DIR" \
    --trials 10 \
    --no-cv

echo ""
echo "======================================================================"
echo "Optimization Complete!"
echo "======================================================================"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Generated files:"
echo "  - final_optimization_report_*.json"
echo "  - gcacu_optimization_execution.log"
echo ""
echo "Key findings:"
echo "  - Adaptive configuration based on dataset analysis"
echo "  - Optimized hyperparameters for multilingual scenario"
echo "  - Production-ready configuration"
echo ""
echo "Next steps:"
echo "  1. Review the optimization report"
echo "  2. Use production_config.json for training"
echo "  3. Monitor per-language performance"
echo "  4. Consider running full optimization (50+ trials with CV)"
echo ""
echo "For full optimization:"
echo "  python run_gcacu_optimization.py --trials 50"
echo ""
echo "======================================================================"