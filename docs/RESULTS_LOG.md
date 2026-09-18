# ChuckleNet — RESULTS LOG (single scoreboard)

> Every reported number lands here. Order = chronological. Label tier per docs/LABEL_HIERARCHY.md.
> **Anchor rule:** Tier-1 numbers are "caption-marker detection" — no gold claims without Tier-2/3 anchor evals.

| # | Date | Data | Labels | Model | Metric | Value | Status | Evidence |
|---|------|------|--------|-------|--------|-------|--------|----------|
| 1 | Jul–Aug 2026 | 87v pipeline | T0 humor-lexicon (RETIRED) | F0 / XLM-R cascade / FusionMLP | seg F1 | "0.94–0.98" | ❌ DISQUALIFIED — label circularity (labels ≈ deterministic fn of prosody; 100% provenance proven) | docs/SCALE1000_NOTEBOOK_FORENSICS.json, FUSION096_FULL_VALIDATION.json |
| 2 | Sep 2026 | Gillick-162v | T3 gold | FusionMLP 795d | seg F1 (video-level split) | **0.5590** | ✅ honest gold anchor | docs/GILLICK_REVALIDATION_RESULTS.json |
| 3 | Aug–Sep 2026 | 118v benchmark | T2 StandUp4AI | FusionMLP, IoU-F1@0.2 merge 0.8 | IoU-F1@0.2 | **0.3302** (naive 0.29) | ✅ honest benchmark anchor | docs/BEST_118V_RESULTS.md |
| 4 | — | StandUp4AI paper | T2 | theirs | IoU-F1 | 0.51 | external baseline | paper |
| 5 | **Sep 8** | **GATE: 20 curated v** | **T1 VTT markers** | FusionMLP 795d, GroupKFold5 | PR-AUC | 0.208 ± 0.082 (2.6× random 0.079) | ✅ weak-label gate, FULL | results/RESULTS_V21_GATE_20CURATED.json |
| 6 | **Sep 8** | same FULL | T1 | same | IoU-F1@0.2 | 0.197 ± 0.034 | ✅ below naive | same |
| 7 | **Sep 8** | **GATE: 9 RICH v** | **T1** | same | **IoU-F1@0.2** | **0.407 ± 0.063** | ✅ **first weak-label > naive AND > 0.3302** — ⚠️ NOT comparable (9 marker-selected videos; anchor pending) | same |
| 8 | **Sep 18** | **FULL: 620 v** | **T1 VTT markers** | WavLM-base (frozen) → ChuckleNet v30e MLP 768–256–128–1; 80/20 video split on valid features | seg F1 / AP | **0.2444 @ 0.75** / **0.1642** (val 15,478; 164 pos) | ✅ independent full-scale e2e repeat under 900 s decode window; weak-label baseline | Kaggle `chuckle-e2e-v30e` run 134760029; private HF repo `Hayasuki/chucklenet-v30e`; local `releases/v30e/` |
| 9 | **Sep 18** | same FULL | same | same | **IoU-F1 @ 0.1–0.5** | **0.1743** (P 0.2603, R 0.1310; TP/FP/FN 38/108/252) | ✅ full-scale event baseline under 900 s decode window — not directly comparable to v32 full-feature protocol | same |
| 10 | **Sep 18** | **118v human labels** | **Tier-1 EMNLP B/I/L** | BiGRU paired protocol; 3 seeds × 5 video folds; true/random/local/reverse | paired ΔF1 true−random | **+0.0769**, clustered 95% CI **[+0.0617,+0.0917]** | ✅ P1 primary gate PASS; sequence context matters | `results/p1/p1_temporal_118v_results.json` |
| 11 | **Sep 18** | same | same | same | paired ΔF1 true−local / true−reverse | **−0.0061** [−0.0170,+0.0044] / **+0.0071** [−0.0032,+0.0180] | ⚠️ secondary controls FAIL — fine local order/direction not supported | same |
| 12 | **Sep 18** | 118v (6,211 word-span windows, 44.5% pos) | Tier-1 EMNLP B/I/L | TF-IDF word content vs +7 timing features; MLP; 5 folds × 3 seeds | paired ΔF1 (timing minus words) | **+0.0018** [−0.0046,+0.0080] | ❌ P2 concurrent gate FAIL — timing adds nothing over words at current-window level; redirect to prospective Level A | `results/p2/p2_beyond_words_results.json` |
| 13 | **Sep 18** | 118v, target = laugh in window t+1 from context ≤ t | Tier-1 EMNLP B/I/L | 5 arms (position/words/words+timing/acoustic/acoustic+words); frozen WavLM context; 5 folds × 3 seeds | paired ΔF1 acoustic+words − words | **+0.1117** [+0.0857,+0.1390]; acoustic alone **+0.1074** [+0.0766,+0.1398]; timing null | ✅ **P2 Level A BEYOND-WORDS PROSPECTIVE SUPPORTED** (H3/H4-prospective); caveat: possible early-onset bleed across 5 s boundary; gate sign bug in first readout corrected from saved observations | `results/p2_level_a/p2_level_a_results.json` |
| 14 | **Sep 18** | same 118v, onset-margin stratification | Tier-1 EMNLP B/I/L | retrained Level A arms w/ per-window preds; strata by earliest laugh onset vs context boundary | hit-rate delta (acou+words − words) per stratum | straddle +0.271 · early +0.233 · mid +0.245 · **late (≥2.5s) +0.222 [0.172,0.275]** | ✅ **GENUINE ANTICIPATION — effect NOT onset bleed**; acoustic hits 80% on late positives vs 53% words; claim upgraded to 5 s-horizon reaction anticipation | `results/p2_level_a/p2_levela_onset_margin_results.json` |

## Gate insights (Sep 8)
- Label-noise hypothesis CONFIRMED: RICH-vs-FULL doubles every metric; precision flat (0.447→0.431), recall doubled (0.147→0.296).
- FULL fold-5 anomaly (PR-AUC 0.067 < random 0.079): 4-video folds too small → 620v run fixes fold variance.
- Full-set forensics: pos 1.16% (2,816/243,501), markers in 174/620 videos → FAIL line set to 0.5% (D-GATE-FAIL05).

## Pending
- [x] **Full 620v run** — completed Sep 18 as v30e: 620/620 feature extraction, 0 skips, ~122K indexed / 1,965 weak positives; best val F1 0.2444, AP 0.1642, IoU-F1@0.2 0.1743.
- [x] **P1 paired temporal validation** — completed Sep 18 on 118v human labels. Primary true-vs-random gate passed (+0.0769 F1, CI [+0.0617,+0.0917]); local-shuffle/reverse controls did not separate. Verdict **PARTIAL**: broad sequence context supported, fine local order/direction not supported.
- [ ] **Tier-2 anchor eval**: evaluate v30e and/or the stronger v21 feature pipeline on 118v StandUp4AI-truth set → compare vs 0.3302.
- [ ] **Tier-3 anchor eval**: Gillick-162v → compare vs 0.559.
- [ ] Then: honest paper (weak-label pitfall + label-circularity case study + scaled weak-label numbers).
