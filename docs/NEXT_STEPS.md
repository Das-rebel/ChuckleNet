# Next Steps

This file reflects the actual current plan.

## Immediate

1. Treat the `dialect_aware_contraction_v1` overlap-safe dataset with clause-aware context-masked scoring as the canonical evaluation base
2. Keep the clause-aware `pos5_unfreeze4` XLM-R checkpoint as the active winner under the current promotion policy
3. Treat pre-retokenization teacher and autoresearch results as historical guidance, separate from the new clause-aware teacher rerun
4. Treat `docs/REFINED_LABEL_AUDIT.md` as the explanation for the failed refined-label run on the old split
5. Treat `pos5_unfreeze4` as invalid on the old split because exact duplicate text existed across train/valid/test
6. Keep the overlap-safe split as the only trustworthy promotion base going forward
7. Treat the new clause-aware teacher rerun for prompt version `lexical_target_v2` as complete and non-promoted evidence, not as an open prerequisite
8. Treat `pos5_epochs4` as the closest pre-retokenization clean-split miss: higher validation F1, flat validation IoU-F1, therefore still not promotable
9. Treat the old clean autoresearch queue as exhausted for the old dataset fingerprint, not for the new retokenized fingerprint
10. Treat `af1af34e_pos4` as the first promoted result on the retokenized dataset fingerprint, but not the current winner
11. Treat WESR-style discrete/continuous evaluation as underpowered on the canonical clean split because validation has `0` discrete examples and test has only `3`
12. Treat `data/training/standup_word_level_wesr_balanced` as a benchmark-only companion split for taxonomy-aware evaluation, not as the canonical promotion split
13. Prefer `--prune-best-model-weights` on benchmark and exploratory runs to keep disk usage bounded
14. Leave `training/autonomous_research_loop.py` at its default of pruning non-promoted weights unless a checkpoint must be retained for manual debugging
15. Keep the promoted clause-aware `pos5_unfreeze4` checkpoint as the only retained experiment tensor unless another run is explicitly promoted or needs manual inspection
16. Treat the closed teacher-repair gap and decode-only saturation findings as informative pre-retokenization evidence, not as proof that those branches can never work on the new tokenization
17. Use the old teacher artifacts only for reference until `train_refined*.jsonl` is regenerated against the retokenized `train.jsonl`

## Baseline to beat

Current weak-label baseline:

- validation F1: `0.6667`
- validation IoU-F1: `0.5000`
- test F1: `0.7222`
- test IoU-F1: `0.5652`
- positive class weight: `4.0`
- unfreeze last N layers: `4`

Current clause-aware full-refined comparison:

- validation F1: `0.2000`
- validation IoU-F1: `0.1667`
- test F1: `0.3077`
- test IoU-F1: `0.2464`

Current clause-aware safe-hybrid comparison:

- validation F1: `0.4444`
- validation IoU-F1: `0.3333`
- test F1: `0.6154`
- test IoU-F1: `0.5072`

## Practical follow-up work

1. Treat the refreshed clause-aware teacher rerun as completed evidence: full refined still collapses, and safe hybrid still misses the validation gate
2. Treat the first dialect-adapter probe as completed neutral evidence: the branch is stable and instrumented, but the first bounded runs only tied the promoted baseline
3. Use the `--split-strategy wesr_balanced` path when taxonomy-aware benchmarking is needed, but keep the overlap-safe clean split as the promotion baseline until a comparable validation policy is defined
4. Treat the new external word-level benchmark bridge as implemented and verified; the immediate external-data task is now replacing the local demo StandUp4AI bundle, which currently has zero positive labels across all splits, with the real dataset
5. Keep audio out of the critical path until alignment quality is verified
6. Use `qwen2.5-coder:1.5b` as a teacher only, not as the main detector
7. Treat the old retokenized built-in autoresearch queue as historical, and treat the built-in clause-aware queue as exhausted
8. Treat `--context-token-policy lexical_tail --context-tail-tokens 6` as a tested PRD-aligned side path that ties the older masked baseline, while `clause_lexical_tail` is now the promoted default
9. The built-in clause-aware queue, the first `adaptive_focal` probe, the first bounded dialect-adapter probe, and the first contrast-gate probe are all exhausted as practical next steps
10. Do not replace the full weak-label dataset with teacher-refined labels without a promotion gate
11. Use `docs/LOCAL_TASK_LIST.md` as the fallback task tracker until Taskmaster CLI can create/update tasks again
12. Treat the public StandUp4AI `Examples_label` conversion as the first real non-demo external sanity benchmark, and treat its `0.0000 / 0.0000` result as an actual external failure signal
13. Treat the public StandUp4AI label geometry mismatch as real: the internal dataset trains on exactly one positive token per example, while the public slice averages `141` positive tokens and `3.837` tokens per positive span
14. Treat the first span-aware auxiliary probe as the first structural branch with measurable external gain: `r2w025` ties the internal winner and raises the chunked 4-example public slice to `0.0137 / 0.0169`, while `r3w05` raises it further to `0.0268 / 0.0407` but loses the internal validation F1 gate
15. Treat the first cue-aware token adapter probe as non-promoted evidence: it regresses the internal gate and reaches only `0.0170 / 0.0271` on the chunked 4-example public slice while English stays `0.0000 / 0.0000`
16. Treat `training/evaluate_wesr_benchmark_suite.py` plus `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_benchmark_suite.json` as the new taxonomy-aware baseline: `wesr_balanced` is a usable companion benchmark, but `promotion_ready = false` because validation still has only `3` discrete examples
17. Treat `data/training/standup_word_level_wesr_advanced` plus `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_advanced_suite.json` as the stronger taxonomy-rich companion benchmark: it is `promotion_ready = true` as a benchmark, but benchmark-only because its train split has only `18` examples
18. Treat cue-aware `topk_span` with ratio `0.10`, neighbor margin `-2.0`, max neighbors `2`, and cue bonus `1.0` as the strongest tested benchmark-time decode policy: it keeps canonical validation at `0.7500 / 0.8889` and lifts the public external slice to `0.2308 / 0.1980` plus the English-only slice to `0.1156 / 0.0747`
19. Keep the promoted model registry unchanged until autoresearch can compare candidates under the same decode regime; for now, cue-aware `topk_span` is a benchmark/evaluation policy, not the canonical training-loop default
20. Since the external English slice is now above zero under decode-side span expansion, prioritize stronger language/domain conditioning over more small hyperparameter sweeps
21. Treat cue-biased span supervision as the next benchmark-positive but non-promoted structural probe: it improves the English-only external slice further to `0.1322 / 0.0865`, but its canonical validation under the same `topk_span` decode falls to `0.6851 / 0.8595` and its full public slice reaches only `0.2037 / 0.1826`
22. Keep using the promoted checkpoint plus cue-aware `topk_span` as the external benchmark-time baseline until a new branch clearly beats it on canonical validation and on the full public external slice, not just on the English-only slice

## Resume command

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume
```
