# Task ID: 13

**Title:** Residual teacher-gap analysis

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Document the exact moved-target cases still unresolved after PRD-aligned note repair.

**Details:**

Added training/analyze_remaining_teacher_repairs.py and generated docs/REMAINING_TEACHER_REPAIRS.md plus docs/remaining_teacher_repairs_summary.json. The result is narrow and concrete: all 13 remaining moved-target fallbacks are the same duplicated dating/beach template where the teacher note incorrectly quotes stopword 'My'. This means there is no safe lexical recovery available from note text alone, so the next teacher improvement should come from richer prompting or different note structure rather than another local heuristic.

**Test Strategy:**

No test strategy provided.
