# Claims

## C01: best_fusion_model.pt saturates on word-level EMNLP data
- **Statement**: The existing best_fusion_model.pt (F1=0.975 on Gillick) outputs probabilities 0.45-0.53 (std=0.004) when evaluated on word-level EMNLP data — the model is saturated and needs retraining.
- **Status**: supported
- **Provenance**: ai-suggested
- **Falsification criteria**: If probabilities had std > 0.05 and reasonable distribution (>5% above 0.5 threshold), claim would be refuted.
- **Proof**: Tested directly on 30 word-level videos in `/tmp/word_test2/`. Probabilities clustered 0.45-0.53.
- **Dependencies**: C02
- **Tags**: model-saturation, distribution-shift

## C02: Full FusionMLP with BatchNorm outperforms SimpleMLP without BN
- **Statement**: Using the full architecture (791→512→256→64→1) with BatchNorm gives F1=0.27 on 40 word-level videos vs F1=0.13 with simplified architecture.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If SimpleMLP matched or exceeded full FusionMLP F1, claim would be refuted.
- **Proof**: Test on same 40 videos:
  - SimpleMLP (no BN): F1=0.13
  - Full FusionMLP + BN: F1=0.27
- **Dependencies**: none
- **Tags**: architecture, batchnorm

## C03: Word-level F1 improves with more videos
- **Statement**: Word-level F1 scales with dataset size: 10 videos → F1=0.07, 30 videos → F1=0.13, 40 videos → F1=0.27.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If F1 stays flat or decreases with more data, claim would be refuted.
- **Proof**: Three tests on different dataset sizes, all using same architecture.
- **Dependencies**: C02
- **Tags**: data-scale, learning-curve

## C04: 5-second windows work better than word-level for IoU evaluation
- **Statement**: On the same architecture, segment-level (5s window) features achieve IoU-F1@0.2=0.30 vs word-level=0.19-0.22.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If word-level matched or beat 5s window IoU-F1, claim would be refuted.
- **Proof**: Multiple tests at different data sizes:
  - 118 segment-level videos: IoU=0.30
  - 40 word-level videos: IoU=0.22
- **Dependencies**: none
- **Tags**: granularity, evaluation

## C05: User's Batch 1 features are NOT accessible from Drive
- **Statement**: The word-level features from user's earlier Colab run (Batch 1, 49 videos) are not present in any standard Drive location I can find.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If features were found in `features_255/` or another known location, claim would be refuted.
- **Proof**: Searched `features/`, `features_255/`, `checkpoints/`, `transcripts/` on Drive — all empty or missing for npy files.
- **Dependencies**: none
- **Tags**: data-availability, lost-data

## C06: 118 video training reaches F1=0.676, IoU=0.31
- **Statement**: With proper full FusionMLP training on 118 videos with EMNLP ground truth labels, word-level F1=0.676 and IoU-F1@0.2=0.31 is achievable.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If reproduction yields different results, claim would be weakened.
- **Proof**: `docs/FULL_FUSIONMLP_118V_RESULTS.md` documents the exact training config and results.
- **Dependencies**: C02
- **Tags**: training, results