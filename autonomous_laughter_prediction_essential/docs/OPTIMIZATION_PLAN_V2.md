# 40+ Experiments → 7 Proven Optimizations for WavLM Training

## Sources: 44 hypotheses, 5 sessions, MultiLinguahah 2026, Orchestra review

---

## OPTIMIZATION 1: Focal Loss Instead of Weighted Cross-Entropy
**Source:** H6.1, Session 5 class imbalance
**Finding:** Weighted CE with pos_weight=3.2 helps but focal loss handles hard/easy sample distinction better.
**Implementation:** `FocalLoss(alpha=0.25, gamma=2.0)` — focuses on hard-to-classify samples.
**Expected gain:** +2-5% F1 on imbalanced 15.7% positive rate.

## OPTIMIZATION 2: Label Smoothing
**Source:** H4.4 (label leakage), H2.5 (weak label artifacts)
**Finding:** Weak labels from YouTube VTT are noisy. Label smoothing (0.1) prevents overconfidence on mislabeled examples.
**Implementation:** `CrossEntropyLoss(label_smoothing=0.1)`
**Expected gain:** +1-2% F1, better calibration.

## OPTIMIZATION 3: Cosine Annealing with Warm Restarts
**Source:** Session 3-5 training instability
**Finding:** Single cosine schedule plateaus. Warm restarts (T_0=5, T_mult=2) help escape local minima.
**Implementation:** `CosineAnnealingWarmRestarts(optimizer, T_0=len(dataloader)*5, T_mult=2)`
**Expected gain:** +1-3% F1 at convergence.

## OPTIMIZATION 4: Gradient Accumulation
**Source:** T4 GPU memory constraint
**Finding:** BS=64 is limited by T4 memory. Gradient accumulation simulates BS=256 without OOM.
**Implementation:** `accumulate gradients over 4 batches before optimizer.step()`
**Expected gain:** +1-2% F1 from larger effective batch size.

## OPTIMIZATION 5: BatchNorm Architecture
**Source:** H6.1 (training instability with deep MLPs)
**Finding:** Deep MLP (5 layers) with only Dropout shows variance. BatchNorm stabilizes.
**Implementation:** `Linear → BatchNorm1d → GELU → Dropout` instead of `Linear → GELU → Dropout`
**Expected gain:** +1-2% F1, faster convergence.

## OPTIMIZATION 6: Cosine Embedding Loss (Auxiliary)
**Source:** MultiLinguahah 2026 (BYOL-A contrastive approach)
**Finding:** Laughter embeddings should cluster. Adding contrastive loss as auxiliary task helps.
**Implementation:** Auxiliary loss that pulls same-class embeddings together, pushes different-class apart.
**Expected gain:** +2-4% F1 (literature reports +3-5% with contrastive auxiliary).

## OPTIMIZATION 7: Weight Decay Tuning
**Source:** Session 5 overfitting observation
**Finding:** 517K params on 76K samples with weight_decay=0.01 may be too aggressive. Lower = better generalization.
**Implementation:** `weight_decay=0.001` for 517K params on 76K samples.
**Expected gain:** +1-2% F1 (prevents underfitting).

---

## Estimated Cumulative Gain: +8-18% F1
## Baseline: F1=0.416 (Session 5, simple model, 13.7K samples)
## Target: F1=0.48-0.55 (optimized model, 76K samples)
