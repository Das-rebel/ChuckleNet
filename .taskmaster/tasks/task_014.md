# Task ID: 14

**Title:** Teacher prompt lexical guardrails

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Strengthen the teacher prompt to prefer content-bearing lexical targets and test it on the residual failure cluster.

**Details:**

Updated training/refine_weak_labels_nemotron.py to prompt version lexical_target_v2, explicitly steering the teacher away from punctuation and generic stopwords and requiring the chosen token to be quoted in note. Ran a bounded smoke test on the 13 residual dating/beach failures and observed 13/13 flips from stopword target 'My' to lexical target 'beach'. This is evidence that prompt quality can resolve the remaining cluster, but it is not yet a full clean-split teacher regeneration.

**Test Strategy:**

No test strategy provided.
