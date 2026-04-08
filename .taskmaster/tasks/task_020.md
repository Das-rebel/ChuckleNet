# Task ID: 20

**Title:** Second clause-aware autoresearch cycle

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Run the next evidence-gated clause-aware cycle on length and classifier-LR variants.

**Details:**

Ran `python3 training/autonomous_research_loop.py --max-experiments 2` again on the canonical clause-aware dataset fingerprint 6f1c7e67a16f247b4afdc64ea969275359a5d1b8. `pos5_len320` and `pos5_cls8e-5` both exactly matched the promoted clause-aware baseline at validation F1 0.6667 / IoU-F1 0.5000 and test F1 0.7222 / IoU-F1 0.5652. Neither candidate was promoted, both checkpoint weights were pruned automatically, and the next dry-run pair is `pos5_epochs4` and `pos5_cls6e-5`.

**Test Strategy:**

No test strategy provided.
