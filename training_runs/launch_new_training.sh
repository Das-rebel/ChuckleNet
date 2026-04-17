#!/bin/bash
# Template for launching new training runs with proper numbering
# Usage: ./launch_new_training.sh <run_number> <purpose>

RUN_NUMBER=$1
PURPOSE=$2

if [ -z "$RUN_NUMBER" ] || [ -z "$PURPOSE" ]; then
    echo "❌ Usage: $0 <run_number> <purpose>"
    echo "Example: $0 41 'Testing enhanced biosemotic R² tracking'"
    exit 1
fi

# Format run number with zero padding
RUNFormatted=$(printf "%03d" $RUN_NUMBER)

echo "🚀 Launching Training Run #$RUN_NUMBER"
echo "Purpose: $PURPOSE"
echo "Run Number: $RUNFormatted"
echo ""

# Create output directory
OUTPUT_DIR="models/run_${RUNFormatted}_training"
mkdir -p "$OUTPUT_DIR"
echo "✅ Created output directory: $OUTPUT_DIR"

# Create metadata file
METADATA_FILE="training_runs/run_${RUNFormatted}_metadata.json"
cp training_runs/run_template.json "$METADATA_FILE"

# Update metadata with initial information
sed -i '' "s|\"training_run_number\": null|\"training_run_number\": $RUN_NUMBER|g" "$METADATA_FILE"
sed -i '' "s|\"status\": \"PLANNED\"|\"status\": \"IN_PROGRESS\"|g" "$METADATA_FILE"
sed -i '' "s|\"purpose\": null|\"purpose\": \"$PURPOSE\"|g" "$METADATA_FILE"
sed -i '' "s|\"output_directory\": null|\"output_directory\": \"$OUTPUT_DIR\"|g" "$METADATA_FILE"

# Get current timestamp
START_TIME=$(date +"%Y-%m-%d %H:%M:%S")
sed -i '' "s|\"start_time\": null|\"start_time\": \"$START_TIME\"|g" "$METADATA_FILE"

echo "✅ Created metadata file: $METADATA_FILE"

# Create training script wrapper
WRAPPER_SCRIPT="training_runs/run_${RUNFormatted}_wrapper.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Training Run #$RUN_NUMBER - $PURPOSE
# Started: $START_TIME

cd /Users/Subho/autonomous_laughter_prediction

# TODO: Add your training command here
# Example:
python3 training/train_xlmr_multitask.py \\
  --train-file data/training/final_multilingual_v3_bilingual/train.jsonl \\
  --valid-file data/training/final_multilingual_v3_bilingual/valid.jsonl \\
  --output-dir $OUTPUT_DIR \\
  --epochs 10 \\
  --batch-size 16 \\
  --learning-rate 2e-5 \\
  --classifier-lr 1e-4 \\
  --max-grad-norm 1.0 \\
  --early-stopping-patience 3 \\
  --device cpu \\
  --eval-every-steps 500 \\
  > $OUTPUT_DIR/training.log 2>&1
EOF

chmod +x "$WRAPPER_SCRIPT"
echo "✅ Created wrapper script: $WRAPPER_SCRIPT"

# Update registry
echo "" >> training_runs/TRAINING_REGISTRY.md
echo "### **Training Run #$RUN_NUMBER** - 🟢 IN PROGRESS" >> training_runs/TRAINING_REGISTRY.md
echo "**Status**: 🟢 **IN PROGRESS** (Started: $START_TIME)" >> training_runs/TRAINING_REGISTRY.md
echo "**Purpose**: $PURPOSE" >> training_runs/TRAINING_REGISTRY.md
echo "**Output Dir**: \`$OUTPUT_DIR/\`" >> training_runs/TRAINING_REGISTRY.md
echo "" >> training_runs/TRAINING_REGISTRY.md

echo "✅ Updated training registry"
echo ""
echo "🎯 Training Run #$RUN_NUMBER setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and customize: $WRAPPER_SCRIPT"
echo "2. Launch training: bash $WRAPPER_SCRIPT"
echo "3. Monitor progress: tail -f $OUTPUT_DIR/training.log"
echo "4. Update metadata as training progresses"
