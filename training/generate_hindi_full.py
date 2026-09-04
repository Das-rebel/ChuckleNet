#!/usr/bin/env python3
"""
Hindi synthetic data generation - with proper logging.
"""
import sys
sys.path.insert(0, '.')

import json
import time
import random
from pathlib import Path

from generate_synthetic_hindi import (
    STYLE_TARGETS, generate_examples, convert_to_training_format,
    save_jsonl, validate_dataset, OUTPUT_DIR
)

OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/synthetic_hindi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

progress_file = OUTPUT_DIR / "progress.json"
log_file = OUTPUT_DIR / "generation.log"

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(log_file, 'a') as f:
        f.write(line + '\n')

def update_progress(data):
    with open(progress_file, 'w') as f:
        json.dump(data, f, indent=2)

log("=" * 70)
log("HINDI SYnthetic DATA GENERATION - FULL 4000")
log("=" * 70)
log(f"Target: {sum(STYLE_TARGETS.values())} examples")
log(f"Output: {OUTPUT_DIR}")
log("=" * 70)

start_time = time.time()
all_examples = []
generated = {}

for style, target in STYLE_TARGETS.items():
    log(f"\n{'='*70}")
    log(f"STARTING: {style} ({target} examples)")
    log("=" * 70)
    
    style_start = time.time()
    examples = generate_examples(style, target)
    style_elapsed = time.time() - style_start
    
    log(f"COMPLETED: {style} - {len(examples)} examples in {style_elapsed:.1f}s")
    
    all_examples.extend(examples)
    generated[style] = len(examples)
    
    total = len(all_examples)
    total_target = sum(STYLE_TARGETS.values())
    
    # Update progress
    progress = {
        "status": "generating",
        "current_style": style,
        "total_generated": total,
        "target": total_target,
        "progress_pct": round(100 * total / total_target, 1),
        "elapsed_minutes": round((time.time() - start_time) / 60, 1),
        "generated_by_style": generated
    }
    update_progress(progress)
    
    log(f"PROGRESS: {total}/{total_target} ({100*total/total_target:.1f}%) - {progress['elapsed_minutes']} min elapsed")

total_elapsed = time.time() - start_time
log(f"\n{'='*70}")
log(f"GENERATION COMPLETE: {len(all_examples)} examples in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
log("=" * 70)

# Convert to training format
log("\nConverting to training format...")
training = convert_to_training_format(all_examples)
log(f"Converted: {len(training)} examples")

# Split
random.shuffle(training)
n = len(training)
train = training[:int(0.8*n)]
valid = training[int(0.8*n):int(0.9*n)]
test = training[int(0.9*n):]

# Save
log("Saving files...")
save_jsonl(train, OUTPUT_DIR / "train.jsonl")
save_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
save_jsonl(test, OUTPUT_DIR / "test.jsonl")

log(f"Saved: train={len(train)}, valid={len(valid)}, test={len(test)}")

# Validate
log("\nValidating...")
validate_dataset(train, valid, test)

# Final progress update
final_progress = {
    "status": "complete",
    "total_generated": len(all_examples),
    "train": len(train),
    "valid": len(valid),
    "test": len(test),
    "total_time_minutes": round(total_elapsed / 60, 1),
    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
}
update_progress(final_progress)

log("\n" + "=" * 70)
log("ALL COMPLETE!")
log(f"Total time: {total_elapsed/60:.1f} minutes")
log(f"Output: {OUTPUT_DIR}")
log("=" * 70)