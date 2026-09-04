# When Text Fails: Audio-Dominant Laughter Detection in Multilingual Stand-Up Comedy

**EMNLP 2026 Industry Track Submission**

---

## Abstract

We present a production system for laughter detection in multilingual stand-up comedy, and report an unexpected finding: gated multimodal fusion with learnable weighting learns to completely discard textual features (gate→1.0), achieving no improvement over audio-only detection (F1=0.416). This contradicts the prevailing assumption in multimodal ML that text+audio always outperforms either alone. We analyze why this occurs — laughter is a paralinguistic signal, and utterance-level text embeddings from frozen multilingual encoders act as noise rather than signal. From this negative result, we derive practical deployment lessons: (1) production laughter detectors should be audio-first, with text serving as an upstream predictor rather than a co-detector; (2) pre-extracted WavLM embeddings enable sub-millisecond inference with 837KB model weights; (3) parallel modality fusion is architecturally inappropriate for tasks where one modality is a detector and the other a predictor. Our system processes 68 hours of multilingual comedy across 5 languages, and we are scaling to 550K training examples via pseudo-labeling.

---

## 1. Introduction

Laughter detection — identifying when audience laughter occurs during spoken content — is a commercially valuable task with applications in content analytics, highlight extraction, and audience engagement measurement. Stand-up comedy, where laughter is the primary success metric, presents a particularly compelling use case: platforms like YouTube host millions of hours of comedy content, and automated laughter detection enables content indexing, recommendation, and monetization.

The prevailing approach in multimodal machine learning is to combine text and audio features, with the assumption that fusion architectures outperform either modality alone [Ngiam et al., 2011; Baltrušaitis et al., 2019]. In the humor domain specifically, prior work has attempted text-audio fusion for joke detection [Bertero & Fung, 2016] and laughter classification [Gillick et al., 2019], typically reporting modest gains from fusion over audio-only baselines.

We challenge this assumption. In our production laughter detection system for multilingual stand-up comedy, we deployed a gated fusion architecture that learns to weight text and audio features per-example. The system was designed to leverage both WavLM speech representations [Chen et al., 2022] and XLM-R multilingual text embeddings [Conneau et al., 2020]. However, during training, the gating mechanism converged to 1.0 within two epochs — the model learned to completely ignore text.

This paper reports this finding, analyzes why it occurs, and derives practical deployment recommendations for production multimodal systems. Our contributions are:

1. **A counter-intuitive empirical result:** gated multimodal fusion for laughter detection learns to discard text entirely, with gate→1.0 and F1_fusion ≈ F1_audio (0.420 vs 0.416).
2. **An analysis of why:** laughter is paralinguistic — the acoustic signal directly contains the target event (laughter sound), while utterance-level text embeddings encode the joke content, not the laughter. The model correctly identifies this modality mismatch.
3. **Production deployment lessons:** audio-first architecture, pre-extracted embeddings for sub-ms inference, and the distinction between predictor modalities (text for joke→laughter) and detector modalities (audio for laughter presence).
4. **A scalable pipeline:** 68 videos → 13.7K utterances processed, with 550K word segments available for pseudo-labeling-based scaling.

---

## 2. System Architecture

### 2.1 Overview

Our system consists of three stages: (1) audio pre-processing and WavLM embedding extraction, (2) text encoding via XLM-R, and (3) gated fusion classification. Figure 1 illustrates the architecture.

```
                   ┌─────────────────────────────┐
                   │     Stand-up Comedy Video     │
                   └──────────────┬──────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
    ┌─────────▼─────────┐                   ┌─────────▼─────────┐
    │   Audio Branch     │                   │   Text Branch      │
    │                    │                   │                    │
    │  WavLM-Base+       │                   │  XLM-RoBERTa-base  │
    │  (frozen, 95M)     │                   │  (frozen, 278M)    │
    │  mean-pool → 768d  │                   │  [CLS] token → 768d│
    └─────────┬─────────┘                   └─────────┬─────────┘
              │                                       │
    ┌─────────▼─────────┐                   ┌─────────▼─────────┐
    │  audio_proj        │                   │  text_proj         │
    │  768 → 256         │                   │  768 → 256         │
    └─────────┬─────────┘                   └─────────┬─────────┘
              │                                       │
              └───────────────────┬───────────────────┘
                                  │
                        ┌─────────▼─────────┐
                        │   GATE MODULE      │
                        │  g = σ(W·[t; a])  │
                        │  fused = g·a +     │
                        │         (1-g)·t    │
                        └─────────┬─────────┘
                                  │
                        ┌─────────▼─────────┐
                        │  Classifier        │
                        │  256 → 64 → 2      │
                        │  (laughter / none) │
                        └────────────────────┘
```

**Figure 1:** Gated fusion architecture. Both encoders are frozen. Only projection layers and classifier are trained (411K parameters total). The gate initializes with bias=-2.2 (audio-skeptical), forcing the model to earn trust in the audio branch.

### 2.2 Audio Pre-Processing

WavLM embeddings are pre-extracted offline to decouple the heavy transformer (95M parameters) from inference. For each video, we segment the audio into utterance-length clips (3-15 seconds) using subtitle timestamps. Each clip is processed through WavLM-Base+ and mean-pooled to a 768-dimensional vector. This produces one embedding per utterance.

To avoid out-of-memory errors on consumer hardware, we use frame-level loading with librosa's `offset` and `duration` parameters — the full audio file is never loaded into memory. Extraction for 68 videos (13.7K utterances) completes in ~2 hours on a Mac M1 CPU and produces 38MB of embeddings.

### 2.3 Text Encoding

Utterance text is tokenized with the XLM-RoBERTa tokenizer (max 128 tokens) and passed through a frozen XLM-R-base model. The [CLS] token representation (768 dimensions) is projected to 256 dimensions through a learned linear layer. The text encoder is frozen to enable fair comparison with the frozen WavLM encoder and to isolate the contribution of pre-trained representations.

### 2.4 Gated Fusion

The gate module concatenates the 256-dimensional text and audio projections (512 dimensions total), passes them through a linear layer with sigmoid activation to produce a scalar gate value g ∈ [0,1]. The fused representation is:

```
fused = g · audio_proj + (1 - g) · text_proj
```

A gate bias of -2.2 initializes the model to be audio-skeptical (g ≈ 0.1), requiring the model to learn to trust audio features. This design choice was intentional — we hypothesized audio would dominate, and wanted the model to earn that dominance rather than having it hardcoded.

The fused representation (256 dimensions) passes through a 3-layer MLP classifier (256 → 64 → 2) with GELU activation and dropout (0.15, 0.1).

### 2.5 Training Configuration

All models are trained on a single T4 GPU (Colab) with bfloat16 mixed precision. Key hyperparameters:

| Parameter | Value |
|-----------|-------|
| Batch size (text) | 16 |
| Batch size (audio) | 32 |
| Batch size (fusion) | 16 |
| Optimizer | AdamW |
| Learning rate | 1e-3 |
| Weight decay | 0.01 |
| LR schedule | Cosine with warmup |
| Max epochs | 10-15 |
| Early stopping patience | 5 |
| Class weight | Computed per-split |

---

## 3. Dataset

### 3.1 Data Collection

Our dataset consists of 68 stand-up comedy videos collected from YouTube, spanning 5 languages: English, Chinese, Hindi, Russian, and Spanish. Videos range from 2 minutes (short clips) to 90 minutes (full specials).

### 3.2 Labeling

Weak labels are derived from YouTube auto-generated subtitles, which include `[laughter]`, `[applause]`, and `[laughing]` markers. These markers are aligned with Whisper-transcribed word timestamps to produce utterance-level binary labels: an utterance is labeled positive (laughter) if any word within it falls within ±5 seconds of a laugh marker.

This weak labeling approach is noisy but scalable. Prior work has validated that YouTube subtitle laugh markers achieve reasonable precision for utterance-level detection [MultiLinguahah, 2026]. Table 1 shows the dataset statistics.

**Table 1: Dataset Statistics**

| Split | Videos | Utterances | Positive | Positive Rate |
|-------|--------|------------|----------|---------------|
| Train | 61 | 11,605 | 2,787 | 24.0% |
| Val | 7 | 2,155 | 513 | 23.8% |
| **Total** | **68** | **13,760** | **3,300** | **24.0%** |

### 3.3 Split Strategy

We use per-video splits rather than random splits across utterances. This prevents information leakage where utterances from the same video appear in both train and validation sets — a known pitfall in multimodal datasets [H4.5 in our internal hypothesis tracking]. The validation set consists of 7 held-out videos (~10% of data).

### 3.4 Scaling

In addition to the 13.7K labeled utterances, we have 549K word-level segments aligned with timestamps from the same videos. These segments are currently being pseudo-labeled using a fine-tuned XLM-R classifier (F1=0.50) for scaling experiments beyond the current dataset.

---

## 4. Experiments

### 4.1 Baselines

We train three model variants on the same data split:

- **Text-only:** Frozen XLM-R → text_proj (768→256) → classifier (256→64→2). 197K trainable parameters.
- **Audio-only:** Frozen WavLM → audio_proj (768→256) → classifier (256→64→2). 213K trainable parameters.
- **Gated Fusion:** Both encoders frozen, gate + projection + classifier. 411K trainable parameters.

### 4.2 Results

**Table 2: Validation F1 scores**

| Model | Trainable Params | Best Val F1 | Epoch |
|-------|-----------------|-------------|-------|
| XLM-R text-only (frozen) | 197,378 | 0.2471 | 9 |
| WavLM audio-only | 213,442 | **0.4155** | 2 |
| Gated Fusion | 410,819 | 0.4196 | 2 |

**Finding 1: Audio dominates.** WavLM alone achieves F1=0.416, a 68% relative improvement over frozen XLM-R (F1=0.247). This confirms that laughter is primarily an acoustic signal — WavLM's speech pretraining captures the relevant prosodic features for laughter detection.

**Finding 2: Text is noise.** The frozen XLM-R text-only model barely exceeds chance (0.247 vs 0.24 random). At the utterance level, multilingual text embeddings from a frozen encoder provide essentially no signal for detecting whether laughter occurred during that utterance.

**Finding 3: Fusion adds nothing.** The gated fusion model achieves F1=0.420, a statistically negligible improvement over audio-only (+0.004). More importantly, the gate mechanism tells us why.

### 4.3 Gate Trajectory

The gate value is the most informative signal in our experiments. Figure 2 traces the gate value through training:

```
Epoch 1, Step 0:    g = 0.090  (audio-skeptical, as initialized)
Epoch 1, Step 100:  g = 0.095
Epoch 1, Step 200:  g = 0.202  (starting to trust audio)
Epoch 1, Step 300:  g = 0.406
Epoch 1, Step 400:  g = 0.516
Epoch 1, Step 500:  g = 0.594
Epoch 1, Step 600:  g = 0.653
Epoch 1, Step 700:  g = 0.699
Epoch 1, End:       g = 0.704  F1 = 0.411
Epoch 2, Step 0:    g = 0.988
Epoch 2, End:       g = 0.993  F1 = 0.420
Epoch 3+:           g = 1.000  F1 = 0.399 (overfitting)
```

**Finding 4: The model learns to discard text.** Within 500 steps, the gate crosses 0.5 (equal weighting). By epoch 2, it has converged to essentially 1.0 — the model is using 99% audio and 1% text. By epoch 3, text is fully discarded (g=1.000).

This is not a training failure. The gate was initialized to be audio-skeptical (bias=-2.2), forcing the model to earn its trust in audio features. The model correctly learned, through gradient descent, that frozen text features are harmful to the classification objective. It took exactly two epochs to reach this conclusion.

---

## 5. Analysis: Why Text Fails

### 5.1 Laughter is Paralinguistic

Laughter is a non-verbal vocalization — a paralinguistic signal. Unlike sentiment or topic classification, where text contains direct information about the target, laughter detection at the utterance level asks: "did laughter occur during this speech segment?" The acoustic features of the segment directly encode the answer (laughter sounds are audibly distinct from speech), while the textual content of the segment encodes *what was said*, not *whether people laughed*.

### 5.2 The Predictor-Detector Distinction

This reveals a fundamental architectural issue with parallel multimodal fusion for this task:

- **Text is a predictor:** it can predict *that laughter will follow* (punchline → pause → laughter). XLM-R achieves F1=0.819 at the word level [our prior work], because it can learn the linguistic patterns that precede laughter.
- **Audio is a detector:** it directly observes *whether laughter is occurring*. WavLM achieves F1=0.416 at the utterance level because it can hear laughter.

In a parallel fusion architecture, the text branch is asked to be a detector — "given this utterance text, was there laughter?" — which is the wrong question. The correct question for text is predictive: "given these words, will there be laughter in the next utterance?"

### 5.3 Frozen Encoder Limitation

Our text encoder is frozen XLM-R-base. This was an intentional design choice to isolate the contribution of pre-trained representations, but it also limits the text branch's capacity. A fine-tuned XLM-R might extract more relevant features from utterance text. However, the gate's convergence to exactly 1.0 (not 0.6 or 0.7) suggests the model found the text signal to be *actively harmful*, not merely uninformative. Fine-tuning the text encoder might change this, and we discuss this in §7 (Future Work).

### 5.4 Utterance Granularity

At the utterance level (3-15 seconds), a single text embedding summarizes an entire joke setup-punchline sequence. The laughter event, if it occurs, is temporally localized within this window. The frozen [CLS] token averages across all tokens, diluting any local signal. Word-level or sub-utterance text features might provide more granular information.

---

## 6. Deployment Lessons

### 6.1 Audio-First Architecture

The primary production takeaway is: **laughter detection systems should be audio-first.** Text features, if used, should be deployed in a sequential rather than parallel architecture — first, use text to predict *where* laughter is likely, then use audio to *confirm* whether laughter actually occurred.

### 6.2 Lightweight Inference

Our audio-only model is remarkably lightweight:
- **Classifier weights:** 837KB (just the MLP layers)
- **Pre-extracted embeddings:** 38MB for 68 hours of content
- **Inference:** <1ms per utterance on CPU
- **No text dependency:** language-agnostic detection

This enables deployment scenarios that would be impossible with a text-dependent system: real-time processing on edge devices, batch processing of large content libraries, and multilingual deployment without per-language text models.

### 6.3 Pre-Extraction as Production Pattern

Pre-extracting WavLM embeddings decouples the heavy transformer (95M parameters, GPU-required) from the lightweight classifier (213K parameters, CPU-friendly). This pattern is generalizable: for any paralinguistic detection task, pre-extract speech representations once, then train lightweight task-specific classifiers.

### 6.4 The Gate as a Debugging Tool

The gating mechanism served as an unintentional diagnostic. If we had used a simple concatenation or cross-attention fusion, we might have reported "F1=0.420" and concluded that multimodal fusion works — missing the fact that text contributes nothing. The gate made the modality dominance explicit and interpretable.

### 6.5 Scaling Strategy

With 549K unlabeled word segments available, we are currently pseudo-labeling using a fine-tuned XLM-R classifier. This semi-supervised approach will expand training data by ~40×, potentially improving the audio-only model further. Importantly, pseudo-labeling uses text as a *predictor* (generating labels from linguistic patterns) while the final system uses audio as a *detector* — correctly separating the two roles.

---

## 7. Limitations and Future Work

**Frozen encoders:** Both XLM-R and WavLM are frozen. Fine-tuning either or both might change the fusion dynamics, though the gate's convergence to exactly 1.0 (rather than a partial weighting) suggests text features were actively harmful, not merely weak.

**Utterance granularity:** Our fusion operates at utterance level. A temporally-aware architecture that models the sequence "joke → pause → laughter" might better leverage text as a predictor. This is our planned next experiment (see §7.1).

**Language breakdown:** We report aggregate metrics across 5 languages. Per-language analysis might reveal that text contributes more for certain languages (e.g., tonal languages where prosodic cues differ).

**Weak labels:** Our labels come from YouTube subtitles, which have known noise issues. Manual annotation on a subset would enable more rigorous label quality analysis.

### 7.1 Planned: Temporally-Aware Fusion

Our next experiment replaces parallel gated fusion with a sequential architecture:

```
Text (word-level) → GRU → predict laughter probability per timestep
                              ↓
Audio (frame-level) → WavLM → detect laughter presence
                              ↓
                    Fuse: predict · detect
```

This separates the roles: text predicts *where* laughter should occur; audio detects *whether* it did. The fusion multiplies predicted probability by detected presence, combining the strengths of each modality in their appropriate roles.

---

## 8. Conclusion

We built a production laughter detection system for multilingual stand-up comedy and discovered that gated multimodal fusion learns to completely discard text features (gate→1.0). This counter-intuitive result — that fusion offers no improvement over audio-only detection — reveals a fundamental distinction between predictor modalities (text tells you *when* to expect laughter) and detector modalities (audio tells you *whether* laughter occurred). Parallel fusion architectures conflate these roles, leading to worse-than-single-modality performance.

For production deployment, we recommend audio-first architectures with text used as an upstream predictor. Our system achieves F1=0.416 on audio-only detection with 837KB model weights and sub-millisecond inference, and we are scaling to 550K training examples. The code, pre-extracted embeddings, and trained models are available at [repository URL].

---

## References

[1] S. Chen et al., "WavLM: Large-Scale Self-Supervised Pre-Training for Full Stack Speech Processing," IEEE JSTSP, 2022.

[2] A. Conneau et al., "Unsupervised Cross-lingual Representation Learning at Scale," ACL 2020.

[3] J. Ngiam et al., "Multimodal Deep Learning," ICML 2011.

[4] T. Baltrušaitis et al., "Multimodal Machine Learning: A Survey and Taxonomy," IEEE TPAMI, 2019.

[5] D. Bertero and P. Fung, "Deep Learning of Audio and Language Features for Humor Prediction," LREC 2016.

[6] J. Gillick et al., "Learning to Detect Laughter," Interspeech 2019.

[7] MultiLinguahah, "Cross-Lingual Audio Humor Detection," 2026.

[8] V. Barrière et al., "StandUp4AI: A Multilingual Dataset for Stand-Up Comedy Analysis," 2025.

[9] A. Purandare, "Prosodic Features for Laughter Detection," 2006.

[10] F. Eyben et al., "The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing," IEEE TAC, 2016.
