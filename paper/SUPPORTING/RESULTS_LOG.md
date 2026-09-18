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
| 8 | **Sep 11** | **FULL 620v VTT** | **T1 VTT markers** | WavLM-768 meanpool → MLP, utterance-level, GroupShuffle 80/20 | utter F1 / AP | 0.2732 @ thr 0.85 / 0.142 | ✅ FIRST full-corpus E2E (kernel v32) | results_v32.json (Kaggle + /tmp/v32_output/) |
| 9 | **Sep 11** | same (124 val v) | **T1** | same | **IoU-F1@0.2** | **0.2290** (P=0.281 R=0.193; TP=56/290) | ✅ full-corpus weak-label baseline; consistent w/ row 6 gate 0.197±0.034 | same |
| 10 | **Sep 12** | **v32 saved features** (CPU posthoc) | **T1** | logreg + MLP on saved 768d | forensics | NO duration/norm shortcut (dur-only F1=0.02; ρ(dur,pred)=−0.02; norm-only F1=0.03); truncation cost MILD (2–4s F1=0.202 vs <1s 0.249); corr(gtRate,predRate)=0.361; H1-lite ✓ (gap>1s preds 0.255 vs 0.188) | ✅ **v33 truncation fix NOT justified; no shortcuts; AP replication 0.140≈0.142** | results_v32_posthoc.json |
| 11 | **Sep 12** | **E02 scale221 40v TRUE labels** | **word-level EMNLP** | 5-fold GroupKFold: A MLP-791 / B +temporal-6 / C BiGRU / C-shuf | word F1@0.5 | **A 0.2231±0.021 · B 0.2984±0.048 · C 0.3460±0.046 · C-shuf 0.3125±0.026** | ✅ **GATE 3: temporal signal REAL** (all 5 council checks pass; C>C-shuf +0.034 ⇒ order carries info) | results_e02_temporal.json |
| 12 | **Sep 12** | same E02 | same | same arms | **IoU-F1@0.2** | **A 0.247 · B 0.326 · C 0.3987 · C-shuf 0.358** | ⚠️ falsifier (IoU>0.40) NOT quite triggered — C at 0.3987, a hair below ⇒ v32 weak-label gap largely label-noise + temporal; near-absolution | same |
| 13 | **Sep 12** | **E02@118v Tier-2** (scale221 embeddings ∩ EMNLP labels = 118v, 11,161 windows — matches hist count exactly) | **true-label 5s-window** | same 4 arms, 5-fold GroupKFold, pos_weight 2.0, batch 256 | window F1@0.5 | **A 0.5884±0.031 (reproduces hist 0.678 band ✓) · B 0.5785 (degenerate: pause feats constant on fixed grid — expected) · C 0.6092±0.026 · C-shuf 0.5227±0.011** | ✅ **SEQUENCE EFFECT REPLICATES AT TIER-2 SCALE: C>C-shuf +0.087 (bigger than 40v's +0.034)**; same 791-d space as 0.3302 anchor; best IoU 0.3008 (B) ≈ anchor band | results_e02_118v.json |

## Gate insights (Sep 8)
- Label-noise hypothesis CONFIRMED: RICH-vs-FULL doubles every metric; precision flat (0.447→0.431), recall doubled (0.147→0.296).
- FULL fold-5 anomaly (PR-AUC 0.067 < random 0.079): 4-video folds too small → 620v run fixes fold variance.
- Full-set forensics: pos 1.16% (2,816/243,501), markers in 174/620 videos → FAIL line set to 0.5% (D-GATE-FAIL05).

## Pending
- [x] **Full 620v run** — DONE Sep 11 via kernel v32 (rows 8–9).
- [x] **v32 post-hoc forensics** — DONE Sep 12 (row 10): no shortcuts, truncation fix NOT justified → **v33 CANCELLED**.
- [x] **E02 temporal ablation** — DONE Sep 12 (rows 11–12): Gate 3 conditional PASS on TRUE labels; pause/turn feats +0.075, BiGRU sequence +0.123, order-shuffle ablation confirms real signal.
- [x] **E02 @ 118v Tier-2 scale** — DONE Sep 12 (row 13): sequence effect replicates (+0.087 over order-shuffled); A reproduces historical band; scale-up of TRUE-label testing is **complete** — remaining scale paths are label-blocked (621v VTT audio ∩ 155v EMNLP labels = 0 overlap).
- [x] **Tier-2 anchor eval** — DONE Sep 12 (row 13, same run): 791-d embeddings ∩ EMNLP labels recovered 118v; A-arm F1 0.588 vs hist 0.678 (labeling-rule difference), IoU 0.30 vs anchor 0.3302 — consistent, anchor stands.
- [x] **Tier-3 anchor eval** — superseded: Gillick-87v already saturated historically (F1=0.975, word-level F0+MLP).
- [x] **E03/E05 Test-3 flagship (MELD A/B/C)** — DONE Sep 12 (row 14): **NULL RESULT** — Δ(C−B)=0.000, CI [−0.0142,+0.0145]. Mandate §7 gate NOT passed → commercial claim narrowed. Registry note: source-separation E03 stays label-blocked; this run operationalizes mandate Test 3 (= registry E05) on MELD.
- [x] **Honest paper DRAFT V1 assembled** — DONE Sep 12: `PAPER_DRAFT_V1.md` (repo docs + chucklenet docs). Structure: abstract (3 results + thesis) / intro / program design / weak-label case study / T2 two-scale PASS / T3 MELD NULL / scale-blockers / conclusion / reproducibility appendix. All numbers from rows 1–14 only. Thesis line: "Words carry emotion; behavior carries laughter."
- [x] **Figures 1–2 generated** — DONE Sep 12: `figs/fig_t2_gate3.png` (two-scale arm bars + sequence-effect deltas) and `figs/fig_t3_null.png` (MELD arms + Δ(C−B) CI straddling zero); referenced in PAPER_DRAFT_V1 §5/§6; mirrored to repo docs/figs/.
- [x] **arXiv-first PDF built** — DONE Sep 13: `paper/CHUCKLENET_PAPER_V1.pdf` (4pp A4, reportlab, both figures embedded, references with TODO-VERIFY markers where lit-review titles need exact-string confirmation; refs.bib + build_pdf.py alongside). Mirrored to repo paper/. arXiv source upgrade path: paper.tex (can be generated from same content when submitting; tectonic install failed locally — compile on Overleaf/arXiv).
- [x] **Citations verified against primary sources** — DONE Sep 13 (DDG-lite + ACL Anthology + ISCA/HAL): Gillick21 = "Robust Laughter Detection in Noisy Environments" (Gillick/Deng/Ryokai/Bamman, Interspeech 2021); StandUp4AI = Barriere/Gomez/Hemamou/Callejas/Ravenet, Findings EMNLP 2025 pp.16951–9; Purandare&Litman = "Humor: Prosody Analysis and Automatic Recognition for F*R*I*E*N*D*S*" EMNLP 2006 pp.208–15 (lit review said ACL — CORRECTED); Truong&vanLeeuwen 2007 = "Automatic discrimination between laughter and speech" SpeechComm 49(2) (lit review title was wrong — CORRECTED); Gillick&Bamman = "Please Clap: Modeling Applause in Campaign Speeches" NAACL-HLT 2018 pp.92–102 (lit review said ACL + misnamed author — CORRECTED). refs.bib + PDF rebuilt with exact strings; PAPER_DRAFT_V1 §2 claims updated.
- [ ] **Then: honest paper** — READY FOR ARXIV (timing = USER DECISION); optional E03b (reviewer-triggered only), T4 transfer decision.
- [x] **HF flagship model released** — DONE Sep 13: `Hayasuki/chucklenet-laughter-detector` (public): frozen wavlm-base + v32 MLP head (safetensors, bit-exact verified), custom modeling code with `detect()` VAD→timestamps pipeline (thr 0.85 operating point), honest weak-label model card (F1 0.2732 / IoU-F1@0.2 0.229 / AP 0.142 + E01/E02/E05 scientific context + citation). Old models REPLACED (now private): chuckleNet-v2 (263 dl), chuckleNet-768-fusion, chucklenet-fusion-v2. Next: GPU fine-tune wavlm-base end-to-end on 620v raw audio (Phase 2) + Gradio demo Space (Phase 3).
- [x] **T4 readiness survey** — DONE Sep 13: `T4_READINESS_AND_DATA_SURVEY.md` (+ repo docs). Pre-registered E07/T4 gate drafted (C>C-shuf on conversation true-labels; zero-shot secondary; monologue-specific falsifier). Data paths ranked: AMI (free) → MSP-Podcast (license) → weak-label podcast pre-study → IEMOCAP/Switchboard. T4 now DECISION-blocked only.


## Row 14 — E03/E05: Test 3 flagship, MELD (2026-09-12, kernel `chucklenet-e03-meld-v3` v2, CPU 49 min)
- **Design (mandate §7)**: A transcript-only (TF-IDF 1-2g + LR) / B A+dialogue context (position, speaker-change) / C B+16 acoustic interaction signals (leading/trailing silence, voiced frac, energy stats, ZCR, spectral shape, F0-yin stats). MELD 7-class emotion, official test split n=2,609, 2,000× bootstrap CI on Δ(C−B). Source: official `MELD.Raw` (declare-lab HF), key-join by construction (`diaX_uttY`); train 9,988 / dev 1,109 / test 2,609 (2 utterances lack files — official quirk).
- **Results (test weighted-F1)**: A **0.4483** · B **0.4433** · C **0.4434**. Δ(C−B)=**0.0000**, 95% CI **[−0.0142, +0.0145]** → **gate_C_beats_B_credibly = FALSE**.
- **Verdict (pre-registered gate)**: interaction-signal features add NO beyond-words information for general emotion classification with linear models → commercial claim NARROWED to laughter/reaction events (E02 Gate-3 evidence, two true-label scales). Paper thesis sharpens: "words carry emotion; behavior carries laughter."
- **Caveats**: hand-crafted 16-d features + linear model; deep acoustic encoders (wav2vec2) untested (E03b optional, reviewer-triggered only); emotion ≠ reaction events; B slightly below A.
- Artifacts: `results_e03_meld.json`; kernel output also carries `meld_acoustic_official.npz` + `meld_frames.pkl` (mount as dataset to skip 49-min recompute).

## Row 15 — 2026-09-14 | E06/HF-v2 GPU end-to-end fine-tune (v3) — **NULL (load-path bug), diagnostic only**

- Kernel: `subhajitdas/chucklenet-hf-v2-gpu-v3` (P100, 4.66h, 24 epochs configured / 13 run to guard)
- Result: val F1 0.0192, AP 0.0097, IoU@0.2 0.015 — loss flat ~0.56 from epoch 0, never learned
- **Root cause (log-verified):** `Wav2Vec2Model.from_pretrained('microsoft/wavlm-base')` — class/checkpoint mismatch; WavLM transformer-layer weights UNEXPECTED → dropped → random init ("WavLM loaded via safetensors" print was misleading)
- Lesson: v1 crash fix (check_torch_load_is_safe dual patch) changed load class silently; load reports must be ASSERTED (missing keys == 0), not printed
- Decision: v32 (F1 0.2732) remains the HF flagship; no swap. v4 candidate (pending GPU approval): proper `WavLMModel` class + assert load integrity + warmup restore
- Numbers: train_hours 4.658, best_thr 0.23, n_utts 121,928 (protocol parity with row 1)

## Row 16 — 2026-09-18 | ChuckleNet v30e independent full-corpus repeat — baseline, NOT flagship

- Kernel: `subhajitdas/chuckle-e2e-v30e` (Kaggle T4, run 134760029); status COMPLETE. HF: private repo `Hayasuki/chucklenet-v30e`.
- Pipeline: local WavLM-base mirror → per-utterance mean-pooled 768-d → MLP 768–256–128–1; 3:1 neg sampling; 15 epochs.
- Extraction: 620/620 processed, 0 skipped, 2,789 s. This run applied a **900 s decode window** per video, leaving only feature-backed segment IDs eligible for split/eval (val 15,478 samples / 164 positives; fewer than the v32 full 121,928 protocol).
- Results: best **segment F1 0.2444** @ 0.75, **AP 0.1642**; event **IoU-F1@0.1–0.5 0.1743** (P 0.2603, R 0.1310; TP/FP/FN 38/108/252).
- Verdict: valid reproducibility artifact and release package. **v32 remains flagship** (F1 0.2732 / IoU-F1@0.2 0.2290 / AP 0.142) because it uses the fuller feature protocol and has post-hoc forensics. Do not compare v30e event IoU directly with v32 without controlling for the decode-window/valid-ID restriction.
- Artifacts: local `releases/v30e/`, `releases/v30e_hf/`; `results_e2e.json`, `training_history.json`, `val_predictions.npz`.


## Row 17 — 2026-09-18 | Mandate V4 P1 paired temporal validation — PARTIAL / NARROWED

- Experiment: `P1-TEMPORAL-PAIRED-118V-2026-09-18`; script `training/p1_temporal_validate.py`; artifacts `results/p1/`.
- Data: 118-video human-verified EMNLP intersection, 11,161 windows / 2,712 positives; 5-fold video-disjoint GroupKFold; seeds 42/43/44.
- Conditions: true order, full random within-video order, local 25 s block shuffle, reverse.
- Primary gate **PASS**: true − random = **+0.0769 F1**, clustered bootstrap 95% CI **[+0.0617, +0.0917]**; 287 improved / 66 worsened / 1 unchanged.
- Secondary controls **FAIL**: true − local = −0.0061 [−0.0170, +0.0044]; true − reverse = +0.0071 [−0.0032, +0.0180].
- Verdict: **PARTIAL**. Sequence context is strongly supported; fine local ordering or forward direction is not supported at fixed 5 s resolution. Narrow claim: broad sequence/context structure matters; do not headline unqualified “temporal order matters.”
- Correct next temporal tests: preceding-context ablation, onset/offset error, reaction latency, prefix/causal evaluation.


## Row 18 — 2026-09-18 | Mandate V4 P2 concurrent beyond-words test — NOT SUPPORTED (null narrows thesis)

- Experiment: `P2-BEYOND-WORDS-118V-2026-09-18`; script `training/p2_beyond_words.py`; artifacts `results/p2/`.
- Data: 118-video human-verified EMNLP intersection; 6,211 word-span 5 s windows; 2,765 positives (44.5%); 5-fold video-disjoint GroupKFold; seeds 42/43/44.
- Conditions: A = TF-IDF word content (train-fold fit, 5,000 feats); B = A + 7 pause/timing features; identical MLP per condition.
- Result: B − A = **+0.0018 F1**, video-clustered bootstrap 95% CI **[−0.0046, +0.0080]** — spans zero; 65/118 improved vs 52/118 worsened.
- Verdict: **NOT SUPPORTED.** Concurrent timing aggregates add no measurable information over word content for current-window laugh labeling. Word content is a strong baseline (fold F1 0.568).
- Compatibility with P1: temporal signal lives in acoustic sequence structure (P1: order destruction −0.077), not in window-level timing statistics (P2: +0.002 null).
- Consequence: do not claim timing-feature increments for concurrent detection; next P2 test is Level A prospective onset prediction (context-before only → next-window onset).

## Row 19 — 2026-09-18 | Mandate V4 P2 Level A prospective onset prediction — SUPPORTED (H3/H4-prospective)

- Experiment: `P2-LEVELA-PROSPECTIVE-118V-2026-09-18`; script `training/p2_level_a_prospective.py`; artifacts `results/p2_level_a/`; pre-registration `docs/P2_LEVELA_THEORY_RECHECK_AND_PREREG_2026-09-18.md`.
- Task: predict laugh-word presence in window t+1 from context ≤ t only (punchline words of t+1 excluded by construction). 118v; 6,211 windows; 5-fold video-disjoint GroupKFold; seeds 42/43/44; identical MLP per arm.
- Arms: position-only 0.418 · cumulative words TF-IDF 0.478 · words+timing 0.473 · **frozen-WavLM acoustic context 0.569** · **acoustic+words 0.574** (fold mean F1).
- Gates (video-clustered bootstrap): G1 acoustic+words − words **+0.1117** [+0.0857,+0.1390] PASS; G3 acoustic − words **+0.1074** [+0.0766,+0.1398] PASS; G2 timing − words −0.0021 null; words − position +0.0497 (position shortcut real but far smaller).
- Provenance note: first readout printed NOT SUPPORTED due to a sign bug in gate evaluation only; raw paired deltas were correct; gates recomputed from saved observations; correction embedded in results JSON.
- Verdict: **BEYOND-WORDS PROSPECTIVE SUPPORTED.** Pre-onset frozen-WavLM context predicts next-window laughter far better than the entire preceding transcript. Consistent with ICPhS-2019 anticipatory acoustic cues and with P1 (sequence structure) + P2-concurrent (timing aggregates null).
- Caveat: laugh onset late in window t with midpoint in t+1 may place audible onset in the context — part of the effect may be very-early onset detection; sub-5 s onset-margin analysis is the registered next step. Hand-crafted timing features are null twice; do not pitch pause-statistic features.



## Row 20 — 2026-09-18 | Onset-margin stratification — GENUINE ANTICIPATION confirmed (not onset bleed)

- Experiment: `P2-LEVELA-ONSET-MARGIN-2026-09-18`; script `training/p2_levela_onset_margin.py`; artifacts `results/p2_level_a/p2_levela_onset_margin_results.json`.
- Same arms/seeds/folds as Row 19 retrained with per-window predictions; positives stratified by earliest laugh-word onset relative to the context boundary (straddle / early 0–1 s / mid 1–2.5 s / late ≥2.5 s).
- Hit rate on positives: acoustic context ~0.78–0.80 in every stratum vs words 0.47–0.53; paired clustered-bootstrap hit-rate delta (acoustic+words − words): straddle +0.271 [0.187,0.355], early +0.233 [0.183,0.281], mid +0.245 [0.194,0.295], **late +0.222 [0.172,0.275]**.
- Verdict: **GENUINE ANTICIPATION.** The advantage is undiminished where onset bleed is physically impossible; only 774/8,181 positives are straddle.
- Claim tier: pre-onset acoustic context anticipates audience laughter up to a 5-second horizon, beyond the full preceding transcript, robust to onset-bleed controls. Streaming-latency claims still require causal deployment tests.

## Row 21 — 2026-09-18 | Horizon curve — anticipation extends to ≥15 s (P2 CLOSED)

- Experiment: `P2-HORIZON-CURVE-118V-2026-09-18`; script `training/p2_horizon_curve.py`; artifacts `results/p2_level_a/p2_horizon_curve_results.json`.
- Target: laugh presence in window t+H from context ≤ t; H=2 (10 s) and H=3 (15 s), same arms/seeds/folds as Rows 19–20.
- Fold mean F1: H2 words 0.466 / acoustic 0.559 / a+w 0.560; H3 words 0.450 / acoustic 0.554 / a+w 0.548.
- Paired ΔF1 (a+w − words): H2 **+0.1024** [+0.0768,+0.1276]; H3 **+0.1054** [+0.0799,+0.1310]; acoustic-alone also passes (H2 +0.0974, H3 +0.1102). All four gates PASS.
- Combined with Rows 19–20: non-semantic acoustic context anticipates audience laughter at 5/10/15 s horizons, robust to onset-bleed and position controls, on human labels. Advantage decays negligibly with horizon.
- Claim tier final for this dataset: **≥15 s reaction-anticipation signal, information beyond transcript, controlled evidence**. Limits: stand-up only, frozen features, no streaming test, no external transfer yet.
