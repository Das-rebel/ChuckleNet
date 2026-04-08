# Training Plan 2026

This plan has been updated to match the current stand-up-focused implementation.

## Primary objective

Train a word-level stand-up laughter detector using `FacebookAI/xlm-roberta-base`.

## Training order

1. Convert raw transcripts into weak labels
2. Refine weak labels with a lightweight local teacher
3. Train XLM-R on the weak baseline
4. Train XLM-R on the refined labels
5. Compare both runs and keep only the better one

## Current baseline

Promoted weak-label run:

- validation F1: `0.7850`
- validation IoU-F1: `0.7891`
- test F1: `0.8194`
- test IoU-F1: `0.8798`
- positive class weight: `5.0`

Refined-label run:

- validation F1: `0.0784`
- validation IoU-F1: `0.0408`
- test F1: `0.1231`
- test IoU-F1: `0.0656`

Decision:

- class-weighted weak-label run remains the active winner
- refined-label run is archived for analysis only

## Current model roles

- backbone: `FacebookAI/xlm-roberta-base`
- teacher: `qwen2.5-coder:1.5b`

TurboQuant note:

- useful for KV-cache-heavy generative inference
- not the reason to switch away from XLM-R for this task

## Immediate commands

Refinement resume:

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume
```

Weak-label training:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --test-file data/training/standup_word_level/test.jsonl \
  --output-dir experiments/xlmr_standup_baseline_weak \
  --model-name FacebookAI/xlm-roberta-base
```

Refined-label training:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train_refined.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --test-file data/training/standup_word_level/test.jsonl \
  --output-dir experiments/xlmr_standup_baseline_refined \
  --model-name FacebookAI/xlm-roberta-base
```
