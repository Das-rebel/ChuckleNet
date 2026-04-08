# Task ID: 17

**Title:** Decode-only saturation check

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Test whether single-best-token decoding can move the real promotion gate without changing model weights.

**Details:**

Extended training/xlmr_standup_word_level.py, training/evaluate_saved_xlmr_model.py, and training/run_xlmr_standup_pipeline.py with decode_strategy support, including single_best decoding with a configurable margin. Evaluated the promoted baseline checkpoint across a margin sweep and stored the results in experiments/xlmr_standup_baseline_weak_pos5_clean/decode_sweep_single_best.json. The sweep materially improved token F1, reaching validation F1 0.5000 and test F1 0.5882, but validation IoU-F1 stayed fixed at 0.3333 across all tested margins. That closes the decode-only branch as another non-solution for the current blocker.

**Test Strategy:**

No test strategy provided.
