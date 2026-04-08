# Task ID: 7

**Title:** PRD-aligned trigger localization improvements

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Implement and evaluate PRD-aligned trigger-localization improvements for teacher-refined stand-up labels.

**Details:**

Implemented note-anchored lexical repair for teacher-retargeted punctuation/stopword moves in training/build_safe_hybrid_dataset.py, rebuilt the clean hybrid dataset, and evaluated it against the clean weak-label baseline. The repaired hybrid accepted 51 note-repaired moved targets and reached validation F1 0.4000 with validation IoU-F1 0.3333, so it improved plain F1 but did not beat the baseline on the dual-metric promotion gate.

**Test Strategy:**

No test strategy provided.
