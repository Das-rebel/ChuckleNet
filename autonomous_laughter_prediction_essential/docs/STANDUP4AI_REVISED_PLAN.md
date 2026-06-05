# StandUp4AI + Laughter Detection - CORRECTED PLAN

## CURRENT STATUS

### What's Done
| Component | Status | Details |
|-----------|--------|---------|
| StandUp4AI Dataset | ✅ | Git cloned at `/tmp/standup4ai_dataset/` |
| Pre-labeled Examples | ✅ | 4 CSV files, 3,203 words, 17.6% laughter (O/L labels) |
| Transcripts (Local) | ⚠️ | 195 videos transcribed |
| Transcripts (Colab) | ⚠️ | ~170 videos processed |
| Laughter Detection | ❌ | NOT YET APPLIED |

### Languages in Dataset
| Language | Videos | Hours |
|---------|--------|-------|
| Spanish (es) | 1,375 | 77h |
| French (fr) | 652 | 86h |
| English (en) | 582 | 70h |
| Italian (it) | 567 | 55h |
| Portuguese (pt) | 245 | 23h |
| Czech (cs) | 123 | 12h |
| Hungarian (hu) | 73 | 11h |
| **TOTAL** | **3,617** | **334h** |

---

## CORRECTED PLAN

### PHASE 1: TRAIN ON EXISTING LABELS (IMMEDIATE)
**Use the 4 pre-labeled CSV files to train laughter detection model**

1. Convert StandUp4AI labeled CSVs → training format
2. Train XLM-R word-level model on 3,203 labeled words
3. Evaluate on held-out labeled examples
4. **Result**: Trained laughter detector ready to apply

### PHASE 2: TRANSCRIBE + APPLY MODEL (PARALLEL)
**Transcribe remaining videos and apply trained model**

1. Continue transcription (already ~170 videos done)
2. Apply trained laughter model to transcribed words
3. Generate predicted O/L labels for all transcripts
4. **Result**: Large dataset with predicted laugh labels

### PHASE 3: RETRAIN ON EXPANDED DATA
**Combine real labels + predicted labels**

1. Merge Phase 1 (real) + Phase 2 (predicted) training data
2. Retrain on expanded dataset
3. **Result**: Final model trained on more data

---

## KEY FILES

### Pre-labeled Data (USE FIRST)
```
/tmp/standup4ai_dataset/Examples_label/
├── -1FrUOEswOk.csv  (French, ~800 words)
├── 0g7nezWZyfY.csv  (English, ~800 words)
├── 1xvwYZwm8Ig.csv  (English, ~800 words)
└── 6JQzl2LlXbQ.csv  (Spanish, ~800 words)
```

Format: `text,timestamp,label` where label is:
- `L` = Laughter
- `O` = Outside (no laughter)

### Transcripts (ALREADY GENERATED)
```
/tmp/standup4ai_full/transcripts/   # 195 transcripts
/content/drive/MyDrive/standup4ai/transcripts/  # Colab output
```

---

## IMMEDIATE NEXT STEPS

### Step 1: Convert labeled CSVs to training format
```python
# Convert StandUp4AI CSV format to our JSONL format
# Input: text,timestamp,label (L/O)
# Output: {words: [], labels: [], language: '', ...}
```

### Step 2: Train on 3,203 labeled examples
- Use XLM-R base
- Word-level classification
- Evaluate with cross-validation

### Step 3: Apply to transcribed videos
- Use trained model to predict laugh labels on remaining ~170 transcribed videos
- Generate more training data

### Step 4: Continue transcription efficiently
- Focus on English (582 videos) first - matches existing en model
- Use batch processing to avoid Colab timeout

---

## COLAB NOTEBOOK
https://colab.research.google.com/gist/Das-rebel/0ddb26112af0d559bce0e2345f767762

---

## ESTIMATED TIMELINE

| Phase | Action | Time | Result |
|-------|--------|------|--------|
| 1 | Convert + Train on 3,203 labeled | 1 hour | Trained model |
| 2a | Apply model to 195 existing transcripts | 10 min | ~50K more words with predicted labels |
| 2b | Transcribe remaining (3,400 videos) | ~20 hours (Colab) | ~3M words |
| 3 | Retrain on full data | 2 hours | Final model |

**Total: ~24 hours with all 7 languages**

---

## RISKS

1. **Colab timeout** - 90 min limit; need checkpointing
2. **Language imbalance** - Spanish has 38% of data, English only 16%
3. **Transfer learning** - Model trained on 4 videos, applied to 3,617
4. **Quality** - Predicted labels vs real labels

---

## CRITICAL POINT

**Use the pre-labeled examples FIRST** before transcribing everything. The plan was backwards - it was transcribing first, then planning to train. The correct approach:

1. Train on 4 labeled videos (3,203 words)
2. Apply to remaining 3,613 videos
3. Evaluate on held-out labeled examples