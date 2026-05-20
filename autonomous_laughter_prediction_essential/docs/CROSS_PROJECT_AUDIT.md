# CROSS-PROJECT AUDIT — Similar Projects & Reusable Assets
**Date:** 2026-05-16  
**Scope:** Full scan of /Users/Subho for laughter/humor/ML projects

---

## 🚨 CRITICAL FINDING: We Already Have 2 Submitted Papers

### Paper 1: FINAL_SUBMISSION/acl_emnlp/ (ACL/EMNLP 2026)
- **Title:** "Biosemotic Humor Recognition: A Multi-Task Framework"
- **System:** "ChuckkleNet" — 9 biosemotic dimensions + XLM-RoBERTa
- **Claimed result:** F1 = 0.8880 ("World-Record for Biosemotic Humor Recognition")
- **Data:** 10,000+ Reddit posts from r/Jokes and r/Sarcasm
- **Status:** LaTeX ready, figures included, references.bib complete
- **⚠️ PROBLEM:** Uses Reddit social media data, NOT stand-up comedy. Different task entirely.

### Paper 2: FINAL_SUBMISSION/coling/ (COLING 2026)
- **Title:** "Cross-Cultural Biosemotic Sarcasm Detection"
- **Claimed result:** 75.9% accuracy, outperforms SemEval winners by +2%
- **Data:** SemEval 2018/2020/2021 tasks (English, Spanish, Chinese)
- **Status:** LaTeX ready, figures included, references.bib complete
- **⚠️ PROBLEM:** Sarcasm detection ≠ laughter prediction. Different task, different data.

### Paper 3: PAPER_DRAFT_ACL_EMNLP.md (In Review)
- **Title:** "Word-Level Laughter Prediction in Multilingual Stand-up Comedy"
- **Result:** F1=0.819 (EN), 0.752 (ZH), 0.68 (HI)
- **Data:** 10,048 training examples from stand-up comedy
- **Status:** Markdown draft, Orchestra review: 2.75/6

**These are 3 DIFFERENT papers for 3 DIFFERENT venues with 3 DIFFERENT tasks.**
The current project (Paper 3) is the strongest actual contribution.

---

## ALL RELATED PROJECTS

| # | Directory | What It Is | Reusable? |
|---|-----------|-----------|-----------|
| 1 | `ChuckleNet/` | Monster repo (643+ files) — contains everything | ✅ Scripts, data, architecture |
| 2 | `autonomous_laughter_prediction/` | OLDER copy of the project (pre-essential) | ✅ Data overlaps, some unique scripts |
| 3 | `autonomous_laughter_prediction_essential/` | **ACTIVE** project | ✅ This is where we work |
| 4 | `FINAL_SUBMISSION/` | 2 completed LaTeX papers (ACL + COLING) | ✅ .bib files, LaTeX templates |
| 5 | `biosemotic-ai/` | CI/CD infrastructure for biosemotic project | ❌ No ML content |
| 6 | `biosemotic-deployment/` | FastAPI + Docker for MELD model | ✅ Deployment scripts |
| 7 | `comedy-dataset-strategy/` | Strategy docs (47KB roadmap) | ✅ Comedian catalog, legal framework |
| 8 | `cross_domain_results/` | Cross-domain eval (StandUp4AI F1=0.699 zero-shot) | ✅ Results for paper |
| 9 | `individual_component_training/` | ToM, GCACU, ensemble training | ✅ Component scripts |
| 10 | `meld_models/` | 3 trained sklearn models (130KB each) | ⚠️ Basic TF-IDF, not deep learning |
| 11 | `datasets/MELD/` | Full MELD emotion dataset | ✅ External benchmark |
| 12 | `datasets/humor_direct/` | Nearly empty (no actual data) | ❌ |
| 13 | `datasets/kaggle_humor/` | Empty | ❌ |

---

## REUSABLE ASSETS FOUND

### Trained Models
| Model | Location | Size | Status |
|-------|----------|------|--------|
| WavLM Phase A checkpoint | `_essential/experiments/wavlm_v2_phaseA/last.pt` | **361MB** | 1 epoch, not converged |
| MELD GradientBoosting | `meld_models/gradient_boosting_improved/` | 130KB | Working sklearn model |
| MELD LogisticRegression | `meld_models/logistic_regression_improved/` | 2KB | Working sklearn model |
| MELD RandomForest | `meld_models/random_forest_improved/` | 2.7MB | Working sklearn model |
| LoRA adapter (unknown) | `~/Downloads/adapter_model.safetensors` | 1.1MB | Unknown provenance |

### Reusable Scripts from ChuckleNet
| Script | Size | What It Does |
|--------|------|-------------|
| `xlmr_standup_word_level.py` | **75KB** | Most complete XLM-R training pipeline |
| `finetune_biosemotic_humor_bert.py` | 31KB | BERT fine-tuning with biosemotic features |
| `finetune_final_unified_humor_bert.py` | 29KB | Final unified BERT training |
| `train_ablation_proven.py` | 34KB | Ablation study framework |
| `mlx_integration.py` | 28KB | **Apple MLX** for Mac GPU training |
| `mlx_training_pipeline.py` | 21KB | MLX training pipeline |
| `train_xlmr_multitask.py` | 26KB | Multi-task XLM-R training |
| `load_ur_funny.py` | 39KB | UR-FUNNY dataset loader |
| `load_youtube_comedy.py` | 34KB | YouTube comedy data loader |
| `ensemble_predictor.py` | ~9KB | Ensemble methods |

### Reusable Architecture (ChuckleNet/core/)
| Module | What It Does |
|--------|-------------|
| `integrated_biosemotic_model.py` | Full integrated model |
| `acoustic_biosemotic_enhancer.py` | **Acoustic feature extraction** |
| `voxceleb_acoustic_interspeech_enhancer.py` | VoxCeleb acoustic features |
| `gcacu/gcacu.py` | Generalized Cognitive Architecture |
| `tom/theory_of_mind.py` | Theory of Mind layer |
| `clost/clost.py` | CLoST layer |
| `sevade/sevade.py` | SEVADE evaluator |

### Cross-Domain Results (for paper)
| Benchmark | Zero-Shot F1 | Source |
|-----------|-------------|--------|
| StandUp4AI | **0.699** | cross_domain_results/ |
| UR-FUNNY | 0.552 | cross_domain_results/ |
| TED Laughter | 0.515 | cross_domain_results/ |

### LaTeX Assets (from FINAL_SUBMISSION)
| Asset | Location | Reusable For |
|-------|----------|-------------|
| ACL LaTeX template + `acl.sty` | `FINAL_SUBMISSION/acl_emnlp/` | Paper 3 conversion |
| `references.bib` (30+ citations) | `FINAL_SUBMISSION/acl_emnlp/` | Base bibliography |
| COLING template + `coling2026.sty` | `FINAL_SUBMISSION/coling/` | Alternative venue |
| `references.bib` (20+ citations) | `FINAL_SUBMISSION/coling/` | Cross-cultural refs |
| Performance comparison PDF figure | `acl_emnlp/acl_emnlp_figure2_*.pdf` | Template for our Figure |

---

## 🔴 KEY FINDING: Apple MLX Integration EXISTS

Two scripts in ChuckleNet/training/ that use **Apple MLX** framework:
- `mlx_integration.py` (28KB)
- `mlx_training_pipeline.py` (21KB)

**Why this matters:** The user has an Apple Mac (M-series). MLX provides:
- Unified memory (GPU shares RAM = no VRAM limit)
- Native Apple Silicon acceleration
- Could train WavLM + XLM-R locally WITHOUT needing Colab/Vast.ai
- **This was NEVER used or mentioned in any planning doc**

---

## 🔴 KEY FINDING: Ensemble Predictor EXISTS

`individual_component_training/ensemble_predictor.py` exists but was never integrated. Could be used for:
- Combining WavLM + XLM-R + acoustic features
- Stacking approach instead of (or in addition to) cross-attention fusion

---

## 🔴 KEY FINDING: Cross-Domain Results EXIST

The cross_domain_results report shows:
- StandUp4AI zero-shot F1=0.699 (decent transfer from internal model)
- UR-FUNNY zero-shot F1=0.552
- TED Laughter zero-shot F1=0.515
- Internal accuracy drops from 61.7% to 30-41% on external data

**These results could go in the paper as "Generalization" experiments!**

---

## WHAT THE ESSENTIAL PROJECT IS MISSING (Found Elsewhere)

| Asset | Where It Lives | Why We Need It |
|-------|---------------|----------------|
| **MLX training pipeline** | ChuckleNet/training/ | Train on Mac without GPU cloud |
| **Acoustic feature enhancer** | ChuckleNet/core/ | Audio features proven in literature |
| **UR-FUNNY loader** | ChuckleNet/training/ | External benchmark for paper |
| **Ensemble predictor** | individual_component_training/ | Multi-model stacking |
| **Cross-domain results** | cross_domain_results/ | Paper generalization section |
| **LaTeX templates + .bib** | FINAL_SUBMISSION/ | Skip LaTeX conversion from scratch |
| **MELD dataset** | datasets/MELD/ | External emotion benchmark |
| **Comedian catalog** | comedy-dataset-strategy/ | Data collection planning |
