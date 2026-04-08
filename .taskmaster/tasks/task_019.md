# Task ID: 19

**Title:** First clause-aware autoresearch cycle

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Run the first evidence-gated autoresearch cycle against the promoted clause-aware baseline.

**Details:**

Regenerated the canonical dataset with clause-aware context, confirmed the new promoted baseline in experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted, and ran `python3 training/autonomous_research_loop.py --max-experiments 2` on dataset fingerprint 6f1c7e67a16f247b4afdc64ea969275359a5d1b8. `focal_pos5_g15` reached validation F1 0.6000 and test F1 0.6667 but only tied validation IoU-F1 at 0.5000. `pos6` exactly matched the promoted baseline on validation and test. Neither candidate was promoted, both non-promoted checkpoints were pruned automatically, and the next dry-run pair is `pos5_len320` and `pos5_cls8e-5`.

**Test Strategy:**

No test strategy provided.
