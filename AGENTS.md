# Agent Handoff

This repository contains many historical status reports. Several of them overstate readiness or describe pipelines that are not the current path.

Start here:

1. `CURRENT_STATUS.md`
2. `docs/XLMR_STANDUP_ROADMAP.md`
3. `data/training/standup_word_level/README.md`
4. `experiments/promoted_model.json`
5. `docs/AUTORESEARCH.md`

## Current canonical path

The active training pipeline is:

1. `training/convert_standup_raw_to_word_level.py`
2. `training/refine_weak_labels_nemotron.py`
3. `training/xlmr_standup_word_level.py`
4. `training/run_xlmr_standup_pipeline.py`
5. `training/autonomous_research_loop.py`

This is a stand-up-focused, text-first, word-level sequence-labeling pipeline.

## Validated state as of 2026-03-29

- Main backbone: `FacebookAI/xlm-roberta-base`
- Local teacher: `qwen2.5-coder:1.5b`
- Promoted current winner: weak-label XLM-R with `positive_class_weight=5.0`
- Best promoted metrics:
  - validation F1: `0.7850`
  - validation IoU-F1: `0.7891`
  - test F1: `0.8194`
  - test IoU-F1: `0.8798`
- Promoted output dir: `experiments/xlmr_standup_baseline_weak_pos5`
- Teacher refinement completed successfully with incremental writes and `--resume`
- Teacher refinement output: `475` kept, `45` dropped
- Refined-label XLM-R run underperformed badly and is not the promoted model
  - refined validation F1: `0.0784`
  - refined test F1: `0.1231`
- First real autoresearch cycle completed with no promotion
  - tested `pos4` and `pos6`
  - both lost to the promoted baseline

## Important constraints

- Do not assume legacy "production ready" reports are accurate.
- TurboQuant matters for KV-cache-heavy LLM inference, not for selecting the main encoder backbone here.
- The main model choice is still XLM-R, not a quantized chat model.
- The current winning checkpoint is `experiments/xlmr_standup_baseline_weak_pos5`.

## Historical files

Treat these as historical unless they are explicitly brought up for audit:

- `AGENT_*`
- `*_FINAL_SUMMARY.md`
- `*_COMPLETION_REPORT.md`
- old top-level deployment/status reports
- `research_log.json` entries without `loop_version = "real_v1"`

## Resume command

If refinement is interrupted, resume with:

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume
```
