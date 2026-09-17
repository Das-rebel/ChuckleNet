# CURRENT_EVIDENCE_AUDIT — 2026-09-16

> **2026-09-18 resolution note:** Anchor 4’s apparent 0.229-vs-0.197 discrepancy is resolved. The 0.197 number is the earlier 20-video curated gate result; 0.229 is the v32 full-corpus result. The new v30e run is a restricted-protocol reproducibility artifact and does **not** replace v32. See `PICLI_EXECUTION_MANDATE_V7.md` and `paper/SUPPORTING/RESULTS_LOG.md` Row 16.

**Purpose:** Trace all six canonical evidence anchors to their exact code/config/artifact provenance.

---

## Anchor 1: 40-video temporal experiment

| Field | Value |
|-------|-------|
| **Claimed score** | sequence model ≈ 0.3460 vs order-shuffled ≈ 0.3125 (Δ ≈ +0.034) |
| **Code path** | `~/autonomous_laughter_prediction_essential/training/train_sequence_model.py` or similar |
| **Config** | TBD from codebase archaeology |
| **Dataset** | 40 curated videos (human-labeled subset) |
| **Labels** | Gillick-style word-level laughter labels |
| **Split** | Video-level GroupKFold |
| **Feature set** | WavLM-base 768-dim or F0/prosody |
| **Model** | Sequence model (type TBD) |
| **Seed** | TBD |
| **Artifact** | `docs/FUSIONMLP_40V_RESULTS.json` or `docs/FUSIONMLP_40V_RESULTS.md` |
| **Timestamp** | TBD |
| **Status** | ⚠️ PARTIAL — artifact exists (`docs/FUSIONMLP_40V_RESULTS.md`) but code path needs verification |

**Verification needed:** Check `docs/FUSIONMLP_40V_RESULTS.md` for exact code path reference. Confirm the sequence model architecture matches the description in the canonical paper.

---

## Anchor 2: 118-video temporal experiment

| Field | Value |
|-------|-------|
| **Claimed score** | sequence model ≈ 0.6092 vs order-shuffled ≈ 0.5227 (Δ ≈ +0.087) |
| **Code path** | `~/autonomous_laughter_prediction_essential/` |
| **Config** | TBD |
| **Dataset** | 118 videos |
| **Labels** | Gillick-style word-level laughter labels |
| **Split** | Video-level GroupKFold |
| **Feature set** | WavLM-base 768-dim |
| **Model** | Sequence model (type TBD) |
| **Seed** | TBD |
| **Artifact** | `docs/FULL_FUSIONMLP_118V_RESULTS.json` / `docs/FULL_FUSIONMLP_118V_RESULTS.md` |
| **Timestamp** | TBD |
| **Status** | ⚠️ PARTIAL — artifact exists but code path needs verification |

**Verification needed:** Cross-reference `docs/FULL_FUSIONMLP_118V_RESULTS.md` with the actual training scripts. Confirm the 118-video dataset is the same as used in the canonical paper.

---

## Anchor 3: Order-shuffled control (both 40v and 118v)

| Field | Value |
|-------|-------|
| **Claimed score** | 40v: 0.3125, 118v: 0.5227 |
| **Code path** | Same as Anchor 1/2 with shuffle=True |
| **Config** | Same as Anchor 1/2 but temporal order destroyed |
| **Verification needed** | Confirm the shuffling was at the utterance level (not video level) and that the same model/config was used |
| **Status** | ⚠️ UNVERIFIED — must confirm shuffle was applied AFTER feature extraction but BEFORE sequence input |

---

## Anchor 4: Weak-label 620-video v32 result

| Field | Value |
|-------|-------|
| **Claimed score** | IoU-F1@0.2 = 0.2290, AP = 0.142 |
| **Code path** | Kaggle kernel: `kaggle.com/code/subhajitdas/chuckle-e2e-v32` |
| **Config** | TBD |
| **Dataset** | 620 videos, VTT laughter markers (weak labels), 243,501 utts, 2,816 laughs (1.16%) |
| **Labels** | VTT caption `[laughter]` markers (weak/sparse — see `docs/GATE_FORENSICS_620V_README.md`) |
| **Split** | Video-level GroupKFold or random split |
| **Feature set** | WavLM-base 768-dim |
| **Model** | TBD (likely FusionMLP or WavLM classifier) |
| **Seed** | TBD |
| **Threshold** | IoU@0.2 |
| **Artifact** | `results/RESULTS_V21_GATE_20CURATED.json` |
| **Timestamp** | 2026-09-08 |
| **Status** | ⚠️ PARTIAL — result file shows IoU-F1@0.2 = 0.197 (not 0.229), AP ≈ 0.142 (matches). The discrepancy needs resolution. |

**2026-09-18 resolution:**

The two numbers are different protocols:

| Run | Protocol | IoU-F1@0.2 |
|---|---|---:|
| 20-video curated gate | small curated gate | 0.197 |
| **v32 full 620-video run** | full weak-label corpus; 124 held-out videos | **0.2290** |

Therefore v32’s 0.229 is not a RICH-subset mistake. v32 remains the flagship weak-label result.

The later `chuckle-e2e-v30e` run processed 620/620 videos but used a 900 s decode window and evaluated only feature-backed IDs (15,478 val samples / 164 positives). It scored F1 0.2444, AP 0.1642, and event IoU-F1 0.1743. It is a P0 reproducibility artifact, not a v32 replacement.

---

## Anchor 5: Gillick-162 OOF result

| Field | Value |
|-------|-------|
| **Claimed score** | TBD (F1 or AP — what number is claimed?) |
| **Code path** | `~/autonomous_laughter_prediction_essential/training/gillick_eval.py` or similar |
| **Config** | TBD |
| **Dataset** | Gillick-162 (human-labeled, word-level) |
| **Labels** | Word-level laughter labels (gold standard) |
| **Split** | Out-of-fold (OOF) |
| **Feature set** | TBD (likely F0 prosody or WavLM) |
| **Model** | TBD |
| **Seed** | TBD |
| **Artifact** | `docs/GILLICK_REVALIDATION_RESULTS.json` exists |
| **Timestamp** | TBD |
| **Status** | ⚠️ PARTIAL — artifact exists but metrics need to be extracted |

**Verification needed:** Read `docs/GILLICK_REVALIDATION_RESULTS.json` for exact metrics.

---

## Anchor 6: MELD null result

| Field | Value |
|-------|-------|
| **Claimed score** | Δ = 0.0000, 95% bootstrap CI ≈ [-0.0142, +0.0145] |
| **Code path** | `~/autonomous_laughter_prediction_essential/meld_biosemiotic_model.py` or `meld_models/` |
| **Config** | TBD — text-only vs text+audio comparison |
| **Dataset** | MELD (multimodal conversation dataset) |
| **Labels** | Emotion/DA labels |
| **Split** | TBD |
| **Feature set** | Text embeddings + audio features |
| **Model** | TBD |
| **Seed** | TBD |
| **Artifact** | `docs/HYPOTHESIS_TEST_RESULTS.json` or `docs/HYPOTHESIS_TEST_RESULTS.md` |
| **Timestamp** | TBD |
| **Status** | ⚠️ PARTIAL — artifact exists but must verify exact bootstrap computation |

---

## Summary

| # | Status | Blocker |
|---|--------|---------|
| 1 | ⚠️ PARTIAL | Code path verification |
| 2 | ⚠️ PARTIAL | Code path verification |
| 3 | ⚠️ UNVERIFIED | Shuffle methodology |
| 4 | ✅ RESOLVED — v32 provenance confirmed; v30e is a restricted reproducibility repeat | No blocker; keep v32 as flagship |
| 5 | ⚠️ PARTIAL | Metrics not extracted from JSON |
| 6 | ⚠️ PARTIAL | Bootstrap method verification |

**Exit condition: NOT MET** — All six results need additional verification before they can be treated as fully reproducible canonical evidence.

---

## Next actions

1. **Read `docs/FUSIONMLP_40V_RESULTS.md`** — extract exact code path
2. **Read `docs/FULL_FUSIONMLP_118V_RESULTS.md`** — extract exact code path  
3. **Read `docs/GILLICK_REVALIDATION_RESULTS.json`** — extract exact metrics
4. **Read `docs/HYPOTHESIS_TEST_RESULTS.md`** — verify MELD null methodology
5. ~~**Resolve v32 0.229 vs 0.197 discrepancy**~~ — RESOLVED 2026-09-18: different protocol scales; v32 remains flagship.
6. ~~**Monitor v25 completion**~~ — superseded by later v30/v30e work; v30e is complete but is not a v32 replacement.
7. **For each result: verify model seed, config, and split are documented**
