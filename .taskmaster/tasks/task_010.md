# Task ID: 10

**Title:** Built-in checkpoint pruning

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Add a storage-aware cleanup path so exploratory and benchmark runs can keep summaries without keeping tensor weights.

**Details:**

Extended training/xlmr_standup_word_level.py with --prune-best-model-weights so best_model tensor files are deleted after evaluation while leaving config/tokenizer artifacts and training_summary.json intact. Extended training/run_xlmr_standup_pipeline.py with --split-strategy and --prune-best-model-weights so WESR-balanced benchmark runs can be driven from the top-level runner without manual cleanup. Verified with a one-epoch smoke run in /tmp/xlmr_prune_smoke; the summary recorded removed_files=["model.safetensors"] and the best_model directory retained only lightweight tokenizer/config files.

**Test Strategy:**

No test strategy provided.
