# Task ID: 15

**Title:** Full lexical-target teacher rerun

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Run the full clean teacher refinement with lexical_target_v2, rebuild the safe hybrid, and re-evaluate the teacher path end to end.

**Details:**

Completed the full clean teacher rerun with prompt version lexical_target_v2: 505 processed, 502 kept, 3 dropped, and 213 moved kept targets. Rebuilt the safe hybrid with a wider note-repair window (max_note_repair_shift=24), which accepted 205 note-repaired moves and reduced the remaining unresolved cluster to only 5 punctuation-heavy 'it' cases on one repeated coffee-cost template. Re-ran both training comparisons: full refined at experiments/xlmr_standup_baseline_refined_pos5_clean_lexical_v2 still lost at validation F1 0.3077 / IoU-F1 0.2778, while the rebuilt hybrid at experiments/xlmr_standup_safe_hybrid_note_repair_pos5_clean_shift24 improved to validation F1 0.4359 and test F1 0.5000 but still failed promotion because validation IoU-F1 stayed at 0.3333.

**Test Strategy:**

No test strategy provided.
