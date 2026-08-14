# Local Task List

Date: 2026-04-01

This file is the fallback task tracker while Taskmaster CLI updates are blocked by missing API keys.

## Done

1. Clause-aware weak-label baseline promoted and checkpoint preserved.
2. Clause-aware teacher rerun and safe-hybrid comparison completed; neither promoted.
3. `adaptive_focal` branch implemented and tested; not promoted.
4. Lightweight dialect-aware adapter branch implemented and tested; tied the promoted baseline.
5. External word-level benchmark bridge implemented in `training/evaluate_external_wordlevel_benchmark.py`.
6. Bridge smoke run verified against the current promoted checkpoint.
7. First local StandUp4AI bridge run completed and diagnosed the local dataset as demo-only / degenerate.
8. Public StandUp4AI repo resolved and downloaded to `/tmp/standup4ai_dataset_main`.
9. Public `Examples_label/*.csv` files converted into `benchmarks/data/standup4ai_examples.jsonl`.
10. First real non-demo external sanity run completed; promoted checkpoint scored `0.0000 / 0.0000`.
11. English-only rerun and `max_length=512` rerun also stayed at `0.0000 / 0.0000`.
12. Chunked full-coverage external rerun completed; 4-example public slice improved only to `0.0104 / 0.0204`, while the English-only slice remained `0.0000 / 0.0000`.
13. First GCACU-lite contrast-gate probe completed; internal validation tied, test regressed, and chunked public external score dropped to `0.0035 / 0.0102`.
14. External label-geometry audit completed: the internal clause-aware dataset has exactly one positive token per example, while the public StandUp4AI slice averages `141` positive tokens and `3.837` tokens per positive span.
15. Span-aware auxiliary supervision branch implemented in `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py`.
16. First span-aware probe (`r2w025`) completed; it tied the internal promoted baseline and improved the chunked 4-example public slice to `0.0137 / 0.0169`, while English stayed `0.0000 / 0.0000`.
17. Stronger span-aware probe (`r3w05`) completed; it improved the chunked 4-example public slice to `0.0268 / 0.0407` but regressed internal validation F1 to `0.6000`, so it was not promotable.
18. Non-promoted span-aware checkpoints were pruned after evaluation.
19. English public-slice inspection completed; the promoted model's few positive hits land far from the labeled filler/discourse spans.
20. Cue-aware token adapter branch implemented in `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py`.
21. First cue-plus-span probe completed; it regressed the internal gate to validation F1 `0.5455`, reached only `0.0170 / 0.0271` on the chunked 4-example public slice, and still stayed `0.0000 / 0.0000` on the English-only slice.
22. Non-promoted cue checkpoint was pruned after evaluation.
23. Per-type IoU-F1 reporting added to `training/xlmr_standup_word_level.py`.
24. `training/evaluate_wesr_benchmark_suite.py` implemented and run on the promoted checkpoint.
25. WESR suite baseline recorded: `wesr_balanced` is a usable companion benchmark with validation macro F1 / IoU-F1 `0.6694 / 0.6694` and test macro F1 / IoU-F1 `0.7500 / 0.7500`, but `promotion_ready = false` because validation has only `3` discrete examples.
26. `wesr_advanced` split strategy implemented in `training/convert_standup_raw_to_word_level.py`.
27. Advanced WESR companion dataset generated at `data/training/standup_word_level_wesr_advanced` with validation `122` continuous / `123` discrete and test `246` continuous / `121` discrete.
28. Advanced WESR suite run completed on the promoted checkpoint: validation macro F1 / IoU-F1 `0.9959 / 0.9959`, test macro F1 / IoU-F1 `0.8963 / 0.8963`, `promotion_ready = true` as a benchmark, but benchmark-only because the train split has only `18` examples.
29. Decode-only `topk_span` strategy implemented across trainer/evaluators/pipeline.
30. Bounded `topk_span` sweep completed on the promoted checkpoint; best tested setting is ratio `0.10`, neighbor margin `-2.0`, max neighbors `2`.
31. Best `topk_span` decode raises the public external slice to `0.2135 / 0.1724` and the English-only slice to `0.0978 / 0.0586`, while improving canonical validation IoU-F1 to `0.8889`.
32. Model registry intentionally left unchanged; `topk_span` is recorded as the strongest benchmark-time decode policy, not yet the training-loop default.
33. Cue-biased span supervision implemented in `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` via `--cue-span-bias-enabled` and `--cue-span-bias-strength`.
34. Bounded cue-biased span probe completed at `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075`; default argmax regressed to validation F1 `0.6000` while only tying validation IoU-F1 at `0.5000`, so it was not promotable.
35. Under the best `topk_span` decode, that cue-biased checkpoint reached canonical validation `0.6851 / 0.8595`, public external `0.2037 / 0.1826`, and English-only external `0.1322 / 0.0865`.
36. Cue-biased span supervision is therefore the strongest English-only external branch so far, but it still does not beat the promoted checkpoint plus `topk_span` on the full public slice or on the canonical validation gate.
37. Cue-aware reranking was added to `topk_span` via `--topk-span-cue-bonus` in the trainer and evaluator stack.
38. Bounded cue-aware decode sweep completed at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_sweep/summary.json`.
39. Best tested cue-aware decode is ratio `0.10`, neighbor margin `-2.0`, max neighbors `2`, cue bonus `1.0`; it keeps canonical validation at `0.7500 / 0.8889` and improves the public external slice to `0.2308 / 0.1980` plus the English-only slice to `0.1156 / 0.0747`.
40. Cue-aware `topk_span` is now the strongest benchmark-time decode policy and replaces plain `topk_span` as the decode baseline for future external comparisons.

## Next

1. Replace `/Users/Subho/data/standup4ai` demo annotations with the real StandUp4AI dataset if a packaged release is obtainable.
2. Use the WESR suite as a required companion benchmark, but keep the canonical split as the only promotion gate until the taxonomy validation support is stronger.
3. Use `wesr_advanced` as the stronger taxonomy companion benchmark and keep `wesr_balanced` only as a lighter secondary reference.
4. Treat cue-aware `topk_span` as the current best benchmark-time decode policy and use it as the decode baseline for future external comparisons.
5. Prioritize stronger language/domain conditioning now that decode-side span expansion already pushed the English external slice above zero.
6. Prefer structural/domain-transfer work over more local decode or minor hyperparameter sweeps.
7. After the next structural branch, re-run both chunked external slices, the `wesr_advanced` suite, and the best `topk_span` decode comparison before trusting any internal gain.
8. Keep using the chunked external eval outputs (`standup4ai_examples_eval_chunk128.json`, `standup4ai_examples_en_eval_chunk128.json`) as the current external reality check.
9. Treat the first contrast-gate branch, the first span-aware branch, the first cue-aware branch, and the first cue-biased span branch as exhausted baseline references for future domain-transfer work.
10. Keep the promoted checkpoint plus cue-aware `topk_span` as the benchmark-time baseline until a new branch beats it on both canonical validation and the full public external slice.

## Blockers

1. `task-master add-task` and related AI-backed updates fail because `ANTHROPIC_API_KEY` and `PERPLEXITY_API_KEY` are not configured.
2. The local `/Users/Subho/data/standup4ai` bundle is a demo dataset with zero positive labels in every split, so it cannot support a meaningful full-benchmark score.
3. The public `https://github.com/Standup4AI/dataset` repo exposes only example labels plus data-generation code, not a packaged full benchmark release.
