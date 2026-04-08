# Hugging Face Humor Proxy Dataset Report

## Validation Summary

- Emotion dataset path: `/Users/Subho/datasets/manual_acquisition/emotion`
- SST-2 dataset path: `/Users/Subho/datasets/manual_acquisition/sst2`
- Emotion label mapping: `['sadness', 'joy', 'love', 'anger', 'fear', 'surprise']`
- Emotion positive label used: `joy` (id `1`)
- SST-2 positive label used: `positive` (id `1`)
- Quality filter: min chars `10`, max chars `500`, English-only heuristic, quality score threshold `85.0`

## Output Counts

- Unified rows: `77526`
- Humor rows: `37580`
- Non-humor rows: `39946`
- Mean quality score: `99.2`

## Split Counts

- Train: `70849`
- Validation: `2867`
- Test: `3810`

## Success Criteria

- Minimum 15,000 positive samples: `True` (37580 available)
- Mean quality score > 85: `True` (99.2)
- Ready-to-train files created: `True`

## Files

- emotion_positive_csv: `data/training/hf_humor_proxy/emotion_joy_humor.csv`
- emotion_negative_csv: `data/training/hf_humor_proxy/emotion_non_joy_non_humor.csv`
- sst2_positive_csv: `data/training/hf_humor_proxy/sst2_positive_humor.csv`
- sst2_negative_csv: `data/training/hf_humor_proxy/sst2_negative_non_humor.csv`
- unified_csv: `data/training/hf_humor_proxy/hf_humor_proxy_unified.csv`
- train_csv: `data/training/hf_humor_proxy/hf_humor_proxy_train.csv`
- validation_csv: `data/training/hf_humor_proxy/hf_humor_proxy_validation.csv`
- test_csv: `data/training/hf_humor_proxy/hf_humor_proxy_test.csv`
- quality_report_json: `data/training/hf_humor_proxy/quality_report.json`
- quality_report_md: `data/training/hf_humor_proxy/quality_report.md`

## Rejection Counts

- emotion: emotion:content=9, emotion:length=4
- sst2: sst2:content=12452, sst2:language=118, sst2:length=4093
