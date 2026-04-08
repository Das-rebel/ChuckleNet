# Task ID: 22

**Title:** Clause-aware teacher refresh and comparison

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Regenerate teacher artifacts on the canonical clause-aware dataset, rebuild the hybrid, and compare both teacher-derived training paths to the active weak-label winner.

**Details:**

Re-ran training/refine_weak_labels_nemotron.py on data/training/standup_word_level/train.jsonl with prompt version lexical_target_v2 and completed 505/505 kept examples with zero drops. Refreshed docs/refined_label_audit_clean_summary.json now shows 134 moved targets and average absolute shift 3.739 tokens, while the rebuilt safe hybrid in data/training/standup_word_level/train_refined_safe_hybrid_summary.json accepted 371 same-index teacher labels and 134 note-repaired moved labels with zero rejections. Then trained clause-aware promotion-comparable comparisons with the active weak-label recipe (unfreeze_last_n_layers=4, positive_class_weight=4.0): full refined at experiments/xlmr_standup_baseline_refined_clause_unfreeze4_pos4 collapsed to validation F1 0.2000 / IoU-F1 0.1667 and test F1 0.3077 / IoU-F1 0.2464, while the rebuilt safe hybrid at experiments/xlmr_standup_safe_hybrid_clause_unfreeze4_pos4 reached validation F1 0.4444 / IoU-F1 0.3333 and test F1 0.6154 / IoU-F1 0.5072. Neither teacher-derived path was promotable, both checkpoints were pruned, and adaptive_focal support was added to the trainer and top-level pipeline as the next non-built-in objective family.

**Test Strategy:**

No test strategy provided.
