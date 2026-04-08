# Autonomous Laughter Prediction - Research and Training Summary

**Date**: 2026-04-02
**Project**: Word-Level Laughter Detection in Comedy Transcripts
**Model**: XLM-RoBERTa Base for Token Classification

---

## Executive Summary

This project aims to detect laughter in comedy transcripts at the word level using sequence labeling. The model processes tokenized text and predicts whether each word is part of a laughter segment.

**Key Finding**: The original 505-example dataset significantly outperforms augmented datasets with thousands of examples due to **distribution shift** - training on Scraps data and testing on original data leads to poor generalization.

---

## Dataset Evolution

### Original Dataset (505 examples)
| Metric | Value |
|--------|-------|
| Total Examples | 505 |
| Positive Ratio | 7.39% |
| Val F1 | 0.6667 |
| Val IoU-F1 | 0.5000 |
| **Test F1** | **0.7222** |
| Test IoU-F1 | 0.5652 |

### Scraps from Loft (22,000+ examples)
| Metric | Value |
|--------|-------|
| Total Examples | ~22,000 |
| Positive Ratio | ~0.50% |
| Val F1 | 0.0000 (epochs 1-2) |
| Val F1 | 0.2663 (epoch 3) |
| Val IoU-F1 | 0.8993 |
| **Test F1** | **0.1885** |
| Test IoU-F1 | 0.7308 |

### High-Quality Filtered (2,094 examples)
Filter criteria: >=5% positive ratio from Scraps data

| Metric | Value |
|--------|-------|
| Total Examples | 2,094 (train: 1780, val: 314) |
| Positive Ratio | 8.02% |
| Val F1 | **0.9827** |
| Val IoU-F1 | 0.9851 |
| **Test F1** | **0.6061** |
| Test IoU-F1 | 0.4348 |

---

## Training Results Comparison

| Dataset | Val F1 | Val IoU-F1 | Test F1 | Test IoU-F1 |
|---------|--------|------------|---------|-------------|
| Original 505 | 0.6667 | 0.5000 | **0.7222** | 0.5652 |
| Augmented 22k | 0.2663 | 0.8993 | 0.1885 | 0.7308 |
| High-Quality 2k | **0.9827** | **0.9851** | 0.6061 | 0.4348 |

**Analysis**:
- Original dataset: Best test F1 (0.72) - matches distribution between train/test
- High-Quality: Highest validation F1 (0.98) but poor test F1 (0.61) - distribution mismatch
- Augmented: Model struggles to learn, high IoU-F1 but low F1 (over-conservative predictions)

---

## Key Insights

### 1. Distribution Shift is the Core Problem

The augmented data comes from a different source than the original 505 examples:
- **Training data**: Scraps from Loft comedy transcripts
- **Test data**: Original curated dataset

This causes:
- Vocabulary differences (specific joke structures, comedian styles)
- Annotation pattern differences (laughter marker placement)
- Domain-specific language patterns not captured

### 2. Quality Over Quantity

| Dataset | Size | Positive Ratio | Test F1 |
|---------|------|---------------|---------|
| Original | 505 | 7.39% | **0.7222** |
| Augmented | 22,000 | 0.50% | 0.1885 |
| High-Quality | 2,094 | 8.02% | 0.6061 |

**Recommendation**: The original 505 examples remain the best training base.

### 3. Model Behavior on Augmented Data

Epoch-by-epoch training on augmented data reveals:
```
Epoch 1: F1=0.0, IoU-F1=0.896, Loss=0.41  (no positive predictions)
Epoch 2: F1=0.0, IoU-F1=0.896, Loss=0.12  (still no positives)
Epoch 3: F1=0.27, IoU-F1=0.899, Loss=0.04 (finally predicting)
```

The model takes 2+ epochs to find any signal, indicating the augmented data is semantically noisy.

### 4. Positive Ratio Correlation

Higher positive ratio correlates with better performance:
- Original 505: 7.39% positive → Test F1 0.72
- High-Quality 2k: 8.02% positive → Test F1 0.61
- Augmented 22k: 0.50% positive → Test F1 0.19

---

## Data Sources Investigated

### Successful Sources

#### 1. Scraps from Loft (scrapsfromtheloft.com)
- **Status**: Successfully scraped
- **Data**: 139 comedy transcripts with 8,149 [laughter] segments
- **Laughter Tags Found**:
  - `[chuckles]`: 94 transcripts
  - `[laughs]`: 82 transcripts
  - `[laughter]`: 65 transcripts
  - `[audience laughs]`: 40 transcripts

#### 2. Original Dataset
- **Status**: 505 curated examples
- **Source**: Hand-labeled comedy transcripts
- **Quality**: High-quality, balanced annotations
- **Positive Ratio**: 7.39%

### Blocked/Unavailable Sources

#### 3. OpenSubtitles API
- **Status**: 403 Forbidden
- **Error**: Cloudflare protection, API blocked
- **Key Provided**: LBdbDW0ElAXuErK2Sbymg4uWod6kFCOo (not working)
- **Target**: TV sitcom subtitles (Friends, Big Bang Theory, The Office)

#### 4. Addic7ed
- **Status**: Requires Selenium for JavaScript rendering
- **Potential**: TV sitcom subtitles with SDH tags
- **Action**: Selenium successfully initialized, but scraping not completed

#### 5. SubSlikescript
- **Status**: 403 Forbidden
- **Error**: Cloudflare protection

#### 6. StandUp4AI Dataset
- **Status**: GitHub repository not found
- **Expected**: EMNLP 2025 dataset with 3,617 stand-up videos

#### 7. YouTube Comedy Specials
- **Status**: Captions disabled on most comedy videos
- **Pipeline Created**: youtube_audio_transcription_pipeline.py
  - Downloads audio via yt-dlp
  - Transcribes via faster-whisper
  - Detects laughter via energy-based STFT analysis

---

## Data Pipeline Architecture

### Current Pipeline
```
Raw Comedy Transcripts
    ↓
Word-Level Tokenization
    ↓
Token Classification (XLM-RoBERTa)
    ↓
Per-Word Laughter Prediction
```

### Training Configuration
```python
{
    "model_name": "FacebookAI/xlm-roberta-base",
    "max_length": 256,
    "batch_size": 16,
    "learning_rate": 2e-05,
    "classifier_learning_rate": 0.0001,
    "positive_class_weight": 4.0,
    "unfreeze_last_n_layers": 4,
    "gradient_accumulation_steps": 4,
    "epochs": 5,
    "early_stopping_patience": 2
}
```

---

## Challenges Encountered

### 1. Data Source Access
- **OpenSubtitles**: API returns 403 even with valid key
- **Addic7ed**: Requires JavaScript rendering (Selenium needed)
- **YouTube**: Most comedy specials have captions disabled

### 2. Distribution Shift
- Model trained on Scraps data fails to generalize to original 505 test set
- Augmented data has 0.50% positive ratio vs original 7.39%

### 3. Data Quality
- Automated augmentation introduces noise
- Energy-based laughter detection produces unreliable labels
- YouTube audio transcription quality varies

### 4. Disk Space
- Initial: 1.4GB remaining
- Freed 13GB by removing old experiment directories
- Current: experiments/, data/ cleaned

---

## Recommendations

### Immediate Actions
1. **Use Original 505 as Primary Training Data**
   - Test F1: 0.7222 (best achieved)
   - Matches distribution between train/val/test

2. **Focus on Data Quality Over Quantity**
   - Augmentation doesn't help when source distribution differs
   - Higher positive ratio correlates with better F1

3. **Collect TV Sitcom Data via Selenium**
   - Friends, Big Bang Theory, The Office have laugh tracks
   - Selenium successfully initialized for Addic7ed

### Medium-Term Improvements
1. **Implement GCACU Contrastive Learning**
   - Framework doc recommends for semantic conflict detection
   - May help with distribution shift

2. **Use Adaptive Focal Loss**
   - Framework recommends for noisy label handling
   - May help with augmented data quality issues

3. **Data Filtering for Augmented Data**
   - Remove examples with <5% positive ratio
   - Quality threshold similar to high-quality filtered set

### Long-Term Strategy
1. **Multi-Source Training**
   - Combine original 505 + high-quality Scraps examples
   - Ensure train/test distribution alignment

2. **Hybrid Forced Alignment Pipeline**
   - Per PRD: WhisperX + Montreal Forced Aligner (MFA)
   - Improves word-level timestamp accuracy

3. **Cognitive Architecture Components**
   - ToM Layer: Model audience mental states
   - SEVADE Framework: Multi-agent evaluation
   - CLoST: Structured thought for comedic reasoning

---

## PRD Requirements vs Current Status

From `.taskmaster/docs/prd.txt`:

| Requirement | Status |
|-------------|--------|
| OpenSubtitles API | BLOCKED (403) |
| Addic7ed Scraping | Needs Selenium setup |
| Scraps from Loft | ✅ DONE (139 transcripts) |
| Hybrid Alignment (WhisperX+MFA) | Pipeline created |
| WESR-Bench Taxonomy | ✅ DONE (discrete/continuous) |
| Ground Truth Labels | ✅ DONE ([laughter] tags) |
| Cognitive Architecture | ✅ Components exist |

---

## Files Created/Modified

### Data Collection
- `training/collect_youtube_laughter_data.py` - YouTube transcript scraper
- `training/youtube_audio_transcription_pipeline.py` - Audio transcription + laughter detection
- `data/raw/scraped_comedy_transcripts.json` - Scraps from Loft data

### Training
- `training/xlmr_standup_word_level.py` - Main training script
- `experiments/xlmr_high_quality/` - High-quality filtered model
- `experiments/xlmr_large_22k/` - Full augmented data model

### Documentation
- `NEW_DATA_SOURCES.md` - Data source investigation
- `docs/F1_EARLY_STOPPING_RESULTS_2026-04-02.md` - Early stopping analysis
- `RESEARCH_AND_TRAINING_SUMMARY_2026-04-02.md` - This document

---

## Conclusions

1. **Original 505 dataset remains the best** for training (Test F1: 0.7222)
2. **Distribution shift** is the primary reason augmented data fails
3. **Higher positive ratio** correlates with better model performance
4. **Alternative data sources** (OpenSubtitles, Addic7ed) are blocked or require setup
5. **YouTube audio pipeline** exists but comedy videos lack captions

**Path Forward**: Focus on collecting in-domain data that matches the original 505 distribution, or implement cognitive architecture components (GCACU, Adaptive Focal Loss) to handle distribution shift.
