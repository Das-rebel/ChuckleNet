# Final Report

This file is no longer a claim that the entire historical integrated system is complete.

## Current truthful summary

The current validated production candidate in this repo is the stand-up-specific XLM-R pipeline:

- `training/convert_standup_raw_to_word_level.py`
- `training/refine_weak_labels_nemotron.py`
- `training/xlmr_standup_word_level.py`

Validated weak-label baseline:

- validation F1: `0.7045`
- validation IoU-F1: `0.6327`
- test F1: `0.8142`
- test IoU-F1: `0.7322`

Current source of truth:

- `AGENTS.md`
- `CURRENT_STATUS.md`
- `docs/XLMR_STANDUP_ROADMAP.md`

Historical integrated-stack reports in this repository should be treated as archived material unless they are explicitly audited.
