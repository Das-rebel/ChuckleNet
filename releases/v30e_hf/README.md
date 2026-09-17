---
license: mit
tags:
- laughter-detection
- wavlm
- weak-labels
- audio-classification
- comedy
- chucklenet
library_name: transformers
pipeline_tag: audio-classification
---

# ChuckleNet v30e — Full 620-video weak-label laughter head

**Research artifact, not production-ready.** This is an independent completed full-scale 620-video run of the WavLM → lightweight head pipeline under a 900 s per-video decode window. The established flagship remains `Hayasuki/chucklenet-laughter-detector` / v32, which uses the fuller 121,928-segment protocol and has post-hoc forensics. This repository is for reproducibility and as a restricted-protocol baseline, not as a deployable laughter detector.

## Input contract

This checkpoint expects a **mean-pooled WavLM-base last-hidden-state embedding** with shape `[batch, 768]`. It does **not** process raw audio by itself.

Pipeline:

```text
16 kHz mono audio → WavLM-base → segment representation → mean-pool [768]
                  → ChuckleNetDetector → laughter logit → sigmoid → probability
```

At inference, probabilities `>= 0.75` were selected as laughter on the held-out split.

## Results

Independent full Kaggle T4 repeat on the 620-video chuckle corpus, restricted to feature-backed IDs after a 900 s audio decode window:

- Videos processed: **620 / 620** (0 skipped)
- Total VTT-derived segments indexed: **121,928**
- Positive laughter labels in full index: **1,965**
- 80/20 video-group split over valid/saved segments only
- Validation samples evaluated: **15,478**
- Validation positives: **164**
- Best epoch: **10 / 15**
- Validation frame/segment F1: **0.2444**
- Best threshold: **0.75**
- Average precision: **0.1642**
- Event-level IoU-F1 @ 0.1 / 0.2 / 0.3 / 0.5: **0.1743**
  - Precision: **0.2603**
  - Recall: **0.1310**
  - TP / FP / FN: **38 / 108 / 252**

These results are honest weak-label numbers. The earlier historical 0.96-family claim is not treated as valid laughter-detection evidence and is unrelated to this checkpoint.

## Relation to the v32 flagship

| Run | Validation protocol | F1 | AP | IoU-F1@0.2 |
|---|---|---:|---:|---:|
| **v32 flagship** (`chucklenet-laughter-detector`) | fuller 121,928-segment protocol; post-hoc forensics | 0.2732 | 0.142 | **0.2290** |
| **v30e** (this model) | valid feature-backed IDs after 900 s decode window; 15,478 val / 164 pos | **0.2444** | **0.1642** | 0.1743 |

These rows are **not directly interchangeable** because v30e excludes segments beyond the decoded window. v32 should be cited as the flagship weak-label result; v30e is the packaged independent repeat.

## Training setup

- Backbone: frozen `subhajitdas/wavlm-base-mirror`
- Head: `768 → 256 → 128 → 1`, ReLU + dropout
- Loss: BCEWithLogitsLoss
- Negative:positive sampling ratio during training: **3:1**
- Optimizer: AdamW, cosine LR schedule
- Epochs: **15**
- Split: video-level group split, no video overlap between train/validation
- Labels: VTT `[laughter]` markers, i.e. weak labels
- Segment decode cap: **900 s per video audio window**
- Feature extraction: **620 / 620 processed, 0 skipped**, in 2,789 s on Kaggle T4
- Training runtime: under 10 s for all 15 epochs after feature caching

## Usage

```python
import torch
from transformers import AutoConfig, AutoModelForAudioClassification

repo = "Hayasuki/chucklenet-v30e"
model = AutoModelForAudioClassification.from_pretrained(repo, trust_remote_code=True)

# x: [batch, 768] mean-pooled WavLM-base embedding
x = torch.randn(2, 768)
logits = model(wavlm_embedding=x)
probs = torch.sigmoid(logits)
preds = (probs >= model.config.threshold).long()
```

To build embeddings, extract WavLM-base last-hidden-state outputs and mean-pool over the valid time dimension for each candidate utterance.

## Files

- `model.safetensors` — ChuckleNet v30e head checkpoint
- `config.json` — architecture and threshold metadata
- `modeling_chucklenet.py` — custom transformers module
- `results_e2e.json` — primary metrics
- `training_history.json` — per-epoch validation metrics
- `val_predictions.npz` — held-out predictions, labels, video IDs, and utterance indices

## Limitations

- Weak labels derived from caption `[laughter]` markers contain noise.
- The model consumes precomputed WavLM embeddings, not raw waveform.
- Performance is far below production thresholds.
- Validation contains only 164 positives, so confidence intervals are broad.
- Training/eval material is mainly English public speaking/comedy-style audio.
- Event IoU is unchanged across 0.1–0.5 because predicted/ground-truth segment overlaps are sparse.
- Do not use this checkpoint as evidence that laughter detection is solved, and do not deploy it in user-facing moderation or accessibility systems without substantially stronger labeled validation.

## Provenance

- Kaggle kernel: `subhajitdas/chuckle-e2e-v30e`
- Kaggle run ID: `134760029`
- Status: `COMPLETE`
- Training history and predictions are included in this repository.
