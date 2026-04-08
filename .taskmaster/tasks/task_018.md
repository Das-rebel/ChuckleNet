# Task ID: 18

**Title:** Clause-aware context promotion

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Promote clause-aware lexical context after a bounded adapted sweep on the retokenized split.

**Details:**

Tested PRD-aligned clause-aware context on an alternate overlap-safe dataset that keeps only the last lexical tokens from the previous non-empty clause. The old promoted checkpoint tied the older masked baseline on this data, so a bounded adapted sweep was run instead. `experiments/xlmr_standup_clause_lexical_tail_pos5_epochs4` improved validation F1 to 0.4444 but left validation IoU-F1 flat at 0.3333. `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted` then improved both validation gates to F1 0.6667 / IoU-F1 0.5000, with test F1 0.7222 / IoU-F1 0.5652. The saved-model eval was written to experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/clause_lexical_tail_eval.json, pipeline defaults were updated to clause-aware context plus unfreeze-last-n-layers=4, and the old checkpoint was pruned so only the promoted weight remains.

**Test Strategy:**

No test strategy provided.
