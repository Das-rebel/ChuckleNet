# Task ID: 11

**Title:** Autoresearch weight pruning

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Keep future autoresearch cycles from re-accumulating checkpoint tensors for non-promoted candidates.

**Details:**

Extended training/autonomous_research_loop.py so non-promoted candidate checkpoint weights are pruned by default after metrics are recorded, with an escape hatch via --keep-non-promoted-weights. Verified in /tmp/autoresearch_prune_smoke with a real pos4 clean-split run: the cycle record logged checkpoint_cleanup.removed_files=["model.safetensors"], the candidate remained non-promoted, and the experiment directory retained only tokenizer/config files plus training_summary.json.

**Test Strategy:**

No test strategy provided.
