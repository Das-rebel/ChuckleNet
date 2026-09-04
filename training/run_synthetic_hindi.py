#!/usr/bin/env python3
"""
Fully automated Hindi/Hinglish data generation.
Run in background: nohup python3 run_synthetic_hindi.py &
"""
import sys
sys.path.insert(0, '.')

from generate_synthetic_hindi import (
    STYLE_TARGETS, generate_examples, convert_to_training_format,
    save_jsonl, validate_dataset, OUTPUT_DIR
)
import random
import time
import json

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

log_file = open('synthetic_hindi_progress.json', 'w')

def log(msg):
    print(msg)
    log_file.write(msg + '\n')
    log_file.flush()

log('=' * 70)
log('FULLY AUTOMATED HINDI DATA GENERATION')
log('=' * 70)
log(f'Target: {sum(STYLE_TARGETS.values())} examples')
log(f'Output: {OUTPUT_DIR}')
log(f'Started at: {time.strftime("%Y-%m-%d %H:%M:%S")}')

all_examples = []
generated_counts = {}

# Generate for each style
for style, target_count in STYLE_TARGETS.items():
    log(f'\n{"="*70}')
    log(f'Generating {style} ({target_count} examples)...')
    log('='*70)
    
    start = time.time()
    examples = generate_examples(style, target_count)
    elapsed = time.time() - start
    
    log(f'Generated {len(examples)} {style} examples in {elapsed:.1f}s')
    all_examples.extend(examples)
    generated_counts[style] = len(examples)
    
    # Save progress
    with open('synthetic_hindi_progress.json', 'w') as f:
        json.dump({
            'total_generated': len(all_examples),
            'target': sum(STYLE_TARGETS.values()),
            'generated_counts': generated_counts,
            'current_style': style,
            'elapsed': elapsed
        }, f, indent=2)

log(f'\n{"="*70}')
log(f'Total generated: {len(all_examples)} examples')
log(f'Expected: {sum(STYLE_TARGETS.values())}')
log('='*70)

# Convert to training format
log('\nConverting to training format...')
training_examples = convert_to_training_format(all_examples)
log(f'Converted {len(training_examples)} examples')

# Split into train/valid/test
random.shuffle(training_examples)
n_total = len(training_examples)
n_train = int(0.8 * n_total)
n_valid = int(0.9 * n_total)

train = training_examples[:n_train]
valid = training_examples[n_train:n_valid]
test = training_examples[n_valid:]

# Save
save_jsonl(train, OUTPUT_DIR / 'train.jsonl')
save_jsonl(valid, OUTPUT_DIR / 'valid.jsonl')
save_jsonl(test, OUTPUT_DIR / 'test.jsonl')

log(f'\nSaved:')
log(f'  Train: {len(train)} examples')
log(f'  Valid: {len(valid)} examples')
log(f'  Test: {len(test)} examples')

# Validate
log(f'\n{"="*70}')
log('Validating dataset...')
log('='*70)
validate_dataset(train, valid, test)

log(f'\n{"="*70}')
log('AUTOMATED GENERATION COMPLETE')
log(f'Finished at: {time.strftime("%Y-%m-%d %H:%M:%S")}')
log('='*70)

log_file.close()