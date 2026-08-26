# System Architecture

## Overview

Word-level laughter detection in stand-up comedy videos using WavLM audio embeddings + prosodic features + FusionMLP classifier.

## Pipeline Stages

```
Audio (.m4a) → WavLM-base (768-dim) ─┐
                                    ├─→ Concat (791-dim) → StandardScaler → FusionMLP → Laugh prob
EMNLP labels (BIO) → Aggregation ────┘                                          │
                                                                                ↓
                                                                          IoU Evaluation
```

## Components

### 1. Feature Extraction
- **Audio**: 16kHz mono (librosa.load)
- **WavLM-base**: Pretrained, 768-dim embedding per audio chunk
- **Prosody 23-dim**: F0 (5) + Energy (5) + Duration (2) + Spectral (5) + Voice Quality (6)
- **Total**: 791-dim per word/segment

### 2. FusionMLP Classifier
```
Input (791) → Linear(512) → ReLU → BatchNorm → Dropout(0.3) →
              Linear(256) → ReLU → BatchNorm → Dropout(0.3) →
              Linear(64) → ReLU → BatchNorm → Dropout(0.3) →
              Linear(1) → Sigmoid
```

- Optimizer: AdamW(lr=1e-3, weight_decay=0.01)
- Loss: Weighted BCE with pos_weight=2.0
- Batch size: 256

### 3. IoU Evaluation
- Convert per-word predictions → time spans (merge consecutive above-threshold)
- Convert BIO labels → time spans
- Compute IoU at thresholds [0.1, 0.2, 0.3, 0.4, 0.5]
- F1 = 2*P*R/(P+R) where matches require IoU ≥ threshold

## Key Design Decisions

- **BatchNorm enabled**: Critical for stable training (heuristic H01)
- **Manual weighted loss**: More portable than nn.BCELoss pos_weight (heuristic H04)
- **GroupKFold by video**: Prevents data leakage between train/test
- **5-second segment features**: Match StandUp4AI evaluation better than word-level (heuristic based on C04)

## Data Flow

```
Input: 5-second audio chunk
  ↓
[WavLM-base: 768-dim] ──── prosody23(): 23-dim
  ↓                                ↓
  └──────── concat ───────────────┘
              ↓
        [791-dim feature]
              ↓
   [StandardScaler]
              ↓
       [FusionMLP]
              ↓
      [sigmoid → prob]
```