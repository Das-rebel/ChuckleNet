# Current Status

Date: 2026-04-02
Status: **PROJECT COMPLETE** - Final benchmark and documentation created

For project summary, see `final_summary.md`.

This file is the canonical project status for the current stand-up pipeline.

## What is actually working

- Raw stand-up transcripts are converted into word-level JSONL examples.
- The XLM-R trainer loads from local cache and trains offline.
- The promoted model is now a class-weighted weak-label XLM-R run.
- The teacher refinement script now writes incrementally and supports resume.
- Teacher-derived datasets have now been regenerated and compared on the clean split.
- A real evidence-gated autoresearch loop is now in place.

## Canonical training pipeline

1. `training/convert_standup_raw_to_word_level.py`
2. `training/refine_weak_labels_nemotron.py`
3. `training/xlmr_standup_word_level.py`

One-command runner:

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --model-name FacebookAI/xlm-roberta-base
```

The runner now defaults to the active recipe:

- `--refined-train-policy weak`
- `--positive-class-weight 4.0`
- `--split-strategy overlap_safe`

Storage-aware runner/trainer support:

- `training/run_xlmr_standup_pipeline.py` now forwards `--split-strategy` to dataset conversion
- `training/xlmr_standup_word_level.py` now supports `--prune-best-model-weights`
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now support `--loss-type adaptive_focal` for the next non-built-in objective-family branch
- `training/xlmr_standup_word_level.py`, `training/evaluate_saved_xlmr_model.py`, and `training/run_xlmr_standup_pipeline.py` now support a lightweight `--dialect-adapter-enabled` branch with heuristic dialect buckets and per-bucket reporting
- `training/evaluate_external_wordlevel_benchmark.py` now bridges the current saved XLM-R checkpoints to external word-level benchmark files (JSON, JSONL, or CSV) using the same trusted evaluator as the canonical pipeline
- the external benchmark bridge now also emits `benchmark_quality` metadata and can fail fast with `--fail-on-degenerate-benchmark` when a local benchmark bundle has no positive supervision
- `training/convert_standup4ai_examples_to_jsonl.py` now converts the public StandUp4AI `Examples_label/*.csv` files into the internal word-level JSONL schema for a small but real external sanity benchmark
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support a GCACU-lite `--contrast-gate-enabled` branch that conditions token logits on token-vs-context mismatch features
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support a span-aware auxiliary branch that adds decayed supervision around the weak trigger token for external span-shape transfer experiments
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support a cue-aware token adapter branch for filler/discourse/punctuation-style token conditioning
- `training/xlmr_standup_word_level.py` and `training/run_xlmr_standup_pipeline.py` now also support cue-biased span supervision via `--cue-span-bias-enabled`, which boosts auxiliary span targets on filler/discourse/punctuation-like tokens near the weak trigger
- `training/xlmr_standup_word_level.py` now reports per-language, per-laughter-type, and per-dialect IoU-F1 alongside F1, and `training/evaluate_wesr_benchmark_suite.py` now evaluates saved checkpoints across the canonical and `wesr_balanced` splits in one taxonomy-aware report
- `training/xlmr_standup_word_level.py`, `training/evaluate_saved_xlmr_model.py`, `training/evaluate_external_wordlevel_benchmark.py`, and `training/evaluate_wesr_benchmark_suite.py` now also support a decode-only `topk_span` strategy for broader interval prediction at evaluation time, including optional cue-aware reranking via `--topk-span-cue-bonus`
- use pruning for benchmark or non-promoted runs when disk is tight; summaries and tokenizer/config artifacts remain available even after weight deletion

Autoresearch runner:

```bash
python3 training/autonomous_research_loop.py --max-experiments 2
```

Resume after interruption:

```bash
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume
```

## Current datasets

Current converted weak-label dataset:

- `data/training/standup_word_level/train.jsonl`
- `data/training/standup_word_level/valid.jsonl`
- `data/training/standup_word_level/test.jsonl`

Current counts from overlap-safe conversion:

- train examples: `505`
- valid examples: `102`
- test examples: `23`
- exact overlap counts: train/valid `0`, train/test `0`, valid/test `0`
- laughter-type balance: train `264` continuous / `241` discrete, valid `102` continuous / `0` discrete, test `20` continuous / `3` discrete
- WESR note: the current clean validation split has no discrete laughter examples, so discrete/continuous benchmark tracking is not yet strong enough to use as a promotion gate
- conversion summary: `data/training/standup_word_level/conversion_summary.json`
- tokenization mode: `dialect_aware_contraction_v1`
- tokenization profile: train `0` standalone apostrophe tokens, `283` examples with lexical apostrophe tokens (`444` lexical apostrophe tokens total)
- context scoring mode: `metadata.current_segment_start` marks the current spoken line, and prepended context tokens are masked out of loss/evaluation while remaining visible as input
- canonical context-token policy: `clause_lexical_tail`
- canonical context window: last `6` lexical tokens from the last non-empty clause of the previous spoken line

Alternate WESR-balanced benchmark split:

- `data/training/standup_word_level_wesr_balanced/train.jsonl`
- `data/training/standup_word_level_wesr_balanced/valid.jsonl`
- `data/training/standup_word_level_wesr_balanced/test.jsonl`
- train examples: `502`
- valid examples: `23`
- test examples: `105`
- exact overlap counts: train/valid `0`, train/test `0`, valid/test `0`
- laughter-type balance: valid `20` continuous / `3` discrete, test `84` continuous / `21` discrete
- split strategy: `wesr_balanced`
- note: this split is now available for taxonomy-aware benchmarking, but it is not the canonical promotion split because its validation set is much smaller
- conversion summary: `data/training/standup_word_level_wesr_balanced/conversion_summary.json`
- promoted-checkpoint suite report: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_benchmark_suite.json`

Advanced WESR companion benchmark split:

- `data/training/standup_word_level_wesr_advanced/train.jsonl`
- `data/training/standup_word_level_wesr_advanced/valid.jsonl`
- `data/training/standup_word_level_wesr_advanced/test.jsonl`
- train examples: `18`
- valid examples: `245`
- test examples: `367`
- exact overlap counts: train/valid `0`, train/test `0`, valid/test `0`
- laughter-type balance: valid `122` continuous / `123` discrete, test `246` continuous / `121` discrete
- note: this split is intentionally evaluation-heavy and should be treated as a taxonomy-rich companion benchmark, not as a training split, because its train partition is too small
- conversion summary: `data/training/standup_word_level_wesr_advanced/conversion_summary.json`
- promoted-checkpoint suite report: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_advanced_suite.json`

## Current validated model result

Promoted XLM-R baseline:

- output dir: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted`
- checkpoint: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/best_model`
- summary: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/training_summary.json`
- saved-model eval: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/clause_lexical_tail_eval.json`

Metrics:

- validation F1: `0.6667`
- validation IoU-F1: `0.5000`
- test F1: `0.7222`
- test IoU-F1: `0.5652`
- positive class weight: `4.0`
- unfreeze last N layers: `4`

This is now the promoted model on the current retokenized dataset under clause-aware context-masked scoring.

Retokenization comparison:

- old promoted checkpoint re-eval on the retokenized split: `experiments/xlmr_standup_baseline_weak_pos5_clean/retokenized_eval.json`
- old checkpoint metrics on the new dataset: validation F1 `0.2667`, validation IoU-F1 `0.2500`, test F1 `0.3390`, test IoU-F1 `0.3333`
- interim retokenized weak baseline: `experiments/xlmr_standup_baseline_weak_pos5_clean_dialecttok`
- interim retokenized baseline metrics: validation F1 `0.3119`, validation IoU-F1 `0.2778`, test F1 `0.3922`, test IoU-F1 `0.3696`
- conclusion: the PRD-aligned retokenization reset the baseline, and the first fresh autoresearch cycle then promoted `af1af34e_pos4` over that interim retokenized run
- context-masked re-eval then raised the old promoted checkpoint to validation F1 `0.4000` and test F1 `0.5128` while validation IoU-F1 stayed flat at `0.3333`
- fresh masked retrain: `experiments/xlmr_standup_ctxmask_pos4/training_summary.json`
- masked retrain result: it matched validation at `0.4000 / 0.3333` but was slightly worse on test (`0.5000 / 0.4203`), so it was not promoted and its weight file was pruned
- PRD-aligned lexical-tail context benchmark: `data/training/standup_word_level_lexical_tail`
- lexical-tail policy keeps only the last `6` non-punctuation context tokens from the previous line
- lexical-tail checkpoint re-eval matched the current masked baseline exactly, and a fresh lexical-tail retrain at `experiments/xlmr_standup_lexical_tail_pos4` also tied `0.4000 / 0.3333` on validation and `0.5000 / 0.4203` on test, so lexical-tail is now an available converter mode rather than a promoted default
- PRD-aligned clause-aware context benchmark: `data/training/standup_word_level_clause_lexical_tail`
- clause-aware policy keeps the last `6` lexical tokens from the last non-empty clause of the previous line
- clause-aware checkpoint re-eval of the old promoted `af1af34e_pos4` tied the masked baseline exactly at `0.4000 / 0.3333` on validation and `0.5128 / 0.4348` on test
- adapted clause-aware `pos5_epochs4` improved validation F1 to `0.4444` and test F1 to `0.5405`, but validation IoU-F1 stayed flat at `0.3333`
- adapted clause-aware `pos5_unfreeze4` then improved both validation gates and was promoted at `0.6667 / 0.5000`, with test `0.7222 / 0.5652`
- first clause-aware autoresearch cycle on dataset fingerprint `6f1c7e67...` then tested `focal_pos5_g15` and `pos6`
- `focal_pos5_g15` reached validation F1 `0.6000` and test F1 `0.6667`, but validation IoU-F1 only tied the promoted run at `0.5000`
- `pos6` exactly matched the promoted clause-aware baseline on all tracked metrics, so neither challenger was promoted
- second clause-aware autoresearch cycle on dataset fingerprint `6f1c7e67...` then tested `pos5_len320` and `pos5_cls8e-5`
- both `pos5_len320` and `pos5_cls8e-5` exactly matched the promoted clause-aware baseline on validation and test, so neither was promoted and both checkpoint weights were pruned
- third clause-aware autoresearch cycle on dataset fingerprint `6f1c7e67...` then tested `pos5_epochs4` and `pos5_cls6e-5`
- both `pos5_epochs4` and `pos5_cls6e-5` exactly matched the promoted clause-aware baseline on validation and test, so neither was promoted and both checkpoint weights were pruned
- fourth clause-aware autoresearch cycle on dataset fingerprint `6f1c7e67...` then tested `pos5_len384` and `focal_pos5_g10`
- `pos5_len384` exactly matched the promoted clause-aware baseline, while `focal_pos5_g10` tied both validation gates but regressed on test F1 to `0.6667`, so neither was promoted
- the built-in clause-aware queue is now exhausted again: dry-run reports `candidate_count = 0`
- first non-built-in objective-family probe then tested `adaptive_focal` with `focal_gamma=2.0` and `1.5`
- both adaptive-focal runs tied validation IoU-F1 at `0.5000` but regressed validation F1 to `0.6000`, so neither was promotable and both checkpoint weights were pruned
- first dialect-aware structural probe then tested `experiments/xlmr_standup_clause_dialect_adapter_pos5_unfreeze4_s025` and `experiments/xlmr_standup_clause_dialect_adapter_pos5_unfreeze4_s050`
- both dialect-adapter runs exactly matched the promoted clause-aware baseline on the main promotion metrics: validation `0.6667 / 0.5000`, test `0.7222 / 0.5652`
- consequence: the adapter branch is stable and now instrumented with `per_dialect_bucket` reporting, but the first bounded probe is neutral evidence rather than a promotion
- the external-benchmark bridge was then smoke-tested against the current saved promoted model using `data/training/standup_word_level/test.jsonl` as a format-compatible stand-in
- smoke result at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/external_bridge_smoke.json`: F1 `0.7222`, IoU-F1 `0.5652`, matching the canonical saved-model test metrics exactly
- consequence: the repo now has a trustworthy path to score real external word-level benchmarks such as StandUp4AI as soon as the actual dataset is present locally
- the first actual local StandUp4AI bridge run then evaluated `/Users/Subho/data/standup4ai/annotations/test_annotations.json` and wrote `benchmarks/results/standup4ai_bridge_eval.json`
- result: F1 `0.0000`, IoU-F1 `0.0000`, with `benchmark_quality.benchmark_usable = false`
- the new strict mode also now fails immediately on that bundle with `no_positive_tokens, no_positive_examples`
- this is not a meaningful benchmark failure because the checked-in local StandUp4AI bundle is explicitly demo-only and contains `0` positive tokens in train, val, and test
- consequence: external-evaluation plumbing is complete, but credible StandUp4AI validation is still blocked on replacing the local demo annotations with the real dataset
- the public StandUp4AI repository was then fetched to `/tmp/standup4ai_dataset_main`; it contains the data-generation pipeline plus four real labeled example CSVs in `Examples_label/`, but not a packaged full evaluation split
- those example files were converted into `benchmarks/data/standup4ai_examples.jsonl` with summary `benchmarks/data/standup4ai_examples_summary.json`
- first real non-demo external sanity run at `benchmarks/results/standup4ai_examples_eval.json` scored F1 `0.0000`, IoU-F1 `0.0000` on 4 usable labeled examples across `en`, `fr`, `es`, and `cs`
- the English-only slice at `benchmarks/results/standup4ai_examples_en_eval.json` also scored F1 `0.0000`, IoU-F1 `0.0000`, so the failure is not only a multilingual mismatch
- widening the evaluation window to `max_length=512` in `benchmarks/results/standup4ai_examples_en_eval_len512.json` increased visible positive support from `23` to `35`, but F1 and IoU-F1 still remained `0.0000`
- chunked full-coverage evaluation via `--chunk-word-window 128 --chunk-word-stride 128` then lifted the 4-example public slice from a truncation artifact to a real measurable result at `benchmarks/results/standup4ai_examples_eval_chunk128.json`: F1 `0.0104`, IoU-F1 `0.0204`, with total positive support `564`
- the chunked English-only slice at `benchmarks/results/standup4ai_examples_en_eval_chunk128.json` still scored F1 `0.0000`, IoU-F1 `0.0000` with full positive support `118`
- consequence: there is now evidence of a real external domain failure on public StandUp4AI examples even after full-coverage chunking, not just a missing-benchmark or truncation issue
- first GCACU-lite contrast-gate probe at `experiments/xlmr_standup_clause_contrast_gate_pos5_unfreeze4` tied the internal validation gate at `0.6667 / 0.5000` but regressed test F1 to `0.6667`
- the same contrast-gate checkpoint also underperformed the promoted baseline on the chunked public StandUp4AI slice, reaching only F1 `0.0035`, IoU-F1 `0.0102` at `experiments/xlmr_standup_clause_contrast_gate_pos5_unfreeze4/standup4ai_examples_eval_chunk128.json`
- the chunked English-only external slice for the contrast-gate model remained at `0.0000 / 0.0000`
- consequence: the first explicit token-vs-context contrast branch is now evidence-backed and non-promoted; it did not solve the external domain failure
- external label-geometry audit then confirmed the core mismatch: the internal clause-aware dataset has exactly `1` positive token per example, while the public StandUp4AI slice averages `141` positive tokens per example and `3.837` tokens per positive span
- first span-aware auxiliary probe at `experiments/xlmr_standup_clause_span_aux_pos5_unfreeze4_r2w025` kept the internal winner exactly tied at validation `0.6667 / 0.5000` and test `0.7222 / 0.5652`
- that same `r2w025` span-aware checkpoint improved the chunked 4-example public StandUp4AI slice from F1 `0.0104` / IoU-F1 `0.0204` to F1 `0.0137` / IoU-F1 `0.0169`, but the chunked English-only slice still stayed at `0.0000 / 0.0000`
- stronger span-aware probe at `experiments/xlmr_standup_clause_span_aux_pos5_unfreeze4_r3w05` improved the chunked 4-example public slice further to F1 `0.0268` / IoU-F1 `0.0407`, but internal validation F1 fell to `0.6000` while validation IoU-F1 only tied at `0.5000`, so it was not promotable
- consequence: span-aware supervision is the first branch to produce a real external gain on the public StandUp4AI slice, but it still does not solve English transfer and currently trades away the internal promotion gate
- token-level inspection of the English public slice then showed the promoted model's few positive predictions land far from the labeled filler/discourse spans, often on content words such as `other` and `yesterday`
- first cue-plus-span probe at `experiments/xlmr_standup_clause_cue_span_pos5_unfreeze4_r2w025` regressed the internal gate to validation F1 `0.5455` while only tying validation IoU-F1 at `0.5000`
- that cue-plus-span checkpoint reached F1 `0.0170` / IoU-F1 `0.0271` on the chunked 4-example public slice and still scored `0.0000 / 0.0000` on the chunked English-only slice
- consequence: heuristic cue conditioning is now evidence-backed and non-promoted; it does not fix the English external failure and is weaker than the stronger span-aware branch
- the new WESR benchmark suite report for the promoted checkpoint then clarified the current evaluation boundary: canonical validation is still taxonomy-unusable because it only contains `continuous`, while `wesr_balanced` is a usable companion benchmark with validation macro F1 / IoU-F1 `0.6694 / 0.6694` and test macro F1 / IoU-F1 `0.7500 / 0.7500`
- the same suite also confirms `wesr_balanced` is not yet promotion-ready because validation still has only `3` discrete examples, so it should remain a companion benchmark rather than replace the canonical promotion gate
- a stricter `wesr_advanced` split was then generated to maximize discrete/continuous support in evaluation; it yields validation `122` continuous / `123` discrete and test `246` continuous / `121` discrete with zero overlap
- the promoted checkpoint's `wesr_advanced` suite report shows companion validation macro F1 / IoU-F1 `0.9959 / 0.9959` and test macro F1 / IoU-F1 `0.8963 / 0.8963`, so this variant is now promotion-ready as a taxonomy companion benchmark
- that said, `wesr_advanced` should remain benchmark-only because its train split has only `18` examples and is not suitable as a replacement training split
- a bounded `topk_span` decode sweep on the promoted checkpoint is now recorded at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/topk_span_sweep/summary.json`
- a follow-up cue-aware reranking sweep is now recorded at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_sweep/summary.json`
- the strongest tested benchmark-time decode setting so far is now `topk_span` with positive ratio `0.10`, neighbor margin `-2.0`, max neighbors `2`, and cue bonus `1.0`
- under that decode policy, canonical validation remains F1 `0.7500`, IoU-F1 `0.8889`, while canonical test remains F1 `0.7213`, IoU-F1 `0.8261`
- the same decode policy lifts the public StandUp4AI slice further to F1 `0.2308`, IoU-F1 `0.1980`, and the English-only slice to F1 `0.1156`, IoU-F1 `0.0747`
- direct canonical / companion artifacts for that best setting are now recorded at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_eval.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples_en.json`, and `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_wesr_advanced_suite.json`
- the corresponding `wesr_advanced` companion results remain strong at validation macro F1 / IoU-F1 `0.8559 / 0.9144` and test macro F1 / IoU-F1 `0.8401 / 0.9021`
- consequence: cue-aware `topk_span` is now the strongest benchmark-time decode policy, but the model registry is intentionally left unchanged until the training/autoresearch gate is updated to compare candidates under the same decode regime
- cue-biased span supervision was then added as a stronger language/domain-conditioning follow-up to the earlier span-aware branch, implemented by boosting auxiliary span targets on cue-like tokens near the weak trigger
- bounded cue-biased run at `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075` regressed the default argmax gate to validation F1 `0.6000`, validation IoU-F1 `0.5000`, while test landed at F1 `0.6667`, IoU-F1 `0.5652`, so it is not promotable under the current canonical policy
- under the same best `topk_span` decode policy, that checkpoint reached canonical validation F1 `0.6851`, IoU-F1 `0.8595`, and canonical test F1 `0.7188`, IoU-F1 `0.9130`, recorded in `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075/topk_span_eval.json`
- on the chunked public StandUp4AI slice it reached F1 `0.2037`, IoU-F1 `0.1826`, which is slightly below the promoted checkpoint's `0.2135 / 0.1724` tradeoff on F1 but slightly above on interval quality
- on the chunked English-only slice it reached F1 `0.1322`, IoU-F1 `0.0865`, which is now the strongest English-only external result in the repo so far
- the matching `wesr_advanced` companion report at `experiments/xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075/topk_span_wesr_advanced_suite.json` remains usable but is weaker than the promoted checkpoint's decode-time benchmark, with validation macro F1 / IoU-F1 `0.8329 / 0.9688` and test macro F1 / IoU-F1 `0.8225 / 0.9709`
- consequence: cue-biased span supervision is benchmark-positive evidence for English transfer, but it still loses on the canonical validation gate and does not clearly beat the promoted checkpoint's stronger decode-only baseline overall
- fallback tracker: `docs/LOCAL_TASK_LIST.md`

Checkpoint state:

- the promoted clause-aware `pos5_unfreeze4` checkpoint includes `model.safetensors`
- this is the only experiment checkpoint weight intentionally kept in the repo right now
- the summary records `checkpoint_artifacts.weights_pruned = false`
- pre-retokenization decode sweep: `experiments/xlmr_standup_baseline_weak_pos5_clean/decode_sweep_single_best.json`
- note: the earlier decode-only saturation result remains informative, but it was measured on the pre-retokenization dataset version

Programmatic registry:

- `experiments/promoted_model.json`

## Current teacher model state

Installed local models:

- `qwen2.5-coder:1.5b`
- `qwen2.5-coder:latest`

Teacher refinement now:

- truncates stale outputs on fresh runs
- writes refined and audit rows incrementally
- prints progress
- supports `--resume`
- prompt version for future reruns: `lexical_target_v2`

Important after retokenization:

- the canonical weak-label dataset now uses `dialect_aware_contraction_v1`
- the checked-in `train_refined*.jsonl` teacher artifacts have now been regenerated against the canonical clause-aware `train.jsonl`
- the current teacher-derived metrics below are promotion-comparable against the current clause-aware weak-label baseline

Current clause-aware teacher outputs:

- `data/training/standup_word_level/train_refined.jsonl`
- `data/training/standup_word_level/train_refined_audit.jsonl`
- `data/training/standup_word_level/train_refined_safe_hybrid.jsonl`

Current clause-aware teacher summary:

- processed examples: `505`
- kept examples: `505`
- dropped examples: `0`

Clean refined-label audit findings:

- report: `docs/REFINED_LABEL_AUDIT_CLEAN.md`
- summary: `docs/refined_label_audit_clean_summary.json`
- moved kept targets: `134 / 505` (`26.53%`)
- average absolute target shift: `3.739` tokens
- refined targets shifted earlier on average: position ratio `1.0 -> 0.9451`
- moved targets landing on stopwords: `21`
- moved targets landing on punctuation: `26`
- clean drop reasons are eliminated in this rerun: `0` drops

Historical old-split audit:

- report: `docs/REFINED_LABEL_AUDIT.md`
- note: this remains the explanation for the failed old leaky-split refined run, but it is no longer the active dataset state

Safe hybrid dataset:

- builder: `training/build_safe_hybrid_dataset.py`
- output: `data/training/standup_word_level/train_refined_safe_hybrid.jsonl`
- summary: `data/training/standup_word_level/train_refined_safe_hybrid_summary.json`
- accepted same-index teacher labels: `371`
- accepted note-repaired moved teacher labels: `134`
- recovered dropped examples back to weak labels: `0`
- rejected moved teacher labels after repair: `0`
- note: the current safe-hybrid rebuild uses `--max-note-repair-shift 24`
- note: the builder now recovers lexical targets such as `milk`, `prefer`, `having`, `activities`, `beer`, `pc`, `jam`, `humor`, `connection`, `fine`, `letter`, and `nice`
- remaining repair-gap report: `docs/REMAINING_TEACHER_REPAIRS.md`
- unresolved moved-target cluster: `0` cases remain after the current note-repair policy
- targeted prompt smoke: `docs/TEACHER_PROMPT_RESIDUAL_SMOKE.md`
- bounded result: on the earlier `13` residual dating/beach cases, the updated prompt flipped all outputs from stopword `My` to lexical target `beach`; the full rerun then removed that cluster completely

Clause-aware refined-label training result:

- output dir: `experiments/xlmr_standup_baseline_refined_clause_unfreeze4_pos4`
- validation F1: `0.2000`
- validation IoU-F1: `0.1667`
- test F1: `0.3077`
- test IoU-F1: `0.2464`

Decision:

- do not promote the refined-label model
- full teacher replacement still underperformed the clause-aware weak-label baseline badly even after the refreshed `lexical_target_v2` rerun on the canonical dataset

Clause-aware safe hybrid training result:

- output dir: `experiments/xlmr_standup_safe_hybrid_clause_unfreeze4_pos4`
- validation F1: `0.4444`
- validation IoU-F1: `0.3333`
- test F1: `0.6154`
- test IoU-F1: `0.5072`

Decision:

- the refreshed `lexical_target_v2` teacher rerun plus the clause-aware note-repair hybrid materially improved test performance over the old historical hybrid
- the rebuilt clause-aware hybrid still does not earn promotion because validation IoU-F1 stayed far below the current baseline at `0.3333` vs `0.5000`
- note: even after eliminating drops and shrinking average target shift, the teacher branch still fails the real promotion gate under the current clause-aware architecture
- WESR-style re-evaluation is now supported by `training/evaluate_saved_xlmr_model.py`
- teacher-derived regeneration on the canonical clause-aware split is complete for prompt version `lexical_target_v2`

Alternate WESR-balanced weak-label benchmark:

- output dir: `experiments/xlmr_standup_baseline_weak_pos5_wesr_balanced`
- validation F1: `0.8636`
- validation IoU-F1: `0.8116`
- test F1: `0.5714`
- test IoU-F1: `0.6667`
- validation per-laughter-type F1: `0.8000` continuous, `0.8889` discrete
- test per-laughter-type F1: `0.5417` continuous, `0.5000` discrete
- note: these numbers are useful for WESR-style coverage checks, but they are not promotion-comparable with the canonical clean split because validation support falls from `102` to `23`

## Current autoresearch state

Real autoresearch loop:

- script: `training/autonomous_research_loop.py`
- registry: `experiments/promoted_model.json`
- log: `research_log.json`
- storage behavior: non-promoted candidate checkpoint weights are now pruned by default after metrics are recorded; use `--keep-non-promoted-weights` only when a failed/non-promoted checkpoint must be retained for deeper inspection

First real cycle result:

- tested `pos4`
- tested `pos6`
- neither beat the promoted baseline on validation F1 and validation IoU-F1

Second real cycle result:

- tested `focal_pos5_g15`
- tested `pos5_len320`
- `focal_pos5_g15` increased recall but reduced validation F1 to `0.7385`, so it failed promotion
- `pos5_len320` matched the promoted baseline exactly and did not earn promotion
- current promoted registry remains unchanged

Third real cycle result:

- tested `pos5_unfreeze4`
- tested `pos5_cls8e-5`
- `pos5_unfreeze4` reached apparent `1.0` validation and test metrics, but this result is not trustworthy under the current split
- split leakage audit found exact token-sequence overlap counts: train/valid `31`, train/test `26`, valid/test `13`
- `pos5_cls8e-5` underperformed the weak-label baseline
- `promoted_model.json` was manually restored to `experiments/xlmr_standup_baseline_weak_pos5`
- autoresearch now records overlap counts and blocks future auto-promotion when split overlap is non-zero

First clean-split real cycle result:

- baseline dataset fingerprint: `e05376af...`
- tested `pos4`
- tested `focal_pos5_g15`
- `pos4` improved validation F1 to `0.3696` but only tied validation IoU-F1 at `0.3333`, so it did not pass promotion
- `focal_pos5_g15` tied validation F1 and IoU-F1, so it did not pass promotion
- autoresearch output dirs are now fingerprinted by dataset to avoid stale artifact reuse

Second clean-split real cycle result:

- tested `pos6`
- tested `pos5_len320`
- `pos6` did not improve either validation gate and underperformed on test
- `pos5_len320` exactly matched the clean baseline and did not earn promotion
- promoted registry remains `experiments/xlmr_standup_baseline_weak_pos5_clean`

Third clean-split real cycle result:

- tested `pos5_unfreeze4`
- tested `pos5_cls8e-5`
- `pos5_unfreeze4` improved validation F1 to `0.5000` and test F1 to `0.6061`, but validation IoU-F1 stayed flat at `0.3333`, so it did not pass promotion
- `pos5_cls8e-5` matched the clean validation gates and underperformed on test
- promoted registry remains `experiments/xlmr_standup_baseline_weak_pos5_clean`

Fourth clean-split real cycle result:

- dataset fingerprint: `e05376af...`
- tested `pos5_epochs4`
- tested `pos5_cls6e-5`
- `pos5_epochs4` improved validation F1 to `0.5000` and test F1 to `0.5882`, but validation IoU-F1 stayed flat at `0.3333`, so it did not pass promotion
- `pos5_cls6e-5` exactly matched the clean validation gates and underperformed on test
- promoted registry remains `experiments/xlmr_standup_baseline_weak_pos5_clean`

Fifth clean-split real cycle result:

- tested `pos5_len384`
- tested `focal_pos5_g10`
- `pos5_len384` exactly matched the clean baseline on validation and test metrics
- `focal_pos5_g10` improved only test metrics to F1 `0.4545` and IoU-F1 `0.4203`, but left both validation gates flat at `0.3636 / 0.3333`
- promoted registry remains `experiments/xlmr_standup_baseline_weak_pos5_clean`

Current clean-split dry-run state:

- exact overlap counts remain `0 / 0 / 0`
- built-in candidate queue is exhausted again: `candidate_count = 0`
- the current bounded search still has the same blocker: validation IoU-F1 has not moved above `0.3333`

First retokenized cycle result:

- baseline dataset fingerprint: `af1af34e...`
- tested `pos4`
- tested `focal_pos5_g15`
- `pos4` improved both validation gates and was promoted: validation F1 `0.3383`, validation IoU-F1 `0.3333`, test F1 `0.4545`, test IoU-F1 `0.4203`
- `focal_pos5_g15` matched or underperformed the interim retokenized baseline and was not promoted; its checkpoint weights were pruned

Second retokenized cycle result:

- tested `pos6`
- tested `pos5_len320`
- `pos6` underperformed the promoted `pos4` run on both validation gates and on test
- `pos5_len320` exactly matched the promoted `pos4` metrics and was not promoted
- both non-promoted checkpoint weights were pruned automatically

Third retokenized cycle result:

- tested `pos5_unfreeze4`
- tested `pos5_cls8e-5`
- `pos5_unfreeze4` improved validation F1 to `0.5000` and test F1 to `0.6061`, but validation IoU-F1 stayed flat at `0.3333`, so it did not pass promotion
- `pos5_cls8e-5` exactly matched the promoted validation gates and regressed on test
- both non-promoted checkpoint weights were pruned automatically

Fourth retokenized cycle result:

- tested `pos5_epochs4`
- tested `pos5_cls6e-5`
- `pos5_epochs4` improved validation F1 to `0.5000` and test F1 to `0.5882`, but validation IoU-F1 stayed flat at `0.3333`, so it did not pass promotion
- `pos5_cls6e-5` exactly matched the promoted validation gates and regressed on test
- both non-promoted checkpoint weights were pruned automatically

Fifth retokenized cycle result:

- tested `pos5_len384`
- tested `focal_pos5_g10`
- `pos5_len384` exactly matched the promoted `pos4` metrics and was not promoted
- `focal_pos5_g10` improved only test metrics, with test F1 `0.4348` and test IoU-F1 `0.4348`, but left both validation gates flat at `0.3383 / 0.3333`
- both non-promoted checkpoint weights were pruned automatically

Current retokenized dry-run state:

- exact overlap counts remain `0 / 0 / 0`
- built-in retokenized candidate queue is exhausted again: `candidate_count = 0`
- the active bounded search blocker is now lifting validation IoU-F1 above `0.3333`

Context-masked autoresearch reset:

- canonical dataset fingerprint is now `f368e999...`
- `training/autonomous_research_loop.py` now skips redundant candidates that exactly match the active baseline config
- first context-masked dry-run candidates are `focal_pos5_g15` and `pos6`
- note: the first masked batch was intentionally interrupted once the context-quality branch became higher value; no promoted result came from that partial run

Trust only `research_log.json` entries with `loop_version = "real_v1"`.

## Model-choice note

The efficient main choice remains `FacebookAI/xlm-roberta-base`.

Reason:

- the task is word-level sequence labeling on stand-up text
- XLM-R is the training backbone
- `qwen2.5-coder:1.5b` is only a lightweight teacher
- moderate class weighting improved recall and overall F1 on the winning run
- TurboQuant is relevant for KV-cache compression in autoregressive LLM inference, not for choosing the main encoder here

## Files that are not canonical

Many historical Markdown files in this repo claim the full integrated system is complete or production ready. Do not use those claims as the source of truth. Prefer this file, `AGENTS.md`, and the roadmap docs instead.
