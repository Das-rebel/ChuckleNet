# XLM-R Stand-Up Roadmap

This repo is now centered on a text-first stand-up pipeline using `FacebookAI/xlm-roberta-base` for word-level laughter prediction.

## Canonical pipeline

1. Convert raw transcripts into word-level JSONL
2. Optionally refine weak labels with a small local teacher
3. Train XLM-R
4. Evaluate on validation and test splits

Scripts:

- `training/convert_standup_raw_to_word_level.py`
- `training/refine_weak_labels_nemotron.py`
- `training/xlmr_standup_word_level.py`
- `training/run_xlmr_standup_pipeline.py`
- `training/autonomous_research_loop.py`

## Why this path

- Stand-up comedy is the target domain.
- The task is better modeled as word-level sequence labeling than generic clip-level humor classification.
- Audio reliability is still uncertain, so audio is not required for the first production-quality baseline.
- TurboQuant does not change the backbone decision here because the main model is an encoder, not a KV-cache-heavy autoregressive LLM.

## Current machine profile

Verified local models:

- `FacebookAI/xlm-roberta-base`
- `qwen2.5-coder:1.5b`
- `qwen2.5-coder:latest`

Recommended roles:

- backbone: `FacebookAI/xlm-roberta-base`
- teacher: `qwen2.5-coder:1.5b`

## Current dataset status

Converted internal stand-up corpus:

- train examples: `520`
- valid examples: `49`
- test examples: `61`

Files:

- `data/training/standup_word_level/train.jsonl`
- `data/training/standup_word_level/valid.jsonl`
- `data/training/standup_word_level/test.jsonl`

## Current validated result

Promoted XLM-R baseline:

- validation F1: `0.7850`
- validation IoU-F1: `0.7891`
- test F1: `0.8194`
- test IoU-F1: `0.8798`
- positive class weight: `5.0`

Artifacts:

- `experiments/xlmr_standup_baseline_weak_pos5/best_model`
- `experiments/xlmr_standup_baseline_weak_pos5/training_summary.json`

## Teacher refinement status

`training/refine_weak_labels_nemotron.py` now:

- writes outputs incrementally
- truncates stale outputs on fresh runs
- supports `--resume`
- prints progress during long runs

Completed teacher pass:

- processed examples: `520`
- kept examples: `475`
- dropped examples: `45`

Refined-label XLM-R result:

- validation F1: `0.0784`
- validation IoU-F1: `0.0408`
- test F1: `0.1231`
- test IoU-F1: `0.0656`

Promotion decision:

- reject the refined-label model
- keep the class-weighted weak-label baseline as the current production candidate

Autoresearch status:

- first real cycle completed
- tested `pos4` and `pos6`
- no candidate beat the promoted baseline

Resume command:

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume
```

## Memory-aware defaults

- `batch_size=2`
- `eval_batch_size=2`
- `max_length=256`
- `gradient_accumulation_steps=4`
- `freeze_encoder_epochs=1`
- `unfreeze_last_n_layers=2`

These defaults are conservative and are intended for local Apple Silicon workflows.

## Next priorities

1. Inspect why teacher-refined labels collapsed recall
2. Try focal loss or tune `positive_class_weight` around the winning `5.0` run
3. Try a stricter teacher policy or a high-confidence subset instead of full replacement
4. Integrate StandUp4AI as the external benchmark target
