# Heuristics

## H01: Use FULL FusionMLP architecture with BatchNorm
- **Rationale**: BatchNorm enables stable training with larger batches. SimpleMLP without BN had NaN issues and worse convergence. Full architecture with BN achieved F1=0.27 vs 0.13 without BN.
- **Provenance**: ai-executed
- **Sensitivity**: high
- **Code ref**: `Process_All_255_Colab.ipynb`, `Test_Hypothesis_Batch1.ipynb`

## H02: pos_weight ≤ 3.0 (from historical failures)
- **Rationale**: pos_weight=5.0 caused model saturation (predicting all 1.0). At 12% positive rate, pos_weight=2.0 gives best F1. Capped at 3.0 to prevent the documented failure mode.
- **Provenance**: user (from 18 historical failure patterns in `docs/HISTORICAL_TRAINING_FAILURES.md`)
- **Sensitivity**: medium
- **Code ref**: All training notebooks use `pos_weight = min((1.0 - pos_rate) / max(pos_rate, 1e-6), 3.0)`

## H03: Lower min word duration threshold for feature extraction
- **Rationale**: Original threshold (0.02s) + WavLM chunk min (0.1s) was dropping 75% of short words. Lowering to 0.005s and 0.01s recovers them.
- **Provenance**: ai-executed
- **Sensitivity**: medium
- **Code ref**: `Process_All_255_Colab.ipynb` Cell 4 `word_features()` function

## H04: Use BCEWithLogitsLoss with manual weighted loss
- **Rationale**: nn.BCELoss() in older PyTorch versions doesn't support pos_weight parameter. Manual implementation: `loss = -(weights * BCE_per_sample).mean()` works on all versions.
- **Provenance**: ai-executed
- **Sensitivity**: low
- **Code ref**: Multiple notebooks, training functions

## H05: NaN-clean features before StandardScaler
- **Rationale**: librosa.pyin can produce NaN on short/quiet audio segments. `np.nan_to_num(X, nan=0.0)` is applied before StandardScaler to prevent NaN propagation through BatchNorm.
- **Provenance**: ai-executed
- **Sensitivity**: high
- **Code ref**: All training code applies `np.nan_to_num` before scaler.fit_transform

## H06: Use existing Kaggle datasets instead of downloading
- **Rationale**: scale221 embeddings and EMNLP labels are already on Kaggle as public datasets. Re-downloading from Drive is slow (~3-5 files/min) when data is already cached.
- **Provenance**: ai-suggested
- **Sensitivity**: high
- **Code ref**: Hypothesis test notebooks use `subhajitdas/scale221` and `subhajitdas/standup4ai-en-uk-labels` from Kaggle

## H07: Use manual weighted loss instead of BCELoss pos_weight
- **Rationale**: The `pos_weight` parameter in nn.BCELoss is only available in newer PyTorch. Using `BCEWithLogitsLoss(pos_weight=...)` is more portable, but manual weighted BCE works everywhere.
- **Provenance**: ai-executed
- **Sensitivity**: low
- **Code ref**: Training scripts that use `pos_weight` parameter

## H08: Save features to Drive, not local Colab working dir
- **Rationale**: Colab sessions are ephemeral. Local `/content/process255/` is lost on disconnect. Saving to Drive `/content/drive/MyDrive/standup4ai/features_255/` ensures persistence.
- **Provenance**: ai-executed
- **Sensitivity**: high
- **Code ref**: `Process_All_255_Colab.ipynb` Cell 5 (saves to `DRIVE_FEATURES`)

## H09: IoU evaluation works with merged segment predictions
- **Rationale**: Convert per-word or per-segment probabilities into continuous time spans by merging consecutive above-threshold predictions. Then compute IoU against ground truth BIO-derived spans.
- **Provenance**: ai-executed
- **Sensitivity**: medium
- **Code ref**: `merge()` function in test notebooks

## H10: pos_weight=2.0 is optimal for ~12% positive rate
- **Rationale**: Empirically tested {1.0, 2.0, 3.0}. pw=2.0 gave best F1 (0.676) for 12% positive rate.
- **Provenance**: ai-executed
- **Sensitivity**: medium
- **Code ref**: 118-video training with `pos_weight=2.0`