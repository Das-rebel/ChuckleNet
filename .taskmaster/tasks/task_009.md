# Task ID: 9

**Title:** WESR-balanced benchmark split

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Add an alternate overlap-safe split mode that supports taxonomy-aware benchmarking without replacing the canonical clean split.

**Details:**

Extended training/convert_standup_raw_to_word_level.py with --split-strategy wesr_balanced so component assignment can favor discrete/continuous coverage in validation and test. Generated data/training/standup_word_level_wesr_balanced with zero exact overlap, counts 502 train / 23 valid / 105 test, and both laughter types present in valid and test. Trained a benchmark weak-label baseline that reached validation F1 0.8636 / IoU-F1 0.8116 and test F1 0.5714 / IoU-F1 0.6667, but documented it as benchmark-only because the validation split is much smaller than the canonical clean split.

**Test Strategy:**

No test strategy provided.
