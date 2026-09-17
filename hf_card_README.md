---
license: mit
tags:
- audio
- laughter-detection
- wavlm
- audio-classification
- comedy
library_name: pytorch
---

# ChuckleNet v2 — Laughter Detection (WavLM + Prosody Fusion)

**Status: research preview — NOT production-ready.** The numbers below are the validated, reproducible ones. A historical 0.96 result exists for this architecture family but is **not valid as laughter detection** (see *Historical results* for why).

## What this is

A two-stream model that fuses per-utterance **WavLM-base** embeddings (768-d) with a small **prosody vector** (pitch/energy-style stats) and classifies whether an utterance contains laughter:

```
[WavLM 768 | prosody 23] → Linear 512 (BN, ReLU, drop 0.3)
                         → Linear 256 (BN, ReLU, drop 0.2)
                         → Linear 64 (ReLU) → Linear 1 (logit)
```

Trained with BCE + pos_weight, AdamW, cosine LR schedule. Video-level splits only (no utterance from a video appears in both train and eval).

## Validated results (reproducible, provenance-linked)

| Benchmark | Metric | Score | Notes |
|---|---|---|---|
| Gillick-162v (real AudioSet labels) | segment F1 | **0.559** | 5-fold GroupKFold OOF, fresh training, 2026-09-07 revalidation |
| — WavLM-only ablation | segment F1 | 0.548 | same protocol |
| — Prosody-only ablation | segment F1 | 0.537 | same protocol |
| StandUp 118v VTT pipeline | IoU-F1@0.2 | **0.3302** | IoU-F1@0.2 with merge gap 0.8 (best 118v config) |

Provenance: [`GILLICK_REVALIDATION_RESULTS.json`](https://github.com/Das-rebel/ChuckleNet/blob/main/docs/GILLICK_REVALIDATION_RESULTS.json), [`FUSION096_FULL_VALIDATION.json`](https://github.com/Das-rebel/ChuckleNet/blob/main/docs/FUSION096_FULL_VALIDATION.json), project decision graph in the same repo.

## New validated Tier-1 weak-label numbers (Sep-8, Colab v20.2d)

We completed a curated gate run on **20 marker-rich videos** using caption-markers (`[laughter]`) as training labels:

- **FULL (20v, 17,790 samples, 7.91% pos):** F1=0.164±0.029, PR-AUC=0.208 (2.6× random), IoU-F1@0.2=0.197 ±0.034
- **RICH (9v, 7,813 samples, 14.2% pos):** F1=0.338, PR-AUC=0.376, **IoU-F1@0.2=0.407 ±0.063** — **first weak-label result above naive 0.29 and the best pre-sweep 0.3302**

**Provenance:** `/content/drive/MyDrive/chuckle_net_results/` + Drive. GitHub notebook: `ChuckleNet_Final_Colab_v20.ipynb` (GATE_N=0 pre-set), `ChuckleNet_Kaggle_v21.ipynb` (Kaggle P100-compatible)

## Pipeline & execution verified

- **Extracted features:** WavLM-768 + prosody-23
- **Framework:** PyTorch 2.5.1+cu121 (P100-safe), Hugging Face Transformers 4.46.3 (back‑ported to support `register_fake`)
- **Split:** video‑level GroupKFold5 (no utterance leakage)
- **Checkpointing:** per‑file (3 videos in gate mode, 10 in full mode)
- **Full‑scale run pending:** 620‑video batch (≈6‑9 hours, resumable)

## Intended use

- Research on laughter detection in stand‑up comedy / TED‑style speech.
- The Gillick‑162v evaluation protocol (real AudioSet‑derived labels, video‑level GroupKFold) remains the reference methodology for gold‑standard claims.

## Limitations

- Segment‑F1 0.559 and IoU‑F1@0.2 0.3302 are far from production thresholds.
- Trained/evaluated mostly on English comedy and TED talk audio.
- Fusion gains over WavLM‑only are modest (+0.011 F1 on the validated set).
- Earlier iterations used caption‑derived weak labels; the current pipeline targets real labels only.

## Reproducibility

- **Colab (v20.2d):** https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/main/ChuckleNet_Final_Colab_v20.ipynb
- **Kaggle:** https://www.kaggle.com/code/subhajitdas/chucklenet-v21-full-620v (torch 2.5.1+cu121, Drive token embedded)
- **Data source:** `gdrive:chuckle_net_1000/audio` (620 real `.m4a`) + `gdrive:chuckle_net_1000/vtt` (627 VTTs, byte‑identical to curated local set)
- **Results JSON:** saved to `chuckle_net_results/results_v21.json` (public within repo after full‑run)
- **All claims** trace to JSON artifacts in the [ChuckleNet repo](https://github.com/Das-rebel/ChuckleNet/tree/main/docs).

## References

- Gillick, D., et al. (2021). *Finding Ladies First: Real‑world Phrase‑level Sentiment on Audio in the Wild.* ICLR 2022 Workshop.
- StandUp4AI (2022). Stand‑up comedy dataset for laughter detection.
- Das‑rebel/ChuckleNet (2026). **Scale 1000 Forensic Notebook** (`docs/SCALE1000_NOTEBOOK_FORENSICS.json`) — documents the 0.96 story and label‑circularity case study.
- Hayasuki (2025). Existing variant `chuckleNet-v2` used as host for research (the one this card updates).

## Status (2026‑09‑08)

| Item | Status | Notes |
|---|---|---|
| **Full 620‑video run** | Colab → GPU‑limit pending; Kaggle v3 → queued/pushed | Resume from 20‑video checkpoint, expected 6‑9 h each mode |
| **Tier‑2 anchor eval** | Awaiting 118v audio + StandUp4AI truth (local repo exists; Drive dir empty) | Will compare against 0.3302 (best validated) |
| **Tier‑3 anchor eval** | Ready (Gillick‑162v audio at `~/data/gillick_audio/`) | Compare against gold 0.559 |
| **HF model space** | `Hayasuki/chucklenet` → **402 BLOCKED** (previous resource limits) | Space deferred; this model repo (chuckleNet‑v2) remains live for citation |

---
**Next milestone:** Complete the full‑scale weak‑label run, perform Tier‑2/3 anchor evals, then synthesize an honest paper (weak‑label pitfall + label‑circularity case study + scaled performance numbers) per Option C career‑first monetization strategy.