# Research Tree Expanded - Final Version

**Date:** 2026-05-16  
**Updated:** With Interaction Model + MultiLinguahah analysis

---

## User Interests
- Prosody (F0, energy, rate) ✅
- ToM (Theory of Mind for political comedy) ✅
- Combining both with text ✅

---

## NEW ARCHITECTURES TO MODEL ON

### 1. Interaction Model (thinkingmachines.ai/blog/interaction-models/)

| Feature | Benefit for Laughter Detection |
|---------|-------------------------------|
| 200ms chunks | Aligns with word timing (~150-250ms) |
| Native time-awareness | Captures pause direction (before punchline) |
| No VAD harness | Model learns boundaries natively |
| Concurrent streams | Handle overlapping laughter + speech |
| Early fusion | All modalities processed jointly |

### 2. MultiLinguahah (arxiv:2605.06309)

| Feature | Benefit |
|---------|---------|
| BYOL-A encoder | Self-supervised, cross-lingual |
| Isolation Forest | Unsupervised laughter detection |
| Energy segmentation | No labeled data needed |
| Universal laughter | Works across en/zh/hi |

**Pipeline:** Audio → Voice Removal → Energy Segmentation → BYOL-A → Isolation Forest

### 3. Gillick 2019 (Interspeech)
- CNN on mel-spectrograms
- F1=0.89 on podcast audio
- 200ms windows, CTC loss

### 4. Purandare 2006 (EMNLP)
- Pause 0.8s before punchline (p<0.001)
- Most predictive single feature

---

## HYPOTHESIS MAP (Complete)

### BRANCH A: TEXT FEATURES (F1=0.82)
| Hypothesis | Status | Result |
|------------|--------|--------|
| A1. Word embeddings (XLM-R) | ✅ | F1=0.82 |
| A6. TF-IDF baseline | ✅ | F1=0.73 |
| A8. Contextual + labels | ❌ | LEAKAGE F1=0.94 |

### BRANCH B: AUDIO PROSODY (F1=0.20 → Target >0.50)
| Hypothesis | Evidence | Priority |
|------------|----------|----------|
| H6.1: F0 DROP at punchline | Pickering 2009 | 🔴 HIGH |
| H6.2: Pause >1s | Purandare 2006 (p<0.001) | 🔴 HIGH |
| H6.3: F0 variability | Bachorowski 2001 | 🟡 MED |
| H6.4: Speech rate slows | Pickering 2009 | 🟡 MED |
| H6.5: Energy contrast | Bertero 2016 | 🟡 MED |

### BRANCH C: THEORY OF MIND (ToM)
| Hypothesis | Description | Priority |
|------------|-------------|----------|
| H7.1: Entity references | Politicians, policies → ToM | 🟡 MED |
| H7.2: Modal verbs | would/could → reality gap | 🟡 MED |
| H7.3: "They said X, we know Y" | Gap detection | 🟡 MED |
| H7.4: Taboo topics | Norm violation → laughs | 🟢 NEW |

### BRANCH D: TEMPORAL POSITION (CONFIRMED)
| Finding | Evidence |
|---------|----------|
| Peak at 20-30% through show | Chi-square p=4e-143 |
| Min at 90-100% | 10.1% laugh rate |

### BRANCH E: INTERACTION MODEL (NEW)
| Hypothesis | Description | Priority |
|------------|-------------|----------|
| H12.1: 200ms chunks > word-level | Fixed windows vs Whisper boundaries | 🔴 HIGH |
| H12.2: Pause trajectory > scalar | ±3 word context | 🔴 HIGH |
| H12.3: No VAD > Whisper VAD | CTC-learned boundaries | 🟡 MED |
| H12.4: CTC loss | Native boundary learning | 🟡 MED |

### BRANCH F: MULTILINGUAHAH (NEW)
| Hypothesis | Description | Priority |
|------------|-------------|----------|
| H13.1: BYOL-A > MFCCs | Self-supervised encoder | 🔴 HIGH |
| H13.2: Isolation Forest | Unsupervised detection | 🟡 MED |
| H13.3: Label augmentation | Unsupervised to add labels | 🟡 MED |
| H13.4: Multilingual transfer | en→zh→hi | 🔴 HIGH |

### BRANCH G: HYBRID TEXT+AUDIO (NEW)
| Hypothesis | Description | Priority |
|------------|-------------|----------|
| H14.1: XLM-R + prosody | Combined features | 🔴 HIGH |
| H14.2: Early fusion > late | Concatenate at feature level | 🟡 MED |
| H14.3: Cross-modal attention | Audio ↔ text attention | 🟡 MED |

---

## KEY PAPERS FOR ARCHITECTURE

| Paper | Architecture | Key Feature | F1 |
|-------|-------------|-------------|-----|
| Gillick 2019 | CNN on spectrograms | 200ms windows, CTC | 0.89 |
| MultiLinguahah 2026 | BYOL-A + Isolation Forest | Unsupervised cross-lingual | 0.68 |
| Interaction Model | Streaming transformer | 200ms chunks, no VAD | N/A |
| Purandare 2006 | Pause features | Pause 0.8s before punchline | - |
| Pickering 2009 | F0 analysis | F0 DROP at punchline | - |

---

## IMPLEMENTATION ROADMAP

### IMMEDIATE (This Week)
1. **Pause trajectory feature (H12.2)**
   - Compute pause for ±3 word context
   - Feed as time series to existing model
   - Target: Beat F1=0.20

### SHORT-TERM (Next Week)
2. **WavLM/BYOL-A encoder (H13.1)**
   - Use pre-trained self-supervised encoder
   - Extract audio features at 200ms
   - Target: F1 > 0.70 audio-only

3. **F0 extraction (H6.1)**
   - Use librosa.pyin for pitch
   - Detect F0 DROP before punchline

### MEDIUM-TERM (This Month)
4. **XLM-R + Prosody fusion (H14.1)**
   - Combine text features with audio
   - Early fusion (concatenate)
   - Target: F1 > 0.87

5. **Multilingual transfer (H13.4)**
   - Test en→zh, en→hi
   - Use BYOL-A for language-agnostic audio

### LONG-TERM (Future)
6. **CTC + No VAD (H12.4)**
   - Train model with CTC loss
   - Native boundary learning

7. **Cross-modal attention (H14.3)**
   - Transformer with audio-text attention

---

## STATUS

- [x] Research Interaction Model architecture
- [x] Research MultiLinguahah paper
- [x] Identify key architectural features
- [ ] Extract pause trajectory features
- [ ] Test BYOL-A/WavLM encoder
- [ ] Implement text + audio fusion
- [ ] Test multilingual transfer

---

## FILES CREATED

1. `docs/RESEARCH_TREE_EXPANDED.md` - Full hypothesis tree
2. `docs/MULTILINGUAHAH_ANALYSIS.md` - MultiLinguahah insights
3. `docs/HYPOTHESIS_RESULTS_SESSION3.md` - Session 3 findings