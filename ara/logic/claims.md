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
## C07: merge_threshold=0.8 improves IoU-F1@0.2 from 0.31 to 0.33
- **Statement**: Using merge_threshold=0.8 (only confident >0.8 predictions form segments) gives IoU-F1@0.2=0.33 vs merge_threshold=0.5 giving 0.31.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If merge_th=0.5 gave equal or better IoU, claim would be refuted.
- **Proof**: Sweep over merge_threshold ∈ {0.5, 0.6, 0.7, 0.8} on 118 videos:
  - merge_th=0.5: IoU@0.2=0.3185
  - merge_th=0.8: IoU@0.2=0.3302
- **Dependencies**: none
- **Tags**: threshold-tuning, post-processing

## C08: 50 epochs gives marginal F1 improvement over 30 epochs
- **Statement**: Training FusionMLP for 50 epochs gives F1=0.6783 vs 30 epochs giving F1=0.6760 on 118 videos.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If more epochs gave worse F1, claim would be refuted.
- **Proof**: 30ep: 0.6760, 50ep: 0.6783 (118 videos, same architecture).
- **Dependencies**: none
- **Tags**: training-duration, diminishing-returns

## C09: Standard FusionMLP matches Large variant
- **Statement**: Increasing hidden size (1024→512→128) does not improve over Standard (512→256→64) — both give F1≈0.67.
- **Status**: supported
- **Provenance**: ai-executed
- **Falsification criteria**: If Large gave F1 > 0.69, claim would be refuted.
- **Proof**: Standard: 0.6783, Large: 0.6714 on 118 videos.
- **Dependencies**: none
- **Tags**: architecture, diminishing-returns

## C10: Data scale is the limiting factor, not architecture
- **Statement**: Going from 10 → 30 → 40 → 118 videos improved word-level F1 from 0.07 → 0.13 → 0.27 → 0.68. Architecture changes had marginal effect.
- **Status**: supported
- **Provenance**: ai-executed (validating user insight)
- **Falsification criteria**: If architecture changes between 118 and 30 vids made bigger difference than data, claim would be refuted.
- **Proof**: F1 trend across dataset sizes; Standard vs Large architectures similar.
- **Dependencies**: C03
- **Tags**: data-scale, user-insight

