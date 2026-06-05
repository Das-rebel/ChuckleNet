# Training Pipeline — Autonomous Laughter Prediction

**Project:** ChuckleNet
**Last Updated:** 2026-05-24
**Status:** Text-only pipeline working (F1=0.819). Audio fusion broken. Canonical path below.

---

## 1. Canonical Pipeline

The canonical path is **text-only XLM-R word-level sequence labeling**. Audio fusion (Phase 2/3 of `train_fusion_v3.py`) is broken — gate collapses to 1.0, audio learns nothing.

```
S1: Collect/verify raw data
    → data/audio_comedy/transcripts/{comedian}/*_transcript.json

S2: Convert to word-level training format
    → training/process_youtube_transcripts.py --comedian all
    → data/processed/combined/{train,val}.jsonl

S3: Train XLM-R word-level model
    → python3 training/train_xlmr_combined.py --epochs 3 --pos-weight 5.0 --unfreeze 4
    → experiments/xlmr_combined_pos5_uf4/best_model.pt

S4: Evaluate and extract metrics
    → experiments/xlmr_combined_pos5_uf4/training_summary.json

S5: (Optional) Run autonomous research loop
    → python3 training/run_xlmr_standup_pipeline.py --experiment-name {slug}
    (NOTE: run_xlmr_standup_pipeline.py is referenced in docs but NOT present in training/ — use train_xlmr_combined.py directly)

S6: (Optional) Multimodal fusion (BROKEN)
    → python3 training/train_fusion_v3.py --phase 1  (text-only baseline)
    → python3 training/train_fusion_v3.py --phase 2  (DOES NOT WORK — gate collapse)
    → python3 training/train_fusion_v3.py --phase 3  (DOES NOT WORK)
```

---

## 2. Scripts Reference

### Working Scripts

| Script | What It Does | Status |
|--------|--------------|--------|
| `training/train_xlmr_combined.py` | XLM-R word-level sequence labeling. Trains on `data/combined_multilingual/{train,valid,test}.jsonl`. Best result: F1=0.819 | ✅ Working |
| `training/train_fusion_v3.py` | 3-phase multimodal training (text + WavLM). Phase 1 text-only works. Phase 2+3 broken (gate collapse) | ⚠️ Phase 1 only |
| `training/process_youtube_transcripts.py` | Converts raw transcripts to word-level JSONL training format | ✅ Working |
| `training/refine_weak_labels_nemotron.py` | LLM-based label refinement using Ollama teacher. **BROKEN** — produces 0% laughter labels | ❌ Broken |
| `training/align_whisper_to_vtt.py` | Aligns VTT [laughter] markers to Whisper word timestamps | ✅ Working |
| `training/extract_prosody_v1.py` | Extracts F0/RMS/MFCC per word using librosa | ✅ Working |

### Missing Scripts (referenced but not present)

| Script | Reference | Status |
|--------|-----------|--------|
| `convert_standup_raw_to_word_level.py` | AGENTS.md | ❌ NOT FOUND |
| `run_xlmr_standup_pipeline.py` | docs/RESEARCH_LOOP.md | ❌ NOT FOUND |
| `autonomous_research_loop.py` | AGENTS.md | ❌ NOT FOUND |
| `xlmr_standup_word_level.py` | CHECKLIST_INDIAN_COMEDY.md | ❌ NOT FOUND |

**Workaround:** Use `train_xlmr_combined.py` directly for all XLM-R training.

---

## 3. Data Format

Training data at `data/processed/combined/train.jsonl` and `data/combined_multilingual/train.jsonl`:

```json
{"words": ["I", "went", "to", "the", "store"], "labels": [0, 0, 1, 0, 0], "language": "en", "total_words": 5}
```

- `words`: list of word tokens
- `labels`: list of 0/1 per word (1 = audience laughter within ±5s window)
- `language`: `en` | `zh` | `hi-latn` | `bn` | `fr` | `es`
- `total_words`: count of words in example

---

## 4. How to Run

### Full Text-Only Training

```bash
cd ~/autonomous_laughter_prediction

# S2: Convert transcripts to training format
python3 training/process_youtube_transcripts.py --comedian all

# S3: Train XLM-R word-level
python3 training/train_xlmr_combined.py \
  --epochs 3 \
  --batch-size 16 \
  --lr 5e-5 \
  --pos-weight 5.0 \
  --unfreeze 4 \
  --max-length 128 \
  --output-dir experiments/xlmr_combined_pos5_uf4

# S4: Check results
cat experiments/xlmr_combined_pos5_uf4/training_summary.json | jq '{best_val_f1, final_test_f1}'
```

### Resume Interrupted Training

```bash
# train_xlmr_combined.py doesn't have --resume. Restart with same output-dir.
# Checkpoints are NOT saved mid-epoch — restart from epoch 1.
# Best model is saved at experiments/xlmr_combined_pos5_uf4/best_model.pt

# To resume from a specific checkpoint:
python3 training/train_xlmr_combined.py \
  --epochs 5 \
  --pos-weight 5.0 \
  --unfreeze 4 \
  --output-dir experiments/xlmr_combined_pos5_uf4  # Same dir, overwrites best_model.pt
```

### Fusion Training (Phase 1 only — text-only baseline)

```bash
python3 training/train_fusion_v3.py \
  --phase 1 \
  --epochs 5 \
  --batch-size 16 \
  --utterances data/audio_comedy/aligned_utterances.jsonl \
  --embeddings data/audio_comedy/wavlm_utterance_embeddings.pt \
  --output-dir experiments/fusion_v3_phase1

# Resume fusion:
python3 training/train_fusion_v3.py \
  --phase 1 \
  --resume experiments/fusion_v3_phase1/phase1_best.pt \
  --epochs 5
```

---

## 5. Output Directories

| Directory | Contents | Notes |
|----------|----------|-------|
| `experiments/xlmr_combined_pos5_uf4/` | `best_model.pt` (270MB XLM-R weights), `training_summary.json` | Current best: F1=0.819 |
| `experiments/xlmr_standup_baseline_weak_pos5/` | Promoted baseline checkpoint (F1=0.819 test) | Not in Git |
| `experiments/fusion_v3_phase1/` | Phase 1 fusion checkpoint | Text-only |
| `experiments/fusion_v3_phase1_68k/` | 68K utterances expansion run | Phase 1 text-only, PID 80455 |
| `experiments/aligned_xlmr_v1/` | Aligned XLM-R variant | |
| `experiments/wavlm_v2_phaseA/` | WavLM audio-only (F1=0.0 broken) | Do not use |
| `data/processed/combined/` | `{train,val}.jsonl` — primary training data | 15K examples, 32.6% positive |
| `data/combined_multilingual/` | `{train,valid,test}.jsonl` — XLM-R training split | |
| `data/audio_comedy/aligned_utterances.jsonl` | Utterance-level with timestamps | 15,060 utterances |
| `data/audio_comedy/aligned_segments.jsonl` | Word-level segments | 549,334 segments |

---

## 6. Key Metrics

| Model | Val F1 | Test F1 | IoU-F1 | Notes |
|-------|--------|---------|--------|-------|
| XLM-R text-only (best) | 0.819 | 0.819 | 0.880 | Current ceiling |
| TF-IDF baseline | — | 0.73 | — | Valid lower bound |
| Audio prosody (49 feat) | — | 0.29 | — | Floor, not ceiling |
| WavLM audio-only | — | 0.0 | — | Broken, do not use |
| Phase 2 fusion gate | — | — | — | Gate → 1.0, audio learns nothing |

---

## 7. Colab Execution

Colab notebook for audio/WavLM extraction:
**https://colab.research.google.com/gist/Das-rebel/10b79eddcf2dce5ec4ff298ec3a46b0d**

WavLM embedding extraction requires GPU — run in Colab with T4 or higher.
Extract to `data/audio_comedy/wavlm_utterance_embeddings.pt` (~4.6GB).

For text-only training, local Mac/Linux is sufficient:

```bash
# Mac with MPS (M1/M2/M3):
python3 training/train_xlmr_combined.py --epochs 3 --pos-weight 5.0

# Linux with CUDA:
python3 training/train_xlmr_combined.py --epochs 3 --pos-weight 5.0 --device cuda
```

---

## 8. Common Errors and Fixes

### "0% laughter in refined labels" (refine_weak_labels_nemotron.py)

**Symptom:** Teacher model assigns 0% positive labels to all examples.
**Root cause:** Parsing bug in `refine_weak_labels_nemotron.py` — labels not matched correctly to words.
**Fix:** Do not use teacher refinement. Use raw weak labels with `pos_weight=5.0` instead.

```
# Don't do this:
python3 training/refine_weak_labels_nemotron.py --input data/processed/combined/train.jsonl --output train_refined.jsonl

# Do this instead:
python3 training/train_xlmr_combined.py --epochs 3 --pos-weight 5.0  # uses raw labels
```

### "Gate mean = 1.0" in fusion training (train_fusion_v3.py Phase 2/3)

**Symptom:** Fusion gate collapses to 1.0 — audio branch never learns.
**Root cause:** Audio embeddings are either misaligned or too noisy relative to text.
**Fix:** Do not use Phase 2/3. Text-only (Phase 1) is the ceiling.

### "No module named 'whisper'" / "faster_whisper not found"

**Fix:**
```bash
pip install openai-whisper   # or
pip install faster-whisper
```

### "CUDA out of memory" during XLM-R training

**Fix:** Reduce batch size and max_length:
```bash
python3 training/train_xlmr_combined.py --batch-size 8 --max-length 64
```

### "File not found: aligned_utterances.jsonl"

**Fix:** Run alignment first:
```bash
python3 training/align_whisper_to_vtt.py  # align VTT markers to Whisper timestamps
python3 training/align_utterances.py       # split into utterances
```

### "Module not found" in train_fusion_v3.py

**Fix:** Run from project root AND add training/ to path:
```bash
cd ~/autonomous_laughter_prediction
export PYTHONPATH="$PWD:$PWD/training"
python3 training/train_fusion_v3.py --phase 1
```

---

## 9. Quick Reference Card

```bash
# 1. Check data exists
wc -l data/processed/combined/train.jsonl

# 2. Train XLM-R (canonical run)
python3 training/train_xlmr_combined.py --epochs 3 --pos-weight 5.0 --unfreeze 4

# 3. Check results
cat experiments/xlmr_combined_pos5_uf4/training_summary.json | jq '.final_test'

# 4. Run fusion phase 1 (text-only baseline)
python3 training/train_fusion_v3.py --phase 1 --epochs 5

# 5. Extract prosody features (requires audio files)
python3 training/extract_prosody_v1.py --input data/audio_comedy/transcripts --output data/processed/prosody_features.jsonl

# 6. Colab WavLM extraction
# Open: https://colab.research.google.com/gist/Das-rebel/10b79eddcf2dce5ec4ff298ec3a46b0d
```

---

## 10. Known Issues Summary

| Issue | Severity | Workaround |
|-------|----------|------------|
| `refine_weak_labels_nemotron.py` broken | 🔴 Critical | Use raw labels with pos_weight=5.0 |
| Phase 2/3 fusion broken (gate collapse) | 🔴 Critical | Use text-only XLM-R instead |
| `run_xlmr_standup_pipeline.py` missing | 🟡 Medium | Use `train_xlmr_combined.py` directly |
| `autonomous_research_loop.py` missing | 🟡 Medium | Run experiments manually |
| WavLM embeddings require Colab GPU | 🟡 Medium | Use text-only pipeline on local hardware |
| Hindi data too small (48 examples) | 🟡 Medium | Do not trust Hindi F1 (0.68 statistically thin) |
| Gate collapse in fusion | 🔴 Critical | Audio signal is diffuse at word-level — laughter is supra-segmental |

---

*Last verified: 2026-05-24*
*Canonical path: `train_xlmr_combined.py` with pos_weight=5.0, unfreeze=4*