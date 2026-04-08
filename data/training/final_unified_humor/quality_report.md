# Final Unified Humor Dataset Report

## Source Inventory

- `hf_humor_proxy`: status=loaded, loaded=77,526, path=`data/training/hf_humor_proxy/hf_humor_proxy_unified.csv`
- `meld`: status=loaded, loaded=13,708, path=`/Users/Subho/datasets/MELD/data/MELD`
- `real_world_youtube_validation`: status=loaded, loaded=3,004, path=`data/training/youtube_comedy_production/valid.jsonl`
- `reddit_jokes`: status=loaded, loaded=101,609, path=`data/training/reddit_jokes/reddit_jokes_humor.csv`
- `synthetic_humor`: status=loaded, loaded=390, path=`/Users/Subho/datasets/manual_acquisition/synthetic_humor_dataset.csv`

## Validation Summary

- Quality-pass rows: `193,009`
- Retained rows: `184,229`
- Duplicate rows removed: `8,164`
- Conflicting rows removed: `616`
- Label consistency: `99.68%`

## Unified Dataset

- Total rows: `184,229`
- Labels: `{'0': 47407, '1': 136822}`
- Sources: `{'hf_humor_proxy': 69745, 'meld': 11401, 'real_world_youtube_validation': 1440, 'reddit_jokes': 101609, 'synthetic_humor': 34}`
- Quality mean: `99.49`

## Splits

- Train: `147,383`
- Validation: `18,424`
- Test: `18,422`

## Training Recommendations

- Use class weighting or focal loss because Reddit introduces a positive-heavy distribution.
- Treat `meld` and `hf_humor_proxy` as proxy-labeled sources and consider source-aware sampling.
- Keep `real_world_youtube_validation` available as a separate evaluation slice if you want a stricter external benchmark.

## Performance Projection

- Conservative projected F1: `0.786`
- Target-band projected F1: `0.786-0.841`
- Basis: Inference from dataset scale, label-origin mix, and retained average quality. This is a planning estimate, not a measured benchmark.

## Per-Source Metrics

- `hf_humor_proxy`: loaded=77,526, quality_pass=77,526, retained=69,745, duplicates_removed=7,442, conflicts_removed=340, mean_quality=99.2
- `meld`: loaded=13,708, quality_pass=12,040, retained=11,401, duplicates_removed=370, conflicts_removed=266, mean_quality=94.35
- `real_world_youtube_validation`: loaded=3,004, quality_pass=1,444, retained=1,440, duplicates_removed=6, conflicts_removed=0, mean_quality=76.81
- `reddit_jokes`: loaded=101,609, quality_pass=101,609, retained=101,609, duplicates_removed=0, conflicts_removed=0, mean_quality=99.78
- `synthetic_humor`: loaded=390, quality_pass=390, retained=34, duplicates_removed=346, conflicts_removed=10, mean_quality=97.67
