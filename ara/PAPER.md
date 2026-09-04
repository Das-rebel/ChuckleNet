# ChuckleNet: Laughter Detection Research Project

**Status:** Active research — investigating whether word-level WavLM+prosody fusion can beat StandUp4AI baseline (IoU-F1=0.51)

**Project Repository:** https://github.com/Das-rebel/autonomous_laughter_prediction

**Last Updated:** 2026-08-26

---

## Layer Index

- **logic/** — Problem, claims, heuristics, solutions
- **trace/** — Exploration tree (research DAG) and session records
- **evidence/** — Raw data files (results JSON, notebooks, log files)
- **staging/** — Unclassified observations
- **src/** — Code artifacts (notebooks, configs)

## Current Best Results

| Test | N videos | Word F1 | IoU-F1@0.2 | Notes |
|------|:-:|:-:|:-:|---|
| best_fusion_model.pt (original) | 87 | 0.975 | — | Gillick, pseudo-labels |
| 5-second windows (Kaggle) | 118 | 0.674 | 0.30 | Scale221 + EMNLP labels |
| **Full FusionMLP 118v** | **118** | **0.676** | **0.31** | **Best honest result** |
| Word-level (CPU) | 40 | 0.27 | 0.22 | SimpleMLP+BN, pw=2.0 |
| StandUp4AI baseline | 330 hours | — | **0.51** | External benchmark |

## Key Open Questions

1. Can we close the gap to StandUp4AI's 0.51 IoU-F1@0.2?
2. Will scaling to 200+ videos (user's Batch 1) help?
3. Should we use WavLM-large instead of base?

See `trace/exploration_tree.yaml` for full research DAG.