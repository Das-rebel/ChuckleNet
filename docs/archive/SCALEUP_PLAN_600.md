# Scale-Up Plan: 71 → 600+ Videos

## Current State

| Resource | Count | Status |
|----------|-------|--------|
| Audio files | 780 (645 unique) | ✅ On Google Drive |
| Labeled utterances | 239K (626 videos) | ✅ Local |
| WavLM video-level | 589 files | ✅ Done |
| WavLM utterance-level | 71 files (15K utts) | ✅ Trained |
| **Gap** | **555 videos need utterance extraction** | ❌ To do |

## Target: Utterance-Level WavLM for All 645 Videos

### Step 1: Colab Extraction (2-3 hours)

**Notebook:** `Colab_WavLM_Utterance_Level.ipynb`
- Input: Audio from `chuckle_audio_all/` on Google Drive
- Output: `wavlm_utterance_embeddings.jsonl` on Google Drive
- Checkpoint: Every 50 videos for resume

**Process:**
1. Mount Google Drive
2. Load `utterances_clean.jsonl` (239K utterances)
3. Map video_id → audio file
4. For each utterance: extract 768-dim WavLM embedding
5. Save with labels

**Expected output:**
- ~200K utterances with embeddings
- ~4K positive (2% positive rate)

### Step 2: Download & Merge (10 min)

```bash
# Download from Drive
rclone copy gdrive:wavlm_utterance_embeddings.jsonl ./

# Count
wc -l wavlm_utterance_embeddings.jsonl
```

### Step 3: Train Fusion Model (1 hour CPU)

**Architecture:**
```
Text (XLM-R 768d) + Prosody (21d) + Audio (WavLM 768d)
     ↓                    ↓              ↓
  [Frozen]         [Train MLP]    [Train MLP]
     ↓                    ↓              ↓
  Concat → MLP(789→256→64→2) → Classification
```

**Training:**
- Train: ~160K utterances
- Val: ~20K utterances
- Test: Held-out 3 comedians (~5K utterances)

**Expected results:**
- Prosody-only: F1 ~0.63 (confirmed from prior)
- Text-only: F1 ~0.15 (overfits)
- **Fusion: F1 ~0.65+**

### Step 4: Validate & Submit

**Held-out comedian evaluation:**
- Bill Burr (BFIHCzw3itk)
- Dave Chappelle (BAD4askmGgk)  
- Russell Peters (1Nb3_os4RSA)

## Timeline

| Phase | Duration | Output |
|-------|----------|--------|
| 1. Colab Extraction | 2-3 hours | 200K embeddings on Drive |
| 2. Download & Merge | 10 min | Local JSONL |
| 3. Training | 1 hour | Model checkpoint |
| 4. Validation | 30 min | Final metrics |

**Total: ~5 hours**

## Commands

### Run Colab
1. Open: `https://colab.research.google.com/#notebookId=1lwbOs5xCZ1vghYh4VaA0CgNLjn8dFg1P`
2. Runtime → Run all
3. Monitor checkpoint at `gdrive:wavlm_utterance_checkpoint.json`

### Download Results
```bash
rclone copy gdrive:wavlm_utterance_embeddings.jsonl ./
rclone copy gdrive:wavlm_utterance_checkpoint.json ./
```

### Train
```bash
cd /Users/Subho/autonomous_laughter_prediction_essential/training
python3 train_fusion_expanded.py
```

## Expected Metrics

| Model | Val F1 | Holdout F1 | Notes |
|-------|---------|-------------|-------|
| Prosody-only | 0.63 | TBD | Baseline |
| Text-only | 0.15 | 0.15 | Overfits |
| **Fusion** | **0.65+** | **TBD** | **Target** |

## If Extraction Fails

If Colab times out, we have partial:
- 71 videos (15K utterances) with utterance-level WavLM
- Already trained model achieving F1=0.5865 on held-out

**Fallback:** Use video-level WavLM + utterance labels for training.
