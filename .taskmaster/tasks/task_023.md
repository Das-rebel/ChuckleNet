# Task ID: 23

**Title:** Adaptive focal initial probe

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Test the first new non-built-in objective family against the clause-aware promoted baseline.

**Details:**

Added `adaptive_focal` support to training/xlmr_standup_word_level.py and training/run_xlmr_standup_pipeline.py, then ran the first clause-aware probes at experiments/xlmr_standup_adaptive_focal_clause_pos4_g20 and experiments/xlmr_standup_adaptive_focal_clause_pos4_g15. Both runs used the promoted weak-label recipe except for loss_type=adaptive_focal and focal_gamma values 2.0 / 1.5. Each reached validation F1 0.6000 and validation IoU-F1 0.5000, with test F1 0.6667 and test IoU-F1 0.5652. That means adaptive focal tied the promoted run on IoU but regressed on validation F1 and was therefore not promotable. Both checkpoint weights were pruned automatically.

**Test Strategy:**

No test strategy provided.
