# Evidence Index

## Test Results (JSON)

- `HYPOTHESIS_TEST_RESULTS.json` — 118 video 5-second window test
- `FUSIONMLP_40V_RESULTS.json` — 40 video word-level test (SimpleMLP)
- `WORD_LEVEL_30V_RESULTS.json` — 30 video word-level test
- `FULL_FUSIONMLP_118V_RESULTS.json` — 118 video word-level test (best)

## Test Results (Markdown)

- `HYPOTHESIS_TEST_RESULTS.md` — 118 video 5-second window
- `WORD_LEVEL_HYPOTHESIS.md` — 10 video word-level
- `WORD_LEVEL_30V_RESULTS.md` — 30 video word-level
- `FUSIONMLP_40V_RESULTS.md` — 40 video word-level
- `FULL_FUSIONMLP_118V_RESULTS.md` — 118 video word-level (best)
- `PIPELINE_STATE_AUGUST_25.md` — Pipeline state
- `NEXT_STEPS_AUGUST_26.md` — Recommended next steps
- `IOU_EVALUATION_DECISION_GRAPH.md` — Original decision graph

## Local Evidence (not in repo)

- `/tmp/hyp_test/embeddings/embeddings/` — 221 video embeddings (Kaggle)
- `/tmp/hyp_test/labels/` — 155 EMNLP label CSVs (Kaggle)
- `/tmp/hyp_test/best_probs.npy` — Best model predictions (118 videos)
- `/tmp/hyp_test/final_118v_results.json` — IoU eval results
- `/tmp/hyp_test/full_training_results.json` — All 3 pos_weight configs
- `/tmp/word_test/features/` — 10 word-level videos
- `/tmp/word_test2/features/` — 30 more word-level videos
- `/tmp/word_test2/all_probs_v2.npy` — Predictions for 40 videos

## Key Metrics Summary

| Test | N | Word F1 | IoU-F1@0.2 | Architecture |
|------|:-:|:-:|:-:|---|
| Original | 87 | 0.975 | — | best_fusion_model.pt (Gillick) |
| 5-second windows | 118 | 0.674 | 0.30 | New MLP, scale221 embeddings, EMNLP labels |
| Word-level (SimpleMLP) | 40 | 0.27 | 0.22 | SimpleMLP no BN, pw=2.0 |
| **Word-level (Full)** | **118** | **0.676** | **0.31** | **Full FusionMLP + BN, pw=2.0** |
| StandUp4AI baseline | 330h | — | **0.51** | External benchmark |

## Trained Models

- `scale221/best_fusion_model.pt` (2.2MB) — Original F1=0.975 model
- `scale221/scale221_fusion_model.pt` (2.2MB) — scale221 training
- `scale221/sanity_hypothesis_model.pt` — Sanity test model

## Repositories

- **GitHub**: https://github.com/Das-rebel/autonomous_laughter_prediction
- **Kaggle datasets used**:
  - `subhajitdas/scale221` — 221 video embeddings (62MB)
  - `subhajitdas/standup4ai-en-uk-labels` — 155 EMNLP labels (3MB)