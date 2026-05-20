# MultiLinguahah Paper - Key Architecture Insights

**Paper:** MultiLinguahah: A New Unsupervised Multilingual Acoustic Laughter Segmentation Method  
**Authors:** Sofia Callejas, Nahuel Gomez, Catherine Pelachaud  
**URL:** https://arxiv.org/abs/2605.06309

---

## Architecture: 4-Step Pipeline

```
Audio Input → Voice Removal → Energy-Based Segmentation → BYOL-A Encoder → Isolation Forest (Anomaly Detection)
```

### Step 1: Voice Removal
- Audio source separation to isolate voices from non-vocal audio
- Retain background (laughter, music, ambient)
- For studio recordings: channel subtraction

### Step 2: Energy-Based Segmentation
- `auditok` peak detector on waveform energy
- Threshold to find beginning/end of non-speech events
- Keeps laughter, music, ambient; removes silence

### Step 3: BYOL-A Encoder
- Self-supervised audio representation learning
- Pre-trained on AudioSet (~5,455 hours) + FSD50K (~80 hours)
- Learns non-semantic audio representations (laughter = non-semantic)

### Step 4: Isolation Forest (Anomaly Detection)
- Laughter = anomaly because it has **universal acoustic characteristics**
- Detects outliers via recursive random feature splits
- No labeled data required!

---

## Key Insights for Our Research

### 1. Laughter is UNIVERSAL Across Languages
- Unlike speech, laughter has similar acoustic patterns across cultures
- BYOL-A learns language-agnostic representations
- **Our target: en/zh/hi multilingual is feasible!**

### 2. BYOL-A > Traditional Features
- Self-supervised beats MFCCs/F0 for cross-lingual transfer
- Works on non-semantic audio tasks
- **We should use BYOL-A or similar encoder (WavLM, HuBERT)**

### 3. Isolation Forest Approach
- Treats laughter as anomaly/outlier
- Works without labeled data
- Could augment our VTT-based labels

### 4. Combining Approaches (Hybrid)
- Omine (ASR-based) + MultiLinguahah (acoustic) = complementary gains
- **Our XLM-R (text) + MultiLinguahah (audio) could be powerful combination**

---

## Results

| Setting | Method | F1 @ IoU=0.3 |
|---------|--------|--------------|
| US English Stand-up | Omine | **0.679** |
| Spanish Stand-up | MultiLinguahah | **0.649** |
| Hungarian Stand-up | MultiLinguahah | **0.796** |

MultiLinguahah excels in multilingual settings.

---

## Application to Our Task

### Current Approach:
```
Whisper → Word timestamps → VTT [laughter] markers → Aligned labels → XLM-R (F1=0.82)
```

### Proposed Hybrid:
```
VTT labels → Energy segmentation → BYOL-A encoder → Isolation Forest score
                                                                    ↓
XLM-R text features → Combined features → Word-level laughter prediction
```

### Benefits:
1. **Audio features** from BYOL-A (better than MFCCs)
2. **Unsupervised** laughter detection to augment labels
3. **Multilingual** robustness for en/zh/hi
4. **Hybrid approach** combines text + acoustic anomaly

---

## Action Items

- [ ] Evaluate BYOL-A encoder for our audio features
- [ ] Test Isolation Forest for laughter detection on our data
- [ ] Combine with XLM-R text features (H8.1)
- [ ] Test multilingual transfer (en→zh, en→hi)