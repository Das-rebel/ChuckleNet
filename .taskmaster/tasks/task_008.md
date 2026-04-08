# Task ID: 8

**Title:** WESR taxonomy evaluation reporting

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Add PRD-aligned discrete vs continuous laughter evaluation support and document current split limitations.

**Details:**

Extended training/xlmr_standup_word_level.py to carry laughter_type through evaluation and report per_laughter_type metrics. Added training/evaluate_saved_xlmr_model.py for post-hoc checkpoint evaluation. Confirmed the current clean split is WESR-imbalanced: train 264 continuous / 241 discrete, valid 102 continuous / 0 discrete, test 20 continuous / 3 discrete. The repaired hybrid can now be evaluated by laughter type, but the current split is too imbalanced for taxonomy-aware promotion decisions.

**Test Strategy:**

No test strategy provided.
