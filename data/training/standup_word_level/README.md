# Stand-Up Word-Level Dataset

This directory holds the current stand-up training data used by the XLM-R pipeline.

## Files

- `train.jsonl`
- `valid.jsonl`
- `test.jsonl`
- `train_refined.jsonl`
- `train_refined_audit.jsonl`
- `train_refined_safe_hybrid.jsonl`
- `train_refined_safe_hybrid_summary.json`
- `conversion_summary.json`

## Schema

Each JSONL row contains:

- `example_id`
- `language`
- `comedian_id`
- `show_id`
- `words`
- `labels`

Example:

```json
{
  "example_id": "demo_0001",
  "language": "en",
  "comedian_id": "comic_demo",
  "show_id": "demo_show",
  "words": ["i", "told", "my", "therapist", "i", "hate", "commitment"],
  "labels": [0, 0, 0, 0, 0, 0, 1]
}
```

`labels` are word-level binary targets:

- `0` means no laughter-aligned trigger on that word
- `1` means the word is the laughter trigger

## Data generation

Weak labels are created from inline laughter tags:

```bash
python3 training/convert_standup_raw_to_word_level.py \
  --raw-dir data/raw \
  --output-dir data/training/standup_word_level
```

This converter:

- reads transcript `.txt` files
- emits one example per spoken segment
- marks the last word before a laughter tag as the weak positive target
- keeps transcript-level splits stable to avoid leakage

Current converted counts:

- train: `505`
- valid: `102`
- test: `23`
- exact overlap counts: train/valid `0`, train/test `0`, valid/test `0`
- laughter-type balance: train `264` continuous / `241` discrete, valid `102` continuous / `0` discrete, test `20` continuous / `3` discrete

The converter now groups transcripts into overlap components using exact example
token-sequence matches before assigning splits. This prevents duplicate material
from appearing across train/valid/test even when the raw transcripts use
different transcript IDs.

Alternate taxonomy-aware benchmark split:

```bash
python3 training/convert_standup_raw_to_word_level.py \
  --raw-dir data/raw \
  --output-dir data/training/standup_word_level_wesr_balanced \
  --split-strategy wesr_balanced
```

This alternate split stays overlap-safe but favors discrete/continuous coverage
in both validation and test. Current counts:

- train: `502`
- valid: `23`
- test: `105`
- exact overlap counts: train/valid `0`, train/test `0`, valid/test `0`
- laughter-type balance: valid `20` continuous / `3` discrete, test `84` continuous / `21` discrete

Use it for WESR-style benchmark checks, not for replacing the canonical clean
promotion split, because the validation set is much smaller.

## Optional teacher refinement

Weak labels can be refined with a local teacher:

```bash
python3 training/refine_weak_labels_nemotron.py \
  --input-file data/training/standup_word_level/train.jsonl \
  --output-file data/training/standup_word_level/train_refined.jsonl \
  --audit-file data/training/standup_word_level/train_refined_audit.jsonl \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --model qwen2.5-coder:1.5b
```

Useful flags:

- `--write-every`
- `--progress-every`
- `--resume`

The audit file records every teacher decision, including dropped examples.

Latest clean-split audit outputs:

- `docs/REFINED_LABEL_AUDIT_CLEAN.md`
- `docs/refined_label_audit_clean_summary.json`

Current clean-split teacher summary:

- processed examples: `505`
- kept examples: `502`
- dropped examples: `3`
- moved kept targets: `213 / 502`
- moved targets landing on stopwords: `60`
- moved targets landing on punctuation: `59`

Safe hybrid dataset:

```bash
python3 training/build_safe_hybrid_dataset.py \
  --weak-file data/training/standup_word_level/train.jsonl \
  --refined-file data/training/standup_word_level/train_refined.jsonl \
  --audit-file data/training/standup_word_level/train_refined_audit.jsonl \
  --output-file data/training/standup_word_level/train_refined_safe_hybrid.jsonl \
  --summary-file data/training/standup_word_level/train_refined_safe_hybrid_summary.json
```

This builder keeps the weak-label example by default, recovers dropped examples,
and only accepts moved teacher labels when they are lexical, high-confidence,
and within a bounded shift window. It now also performs note-anchored lexical
repair for punctuation/stopword retargets by matching quoted teacher-note spans
back onto the transcript words.

Current clean safe-hybrid summary:

- accepted same-index teacher labels: `289`
- accepted note-repaired moved teacher labels: `213`
- recovered teacher drops back to weak labels: `3`
- rejected moved teacher labels: `0`
- current build uses `--max-note-repair-shift 24`

## Training

Weak-label baseline:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --test-file data/training/standup_word_level/test.jsonl \
  --output-dir experiments/xlmr_standup_baseline_weak_pos5_clean \
  --model-name FacebookAI/xlm-roberta-base \
  --positive-class-weight 5.0
```

If the run is benchmark-only and you do not need to keep checkpoint weights:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level_wesr_balanced/train.jsonl \
  --valid-file data/training/standup_word_level_wesr_balanced/valid.jsonl \
  --test-file data/training/standup_word_level_wesr_balanced/test.jsonl \
  --output-dir experiments/xlmr_standup_baseline_weak_pos5_wesr_balanced \
  --model-name FacebookAI/xlm-roberta-base \
  --positive-class-weight 5.0 \
  --prune-best-model-weights
```

Refined-label run:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train_refined.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --test-file data/training/standup_word_level/test.jsonl \
  --output-dir experiments/xlmr_standup_baseline_refined_pos5_clean \
  --model-name FacebookAI/xlm-roberta-base \
  --positive-class-weight 5.0
```

Safe hybrid run:

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train_refined_safe_hybrid.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --test-file data/training/standup_word_level/test.jsonl \
  --output-dir experiments/xlmr_standup_safe_hybrid_note_repair_pos5_clean \
  --model-name FacebookAI/xlm-roberta-base \
  --positive-class-weight 5.0
```

Current clean-split outcomes:

- the converter now uses `dialect_aware_contraction_v1`, which preserves lexical contractions like `don't`, `I'm`, and `they're`
- the converter now also records `metadata.current_segment_start`, and the trainer masks prepended context tokens out of loss/evaluation while still using them as input
- the canonical converter default is now `--context-token-policy clause_lexical_tail --context-tail-tokens 6`
- current promoted retokenized run: `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted`
- current weak baseline on the canonical clause-aware split: validation F1 `0.6667`, validation IoU-F1 `0.5000`, test F1 `0.7222`, test IoU-F1 `0.5652`
- the old promoted checkpoint falls to validation F1 `0.2667`, validation IoU-F1 `0.2500`, test F1 `0.3390`, test IoU-F1 `0.3333` when re-evaluated on the retokenized split, so the retrained retokenized baseline is the correct active winner
- the first retokenized autoresearch cycle then improved that interim retokenized baseline again by promoting `pos4`
- a fresh masked retrain matched validation but underperformed the active checkpoint on test, so the active winner stayed the same checkpoint under the new scoring policy
- a PRD-aligned lexical-tail context variant is still available via `training/convert_standup_raw_to_word_level.py --context-token-policy lexical_tail --context-tail-tokens 6`, but it only tied the older masked baseline rather than improving it
- the stronger PRD-aligned clause-aware context variant, `--context-token-policy clause_lexical_tail --context-tail-tokens 6`, is now the promoted default after `pos5_unfreeze4` improved both validation F1 and validation IoU-F1
- the refreshed clause-aware teacher rerun now keeps all `505` training rows, but full refined still collapses to validation F1 `0.2000` / IoU-F1 `0.1667`
- the rebuilt clause-aware safe hybrid improves test F1 to `0.6154`, but validation IoU-F1 remains only `0.3333`, so the weak-label clause-aware baseline still stands
- `training/xlmr_standup_word_level.py` now supports `--loss-type adaptive_focal`, and the first clause-aware probes at gamma `2.0` and `1.5` both tied IoU-F1 but regressed validation F1, so they were not promoted
- `training/xlmr_standup_word_level.py` now also supports `--dialect-adapter-enabled`, and the first clause-aware bounded probes at adapter scales `0.25` and `0.5` both exactly matched the promoted baseline, so the branch is now real but still non-promoted
- `training/evaluate_external_wordlevel_benchmark.py` now lets the saved promoted checkpoint evaluate external word-level benchmark files in JSON, JSONL, or CSV form using the same metrics path as the canonical pipeline
- the first local StandUp4AI bridge run completed, but the local bundle at `/Users/Subho/data/standup4ai` is a demo dataset with zero positive labels in every split, so its `0.0000 / 0.0000` result is only a data-availability sanity check, not a real external benchmark score
- the public StandUp4AI `Examples_label` files now provide a small real external sanity benchmark; under chunked full coverage the promoted baseline reaches only F1 `0.0104`, IoU-F1 `0.0204`, so external transfer is currently poor even before a full benchmark release is obtained
- the first GCACU-lite `--contrast-gate-enabled` branch ties the internal validation gate but does not improve that public external slice, so it is not promoted
- the internal clause-aware dataset still trains on exactly one positive token per example, while the public StandUp4AI slice averages `141` positive tokens and `3.837` tokens per positive span; `--span-aware-enabled` now adds decayed neighboring supervision around the weak trigger token to probe that mismatch directly
- first span-aware probe `xlmr_standup_clause_span_aux_pos5_unfreeze4_r2w025` ties the promoted internal baseline and lifts the chunked public external slice to F1 `0.0137`, IoU-F1 `0.0169`
- stronger span-aware probe `xlmr_standup_clause_span_aux_pos5_unfreeze4_r3w05` lifts the chunked public external slice further to F1 `0.0268`, IoU-F1 `0.0407`, but regresses internal validation F1 to `0.6000`, so it is benchmark-positive but not promotable
- cue-aware token conditioning is now also available via `--cue-adapter-enabled`; the first cue-plus-span probe regressed the internal gate and only reached F1 `0.0170`, IoU-F1 `0.0271` on the chunked public external slice while English stayed at `0.0000 / 0.0000`
- cue-biased span supervision is now also available via `--cue-span-bias-enabled`; it boosts auxiliary span targets on filler/discourse/punctuation-like tokens near the weak trigger without changing the canonical labels
- first cue-biased span probe `xlmr_standup_clause_span_cuebias_pos4_unfreeze4_r2w025_b075` regressed the default argmax gate to validation F1 `0.6000`, but under the best `topk_span` decode it reached public external F1 / IoU-F1 `0.2037 / 0.1826` and English-only external `0.1322 / 0.0865`
- that makes cue-biased span supervision the strongest English-only external branch so far, but it still does not beat the promoted checkpoint plus `topk_span` on the full public slice or on the canonical validation gate
- `training/evaluate_wesr_benchmark_suite.py` now produces a taxonomy-aware suite report across the canonical split and `data/training/standup_word_level_wesr_balanced`; for the promoted checkpoint, that suite shows `wesr_balanced` validation macro F1 / IoU-F1 `0.6694 / 0.6694` and test macro F1 / IoU-F1 `0.7500 / 0.7500`, but still flags `promotion_ready = false` because validation has only `3` discrete examples
- `training/convert_standup_raw_to_word_level.py --split-strategy wesr_advanced` now generates a stronger taxonomy-rich companion benchmark at `data/training/standup_word_level_wesr_advanced`; its validation split has `122` continuous / `123` discrete and its test split has `246` continuous / `121` discrete with zero overlap
- the promoted checkpoint's advanced suite report at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/wesr_advanced_suite.json` reaches validation macro F1 / IoU-F1 `0.9959 / 0.9959` and test macro F1 / IoU-F1 `0.8963 / 0.8963`, but this split remains benchmark-only because its train partition is only `18` examples
- decode-only `topk_span` evaluation is now available, including cue-aware reranking via `--topk-span-cue-bonus`
- the strongest tested benchmark-time setting so far is ratio `0.10`, neighbor margin `-2.0`, max neighbors `2`, and cue bonus `1.0`
- under that cue-aware decode policy, the promoted checkpoint reaches canonical validation F1 / IoU-F1 `0.7500 / 0.8889`, canonical test F1 / IoU-F1 `0.7213 / 0.8261`, public external F1 / IoU-F1 `0.2308 / 0.1980`, and English-only external F1 / IoU-F1 `0.1156 / 0.0747`
- direct artifacts for that best setting are now available at `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_eval.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples.json`, `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_standup4ai_examples_en.json`, and `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted/cue_topk_span_wesr_advanced_suite.json`
- WESR note: the current validation split is continuous-only, so discrete/continuous evaluation is currently too imbalanced to use as a strong promotion criterion

Alternate WESR-balanced benchmark outcome:

- weak-label baseline on `data/training/standup_word_level_wesr_balanced`: validation F1 `0.8636`, validation IoU-F1 `0.8116`, test F1 `0.5714`, test IoU-F1 `0.6667`
- validation per-laughter-type F1: `0.8000` continuous, `0.8889` discrete
- test per-laughter-type F1: `0.5417` continuous, `0.5000` discrete
- treat those metrics as benchmark-only because validation support is `23`, not `102`
