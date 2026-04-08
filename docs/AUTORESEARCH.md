# Autoresearch

The current autoresearch loop is implemented in:

- `training/autonomous_research_loop.py`

It is a real experiment runner for the stand-up XLM-R pipeline, not the older simulated loop.

## What it does

1. Reads the current promoted baseline from `experiments/promoted_model.json`
2. Proposes a small set of bounded training variants
3. Runs the real trainer
4. Compares candidates against the promoted baseline
5. Promotes only if both validation F1 and validation IoU-F1 improve

## Current source of truth

- promoted registry: `experiments/promoted_model.json`
- research log: `research_log.json`

Important:

- only trust entries with `loop_version = "real_v1"` as evidence-backed autoresearch cycles
- older entries in `research_log.json` are historical simulated runs

## First real cycle

Cycle `real_v1` #1 tested:

- `pos4`
- `pos6`

Both underperformed the promoted baseline on validation metrics, so neither was promoted.

Cycle `real_v1` #2 tested:

- `focal_pos5_g15`
- `pos5_len320`

Results:

- `focal_pos5_g15` raised recall but hurt validation F1, so it failed the dual-metric promotion gate
- `pos5_len320` tied the promoted baseline exactly and was not promoted

Cycle `real_v1` #3 tested:

- `pos5_unfreeze4`
- `pos5_cls8e-5`

Results:

- `pos5_unfreeze4` achieved apparent `1.0` metrics, but exact split overlap was later confirmed, so this result is not trusted
- `pos5_cls8e-5` underperformed the weak-label baseline
- autoresearch now blocks promotion when exact split overlap is present

Current split-overlap counts:

- train/valid exact token overlap: `31`
- train/test exact token overlap: `26`
- valid/test exact token overlap: `13`

Baseline remained:

- `experiments/xlmr_standup_baseline_weak_pos5_clean`
- validation F1: `0.3636`
- validation IoU-F1: `0.3333`
- test F1: `0.4444`
- test IoU-F1: `0.4058`

First clean-split cycle (`dataset_fingerprint = e05376af...`) tested:

- `pos4`
- `focal_pos5_g15`

Results:

- `pos4` improved validation F1 but only tied validation IoU-F1, so it was not promoted
- `focal_pos5_g15` tied both validation gates, so it was not promoted
- candidate output dirs are now namespaced by dataset fingerprint to avoid stale summary reuse

Second clean-split cycle (`dataset_fingerprint = e05376af...`) tested:

- `pos6`
- `pos5_len320`

Results:

- `pos6` did not improve either validation gate and regressed on test metrics
- `pos5_len320` exactly matched the clean baseline and was not promoted

Third clean-split cycle (`dataset_fingerprint = e05376af...`) tested:

- `pos5_unfreeze4`
- `pos5_cls8e-5`

Results:

- `pos5_unfreeze4` improved validation F1 and test F1, but validation IoU-F1 stayed flat, so it was not promoted
- `pos5_cls8e-5` matched the clean validation gates and underperformed on test

Clean-split safety state:

- exact overlap counts are `0 / 0 / 0`
- promotion is safe on the current split
- non-promoted candidate checkpoint weights are pruned by default after metrics are recorded, so autoresearch stays disk-bounded unless `--keep-non-promoted-weights` is explicitly used
- the promoted clean baseline checkpoint has been restored and is the only experiment tensor weight intentionally retained

Retokenized baseline reset:

- `training/convert_standup_raw_to_word_level.py` now uses `dialect_aware_contraction_v1`, which keeps contractions like `don't`, `I'm`, and `they're` as lexical tokens instead of `don ' t` fragments
- the canonical overlap-safe dataset still has `505 / 102 / 23` examples and exact overlap `0 / 0 / 0`, but it now has `0` standalone apostrophe tokens in train
- the old promoted checkpoint was re-evaluated on the retokenized dataset at `experiments/xlmr_standup_baseline_weak_pos5_clean/retokenized_eval.json` and dropped to validation F1 `0.2667` / IoU-F1 `0.2500`, test F1 `0.3390` / IoU-F1 `0.3333`
- the retrained PRD-aligned baseline at `experiments/xlmr_standup_baseline_weak_pos5_clean_dialecttok` improved that to validation F1 `0.3119` / IoU-F1 `0.2778`, test F1 `0.3922` / IoU-F1 `0.3696`
- consequence: future autoresearch cycles should treat the retokenized dataset as a fresh fingerprint and should not compare directly against the older `e05376af...` history without that caveat

First retokenized cycle (`dataset_fingerprint = af1af34e...`) tested:

- `pos4`
- `focal_pos5_g15`

Results:

- `pos4` improved both validation gates and was promoted over the interim retokenized baseline
- promoted `pos4` metrics: validation F1 `0.3383`, validation IoU-F1 `0.3333`, test F1 `0.4545`, test IoU-F1 `0.4203`
- `focal_pos5_g15` matched or underperformed the interim retokenized baseline and was not promoted; its checkpoint weights were pruned

Second retokenized cycle (`dataset_fingerprint = af1af34e...`) tested:

- `pos6`
- `pos5_len320`

Results:

- `pos6` underperformed the promoted `pos4` run on both validation gates and on test metrics
- `pos5_len320` exactly matched the promoted `pos4` metrics and was not promoted
- both non-promoted checkpoint weights were pruned

Third retokenized cycle (`dataset_fingerprint = af1af34e...`) tested:

- `pos5_unfreeze4`
- `pos5_cls8e-5`

Results:

- `pos5_unfreeze4` improved validation F1 to `0.5000` and test F1 to `0.6061`, but validation IoU-F1 stayed flat at `0.3333`, so it was not promoted
- `pos5_cls8e-5` exactly matched the promoted validation gates and regressed on test
- both non-promoted checkpoint weights were pruned

Fourth retokenized cycle (`dataset_fingerprint = af1af34e...`) tested:

- `pos5_epochs4`
- `pos5_cls6e-5`

Results:

- `pos5_epochs4` improved validation F1 to `0.5000` and test F1 to `0.5882`, but validation IoU-F1 stayed flat at `0.3333`, so it was not promoted
- `pos5_cls6e-5` exactly matched the promoted validation gates and regressed on test
- both non-promoted checkpoint weights were pruned

Fifth retokenized cycle (`dataset_fingerprint = af1af34e...`) tested:

- `pos5_len384`
- `focal_pos5_g10`

Results:

- `pos5_len384` exactly matched the promoted `pos4` metrics and was not promoted
- `focal_pos5_g10` improved only test metrics, with test F1 `0.4348` and test IoU-F1 `0.4348`, but left both validation gates flat at `0.3383 / 0.3333`
- both non-promoted checkpoint weights were pruned
- the built-in retokenized candidate queue is now exhausted again: `candidate_count = 0`

Context-masked baseline reset:

- `training/convert_standup_raw_to_word_level.py` now records `metadata.current_segment_start`
- `training/xlmr_standup_word_level.py` now masks prepended context tokens out of loss/evaluation while keeping them in the model input
- this produced a new canonical dataset fingerprint: `f368e999...`
- the active promoted checkpoint `af1af34e_pos4` was re-evaluated under context-masked scoring at `experiments/autoresearch/af1af34e_pos4/context_mask_eval.json`
- current masked baseline metrics: validation F1 `0.4000`, validation IoU-F1 `0.3333`, test F1 `0.5128`, test IoU-F1 `0.4348`
- a fresh masked retrain at `experiments/xlmr_standup_ctxmask_pos4` matched validation but was slightly worse on test, so it was not promoted and its checkpoint weight was pruned
- `training/autonomous_research_loop.py` now skips redundant candidates that exactly match the active baseline config
- first context-masked dry-run candidates are `focal_pos5_g15` and `pos6`
- PRD-guided lexical-tail context was also tested via `--context-token-policy lexical_tail --context-tail-tokens 6`
- the lexical-tail alternate dataset at `data/training/standup_word_level_lexical_tail` kept overlap at `0 / 0 / 0`, but both checkpoint re-eval and a fresh `experiments/xlmr_standup_lexical_tail_pos4` retrain tied the masked baseline instead of improving it
- PRD-guided clause-aware lexical context was then tested via `--context-token-policy clause_lexical_tail --context-tail-tokens 6`
- the clause-aware alternate dataset at `data/training/standup_word_level_clause_lexical_tail` also kept overlap at `0 / 0 / 0`
- a checkpoint re-eval of the old promoted `af1af34e_pos4` on clause-aware data tied the masked baseline exactly at validation `0.4000 / 0.3333` and test `0.5128 / 0.4348`
- an adapted clause-aware `experiments/xlmr_standup_clause_lexical_tail_pos5_epochs4` run improved validation F1 to `0.4444` and test F1 to `0.5405`, but validation IoU-F1 stayed flat at `0.3333`
- a second adapted clause-aware run at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted` then improved both validation gates and became the new promoted baseline: validation F1 `0.6667`, validation IoU-F1 `0.5000`, test F1 `0.7222`, test IoU-F1 `0.5652`
- consequence: `clause_lexical_tail` is no longer just a side path; it is now the canonical context policy to beat
- first clause-aware autoresearch cycle (`dataset_fingerprint = 6f1c7e67...`) then tested `focal_pos5_g15` and `pos6`
- `focal_pos5_g15` improved only plain F1, reaching validation F1 `0.6000` and test F1 `0.6667`, but validation IoU-F1 only tied the promoted run at `0.5000`
- `pos6` exactly matched the promoted clause-aware baseline on validation and test, so neither candidate was promoted and both checkpoint weights were pruned
- second clause-aware autoresearch cycle (`dataset_fingerprint = 6f1c7e67...`) then tested `pos5_len320` and `pos5_cls8e-5`
- both `pos5_len320` and `pos5_cls8e-5` exactly matched the promoted clause-aware baseline on validation and test, so neither candidate was promoted and both checkpoint weights were pruned
- third clause-aware autoresearch cycle (`dataset_fingerprint = 6f1c7e67...`) then tested `pos5_epochs4` and `pos5_cls6e-5`
- both `pos5_epochs4` and `pos5_cls6e-5` exactly matched the promoted clause-aware baseline on validation and test, so neither candidate was promoted and both checkpoint weights were pruned
- fourth clause-aware autoresearch cycle (`dataset_fingerprint = 6f1c7e67...`) then tested `pos5_len384` and `focal_pos5_g10`
- `pos5_len384` exactly matched the promoted clause-aware baseline, while `focal_pos5_g10` tied both validation gates but regressed on test F1 to `0.6667`
- consequence: the built-in clause-aware queue is now exhausted again, with dry-run reporting `candidate_count = 0`

Teacher-derived clean-split comparison:

- full refined (`experiments/xlmr_standup_baseline_refined_pos5_clean_lexical_v2`) still lost to the weak baseline on both validation gates even after the `lexical_target_v2` teacher rerun
- the final repaired safe hybrid (`experiments/xlmr_standup_safe_hybrid_note_repair_pos5_clean_shift24_fallback`) improved validation F1 to `0.4359`, but validation IoU-F1 stayed flat at `0.3333`
- same-index teacher accepts are metadata-only, so the useful teacher path is smarter moved-target repair rather than stricter filtering alone
- WESR-style evaluation is now available via `training/evaluate_saved_xlmr_model.py`, but the current clean validation split is `continuous`-only and the test split has only `3` discrete examples, so taxonomy-aware comparison is still data-limited
- `training/convert_standup_raw_to_word_level.py` now supports `--split-strategy wesr_balanced`, which generates a separate overlap-safe benchmark split with discrete and continuous examples in both validation and test
- the resulting benchmark dataset (`data/training/standup_word_level_wesr_balanced`) reached validation F1 `0.8636` / IoU-F1 `0.8116` and test F1 `0.5714` / IoU-F1 `0.6667`, but those numbers are not promotion-comparable because the benchmark validation split is only `23` examples
- `training/analyze_remaining_teacher_repairs.py` now shows `0` unresolved moved-teacher cases under the current policy
- `training/refine_weak_labels_nemotron.py` now uses prompt version `lexical_target_v2`, which explicitly asks for a content-bearing lexical target and an exact quoted token in `note`
- the bounded residual smoke run on the old `13` `My` cases was confirmed by the full clean rerun, and the final punctuation-heavy `it` cluster was also closed by the token fallback; despite that, the overall teacher path still did not move validation IoU-F1
- `single_best` decode sweeps on the promoted baseline increased validation F1 up to `0.5000` and test F1 up to `0.5882`, but validation IoU-F1 remained fixed at `0.3333`, so decode-only sharpening is also not enough
- the teacher and decode-only saturation findings above are all pre-retokenization results; they remain useful directional evidence, but the active canonical dataset is now the retokenized one
- the teacher branch has now also been rerun on the canonical clause-aware dataset: `docs/refined_label_audit_clean_summary.json` shows `505/505` kept, `134` moved targets, zero drops, and reduced average absolute shift to `3.739` tokens
- despite that healthier teacher profile, full replacement at `experiments/xlmr_standup_baseline_refined_clause_unfreeze4_pos4` still collapsed to validation F1 `0.2000` / IoU-F1 `0.1667`
- the rebuilt clause-aware safe hybrid at `experiments/xlmr_standup_safe_hybrid_clause_unfreeze4_pos4` improved test F1 to `0.6154`, but validation IoU-F1 remained only `0.3333`, so it also failed promotion
- consequence: the clause-aware teacher branch is refreshed and evidence-backed now, and it still does not beat the weak-label winner under the current architecture
- `training/xlmr_standup_word_level.py` now supports `adaptive_focal` as a new non-built-in objective family
- first adaptive-focal probe then tested `experiments/xlmr_standup_adaptive_focal_clause_pos4_g20` and `experiments/xlmr_standup_adaptive_focal_clause_pos4_g15`
- `training/xlmr_standup_word_level.py` now also supports a lightweight dialect-aware adapter branch, with heuristic buckets (`neutral`, `contraction_heavy`, `colloquial`) carried through evaluation as `per_dialect_bucket`
- first bounded dialect-adapter probe then tested `experiments/xlmr_standup_clause_dialect_adapter_pos5_unfreeze4_s025` and `experiments/xlmr_standup_clause_dialect_adapter_pos5_unfreeze4_s050`
- both adapter strengths exactly matched the promoted clause-aware baseline on the real promotion metrics: validation F1 `0.6667`, validation IoU-F1 `0.5000`, test F1 `0.7222`, test IoU-F1 `0.5652`
- consequence: the dialect-aware adapter path is now a real, reproducible branch rather than a PRD idea, but the first bounded probe is neutral evidence and does not justify promotion
- `training/evaluate_external_wordlevel_benchmark.py` now bridges the current saved XLM-R checkpoints to external JSON / JSONL / CSV word-level benchmark files using the same evaluator as the canonical training loop
- the bridge was smoke-tested with `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/external_bridge_smoke.json`, which exactly reproduced the promoted checkpoint's saved-model test metrics on a format-compatible benchmark file
- consequence: the blocking item for true external validation is now dataset availability, not evaluator plumbing
- the first actual local StandUp4AI bridge run at `benchmarks/results/standup4ai_bridge_eval.json` returned F1 `0.0000` / IoU-F1 `0.0000`, but inspection of `/Users/Subho/data/standup4ai/annotations/*.json` showed the local bundle is demo-only and has zero positive labels in every split
- `training/evaluate_external_wordlevel_benchmark.py --fail-on-degenerate-benchmark` now fails fast on that local bundle with `no_positive_tokens, no_positive_examples`, so future external runs will not silently treat the demo set as a credible benchmark
- consequence: the next external-validation blocker is not code or model behavior; it is obtaining the real StandUp4AI annotations instead of the all-negative demo set
- the paper's public dataset URL was resolved to `https://github.com/Standup4AI/dataset`, and the public repo was downloaded to `/tmp/standup4ai_dataset_main`
- that repo does not ship a packaged full benchmark split, but it does include four real labeled token-level example CSVs under `Examples_label/`
- `training/convert_standup4ai_examples_to_jsonl.py` now converts those public example files into `benchmarks/data/standup4ai_examples.jsonl`
- the first real non-demo external sanity run at `benchmarks/results/standup4ai_examples_eval.json` scored F1 `0.0000` / IoU-F1 `0.0000` on four usable examples across `en`, `fr`, `es`, and `cs`
- the English-only slice at `benchmarks/results/standup4ai_examples_en_eval.json` also scored `0.0000 / 0.0000`, and a wider `max_length=512` eval at `benchmarks/results/standup4ai_examples_en_eval_len512.json` still stayed at `0.0000 / 0.0000`
- chunked full-coverage evaluation with `--chunk-word-window 128 --chunk-word-stride 128` then produced the first non-truncation external result at `benchmarks/results/standup4ai_examples_eval_chunk128.json`: F1 `0.0104`, IoU-F1 `0.0204`, support `564`
- the chunked English-only slice at `benchmarks/results/standup4ai_examples_en_eval_chunk128.json` still scored `0.0000 / 0.0000`, so the failure is not explained away by multilingual mismatch alone
- consequence: external failure is now evidence-backed even on a small public StandUp4AI slice, and it is not explained away by the demo bundle, by the default `max_length=256`, or by incomplete long-sequence coverage
- `training/xlmr_standup_word_level.py` now also supports a GCACU-lite `--contrast-gate-enabled` branch that computes token-vs-context mismatch features before classification
- first contrast-gate probe at `experiments/xlmr_standup_clause_contrast_gate_pos5_unfreeze4/training_summary.json` tied the internal validation gate at `0.6667 / 0.5000` but regressed test F1 to `0.6667`
- external re-evaluation of that checkpoint at `experiments/xlmr_standup_clause_contrast_gate_pos5_unfreeze4/standup4ai_examples_eval_chunk128.json` reached only F1 `0.0035`, IoU-F1 `0.0102`, which is worse than the promoted baseline on the same public slice
- the chunked English-only external slice at `experiments/xlmr_standup_clause_contrast_gate_pos5_unfreeze4/standup4ai_examples_en_eval_chunk128.json` stayed at `0.0000 / 0.0000`
- consequence: the first explicit contrast/incongruity branch is now evidence-backed and still non-promoted; the next structural branch should be more overtly domain-transfer aware instead of another simple token-context gate
- external label-geometry audit then showed why transfer is so hard: the internal clause-aware dataset still has exactly `1` positive token per example, while the public StandUp4AI slice averages `141` positive tokens per example and `3.837` tokens per positive span
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now support a span-aware auxiliary supervision branch that adds decayed neighboring targets around the weak trigger token without changing the canonical evaluation labels
- first span-aware probe at `experiments/xlmr_standup_clause_span_aux_pos5_unfreeze4_r2w025` tied the promoted baseline exactly on the internal validation and test gates, while improving the chunked 4-example public StandUp4AI slice from F1 `0.0104` / IoU-F1 `0.0204` to F1 `0.0137` / IoU-F1 `0.0169`
- the chunked English-only external slice for `r2w025` still stayed at `0.0000 / 0.0000`, so the gain is not yet solving the hardest transfer case
- stronger span-aware probe at `experiments/xlmr_standup_clause_span_aux_pos5_unfreeze4_r3w05` improved the chunked 4-example public slice further to F1 `0.0268` / IoU-F1 `0.0407`, but internal validation F1 fell to `0.6000` while validation IoU-F1 only tied at `0.5000`, so it was not promoted
- consequence: span-aware supervision is the first structural branch to produce a measurable external gain on the public StandUp4AI slice, but it currently trades away the internal promotion gate and still leaves the English-only slice at `0.0000 / 0.0000`
- direct inspection of the promoted model's English public-slice hits then showed the few positive predictions landing far from the labeled filler/discourse spans, often on content words such as `other` and `yesterday`
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support a cue-aware token adapter branch that conditions on heuristic filler, discourse, and punctuation buckets
- first cue-plus-span probe at `experiments/xlmr_standup_clause_cue_span_pos5_unfreeze4_r2w025` regressed internal validation F1 to `0.5455` while only tying validation IoU-F1 at `0.5000`
- that same cue-plus-span checkpoint reached only F1 `0.0170` / IoU-F1 `0.0271` on the chunked 4-example public StandUp4AI slice and still stayed at `0.0000 / 0.0000` on the chunked English-only slice
- consequence: heuristic cue conditioning is now evidence-backed and non-promoted; it does not solve the English external failure and is weaker than the stronger span-aware branch
- `training/xlmr_standup_word_level.py` now reports per-type IoU-F1 in addition to per-type F1, and `training/evaluate_wesr_benchmark_suite.py` now evaluates a saved checkpoint across the canonical and `wesr_balanced` splits in one taxonomy-aware JSON report
- the promoted checkpoint's suite report at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_benchmark_suite.json` shows the current evaluation boundary clearly: canonical validation is still taxonomy-unusable because it only contains `continuous`, while `wesr_balanced` is a usable companion benchmark with validation macro F1 / IoU-F1 `0.6694 / 0.6694` and test macro F1 / IoU-F1 `0.7500 / 0.7500`
- the same suite also marks `wesr_balanced` as `promotion_ready = false` because validation still has only `3` discrete examples, so it should remain a companion benchmark rather than replace the canonical promotion gate
- `training/convert_standup_raw_to_word_level.py` now also supports `--split-strategy wesr_advanced`, which prioritizes strong discrete/continuous support in evaluation splits rather than count-target matching
- the resulting benchmark dataset at `data/training/standup_word_level_wesr_advanced` has validation `122` continuous / `123` discrete and test `246` continuous / `121` discrete with zero overlap, but only `18` training examples, so it should be treated as evaluation-only
- the promoted checkpoint's advanced suite report at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_advanced_suite.json` reaches companion validation macro F1 / IoU-F1 `0.9959 / 0.9959` and test macro F1 / IoU-F1 `0.8963 / 0.8963`
- consequence: the repo now has a strong taxonomy-rich companion benchmark, but it is benchmark-only and should not replace the canonical training split
- the core evaluator and saved-model tools now also support a decode-only `topk_span` policy for broader interval recovery without retraining, including optional cue-aware reranking via `--topk-span-cue-bonus`
- a bounded sweep at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/topk_span_sweep/summary.json` first found a strong baseline setting at positive ratio `0.10`, neighbor margin `-2.0`, and max neighbors `2`
- that baseline decode policy raised the public StandUp4AI slice to F1 `0.2135`, IoU-F1 `0.1724`, and the English-only slice to F1 `0.0978`, IoU-F1 `0.0586`, which was the first nonzero English external result in the repo
- a follow-up cue-reranking sweep at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_sweep/summary.json` then showed the best tested benchmark-time setting at the same ratio / neighbor config plus cue bonus `1.0`
- under that stronger decode policy, canonical validation remains `0.7500 / 0.8889` and canonical test remains `0.7213 / 0.8261`, so the canonical gate is unchanged
- the same cue-aware decode lifts the public StandUp4AI slice further to F1 `0.2308`, IoU-F1 `0.1980`, and the English-only slice to F1 `0.1156`, IoU-F1 `0.0747`
- direct artifacts for that best setting are now written at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_eval.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples_en.json`, and `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_wesr_advanced_suite.json`
- the matching `wesr_advanced` companion outputs stay strong, with validation macro F1 / IoU-F1 `0.8559 / 0.9144` and test macro F1 / IoU-F1 `0.8401 / 0.9021`
- consequence: cue-aware `topk_span` is now the strongest benchmark-time decode policy, but the model registry is intentionally unchanged until autoresearch can compare candidates under the same decode regime
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support cue-biased span supervision via `--cue-span-bias-enabled`, which boosts auxiliary span targets on filler/discourse/punctuation-like tokens near the weak trigger without changing canonical labels
- bounded cue-biased span probe at `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075` regressed the default argmax gate to validation F1 `0.6000` while only tying validation IoU-F1 at `0.5000`, so it was not promotable under the canonical policy
- under the best tested `topk_span` decode policy, that same checkpoint reached canonical validation F1 `0.6851`, IoU-F1 `0.8595`, and canonical test F1 `0.7188`, IoU-F1 `0.9130`
- on the chunked 4-example public StandUp4AI slice it reached F1 `0.2037`, IoU-F1 `0.1826`, which does not clearly beat the promoted checkpoint's stronger decode-only baseline on full-slice transfer
- on the chunked English-only slice it reached F1 `0.1322`, IoU-F1 `0.0865`, which is the strongest English-only external result in the repo so far
- the matching `wesr_advanced` companion report at `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075/topk_span_wesr_advanced_suite.json` remained usable but weaker than the promoted checkpoint's decode-time benchmark, with validation macro F1 / IoU-F1 `0.8329 / 0.9688` and test macro F1 / IoU-F1 `0.8225 / 0.9709`
- consequence: cue-biased span supervision is real benchmark-positive evidence for English transfer, but it is still not the next promoted default and does not displace `topk_span` on the current winner

Fourth clean-split cycle (`dataset_fingerprint = e05376af...`) tested:

- `pos5_epochs4`
- `pos5_cls6e-5`

Results:

- `pos5_epochs4` improved validation F1 to `0.5000` and test F1 to `0.5882`, but validation IoU-F1 stayed flat at `0.3333`, so it was not promoted
- `pos5_cls6e-5` matched the clean validation gates and underperformed on test
- this keeps the promotion gate focused on the actual blocker: moving validation IoU-F1 above `0.3333`

Fifth clean-split cycle (`dataset_fingerprint = e05376af...`) tested:

- `pos5_len384`
- `focal_pos5_g10`

Results:

- `pos5_len384` exactly matched the clean baseline on validation and test metrics
- `focal_pos5_g10` improved only test metrics, with test F1 `0.4545` and test IoU-F1 `0.4203`, but validation F1 and validation IoU-F1 both stayed flat
- the expanded bounded queue is now exhausted again for `dataset_fingerprint = e05376af...`

## Run a cycle

```bash
python3 training/autonomous_research_loop.py --max-experiments 2
```

## Current next autoresearch targets

1. Add a genuinely new clause-aware candidate family only if it has a plausible path to improving validation IoU-F1 above `0.5000` or to clearly beating the current cue-aware `topk_span` external benchmark without sacrificing the canonical gate
2. Since `wesr_advanced` is now a strong taxonomy-rich companion benchmark and cue-aware `topk_span` is the strongest tested decode policy, use both as side checks while prioritizing stronger language/domain conditioning over reopening teacher refinement or small sweeps
3. Use the WESR-balanced split for taxonomy-aware benchmarking, but do not substitute it for the canonical promotion split without a comparable validation-size policy
4. Regenerate teacher outputs on the retokenized dataset before reviving the teacher branch
5. Use `docs/REFINED_LABEL_AUDIT_CLEAN.md` as the pre-retokenization teacher-failure explanation on the clean split
6. If using teacher outputs, prefer `training/build_safe_hybrid_dataset.py` over full replacement
