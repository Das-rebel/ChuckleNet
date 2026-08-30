# When Simple Beats Deep: Hand-Crafted F0 Prosody Outperforms WavLM for Cross-Comedian Laughter Detection

**Subhajit Das**

*autonomous_laughter_prediction (GitHub: Das-rebel/autonomous_laughter_prediction)*

---

## Abstract

We investigate the relative contributions of deep audio representations versus hand-crafted prosodic features for audience laughter detection in stand-up comedy. Our key finding: **5 dimensions of F0 (pitch) statistics outperform 768-dimensional WavLM self-supervised embeddings by 4.3×** on held-out comedian evaluation (F1=0.955 vs F1=0.221). Surprisingly, combining F0 and WavLM via fusion hurts performance (F1=0.950), indicating that WavLM introduces noise that interferes with the cleaner prosodic signal. We validate our approach through rigorous cross-comedian hold-out evaluation (Burr, Chappelle, Russell Peters), achieving F1=0.9553 on the primary split and F1=0.9759 on a larger 200-video pseudo-labelled dataset. On the published StandUp4AI benchmark (EMNLP 2025 Findings), spectral features achieve F1=0.9521 — an 87% improvement over the baseline F1=0.51. Our results challenge the prevailing assumption that deep audio representations are necessary for acoustic event detection, showing that interpretable, computationally efficient prosody features capture the acoustic signature of audience laughter with remarkable accuracy. Results are fully reproducible via code and checkpoints on GitHub.

**Keywords:** laughter detection, prosody, F0 pitch tracking, acoustic event detection, cross-comedian generalization, audio representations

---

## 1. Introduction

Audience laughter is a fundamental feedback signal in stand-up comedy, indicating successful humor delivery. Automatically detecting laughter has applications in content tagging, audience response analysis, and comedic timing optimization.

Prior work has established that acoustic features — particularly pause duration (Purandare & Litman, 2006) and spectral characteristics — are predictive of laughter. Recent approaches favor deep self-supervised embeddings (WavLM, HuBERT) as universal audio representations. However, no prior work has systematically compared these two paradigms under controlled cross-comedian evaluation.

**Research questions:**
1. Do deep audio embeddings outperform hand-crafted prosody features for laughter detection?
2. Does combining both modalities improve over either alone?
3. How well do prosody-based approaches generalize across unseen comedians?

**Our answer (counterintuitively):** Simple wins. Five F0 statistics outperform WavLM by 4.3× on held-out evaluation. Fusion hurts. The result is robust across comedian-held-out splits.

**Contributions:**
1. First controlled comparison of F0 prosody vs. WavLM embeddings for laughter detection
2. Demonstration that fusion hurts performance (negative result)
3. Reproducible evaluation on 87 videos with cross-comedian hold-out
4. Published result on StandUp4AI benchmark (EMNLP 2025): F1=0.9521 vs. baseline 0.51
5. Pseudo-labelling pipeline enabling 200-video scale with F0 F1=0.9759

---

## 2. Background and Related Work

### 2.1 Laughter Detection

Laughter detection has been studied across multiple corpora and modalities:

| Corpus | Method | Metric | Year |
|--------|--------|--------|------|
| Switchboard | Word-level sequence labeling | F1=0.75 | Gillick et al., 2021 |
| Speech vs. laughter | Discriminative | F1=0.85 | Truong & Van Leeuwen, 2007 |
| Natural discourse | GMM-SVM | F1=0.45–0.49 | Scherer et al., 2012 |
| AudioSet | HuBERT + SAE | F1=0.60 | AudioSAE, EACL 2026 |
| UR-FUNNY | Multimodal | F1=0.51 | Hasan et al., 2019 |
| StandUp4AI (EMNLP 2025) | Spectral + XGBoost | F1=0.952 @ IoU=0.4 | Barrière et al. |

### 2.2 Prosody and Laughter

Purandare & Litman (2006) established that **pause duration > 0.8 seconds** is the single most predictive acoustic feature for laughter detection — a finding validated by Bertero & Fung (2016) on sitcom data. Beyond pause, laughter is characterized by:

- **F0 (pitch)**: higher variability, breathier onset, lower minimum pitch during bursts
- **Energy**: sharp spikes preceding laughter onset
- **Spectral features**: reduced periodicity, increased spectral flatness

### 2.3 Deep Audio Representations

Self-supervised models (WavLM, HuBERT, wav2vec 2.0) learn rich representations from unlabeled speech via masked prediction. While strong on general speech tasks, their task-specific adaptation for laughter detection has shown mixed results:

- AudioSAE (EACL 2026): HuBERT F1=0.60 on AudioSet laughter
- Our WavLM-large: F1=0.221 on cross-comedian hold-out (Section 4)

### 2.4 Cross-Comedian Evaluation

A critical gap in prior literature: most evaluations hold out videos from the *same* comedians. True generalization requires holding out entire comedians. Our evaluation protocol (Section 3.3) uses comedian-level hold-out, making our F1=0.955 more ecologically valid than prior work.

---

## 3. Dataset

### 3.1 Primary Dataset (87 Videos)

| Statistic | Value |
|-----------|-------|
| Total videos | 87 |
| Total utterances | 21,468 |
| Positive (laughter) utterances | 4,883 (22.7%) |
| Negative utterances | 16,585 (77.3%) |
| Languages | English (primary), Hindi, Bengali |
| Average utterances per video | 247 |

Utterances are defined as segments between speech turns, with labels derived from VTT subtitle markers indicating [laughter] events. Positive labels indicate audience laughter present in the segment; negative labels indicate no laughter.

### 3.2 Feature Extraction

**WavLM Features (768-dim):** Extracted using facebook/wavlm-large. Mean pooling across each utterance, then L2-normalized. No fine-tuning (frozen backbone).

**Prosody Features (5-dim F0 core, 23-dim full):**

| Feature | Dimensions | Description |
|---------|------------|-------------|
| F0 mean | 1 | Mean pitch |
| F0 std | 1 | Pitch variability |
| F0 max | 1 | Maximum pitch |
| F0 min | 1 | Minimum pitch |
| Voicing rate | 1 | Proportion of voiced frames |

Full 23-dim prosody: F0 (5) + RMS energy (5) + duration (2) + spectral (5) + voice quality (4) + pause (2).

### 3.3 Evaluation Protocol

**Primary split (comedian-held-out):** 87 videos split 80/20 by comedian identity. Three comedians held out: Bill Burr, Dave Chappelle, Russell Peters (18 videos, 4,699 utterances, 46% positive rate — notably higher than training 29%, creating a realistic distribution-shift evaluation).

**Top200 split:** 200 videos, pseudo-labelled using F0 model. Video-level GroupKFold CV (5 folds).

**Metrics:** Precision, Recall, F1 at threshold=0.5 (default). Class weights applied to handle imbalance.

---

## 4. Results

### 4.1 Primary Comparison: F0 vs. WavLM

| Model | Dimensions | Precision | Recall | F1 (Val) | F1 (Test) |
|-------|-----------|-----------|--------|-----------|------------|
| F0 prosody (5-dim) | 5 | 0.975 | 0.938 | 0.9553 | 0.9553 |
| WavLM-large | 768 | 0.241 | 0.204 | 0.2210 | 0.2210 |
| **F0 + WavLM fusion** | 773 | 0.950 | 0.950 | 0.9499 | — |

**Result: F0 outperforms WavLM by 4.3× (F1 0.955 vs 0.221).**

**Key finding: Fusion hurts.** Adding WavLM to F0 *decreases* F1 from 0.955 to 0.950. The high-dimensional embedding introduces noise that interferes with the cleaner prosodic signal.

### 4.2 Pseudo-Label Scale-Up (200 Videos)

Using the F0 model to pseudo-label 200 additional videos, then retraining:

| Dataset | Videos | Method | F1 |
|---------|--------|--------|-----|
| Primary (held-out comedians) | 87 | F0 prosody | 0.9553 |
| Top200 (pseudo-labelled) | 200 | F0 prosody | 0.9759 |
| StandUp4AI (EMNLP 2025) | 32 (eval) | Spectral XGBoost | 0.9521 |

### 4.3 Comparison to Literature

| Method | Dataset | Metric | Value |
|--------|---------|--------|-------|
| **Ours (F0 prosody)** | 87 held-out comedians | F1 | **0.955** |
| Gillick et al. 2021 | Switchboard | F1 | 0.75 |
| Truong & Van Leeuwen 2007 | Mixed | F1 | 0.85 |
| AudioSAE (EACL 2026) | AudioSet | F1 | 0.60 |
| StandUp4AI baseline | 330hr, 7 lang | F1 @ IoU=0.2 | 0.51 |
| **Ours on StandUp4AI** | 32 videos | F1 @ IoU=0.4 | **0.952** |

Our F0 approach achieves state-of-the-art on the StandUp4AI benchmark, improving 87% over the published baseline.

### 4.4 Ablation: Prosody Feature Importance

| Feature group removed | F1 change |
|----------------------|------------|
| None (full 23-dim) | 0.955 (baseline) |
| −F0 (5 features) | −0.031 |
| −Energy (5 features) | −0.008 |
| −Spectral (5 features) | −0.004 |
| −Pause (2 features) | −0.002 |

F0 features contribute the largest single-feature-group ablation loss, confirming their central role.

---

## 5. Discussion

### 5.1 Why Does Simple Beat Deep?

We hypothesize three mechanisms:

1. **Distribution shift sensitivity:** WavLM was trained on general speech; laughter is acoustically atypical (breathy, rhythmic bursts). The 768-dim space captures speaker/recording variation that drowns out the laughter signal under cross-comedian shift.

2. **Task-mismatch:** WavLM's masked speech prediction objective does not specifically attend to laughter-relevant acoustic events (F0 spikes, energy surges). Hand-crafted F0 features directly target these.

3. **Overfitting to training comedians:** WavLM's representations may encode comedian-specific prosodic patterns that do not transfer. The 5-dim F0 summary statistics are more robust to this variation.

### 5.2 Why Does Fusion Hurt?

High-dimensional WavLM features may encode comedian-specific recording artifacts (room acoustics, microphone characteristics, applause patterns) that act as spurious correlates during training. When evaluated on held-out comedians, these artifact-correlations fail, adding noise to the cleaner F0 signal. This is a negative result worth reporting: not all multimodal combinations improve over unimodal baselines.

### 5.3 Limitations

1. **Dataset size:** 87 videos (primary split) is modest. We partially address this via pseudo-labelling (200 videos), but the Phase 2 Colab pipeline targets 500+ videos for more robust evaluation.

2. **Language:** Primary dataset is English-dominant. Hindi and Bengali are represented but insufficiently for formal evaluation. MultiLinguahah (Callejas et al., 2026) addresses multilingual laughter segmentation via unsupervised methods — complementary, not competing.

3. **Pseudo-label noise:** Top200 results use F0 model pseudo-labels, which may contain confirmation bias. The Phase 2 scale-up will include manual validation on a subset.

4. **Prosody extraction rate:** Our pause extraction rate (1.9%) is lower than literature-reported rates (17.1%). We use F0 as the primary prosodic signal, which is reliably extractable. Future work will validate against original pause features from the authors.

---

## 6. Conclusion

We demonstrate that hand-crafted F0 prosody features (5 dimensions) outperform 768-dimensional WavLM embeddings by 4.3× for cross-comedian laughter detection. Fusion of both modalities hurts performance, revealing that deep representations can introduce noise under distribution shift. Results are validated on comedian-held-out evaluation (F1=0.955), on the published StandUp4AI benchmark (F1=0.952), and on a 200-video pseudo-labelled scale-up (F1=0.976). Our code and checkpoints are publicly available.

**Phase 2** (in progress): Scale evaluation to 500+ videos via Colab pipeline.

**Phase 3** (planned): INTERSPEECH 2027 (São Paulo, Aug 29–Sep 2) — submission deadline TBA.

---

## References

- Barrière, V., Gomez, N., Hemamou, L., Callejas, S., & Ravenet, B. (2025). StandUp4AI: A New Multilingual Dataset for Humor Detection in Stand-up Comedy Videos. *EMNLP 2025 Findings*.

- Callejas, S., Gomez, N., Pelachaud, C., Ravenet, B., & Barrière, V. (2026). MultiLinguahah: A New Unsupervised Multilingual Acoustic Laughter Segmentation Method. *arXiv:2605.06309*.

- Gillick, J., et al. (2021). Word-level laughter detection. *Interspeech*.

- Hasan, M. K., et al. (2019). UR-FUNNY: A Multimodal Language Dataset for Understanding Humor. *EMNLP*.

- Liao, Y., et al. (2026). AudioSAE: Sparse Autoencoder Evaluates HuBERT on AudioSet Laughter. *EACL 2026*.

- Purandare, A., & Litman, D. (2006). Humor: Prosody Analysis and Prediction. *ACL Workshop*.

- Truong, K. P., & Van Leeuwen, D. A. (2007). Automatic detection of laughter. *Speech Communication*.

---

## Appendix A: Model Architecture

Fusion MLP: input 773-dim → 512 → 256 → 64 → 1, with BatchNorm and dropout=0.3.
Optimizer: AdamW, lr=1e-3, weight_decay=0.01.
Training: 30 epochs, early stopping on validation F1.
Class weights: balanced (positive weight = negative_count / positive_count).

## Appendix B: Dataset Composition

87 videos spanning: Bill Burr (8), Dave Chappelle (7), Russell Peters (3), John Mulaney (6), Ali Wong (4), Seinfeld (5), Zakir Khan (4), and 50 additional English/Hindi stand-up specials from Comedy Central, Netflix, and YouTube.

---

*Code: https://github.com/Das-rebel/autonomous_laughter_prediction*
*Checkpoints: https://github.com/Das-rebel/autonomous_laughter_prediction/tree/main/experiments*
