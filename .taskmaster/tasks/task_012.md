# Task ID: 12

**Title:** Promoted checkpoint restoration

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Restore the canonical clean baseline checkpoint so the promoted registry points to a loadable model, not just a summary.

**Details:**

Re-trained experiments/xlmr_standup_baseline_weak_pos5_clean with the exact promoted weak-label recipe and reproduced the canonical metrics: validation F1 0.3636 / IoU-F1 0.3333 and test F1 0.4444 / IoU-F1 0.4058. The best_model directory now includes model.safetensors again, training_summary.json records checkpoint_artifacts.weights_pruned=false, and a standalone saved-model evaluation was written to experiments/xlmr_standup_baseline_weak_pos5_clean/wesr_eval.json.

**Test Strategy:**

No test strategy provided.
