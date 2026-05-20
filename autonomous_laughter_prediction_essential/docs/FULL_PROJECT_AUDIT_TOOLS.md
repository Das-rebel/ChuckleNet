# FULL PROJECT AUDIT — TOOLS, TECHNIQUES & GAPS
**Date:** 2026-05-16  
**Sources:** 12 core planning docs + Orchestra Review + Jenni Peer Review

---

## WHAT'S ALREADY PLANNED BUT NEVER USED

### 🟡 Tools in Docs But NOT in Any Script:
| Tool | Where Mentioned | Why It Matters | Status |
|------|----------------|----------------|--------|
| **Unsloth** | User mentioned "engra, unsloth etc" | 2x faster fine-tuning, 80% less VRAM. Would let us train on Colab T4 what currently needs A100 | ❌ NOT installed or used |
| **LoRA/QLoRA** | Not in ANY doc | PEFT for training WavLM+XLM-R fusion on 16GB VRAM. Standard for parameter-efficient multimodal | ❌ NOT mentioned anywhere |
| **PEFT library** | Not in ANY doc | HuggingFace PEFT for LoRA, adapters, prefix tuning | ❌ NOT used |
| **torch.compile** | EXECUTION_PLAN_10M.md | 1.3x speedup. Mentioned but never implemented in any training script | ⚠️ Planned only |
| **Adam8bit** | EXECUTION_PLAN_10M.md | 1.2x memory savings from bitsandbytes. Mentioned but never implemented | ⚠️ Planned only |
| **Gradient checkpointing** | MODEL_SELECTION.md | Needed for 470M param fusion model on 16GB VRAM. Not implemented | ⚠️ Planned only |
| **MFCC pre-computation** | EXECUTION_PLAN_10M.md, PRD_V4 | 120-dim features. Script planned but never created | ⚠️ Script not created |
| **openSMILE eGeMAPS** | ACOUSTIC_FEATURES_RESEARCH.md | 88 validated acoustic features. Installed but never used in training | ⚠️ Installed, unused |
| **Weights & Biases / TensorBoard** | NOWHERE | No experiment tracking. All results are single-run, no error bars | ❌ Not even mentioned |
| **Bootstrap CI** | Orchestra Review | Statistical significance. Not used anywhere | ❌ Not implemented |

### 🔴 Critical Gaps (Blocks Publication):
1. **No LoRA/QLoRA** — Fusion model (470M params) won't fit T4 16GB without PEFT
2. **No Unsloth** — Could 2x training speed on Colab, currently wasting GPU hours
3. **No experiment tracking** — No way to reproduce results, no error bars
4. **No multi-seed runs** — Single run, no statistical significance
5. **No proper baselines** — Only Random (0.38) and Keyword (0.45)

---

## WHAT EXISTS BUT IS BROKEN/INCOMPLETE

| Component | Script | Status | Root Cause |
|-----------|--------|--------|------------|
| StandUp4AI baseline | `training/train_standup4ai_baseline.py` | Data split done, training never ran | CPU-only hardcoded, likely crashed |
| WavLM Phase A | `training/train_wavlm_audio_v2.py` | F1=0.0 (complete failure) | Unknown — needs debugging |
| Audio extraction | `training/extract_audio_segments.py` | Created, tested (126 seg/s) | Never run at scale |
| Whisper batch | `training/whisper_batch_gdrive.py` | Created | Never run on batch15 (214 MP3s) |
| Fusion model | `training/fusion_crossmodal_train.py` | Created, uses Wav2Vec2 (not WavLM) | Never trained |
| Cross-domain learning | `training/cross_domain_learning.py` | Created | Never used |

---

## MODELS: PLANNED vs ACTUAL

| Model | Planned | Actually Trained | Best F1 |
|-------|---------|------------------|---------|
| XLM-R text (pos5) | ✅ | ✅ | **0.819 test, 0.785 val** |
| XLM-R + biosemotic | ✅ | ✅ | 0.819 test, 0.785 val (+0.003 noise) |
| StandUp4AI XLM-R | ✅ | ❌ Never ran | N/A |
| Wav2Vec2 audio | ✅ | ❌ | N/A |
| WavLM audio Phase A | ✅ | ❌ F1=0.0 failure | 0.0 |
| WavLM Phase B | ✅ | ❌ | N/A |
| WavLM Phase C | ✅ | ❌ | N/A |
| Audio-only baseline | ✅ | ❌ | N/A |
| WavLM + XLM-R fusion | ✅ | ❌ | N/A |
| BiLSTM baseline | ❌ NOT planned | ❌ | N/A |
| CRF baseline | ❌ NOT planned | ❌ | N/A |

---

## TECHNIQUES THAT SHOULD BE ADDED (Based on SOTA)

### 1. Unsloth (for WavLM + XLM-R training)
**Why:** 2x faster fine-tuning, 80% less VRAM, supports WavLM and XLM-R
**Impact:** Could train fusion model on Colab T4 instead of needing A100
**Install:** `pip install unsloth`
```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained("microsoft/wavlm-base-plus")
model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=32)
```

### 2. LoRA/QLoRA via PEFT (for multimodal fusion)
**Why:** Fusion model is 470M params. LoRA reduces trainable params to ~5M (1%)
**Impact:** Fits in 8GB VRAM instead of needing 24GB
**Install:** `pip install peft bitsandbytes`
```python
from peft import LoraConfig, get_peft_model
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["query", "value"])
model = get_peft_model(base_model, lora_config)  # 470M → ~5M trainable
```

### 3. Gradient Checkpointing (for memory)
**Why:** 470M fusion model on T4 16GB
**Impact:** 60% less VRAM at 30% slower training
```python
model.gradient_checkpointing_enable()
```

### 4. torch.compile (for speed)
**Why:** 1.3x free speedup on PyTorch 2.0+
**Impact:** Phase B/C 30% faster
```python
model = torch.compile(model)
```

### 5. Weights & Biases (for experiment tracking)
**Why:** No way to compare runs, no error bars, no reproducibility
**Impact:** Publication-quality experiment management
```python
import wandb
wandb.init(project="laughter-prediction", config=config)
```

### 6. Acoustic Features from ACOUSTIC_FEATURES_RESEARCH.md
**Tier 1 (validated, cheap, NOT used):**
- F0 statistics (pitch) — librosa.pyin
- Pause duration — #1 most predictive feature per research
- Speech rate per word
- RMS energy statistics
- MFCC 1-13
- Spectral centroid/bandwidth/rolloff

**Why use these:** UR-FUNNY shows audio adds +3-5% to text model. Our WavLM training failed (F1=0.0). These handcrafted features are a proven fallback.

---

## REVISED TASK LIST (Incorporating ML Tools)

### Priority Order — What to Do Now:

| # | Task | Tool to Use | Why |
|---|------|-------------|-----|
| LP-1 | Run StandUp4AI baseline | Existing script + enable GPU | External benchmark both reviews demand |
| LP-2 | Add proper baselines | BiLSTM (torch), XLM-R-no-biosemotic | Orchestra demands non-trivial baselines |
| LP-3 | Multi-seed + error bars | wandb for tracking, scipy bootstrap | No error bars = reject |
| LP-4 | Remove RL section | Just edit markdown | Quick win, removes invalid content |
| LP-5 | Fix WavLM training | **Unsloth** + debug F1=0.0 | WavLM Phase A completely failed |
| LP-6 | Audio-only baseline | WavLM via **Unsloth** + Tier 1 acoustic features | Jenni demands this, fallback if SSL fails |
| LP-7 | Fused model | **LoRA** via PEFT + gradient checkpointing | 470M won't fit T4 without PEFT |
| LP-8 | Experiment tracking | **wandb** | All experiments need tracking |
| LP-9 | Update paper references | Just edit markdown | StandUp4AI, M2H2, FunnyNet-W |
| LP-10 | Fix novelty claims | Just edit markdown | Remove "first" claims |
| LP-11 | Teacher-refinement docs | Write methodology section | Negative result IS a contribution |
| LP-12 | Convert to LaTeX | Orchestra templates | Markdown ≠ submission format |

### New Tasks Added (From This Audit):
| # | Task | Why |
|---|------|-----|
| LP-13 | Install Unsloth + PEFT + wandb | Tooling needed for all future training |
| LP-14 | Extract Tier 1 acoustic features | Proven fallback when WavLM fails |
| LP-15 | Debug wavlm_v2_phaseA F1=0.0 | Complete failure needs root cause analysis |

---

## EXECUTION ORDER (A3M — Revised with Tools)

```
STEP 1: LP-4  — Remove RL section (edit only, 5 min)
STEP 2: LP-13 — Install Unsloth + PEFT + wandb (pip install, 5 min)
STEP 3: LP-1  — Run StandUp4AI baseline (GPU needed, ~30 min)
STEP 4: LP-15 — Debug WavLM F1=0.0 (investigate, 30 min)
STEP 5: LP-5  — Fix WavLM with Unsloth (train Phase A, ~1 hr)
STEP 6: LP-14 — Extract acoustic features (CPU, ~1 hr for 733K)
STEP 7: LP-6  — Audio-only baseline (WavLM + acoustic, ~2 hr)
STEP 8: LP-2  — Add BiLSTM + XLM-R-no-bio baselines (~2 hr)
STEP 9: LP-3  — Multi-seed runs with wandb (3-5 seeds × ~3 hr)
STEP 10: LP-7 — Fused model with LoRA (~4 hr)
STEP 11: LP-9/10/11 — Paper edits (1-2 days)
STEP 12: LP-12 — LaTeX conversion (1 day)
```

**Total estimated time: ~2 weeks to submission-ready**
