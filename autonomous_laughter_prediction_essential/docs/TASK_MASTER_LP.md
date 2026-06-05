# Laughter Prediction — Task Master (REVISED)
## Updated: 2026-05-16 (v2 — with ML tools from full audit)
## Sources: Orchestra Research (2.75/6) + Jenni Peer Review (10) + Full Project Audit

### Legend
🔴 CRITICAL | 🟡 HIGH | 🟢 MEDIUM | ⚪ LOW

---

## EXECUTION ORDER (A3M — Strict Sequence)

### STEP 1: LP-4 — Remove RL Section 🟢 [5 min, edit only]
- Delete Section 4.4 from PAPER_DRAFT (PPO, Bradley-Terry — never validated)
- Move to Future Work: 2 sentences max
- No dependencies

### STEP 2: LP-13 — Install ML Tooling 🟢 [5 min]
- `pip install unsloth peft bitsandbytes wandb`
- Verify imports work
- No dependencies

### STEP 3: LP-1 — Run StandUp4AI Baseline 🔴 [30 min GPU]
- Script: `training/train_standup4ai_baseline.py`
- Fix: enable GPU (remove `CUDA_VISIBLE_DEVICES=""`)
- Data: `colab_package/standup4ai_data/` (4 CSVs, 3,207 words, 564 L labels)
- Data split exists (2,561 train / 642 val) — training never ran
- Deliverable: `experiments/standup4ai_baseline/metrics.json`
- THIS IS THE #1 EXTERNAL BENCHMARK BOTH REVIEWS DEMAND

### STEP 4: LP-15 — Debug WavLM F1=0.0 🔴 [30 min]
- `experiments/wavlm_v2_phaseA/results.json` shows F1=0.0 across all metrics
- Investigate: data loading, label distribution, loss function, forward pass
- Root cause likely: all same class, wrong label column, or silent crash
- Deliverable: Root cause documented + fix

### STEP 5: LP-5 — Retrain WavLM with Unsloth 🟡 [1-2 hr GPU]
- Use Unsloth for 2x speed, 80% less VRAM
- Phase A: Frozen WavLM + MLP on 733K segments
- Target: F1 ≥ 0.55 (if acoustic features used as fallback)
- Deliverable: Working WavLM checkpoint + F1 score

### STEP 6: LP-14 — Extract Tier 1 Acoustic Features 🟡 [1 hr CPU]
- Use librosa to extract from 733K aligned segments:
  - F0 statistics (pitch mean, range, slope)
  - Pause duration before/after words (#1 predictive feature)
  - Speech rate, RMS energy, MFCC 1-13
  - Spectral centroid/bandwidth/rolloff
- Based on ACOUSTIC_FEATURES_RESEARCH.md (636 lines of literature review)
- Deliverable: `data/audio_comedy/acoustic_features/` (numpy arrays)

### STEP 7: LP-6 — Audio-Only Baseline 🟡 [2 hr GPU]
- Two approaches in parallel:
  - (A) WavLM SSL features (from LP-5)
  - (B) Handcrafted acoustic features (from LP-14) → simple classifier
- Jenni Comment #4 demands this
- Deliverable: Audio-only F1 scores

### STEP 8: LP-2 — Add Proper Baselines 🔴 [2 hr GPU]
- BiLSTM baseline (torch.nn.LSTM)
- XLM-R without biosemotic features (proves biosemotic claim or disproves it)
- CRF baseline (torchcrf or sklearn-crfsuite)
- Orchestra: "Only trivial baselines = reject"
- Deliverable: Results table with 5+ models

### STEP 9: LP-3 — Multi-Seed + Error Bars 🔴 [3-5 × 3 hr GPU]
- Run 5 seeds (42, 123, 456, 789, 1024) for main model + all baselines
- Track with wandb
- Compute mean ± std F1, bootstrap 95% CI
- Deliverable: Publication-quality results table

### STEP 10: LP-7 — Fused WavLM + XLM-R with LoRA 🟡 [4 hr GPU]
- Use PEFT LoRA (r=16, alpha=32) on both encoders
- Gradient checkpointing for memory
- Cross-attention fusion (4 layers)
- Total: 470M params, ~5M trainable with LoRA → fits T4
- Target: F1 > 0.819 (beat text-only)
- Deliverable: Fused model checkpoint + F1

### STEP 11: LP-9/10/11 — Paper Edits 🟢 [1-2 days]
- LP-9: Add StandUp4AI, FunnyNet-W, M2H2, AVR references
- LP-10: Remove "first" claims, reposition as StandUp4AI extension
- LP-11: Document teacher-refinement failure (Qwen 1.5B, prompt, bug)
- Deliverable: Revised PAPER_DRAFT

### STEP 12: LP-12 — LaTeX Conversion 🟢 [1 day]
- Use Orchestra templates (`~/.orchestra/skills/20-ml-paper-writing/`)
- Create `paper/main.tex` + `paper/refs.bib`
- ACL format submission

---

## Dependency Graph

```
LP-4 (RL remove)     → independent
LP-13 (install tools) → LP-5, LP-7, LP-8
LP-1  (StandUp4AI)   → LP-9 (needs F1 for comparison)
LP-15 (debug WavLM)  → LP-5 (fix and retrain)
LP-5  (WavLM train)  → LP-6 (audio baseline A) → LP-7 (fusion)
LP-14 (acoustic feat) → LP-6 (audio baseline B) → LP-7 (fusion)
LP-2  (baselines)    → LP-3 (multi-seed needs all models)
LP-3  (error bars)   → LP-11 (paper needs final numbers)
LP-9/10/11 (edits)   → LP-12 (LaTeX)
```

## Parallel Tracks

```
TRACK A (experiments):  LP-1 → LP-2 → LP-3 (GPU-bound)
TRACK B (audio):        LP-15 → LP-5 → LP-14 → LP-6 → LP-7 (GPU-bound)
TRACK C (paper edits):  LP-4 → LP-9 → LP-10 → LP-11 → LP-12 (CPU)
```

## Tools Required

| Tool | Install | Used In | Notes |
|------|---------|---------|-------|
| Unsloth | `pip install unsloth` | LP-5, LP-7 | 2x faster, 80% less VRAM |
| PEFT | `pip install peft` | LP-7 (LoRA) | 470M → ~5M trainable params |
| bitsandbytes | `pip install bitsandbytes` | LP-7 (QLoRA) | INT4 quantization |
| wandb | `pip install wandb` | LP-3, LP-8 | Experiment tracking |
| torch.compile | PyTorch 2.0+ | LP-5, LP-7 | Free 1.3x speedup |
| librosa | ✅ installed | LP-14 | F0, MFCC, spectral |
| openSMILE | ✅ installed | LP-14 (eGeMAPS) | 88 validated features |
| Apple MLX | ✅ exists in ChuckleNet | LP-5 (Mac GPU) | 28KB+21KB scripts ready |

## Reusable Assets from Other Projects

| Asset | Source | Use For |
|-------|--------|--------|
| WavLM checkpoint (361MB, 1 epoch) | `_essential/experiments/wavlm_v2_phaseA/last.pt` | Resume training |
| MELD sklearn models (3) | `meld_models/` | Baseline comparison |
| XLM-R training pipeline (75KB) | `ChuckleNet/training/xlmr_standup_word_level.py` | Reference for baselines |
| MLX integration (28KB) | `ChuckleNet/training/mlx_integration.py` | Train on Mac Silicon |
| MLX pipeline (21KB) | `ChuckleNet/training/mlx_training_pipeline.py` | Local GPU training |
| Acoustic enhancer | `ChuckleNet/core/acoustic_biosemotic_enhancer.py` | Audio features |
| UR-FUNNY loader (39KB) | `ChuckleNet/training/load_ur_funny.py` | External benchmark |
| Ensemble predictor | `individual_component_training/ensemble_predictor.py` | Model stacking |
| Cross-domain results | `cross_domain_results/` | Paper generalization section |
| ACL LaTeX template + .bib | `FINAL_SUBMISSION/acl_emnlp/` | Skip LaTeX from scratch |
| COLING LaTeX template + .bib | `FINAL_SUBMISSION/coling/` | Alternative venue |
| Comedy dataset catalog | `comedy-dataset-strategy/` | Data collection |
| MELD full dataset | `datasets/MELD/` | Emotion benchmark |

## Compute Required

| Task | GPU | Time | Cost |
|------|-----|------|------|
| LP-1 StandUp4AI | T4 | 30 min | Colab free |
| LP-15 Debug | CPU | 30 min | $0 |
| LP-5 WavLM Phase A | T4 | 1-2 hr | Colab free |
| LP-14 Acoustic features | CPU | 1 hr | $0 |
| LP-6 Audio baseline | T4 | 2 hr | Colab free |
| LP-2 Baselines | T4 | 2 hr | Colab free |
| LP-3 Multi-seed (5×) | T4 | 15 hr | Colab Pro $10 |
| LP-7 Fusion | T4 | 4 hr | Colab Pro |
| **TOTAL** | | **~26 hr GPU** | **~$10-20** |
