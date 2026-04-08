# Task ID: 21

**Title:** Later clause-aware autoresearch cycles

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Run the remaining built-in clause-aware cycles and confirm whether the queue is exhausted.

**Details:**

Ran two more evidence-gated clause-aware cycles on dataset fingerprint 6f1c7e67a16f247b4afdc64ea969275359a5d1b8. Cycle 3 tested `pos5_epochs4` and `pos5_cls6e-5`; both exactly matched the promoted clause-aware baseline at validation F1 0.6667 / IoU-F1 0.5000 and test F1 0.7222 / IoU-F1 0.5652. Cycle 4 tested `pos5_len384` and `focal_pos5_g10`; `pos5_len384` exactly matched the promoted baseline, while `focal_pos5_g10` tied both validation gates but regressed on test F1 to 0.6667. None of the four candidates were promoted, all non-promoted checkpoint weights were pruned automatically, and a follow-up dry-run now reports `candidate_count = 0`, meaning the built-in clause-aware queue is exhausted again.

**Test Strategy:**

No test strategy provided.
