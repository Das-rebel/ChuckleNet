# Task ID: 16

**Title:** Teacher branch saturation check

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Close the last residual teacher-repair gap and verify whether it actually changes model behavior.

**Details:**

Extended training/build_safe_hybrid_dataset.py with a token-level quoted-span fallback so phrases like "It's like they're recharging us for the cup!" can still recover the lexical token 'cup' when the full quote does not align exactly. Rebuilt the safe hybrid to 213 note-repaired moves and 0 unresolved moved-teacher cases, then trained experiments/xlmr_standup_safe_hybrid_note_repair_pos5_clean_shift24_fallback. The result exactly matched the earlier shift24 hybrid metrics: validation F1 0.4359, validation IoU-F1 0.3333, test F1 0.5000, test IoU-F1 0.3986. That confirms the current teacher branch is saturated under this architecture even after the residual repair gap is fully closed.

**Test Strategy:**

No test strategy provided.
