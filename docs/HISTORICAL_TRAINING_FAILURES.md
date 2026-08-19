# Historical Training Failures — Complete Catalog
**Date:** 2026-08-19 (triple-check via agent ensemble)
**Status:** 18 patterns documented, rules enforced in scale notebook

---

## Critical Rules (never violate)

| # | Rule | Hard Limit |
|---|------|-----------|
| R1 | Minimum positive rate | **≥ 15%** — reject below |
| R2 | pos_weight ceiling | **≤ 3.0** — never exceed |
| R3 | Evaluation metric | **held-out comedians only** — random split is invalid |
| R4 | Feature generation | **label-blind** — LLM must never see labels |
| R5 | Pseudo-labeling source | **F1 > 0.9 teacher only** — no broken models |
| R6 | Boundary detection | **separate heads** — never single head for BIO+boundary |

---

## All 18 Failure Patterns

### Pattern 1: Label Sparsity Catastrophe
- **Symptom:** F0 668 videos (1.2% positive) → F1~0; Gillick 272 (2.2%) → F1=0.04
- **Root Cause:** <5% positive rate → negatives drown gradients → model learns "predict non-laugh always"
- **Evidence:** `docs/CLEAN_PROJECT_PLAN.md` dead data table; `combined_f0_pseudo_labels.npz` = DEAD
- **Prevention:** Hard limit — reject any dataset below 15% positive rate

### Pattern 2: Model Saturation from pos_weight=5.0
- **Symptom:** `top200_prosody_model.pt` outputs all probs = 1.0 (min=1.0, max=1.0, std=0.0)
- **Root Cause:** pos_weight=5.0 over-upweighted positives → model predicts laugh for everything
- **Evidence:** `iou_results_10video.json`; local test on 10 EMNLP videos
- **Prevention:** pos_weight ≤ 3.0, validate output probability distribution every run

### Pattern 3: Word-Level Boundary Problem
- **Symptom:** XLM-R stuck at IoU-F1=0.50, cannot break through
- **Root Cause:** Single classification head must do TWO tasks: BIO labeling + boundary detection
- **Evidence:** `training/autonomous_research_loop.py` targets IoU-F1 but single head can't solve both
- **Prevention:** Separate heads for classification vs boundary, or multi-task learning

### Pattern 4: Teacher Refinement Degraded Labels
- **Symptom:** Refined-label XLM-R → val F1=0.078, test F1=0.123 vs weak-label → val F1=0.785, test F1=0.819
- **Root Cause:** qwen2.5-coder:1.5b teacher introduced more errors than it fixed
- **Evidence:** `AGENTS.md` handoff notes; `xlmr_standup_baseline_weak_pos5` promoted, refined NOT promoted
- **Prevention:** Don't refine already-labeled data with an imperfect teacher

### Pattern 5: Hyperparameter Search Wasted Compute
- **Symptom:** pos4 and pos6 both lost to pos5 baseline in autoresearch loop — no promotion
- **Root Cause:** pos5 was already optimal for this data; local search exhausted
- **Evidence:** `AGENTS.md` ("first real autoresearch cycle completed with no promotion")
- **Prevention:** Only search hyperparameters after major data changes

### Pattern 6: Pseudo-Labeling Amplified Noise
- **Symptom:** `combined_f0_pseudo_labels.npz` produces garbage models
- **Root Cause:** Pseudo-labels from broken F0 model (F1~0) propagate and amplify errors
- **Evidence:** `experiments/pseudo_label_results.json`; dead data table
- **Prevention:** Only pseudo-label with F1 > 0.9 teacher model

### Pattern 7: WavLM Pipeline Failed (2 variants)
- **Symptom:** WavLM Phase A → val_f1=0.0 (all zeros); WavLM Final → val_f1=0.55, holdout_f1=0.16
- **Root Cause:** Pipeline bug (Phase A) + comedian-style memorization (Final)
- **Evidence:** `ablation_fusion_vs_audio.json`; `audio_biosemotic_results.json`
- **Prevention:** Always evaluate on held-out comedians, not random splits

### Pattern 8: F0 Extraction Misaligned
- **Symptom:** Only 68/5000 clips positive (1.4%) despite targeting laughter
- **Root Cause:** Clip extraction windows didn't align with actual laughter audio
- **Evidence:** `hypothesis_validation_matrix.json` H1.2: "F1 extraction results available: false"
- **Prevention:** Verify positive rate of extracted features before scaling

### Pattern 9: StandUp4AI Training val_f1=0.0
- **Symptom:** XLM-R on StandUp4AI data → val_f1=0.0 across all epochs
- **Root Cause:** Undiagnosed — likely data loading, class weights, or learning rate bug
- **Evidence:** `experiments/standup4ai_baseline/h4_6_results.json`
- **Prevention:** val_f1=0.0 means pipeline bug — diagnose data loading first

### Pattern 10: Prosody Feature Plateau at 5-15 Dimensions
- **Symptom:** MLP on top-5 to top-15 features → F1 stuck at 0.31-0.53
- **Root Cause:** Discriminative signal distributed across all 23 features; subset loses signal
- **Evidence:** `experiments/prosody_feature_analysis.json`; top-23 gives F1=0.978 vs top-15 gives F1=0.53
- **Prevention:** Always use full 23-dim prosody feature set

### Pattern 11: Training Overfitting
- **Symptom:** prosody_300videos → train F1=0.992, held-out F1=0.58 (gap=0.41)
- **Root Cause:** Training F1 reflects memorization, not generalization
- **Evidence:** `video_holdout_fair_results.json`; previous video_holdout_f1=0.61
- **Prevention:** Always evaluate on held-out set; training F1 is meaningless

### Pattern 12: Pause from Subtitle Timestamps
- **Symptom:** H0.0 → F1=0.20 vs target 0.25; Cohen's d=0.13 vs threshold 0.5
- **Root Cause:** Subtitle timestamps ~0.5-1.0s resolution; Purandare's 0.8s threshold undetectable
- **Evidence:** `experiments/H0.0_example/results/metrics.json`; `hypothesis_validation_matrix.json` H1.1
- **Prevention:** Extract acoustic features from raw audio with librosa, not from subtitles

### Pattern 13: Biosemiotic Label Leakage
- **Symptom:** Biosemiotic features alone → F1=0.829 without any audio/text input
- **Root Cause:** LLM saw labels during feature generation → features trivially predict labels
- **Evidence:** `hypothesis_validation_matrix.json` H4.4; `task1_statcheck_report.md` C04: INVALID_LABEL_LEAKAGE
- **Prevention:** Any LLM-assisted feature must never see labels

### Pattern 14: Function Word Removal Worse Than Baseline
- **Symptom:** Removing function words → F1 drops 0.080→0.025
- **Root Cause:** Chi-squared test: FW equally distributed in laugh vs non-laugh (p=0.14) — they are neutral
- **Evidence:** `experiments/validation/data_integrity_analysis.json`; "chi2=2.17, p=0.14"
- **Prevention:** Chi-squared test any filtering heuristic before applying

### Pattern 15: Internal ≠ External Generalization
- **Symptom:** Internal 100% → external zero-shot F1 ranges 0.44-0.70 (49% avg transfer ratio)
- **Root Cause:** Models memorize comedian-specific patterns; don't transfer across domains
- **Evidence:** `AGENT_8_KEY_FINDINGS.txt`; "51% performance gap"
- **Prevention:** Cross-comedian and cross-domain evaluation is the only honest measure

### Pattern 16: Hallucinated Citations
- **Symptom:** 4 likely hallucinated, 23 unmatched, 2 wrong year
- **Root Cause:** Copy-paste from other papers without verification
- **Evidence:** `experiments/validation/task3_citation_report.md`
- **Prevention:** Verify every citation at Google Scholar or Semantic Scholar before submission

### Pattern 17: Unvalidated Paper Narrative
- **Symptom:** PARADIGM_SHIFT_PAPER.md argues "audio necessary" but no working audio model demonstrated
- **Root Cause:** Advocacy written before evidence; conflates WavLM pipeline bug with "audio useless"
- **Evidence:** `hypothesis_validation_matrix.json` cross-cutting assessment
- **Prevention:** Demonstrate first, claim second

### Pattern 18: Incomplete External Validation
- **Symptom:** XLM-R achieves F1=0.82 internally but StandUp4AI val_f1=0.0 (never fixed)
- **Root Cause:** Training failure not diagnosed; cross-domain transfer ratios computed without valid baseline
- **Evidence:** `experiments/standup4ai_baseline/h4_6_results.json`; "fix may take 5 minutes of pos_weight tuning"
- **Prevention:** Fix training pipelines before claiming external validation results

---

## Data Quality Thresholds

| Metric | Minimum | Target | Source |
|--------|---------|--------|--------|
| Positive rate | **15%** | 20-30% | Pattern 1 |
| Training examples | 1,000 | 10,000+ | Pattern 9 |
| Held-out videos | 3 | 10+ | Pattern 15 |
| Teacher model F1 | **0.90** | 0.95+ | Pattern 6 |

---

## Validated Results (What Works)

| Model | F1 | Data | Conditions |
|-------|-----|------|------------|
| `best_fusion_model.pt` | 0.975 | 87 videos, 22.7% pos | Held-out comedians |
| video_holdout_fair | 0.960 | 18 held-out videos | Cross-video |
| Gillick 162 validation | 0.54 | 162 external videos | Comparable to literature |

---

*Triple-check complete. Every failure has a root cause, evidence, and prevention rule.*
