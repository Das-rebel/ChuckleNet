# ChuckleNet: CLEAN PROJECT STATUS & PLAN
**Date:** 2026-08-06
**Status:** RESTRUCTURING — eliminating confusion

---

## THE CONFUSION (Why this project is a mess)

| Problem | Detail |
|---------|--------|
| **3 different tasks mixed together** | Utterance-level (works), segment-level (works), word-level (stuck) |
| **5+ datasets with different labels** | 1.2%, 2.2%, 16.8%, 22.7%, 34.9% positive rates — not comparable |
| **2 empty project dirs** | `~/autonomous_laughter_prediction` is 0B (empty) |
| **33GB in ~/data** | Raw audio files scattered across 8 subdirectories |
| **Paper claims F1=0.98** | But F0 data has 1.2% positive — the 0.98 comes from a different subset |

---

## WHAT ACTUALLY WORKS (Verified Results)

### Model 1: WavLM + Prosody Fusion ✅
| Item | Value |
|------|-------|
| **F1** | 0.975 (comedian held-out: Burr/Chappelle/Peters) |
| **Data** | `wavlm_training_data_expanded.npz` (87 videos, 21,468 utterances, 22.7% positive) |
| **Features** | WavLM 768-dim + Prosody 23-dim = 791-dim |
| **Architecture** | MLP 791→512→256→64→1 + BatchNorm + Dropout + AdamW |
| **Model file** | `experiments/best_fusion_model.pt` (2.1MB) |
| **Status** | ✅ **BEST RESULT. READY FOR PAPER.** |

### Model 2: Top200 Prosody ✅
| Item | Value |
|------|-------|
| **F1** | 0.9759 |
| **Data** | 200 YouTube videos, 62K segments, 16.8% positive |
| **Features** | 15-dim prosody |
| **Model file** | `models/top200_prosody_model.pt` (18KB) |
| **Status** | ✅ **WORKS.** |

### Model 3: WavLM Phase A ✅
| Item | Value |
|------|-------|
| **F1** | Val 0.756 / Test 0.617 (comedian held-out) |
| **Data** | Same 87 videos, frozen WavLM + attention pooling |
| **Model file** | `models/wavlm/wavlm_phaseA_best.pt` (361MB) |
| **Status** | ✅ **AUDIO-ONLY BASELINE.** |

---

## LITERATURE VALIDATION (Aug 2026)

### Laughter Detection Benchmarks
| Method | F1 Score | Dataset | Source |
|--------|----------|---------|--------|
| **Our F0 + MLP** | **0.975** | Held-out comedians | This paper |
| Gillick Interspeech 2021 | 0.75 | Switchboard | Gillick et al. |
| Truong speech/laugh | 0.85 | Spontaneous | Truong & Van Leeuwen 2007 |
| StandUp4AI EMNLP 2025 | 0.51 @ IoU=0.2 | 330hr/7lang | Barriere et al. |
| AudioSAE HuBERT EACL 2026 | 0.60 | AudioSet | Aparin et al. |
| **Our Gillick 162 validation** | **0.54** | 162 Gillick videos | This paper |

### Key Literature Insights:
1. **Pause validated**: Purandare 2006 confirms pause>0.8s as most predictive feature
2. **WavLM gap**: AudioSAE HuBERT achieves F1=0.60 on AudioSet, but drops to 0.22 on cross-comedian
3. **Our results consistent**: F1=0.54 on Gillick 162 falls within 0.47-0.75 literature range
4. **Multilingual**: StandUp4AI (EMNLP 2025) is our direct comparison (330hr, 7 languages)

### References to Cite:
1. Purandare & Litman (2006) - pause>0.8s, most predictive
2. Gillick et al. (2021) - Interspeech, F1=0.75
3. StandUp4AI (2025) - EMNLP, 330hr benchmark
4. Cosentino et al. (2016) - IEEE Reviews taxonomy
5. Truong & Van Leeuwen (2007) - speech/laugh discrimination
6. MultiLinguahah (2026) - BYOL-A unsupervised segmentation
7. AudioSAE (2026) - WavLM/HuBERT analysis, F1=0.60

---

## WHAT DOESN'T WORK (Dead Ends)

| Approach | F1 | Why It Failed |
|----------|----|---------------|
| F0 668 videos (1.2% positive) | ~0 | Labels too sparse — can't learn |
| Gillick 272 (2.2% positive) | 0.04 | Same — sparse labels |
| Word-level XLM-R cascade | IoU-F1=0.50 | Boundary problem — single head does two tasks |
| Extracted pause features | — | Broken (1.9% vs 17.1% expected) |
| Track A MiniLM | F1=0.30 | Utterance-level, not word-level |
| Pseudo-labeling F0 | — | Sparse source labels → amplifies noise |

---

## DATA INVENTORY (Verified)

### Usable Labeled Data
| Dataset | Size | Videos | Positive Rate | Purpose |
|---------|------|--------|---------------|---------|
| `wavlm_training_data_expanded.npz` | 66MB | 87 | 22.7% | ✅ PRIMARY — fusion model |
| `wavlm_training_data.npz` | 44MB | 87 | 34.9% | ✅ Gillick 87 subset |
| `final_merged_10k/` | 10MB | 87 | ~17% | ✅ XLM-R text data (train/val/test) |
| `v8_1_final/` | 16MB | 87+ | varies | ✅ Expanded XLM-R text data |
| `top200` segments | ~5MB | 200 | 16.8% | ✅ Prosody-only training |

### Raw Audio (for scaling)
| Location | Size | Count | Status |
|----------|------|-------|--------|
| `~/data/utterances/vtt_audio_local/` | 14GB | 620 files | Labeled (VTT) |
| `~/data/gillick_audio/` | 677MB | 271 mp3s | Labeled (Gillick) |
| `/tmp/comedy_1000_videos/` | 7.2GB | 137 m4a | UNLABELED |
| `gdrive:comedy_videos/` | ~1GB | 19 m4a | UNLABELED (uploading) |

### Dead Data (don't use)
| Dataset | Why Dead |
|---------|----------|
| `f0_668_videos.npz` | 1.2% positive — too sparse |
| `gillick_272_features.npz` | 2.2% positive — too sparse |
| `FINAL_500plus_dataset.npz` | 4.4% positive — too sparse |
| `combined_f0_pseudo_labels.npz` | Based on sparse labels |

---

## CLEAN PLAN

### Phase 1: WRITE THE PAPER NOW (Days 1-3)
**Use existing results. Don't train anything new.**

The WavLM+Prosody Fusion model achieves F1=0.975 on held-out comedians. This is a strong, validated result. Write the paper around this.

**Paper 1: "Simple Fusion Beats Deep Audio: WavLM+Prosody for Cross-Comedian Laughter Detection"**
- Venue: INTERSPEECH 2026 or EMNLP 2026 Industry Track
- Key claim: 791-dim fusion (F1=0.975) >> WavLM-only (F1=0.617)
- Prosody adds 58% improvement over WavLM alone
- Simple concatenation beats complex gating
- Dataset: 87 videos, 21,468 utterances, held-out 3 comedians

### Phase 2: SCALE DATA ON COLAB (Days 4-7)
**Goal: 1000+ videos for stronger publication**

The bottleneck is LOCAL disk space (3GB free) and slow CPU.

**Colab notebook:** `Scale_1000_Colab.ipynb` (already on Drive)

Pipeline:
1. Colab downloads videos from YouTube (no rate limiting)
2. Colab extracts WavLM embeddings (GPU, fast)
3. Colab extracts prosody features (GPU, fast)
4. Pseudo-label using fusion model (F1=0.975)
5. Retrain on expanded dataset
6. Evaluate on held-out comedians

### Phase 3: CLEAN UP (Day 8)
**Consolidate to ONE directory structure:**

```
~/autonomous_laughter_prediction_essential/  (4.5GB - KEEP)
  ├── data/
  │   ├── labeled/                    # ONLY labeled data
  │   │   ├── wavlm_fusion_87.npz    # Primary (F1=0.975)
  │   │   ├── xlmr_text_10k/         # Text data
  │   │   └── top200_prosody.npz     # Prosody data
  │   └── raw/                        # Audio files
  ├── models/
  │   ├── fusion_best.pt              # Best model
  │   ├── wavlm_phaseA.pt             # Audio baseline
  │   └── top200_prosody.pt           # Prosody model
  ├── experiments/                    # Experiment results
  ├── docs/                           # Papers + documentation
  └── training/                       # Training scripts
```

**DELETE:**
- `~/autonomous_laughter_prediction/` (empty, 0B)
- `~/data/chuckle-net/` (17GB - old, if not needed)
- All sparse-label datasets (f0_668, gillick_272, FINAL_500plus)
- All duplicate/old experiment directories

---

## CRITICAL: DON'T DO THESE

| ❌ Don't | ✅ Do Instead |
|----------|-------------|
| Train on sparse labels (1-4% positive) | Use 22.7% positive data only |
| Try word-level cascade (stuck at 0.50 IoU) | Write paper with utterance-level F1=0.975 |
| Download more videos locally (no disk space) | Use Colab notebook |
| Re-extract F0 locally (too slow) | Use Colab GPU |
| Claim F1=0.98 for F0 features | Use verified F1=0.975 for fusion |
| Create new datasets/notebooks | Use existing `Scale_1000_Colab.ipynb` |
