# Real Implementation Status

## Current reality

The real implemented and validated path in this repository is the stand-up word-level XLM-R pipeline.

Working components:

- transcript conversion to word-level JSONL
- offline XLM-R training from local cache
- weak-label baseline training and evaluation
- local teacher refinement with incremental writes and resume

## Current artifacts

- dataset: `data/training/standup_word_level`
- weak-label baseline: `experiments/xlmr_standup_baseline_weak`
- current status: `CURRENT_STATUS.md`

## Current blocker

The full refined-label training run has not been completed yet because the teacher stage is long-running, not because the pipeline is structurally broken. The refinement script has been fixed to support resume.

## Do not rely on

- legacy reports claiming the old integrated system is fully complete
- legacy benchmark claims produced by simulated evaluators
