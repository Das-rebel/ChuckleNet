# Gate Forensics — 620v set (Sep 8, 2026)
**Trigger:** first v20 gate run hard-failed at 0.7% pos (32/4455) — the guard worked.
**Findings (full620_marker_stats.json = per-video parse of all 620):**
- Full set: 243,501 parsed utts, 2,816 marker-positive = **1.16%** pos_rate
- Only **174/620** videos carry ANY laughter markers; 23 have ≥20 positives; only ~10 videos reach ≥10% pos_rate
- Drive VTTs **byte-identical** to curated local label set (~/data/chuckle_vtt_labels) → labels genuine; collection is marker-poor by nature
- YouTube auto-caption VTTs duplicate every cue → parsed counts ~50% inflated → v20.2 dedups + OR-merges flags
**Decision (D-GATE-V202):** 3-tier gate (FAIL<2% / WARN 2–10% proceed / PASS≥10%); curated marker-rich GATE_IDS for gate mode; dual training FULL + RICH subset (pos_pct≥6% & pos≥10); PR-AUC added; checkpoint ns → *_v21.
