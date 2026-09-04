# Problem Definition

## Core Question
**Can our WavLM+prosody fusion pipeline achieve IoU-F1 ≥ 0.51 at IoU=0.2 on EMNLP ground truth, matching or beating StandUp4AI's published result?**

## Background

- **Goal**: Real-time laughter detection in stand-up comedy videos
- **Best published result**: best_fusion_model.pt achieves F1=0.975 on Gillick dataset (87 videos, 22.7% positive rate, pseudo-labels from energy thresholds)
- **Benchmark to beat**: StandUp4AI achieves IoU-F1=0.51 at IoU=0.2 on 330 hours of multilingual data

## Identified Gaps

1. **Distribution shift**: Gillick vs EMNLP datasets have different characteristics
2. **Label type**: Our F1=0.975 used energy-threshold pseudo-labels, not real ground truth
3. **Granularity**: StandUp4AI uses word-level BIO; we used segment-level (5-second windows)
4. **Data scale**: StandUp4AI used 330 hours; we've processed up to 118 videos

## Constraints

- **Compute**: Kaggle P100 has CUDA incompatibility with WavLM (group_norm)
- **Compute**: Colab GPU has daily limits
- **Local CPU**: ~5 min per video for feature extraction
- **Disk**: 3.4GB free locally
- **Existing assets**: best_fusion_model.pt, scale221 embeddings (Kaggle), EMNLP labels (Kaggle)

## Hypothesis (User-Stated)

User insight: "our fusion model was far ahead we just needed a bigger data set"

- The architecture (FusionMLP + WavLM-base + 23-dim prosody) is proven
- The original F1=0.975 was on limited data (87 videos)
- More data with proper ground truth should close the IoU gap to baseline