# PICLI_EXECUTION_MANDATE — V6

> **2026-09-18 SUPERSESSION NOTICE:** This file’s execution status is stale. Strategic control remains Mandate V4; current execution status is `PICLI_EXECUTION_MANDATE_V7.md` / `docs/PICLI_EXECUTION_MANDATE_V7.md`. v30e is complete but is only a P0 reproducibility artifact; v32 remains flagship.


**Date:** 2026-09-16  
**Status:** ACTIVE — v27 running on Kaggle, Modal blocked (payment required for T4 GPU)

## Active Execution

- **v27 Kaggle kernel** (ID: 134616761): WavLM fine-tuning, 620 videos, 5.5h limit
  - Key fix: early heartbeat prints every 30s to detect kernel startup stalls
  - WavLM via HuggingFace (same approach as v24, but now with Cell 1 disk/path check and explicit timing)
  - Dataset: chuckle-vtt-labels + chuckle-audio-620-videos
  - v26 deleted: ran 65+ min with 0 log output (HF download stall?)

## Resource Status

| Resource | Status | Notes |
|----------|--------|-------|
| Kaggle GPU (T4) | ✅ AVAILABLE | v27 running |
| Modal T4 GPU | ❌ BLOCKED | Payment method required |
| HuggingFace | ✅ AVAILABLE | WavLM downloads via HF |
| GitHub | ✅ AVAILABLE | Mandate + audit docs updated |

## Recent History

| Version | Outcome | Issue |
|---------|---------|-------|
| v19 | 40v subset, f1=0.02 | Only 4 val positives |
| v24 | 80/620 videos, cancelled | External cancellation at 15min |
| v25 | OSError: No space left | 122K per-segment .npz files exhausted disk |
| v26 | DELETED (65+ min, 0 logs) | HF download stall / kernel queue |
| v27 | RUNNING | Early heartbeat + explicit HF timing |

## Critical Findings (from audit)

1. **v32 IoU-F1@0.2 discrepancy**: 0.229 (claimed) vs 0.197 (in FULL 620v run) — likely RICH subset (pos≥6%) not FULL
2. **Val positive count**: Full run needed for meaningful evaluation (v19: only 4 positives in 40v)
3. **Class imbalance**: 1.16% positive rate — BCEWithLogitsLoss pos_weight or focal loss may be needed

## Next Steps (Priority Order)

1. **Monitor v27** — expect first log output within 5-10 min
2. **If v27 fails with HF download**: Upload WavLM safetensors to Kaggle dataset, load locally
3. **If v27 succeeds**: Extract metrics, update evidence audit, design P1 temporal study
4. **Modal T4 GPU**: User needs to add payment method at modal.com → Settings → Billing

## P0 Evidence Status

See `CURRENT_EVIDENCE_AUDIT_2026-09-16.md` in both repos for full 6-anchor status.

---
*Mandate V6 — generated automatically*
