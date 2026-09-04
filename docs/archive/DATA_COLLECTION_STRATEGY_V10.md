# Data Collection Strategy v1.0 - Hindi Expansion, Chinese Test Set, and 7-Language StandUp4AI
**Version**: 1.0
**Status**: APPROVED
**Date**: 2026-05-05
**Project**: autonomous_laughter_prediction_essential

---

## Executive Summary

This document details the complete data collection strategy for expanding the laughter prediction dataset. The strategy addresses three critical gaps identified in the May 2026 audits:

1. **Hindi Expansion**: 48 examples (0.5%) → 4,000 examples (40% of dataset)
2. **Chinese Test Set**: 0 examples → 500 examples with verified labels
3. **StandUp4AI 7-Language Processing**: 4 videos (3,203 words) → 700+ videos (~1.5M words)

**Timeline**: 12 weeks
**Total Effort**: ~120 hours human work + ~100 hours Colab compute
**Success Criteria**: All targets met with verified quality

---

## Part 1: Hindi/Hinglish Expansion (48 → 4,000 examples)

### Current State

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Hindi examples | 48 | 4,000 | -3,952 |
| Hindi % of dataset | 0.5% | 40% | -39.5% |
| Laughter rate | 0% (missing) | 35-40% | -35-40% |
| Manual annotation | 48 words | 4,000 words | -3,952 |
| Comedians | 1 (Vir Das) | 10+ | -9 |

**Source**: HINDI_SCALING_STRATEGY.md (2026-05-02)

### Target Distribution

| Language | Training | Validation | Test | Total |
|----------|----------|------------|------|-------|
| English | 18,000 | 4,124 | 4,124 | 26,248 |
| Chinese | 8,000 | 500 | 500 | 9,000 |
| **Hindi/Hinglish** | **3,500** | **250** | **250** | **4,000** |
| Spanish | 1,500 | 100 | 100 | 1,700 |
| French | 1,000 | 100 | 100 | 1,200 |
| Italian | 750 | 75 | 75 | 900 |
| Portuguese | 400 | 50 | 50 | 500 |
| Czech | 200 | 25 | 25 | 250 |
| Hungarian | 150 | 15 | 15 | 180 |
| **TOTAL** | **~33,500** | **~5,000** | **~5,000** | **~44,000** |

---

### Phase H1: Quick Wins (Week 1) - 548 examples

#### Task H1.1: Manual Annotation of Vir Das Videos (48 examples → 48 verified)
**Owner**: Research Team
**Time**: 2 hours
**Input**: `/Users/Subho/autonomous_laughter_prediction/data/processed/indian_ufHrTI_E4Kk.jsonl`

**Process**:
1. Load 48 examples from existing Vir Das collection
2. Each example: listen to audio, mark laughter trigger word
3. Assign `label=1` to trigger word, `label=0` to others
4. Convert to JSONL with word-level timestamps

**Output Format**:
```jsonl
{"words": ["The", "one", "thing", ...], "labels": [0, 0, 1, ...], "language": "hi-latn", "source": "vir_das_manual", "comedian": "Vir Das"}
```

**Expected Output**: 48 examples with verified laughter labels, ~40% laughter rate

**Quality Control**: Double-annotate 10 examples, require 90% agreement

**Success Metric**: 48 examples with <5% label error rate

---

#### Task H1.2: Generate 500 Synthetic Hindi Examples (Phase 1)
**Owner**: Research Team (Ollama/Nemotron)
**Time**: 1 hour
**Model**: `qwen2.5-coder:1.5b` via Ollama

**Prompt Template**:
```
Generate 50 Hindi/Hinglish comedy examples for laughter prediction.

Each example should:
1. Be 15-25 words of stand-up comedy text
2. Contain clear setup + punchline structure
3. Have exactly ONE trigger word marked with [LAUGHTER]
4. Include comedian style indicator

Format as JSON array:
[
  {
    "text": "setup text [LAUGHTER] punchline continues",
    "comedian_style": "zakir_khan",
    "language": "hi-latn"
  },
  ...
]

Generate NOW.
```

**Generation Parameters**:
- Temperature: 0.7
- Top-p: 0.9
- Batch size: 50 per call
- Total: 10 calls = 500 examples

**Output File**: `data/hindi/synthetic_hindi_phase1_500.jsonl`

**Success Metric**: 500 examples generated, 90% parseable

---

#### Task H1.3: Validate Synthetic Examples Quality
**Owner**: Research Team
**Time**: 2 hours
**Input**: `data/hindi/synthetic_hindi_phase1_500.jsonl`

**Validation Checks**:
1. Format check: All fields present (text, style, language)
2. Length check: 15-25 words
3. Laughter marker: Exactly one [LAUGHTER] per example
4. Language check: Hindi or Hinglish (not pure English)
5. Content check: Actual comedy content (not random)

**Quality Rejection Criteria**:
- No [LAUGHTER] marker: Reject
- Multiple [LAUGHTER] markers: Reject
- Pure English text: Reject
- Non-comedy content: Reject
- <10 words or >30 words: Reject

**Expected Output**: ~450 accepted, ~50 rejected (90% acceptance rate)

**Success Metric**: 450+ valid examples with verified format

---

### Phase H2: Scale Up (Weeks 2-3) - 2,500 examples

#### Task H1.4: Generate 2,000 Synthetic Examples (Phases 2-3)
**Owner**: Research Team (Ollama)
**Time**: 4 hours (8 calls × 250 examples)
**Input**: Comedy style targets from HINDI_SCALING_STRATEGY.md

**Distribution by Style**:
| Style | Comedian | Count | Prompt Focus |
|-------|----------|-------|---------------|
| Observational | Zakir Khan | 500 | Indian life, relationships |
| Sardonic | Biswa Kalyan Rath | 500 | Self-deprecating, intellectual |
| Physical | Kaneez Surka | 250 | Situational comedy |
| Wordplay | Atul Khatri | 250 | Language humor |
| Dark | Kunal Kamra | 250 | Social commentary |
| Romantic | Aditi Mittal | 250 | Dating, relationships |

**Output File**: `data/hindi/synthetic_hindi_phase2_2000.jsonl`

**Success Metric**: 1,800+ valid examples across all styles

---

#### Task H1.5: Extract Podcast Comedy Content
**Owner**: Research Team
**Time**: 4 hours
**Sources**:
1. **The Ranveer Show** (comedy episodes) - ~500 words
2. **Aisi Taisi Democracy** (satire) - ~300 words
3. **TVF Pitchers** (comedy) - ~200 words

**Process**:
1. Download podcast audio (YouTube available)
2. Transcribe with Whisper (`openai-whisper`)
3. Identify comedy segments manually
4. Mark laughter triggers (listen and label)
5. Convert to word-level JSONL

**Whisper Command**:
```bash
python -m whisper --model medium --language hi \
  --output_format json \
  --input podcast_audio.mp3 \
  --output data/hindi/podcasts/
```

**Manual Annotation Interface**:
```python
def annotate_laughter_transcript(transcript_json, audio_path):
    """
    Display transcript with audio playback.
    User clicks on word where laughter starts.
    Returns: list of (word_index, label) tuples.
    """
```

**Output File**: `data/hindi/podcasts_annotated_1000.jsonl`

**Success Metric**: ~40 examples (average 25 words each) from 1,000 words

---

#### Task H1.6: Weak Label Generation for Podcast Content
**Owner**: Research Team
**Time**: 3 hours
**Input**: Additional 500 words from podcasts (less confident segments)

**Weak Labeling Heuristics**:
1. **Punctuation**: Words before "!" or "?" have 60% laughter probability
2. **Setup-punchline structure**: Last 3 words of sentence after "but" or "so"
3. **Topic shift**: First word after "anyway" or "moving on"
4. **Audience proxy**: Words followed by silence (pause detection)

**Implementation**:
```python
def weak_label_podcasts(transcript):
    labels = []
    for i, word in enumerate(transcript['words']):
        # Punctuation heuristic
        if word['text'].endswith(('!', '?')):
            labels.append(1)  # Likely laugh trigger
        # Setup-punchline heuristic
        elif i > 0 and transcript['words'][i-1]['text'] in ('but', 'so', 'then'):
            labels.append(1)
        else:
            labels.append(0)
    return labels
```

**Output File**: `data/hindi/podcasts_weak_500.jsonl`

**Success Metric**: 500 examples with heuristic labels

---

### Phase H3: Target Achievement (Week 4) - 1,000 examples

#### Task H1.7: Final Synthetic Generation (500 examples)
**Owner**: Research Team (Ollama)
**Time**: 1 hour
**Focus**: Mixed styles, harder comedy patterns

**Target Patterns**:
- Callback humor (reference to earlier jokes)
- Self-deprecating humor
- Observational comedy about Indian culture
- Wordplay in Hinglish

**Output File**: `data/hindi/synthetic_hindi_phase3_500.jsonl`

---

#### Task H1.8: Semi-Supervised Refinement
**Owner**: Research Team
**Time**: 4 hours
**Input**: All 3,000+ synthetic + manual examples

**Process**:
1. Train initial model on manual examples (48)
2. Predict on synthetic examples
3. Keep predictions with confidence > 0.8
4. Add to training set
5. Retrain
6. Repeat 3 times

**Implementation**:
```python
def semi_supervised_refine(dataset, initial_examples, iterations=3):
    """
    Iterative self-training with confidence threshold.
    """
    model = train_supervised(initial_examples)
    
    for i in range(iterations):
        # Predict on full dataset
        predictions = model.predict(dataset)
        
        # High confidence subset
        high_conf = [p for p in predictions if p.confidence > 0.8]
        
        # Add to training
        initial_examples.extend(high_conf)
        model = train_supervised(initial_examples)
    
    return model
```

**Output**: Refined dataset with ~3,500 examples

---

#### Task H1.9: Quality Control Final Review
**Owner**: Research Team
**Time**: 2 hours
**Input**: Final Hindi dataset (~4,000 examples)

**Checks**:
1. Laughter rate: 35-40% (adjust if needed)
2. Word count distribution: Mean 20±10 words
3. Language distribution: 70% Hinglish, 30% Hindi
4. Style diversity: All 6 styles represented
5. Duplicate detection: Remove near-duplicates

**Validation Commands**:
```bash
python training/validate_hindi_dataset.py \
  --input data/hindi/final_4000.jsonl \
  --expected_laughter_rate 0.37 \
  --expected_size 4000
```

**Success Metric**: Dataset passes all QC checks

---

### Hindi Summary

| Phase | Source | Examples | Laughter Rate | Time | Total |
|-------|--------|----------|---------------|------|-------|
| H1.1 | Manual (Vir Das) | 48 | 40% | 2h | 48 |
| H1.2 | Synthetic Phase 1 | 450 | 40% | 3h | 498 |
| H1.4 | Synthetic Phase 2-3 | 1,800 | 40% | 4h | 2,298 |
| H1.5 | Podcast (manual) | 40 | 35% | 4h | 2,338 |
| H1.6 | Podcast (weak) | 500 | 35% | 3h | 2,838 |
| H1.7 | Synthetic Phase 3 | 450 | 40% | 1h | 3,288 |
| H1.8 | Semi-supervised | +500 | 37% | 4h | 3,788 |
| H1.9 | QC + balance | +212 | 37% | 2h | **4,000** |

**Hindi Total**: 4,000 examples, ~28 hours human work

---

## Part 2: Chinese Test Set Creation (0 → 500 examples)

### Current State

| Metric | Current | Target |
|--------|---------|--------|
| Chinese test examples | 0 | 500 |
| Chinese validation examples | ~100 | 500 |
| Chinese training examples | ~2,051 | 8,000 |

**Source**: STATUS_REPORT_2026_05_04.md (Chinese has 0 test examples)

### Problem

The V8.1 dataset splits Chinese data into train/val/test but the test set is not properly held out or documented. We need a proper 500-example Chinese test set with verified labels.

### Task C1: Identify Chinese Data Sources
**Owner**: Research Team
**Time**: 1 hour
**Sources**:
1. V8.1 Chinese training data - extract 500 for test
2. StandUp4AI Chinese videos (if any)

**Data Path**: `data/v8_1_final/` - Contains `train.jsonl`, `valid.jsonl`, `test.jsonl`

**Verify Chinese Split**:
```bash
python -c "
import json
with open('data/v8_1_final/test.jsonl') as f:
    zh = [json.loads(l) for l in f if json.loads(l).get('language') == 'zh']
print(f'Chinese in test: {len(zh)}')
"
```

**Expected**: May need to re-split if Chinese test is empty or too small

---

### Task C2: Label Quality Verification for Chinese Test Set
**Owner**: Research Team (Chinese speaker preferred)
**Time**: 6 hours
**Input**: 500 Chinese examples

**Label Types in V8.1**:
- **Weak labels**: Extracted from transcript markers (may have noise)
- **Synthetic labels**: Generated by LLM (verified format)

**Verification Process**:
1. For each example, review word-level labels
2. Check that laughter triggers are reasonable for Chinese comedy
3. Mark problematic examples for removal or correction
4. Target: 95% label accuracy

**Quality Criteria**:
- Laughter trigger in reasonable position (not first word)
- Context makes sense (setup-punchline structure)
- Chinese text is natural (not obviously translated)

**Output**: Verified Chinese test set with quality scores

---

### Task C3: Add Chinese to StandUp4AI Transcription Queue
**Owner**: Research Team (Colab)
**Time**: 8 hours
**Scope**: 100 Chinese StandUp4AI videos

**Note**: StandUp4AI primarily has European languages. Chinese videos may be limited.

**Check StandUp4AI Languages**:
```bash
python -c "
import os
# Count videos by language prefix in directory names or metadata
langs = {}
for f in os.listdir('/tmp/standup4ai_dataset/videos/'):
    # Extract language from filename or metadata
    pass
"
```

**If Chinese videos exist**: Transcribe 100 videos
**If not**: Use existing V8.1 Chinese data only

---

### Chinese Summary

| Task | Action | Examples | Time |
|------|--------|----------|------|
| C1 | Identify sources | 500 | 1h |
| C2 | Label verification | 500 | 6h |
| C3 | StandUp4AI (if available) | 100 | 8h |
| **Total** | | **~500-600** | **15h** |

---

## Part 3: StandUp4AI 7-Language Processing

### Current State

| Metric | Value | Source |
|--------|-------|--------|
| Total videos | 3,617 | StandUp4AI docs |
| Total hours | 334h | StandUp4AI docs |
| Pre-labeled videos | 4 | Examples_label/ |
| Pre-labeled words | 3,203 | 4 CSVs |
| Transcribed locally | 195 | /tmp/standup4ai_full/ |
| Processed data dir | MISSING | Must create |

**Source**: STANDUP4AI_REVISED_PLAN.md (2026-05-04)

### Language Distribution

| Language | Code | Videos | Hours | Pre-labeled | Our Priority |
|----------|------|--------|-------|-------------|---------------|
| Spanish | es | 1,375 | 77h | No | 🔴 HIGH |
| French | fr | 652 | 86h | Yes (1 CSV) | 🔴 HIGH |
| English | en | 582 | 70h | Yes (2 CSVs) | 🔴 HIGH |
| Italian | it | 567 | 55h | No | 🟡 MEDIUM |
| Portuguese | pt | 245 | 23h | No | 🟡 MEDIUM |
| Czech | cs | 123 | 12h | No | 🟢 LOW |
| Hungarian | hu | 73 | 11h | No | 🟢 LOW |

---

### Phase S1: Pre-labeled Data Processing (Week 1-2)

#### Task S1.1: Convert StandUp4AI CSV to Training Format
**Owner**: Research Team
**Time**: 2 hours
**Input**: `/tmp/standup4ai_dataset/Examples_label/`

**CSV Files**:
```
/tmp/standup4ai_dataset/Examples_label/
├── -1FrUOEswOk.csv  (French, ~800 words, video ID: -1FrUOEswOk)
├── 0g7nezWZyfY.csv  (English, ~800 words, video ID: 0g7nezWZyfY)
├── 1xvwYZwm8Ig.csv  (English, ~800 words, video ID: 1xvwYZwm8Ig)
└── 6JQzl2LlXbQ.csv  (Spanish, ~800 words, video ID: 6JQzl2LlXbQ)
```

**CSV Format**:
```csv
text,timestamp,label
"por",[19.624, 19.824],O
"qué",[19.824, 20.024],L
"seas",[20.024, 20.224],O
```

**Conversion Script**:
```python
def convert_standup4ai_csv(csv_path, video_id):
    """Convert StandUp4AI CSV to training JSONL"""
    df = pd.read_csv(csv_path)
    
    # Group consecutive same-label words
    words = []
    labels = []
    current_words = []
    current_label = None
    
    for _, row in df.iterrows():
        word = row['text']
        label = 1 if row['label'] == 'L' else 0
        
        if label == current_label:
            current_words.append(word)
        else:
            if current_words:
                words.append(current_words)
                labels.append(current_label)
            current_words = [word]
            current_label = label
    
    # Last group
    if current_words:
        words.append(current_words)
        labels.append(current_label)
    
    return {
        'video_id': video_id,
        'language': detect_language(csv_path),
        'words': words,
        'labels': labels,
        'source': 'standup4ai_labeled'
    }
```

**Output Files**:
- `data/standup4ai/labeled/en_0g7nezWZyfY.jsonl`
- `data/standup4ai/labeled/en_1xvwYZwm8Ig.jsonl`
- `data/standup4ai/labeled/fr_-1FrUOEswOk.jsonl`
- `data/standup4ai/labeled/es_6JQzl2LlXbQ.jsonl`

**Total Output**: ~3,203 words across 4 videos

---

#### Task S1.2: Train Baseline Model on Pre-labeled Data
**Owner**: Research Team
**Time**: 4 hours
**Input**: 3,203 words from Task S1.1

**Command**:
```bash
cd /Users/Subho/autonomous_laughter_prediction_essential
python training/rl_laughter_trainer.py \
  --phase 1 \
  --base_model FacebookAI/xlm-roberta-base \
  --data data/standup4ai/labeled/ \
  --output experiments/standup4ai_baseline \
  --epochs 10 \
  --batch_size 8 \
  --learning_rate 2e-5
```

**Expected Results**:
- Val F1 >= 0.70 (on held-out 20%)
- Trained model for applying to untranscribed videos

**Success Metric**: Model trained, ready for inference

---

### Phase S2: Transcription Infrastructure (Week 2-3)

#### Task S2.1: Set Up Whisper Batch Transcription
**Owner**: Research Team (Colab)
**Time**: 4 hours
**File**: `training/transcribe_standup4ai_batch.py`

**Architecture**:
```python
class StandUp4AITranscriber:
    """
    Batch transcription for StandUp4AI videos.
    
    1. Download video from YouTube (yt-dlp)
    2. Extract audio (ffmpeg)
    3. Transcribe with Whisper (word-level timestamps)
    4. Save JSON with timestamps
    """
    
    def __init__(self, output_dir, language):
        self.output_dir = output_dir
        self.language = language
        self.whisper_model = load_whisper('medium')
        
    def transcribe_video(self, video_id, video_url):
        """Transcribe single video with word-level timestamps"""
        # Download
        audio_path = self.download(video_id, video_url)
        
        # Transcribe
        result = self.whisper_model.transcribe(
            audio_path,
            word_timestamps=True,
            language=self.language
        )
        
        # Save
        output_path = f"{self.output_dir}/{video_id}.json"
        with open(output_path, 'w') as f:
            json.dump(result, f)
            
        return output_path
    
    def batch_transcribe(self, video_ids, max_workers=4):
        """Transcribe multiple videos with parallel workers"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.transcribe_video, vid) 
                       for vid in video_ids]
            return [f.result() for f in futures]
```

**Colab Integration**:
- Save to Google Drive: `/content/drive/MyDrive/standup4ai/transcripts/`
- Checkpoint every 100 videos to avoid timeout loss

---

#### Task S2.2: Create Video ID Lists by Language
**Owner**: Research Team
**Time**: 1 hour
**Input**: `/tmp/standup4ai_dataset/` (StandUp4AI dataset directory)

**Process**:
```python
# Extract video IDs for each language
# Based on directory structure or metadata files

language_video_ids = {
    'es': [],  # Spanish - 1,375 videos
    'fr': [],  # French - 652 videos
    'en': [],  # English - 582 videos
    'it': [],  # Italian - 567 videos
    'pt': [],  # Portuguese - 245 videos
    'cs': [],  # Czech - 123 videos
    'hu': [],  # Hungarian - 73 videos
}
```

**Output Files**:
- `data/standup4ai/video_ids/es_video_ids.txt` (1,375 lines)
- `data/standup4ai/video_ids/fr_video_ids.txt` (652 lines)
- etc.

---

### Phase S3: Batch Transcription (Weeks 3-6)

#### Task S3.1: Batch 1 - English + French (200 videos)
**Owner**: Research Team (Colab)
**Time**: 12 hours Colab compute
**Output**: `data/standup4ai/transcripts_batch1/` (~1M words)

**Commands**:
```bash
# In Colab
python training/transcribe_standup4ai_batch.py \
  --language en \
  --video_ids data/standup4ai/video_ids/en_video_ids.txt \
  --max_videos 100 \
  --output data/standup4ai/transcripts/en/ \
  --checkpoint_every 50

python training/transcribe_standup4ai_batch.py \
  --language fr \
  --video_ids data/standup4ai/video_ids/fr_video_ids.txt \
  --max_videos 100 \
  --output data/standup4ai/transcripts/fr/ \
  --checkpoint_every 50
```

**Checkpoint Strategy**:
- Save progress every 50 videos
- On timeout, resume from last checkpoint
- Store checkpoints in Google Drive

**Success Metric**: 200 videos transcribed, no data loss (checkpoints verified)

---

#### Task S3.2: Batch 2 - Spanish + Italian (300 videos)
**Owner**: Research Team (Colab)
**Time**: 12 hours
**Scope**: 175 Spanish + 125 Italian

**Commands**:
```bash
python training/transcribe_standup4ai_batch.py \
  --language es \
  --video_ids data/standup4ai/video_ids/es_video_ids.txt \
  --max_videos 175 \
  --output data/standup4ai/transcripts/es/ \
  --checkpoint_every 50

python training/transcribe_standup4ai_batch.py \
  --language it \
  --video_ids data/standup4ai/video_ids/it_video_ids.txt \
  --max_videos 125 \
  --output data/standup4ai/transcripts/it/ \
  --checkpoint_every 50
```

---

#### Task S3.3: Batch 3 - Portuguese + Czech + Hungarian (200 videos)
**Owner**: Research Team (Colab)
**Time**: 8 hours
**Scope**: 100 Portuguese + 60 Czech + 40 Hungarian

**Commands**:
```bash
python training/transcribe_standup4ai_batch.py \
  --language pt \
  --max_videos 100 \
  --output data/standup4ai/transcripts/pt/

python training/transcribe_standup4ai_batch.py \
  --language cs \
  --max_videos 60 \
  --output data/standup4ai/transcripts/cs/

python training/transcribe_standup4ai_batch.py \
  --language hu \
  --max_videos 40 \
  --output data/standup4ai/transcripts/hu/
```

---

#### Task S3.4: Apply Laughter Model to All Transcribed Data
**Owner**: Research Team
**Time**: 4 hours
**Input**: `data/standup4ai/transcripts_batch{1,2,3}/`
**Model**: `experiments/standup4ai_baseline/` (from Task S1.2)

**Command**:
```bash
python training/apply_laughter_model.py \
  --model experiments/standup4ai_baseline/best_model \
  --input data/standup4ai/transcripts_batch1/ \
  --input data/standup4ai/transcripts_batch2/ \
  --input data/standup4ai/transcripts_batch3/ \
  --output data/standup4ai_processed/all_with_labels.jsonl \
  --batch_size 16
```

**Output Format**:
```jsonl
{"video_id": "abc123", "language": "es", "words": [...], "predicted_labels": [...], "confidence": [...], "source": "standup4ai_transcribed"}
```

**Expected Output**: ~700 videos, ~1.5M words with predicted labels

---

### Phase S4: Retrain on Expanded Data (Weeks 6-7)

#### Task S4.1: Combine Real Labels + Predicted Labels
**Owner**: Research Team
**Time**: 1 hour
**Input**:
1. Real labels: `data/standup4ai/labeled/` (3,203 words from 4 videos)
2. Predicted labels: `data/standup4ai_processed/all_with_labels.jsonl` (~1.5M words)

**Merged Dataset**:
```python
def merge_datasets(real_labels_path, predicted_labels_path, output_path):
    """
    Merge real and predicted labels.
    Real labels get higher weight (1.0) in training.
    Predicted labels get lower weight (0.7).
    """
    with open(real_labels_path) as f:
        real = [json.loads(l) for l in f]
    
    with open(predicted_labels_path) as f:
        predicted = [json.loads(l) for l in f]
    
    # Mark source
    for r in real:
        r['label_weight'] = 1.0
        r['source'] = 'standup4ai_real'
    
    for p in predicted:
        p['label_weight'] = 0.7
        p['source'] = 'standup4ai_predicted'
    
    merged = real + predicted
    
    with open(output_path, 'w') as f:
        for item in merged:
            f.write(json.dumps(item) + '\n')
    
    return len(merged)
```

**Output File**: `data/standup4ai_processed/merged_1.5M.jsonl`

---

#### Task S4.2: Final Training on Merged Dataset
**Owner**: Research Team
**Time**: 8 hours
**Input**: `data/standup4ai_processed/merged_1.5M.jsonl`

**Command**:
```bash
python training/rl_laughter_trainer.py \
  --phase 1 \
  --base_model FacebookAI/xlm-roberta-base \
  --data data/standup4ai_processed/merged_1.5M.jsonl \
  --output experiments/standup4ai_final \
  --epochs 10 \
  --batch_size 16 \
  --learning_rate 2e-5 \
  --label_weight_key label_weight  # Use per-example weights
```

**Expected Results**:
- Training on ~1.5M words (including 3,203 real labels)
- Model should generalize better with more data
- Especially for under-represented languages (pt, cs, hu)

---

### StandUp4AI Summary

| Phase | Task | Videos | Words | Time | Output |
|-------|------|--------|-------|------|--------|
| S1.1 | Convert CSV | 4 | 3,203 | 2h | 4 JSONL files |
| S1.2 | Train baseline | - | 3,203 | 4h | Model |
| S2.1 | Setup transcriber | - | - | 4h | Script |
| S2.2 | Create ID lists | - | - | 1h | 7 TXT files |
| S3.1 | Batch 1 (en+fr) | 200 | ~500K | 12h | Transcripts |
| S3.2 | Batch 2 (es+it) | 300 | ~750K | 12h | Transcripts |
| S3.3 | Batch 3 (pt+cs+hu) | 200 | ~250K | 8h | Transcripts |
| S3.4 | Apply model | 700 | ~1.5M | 4h | Labeled JSONL |
| S4.1 | Merge datasets | - | ~1.5M | 1h | Merged JSONL |
| S4.2 | Final training | - | ~1.5M | 8h | Final model |
| **TOTAL** | | **~700** | **~1.5M** | **~56h** | **7 languages** |

---

## Part 4: Quality Assurance

### QA Protocol for All Data

#### Automated Validation
```python
def validate_dataset(dataset_path, expected_schema, expected_language):
    """
    Automated validation checks:
    1. JSONL format (parseable)
    2. Schema fields present
    3. Language matches expected
    4. Label values valid (0 or 1)
    5. Words/labels length match
    6. No empty examples
    """
    with open(dataset_path) as f:
        for i, line in enumerate(f):
            item = json.loads(line)
            
            # Schema check
            for field in expected_schema:
                assert field in item, f"Line {i}: missing {field}"
            
            # Length match
            assert len(item['words']) == len(item['labels']), \
                f"Line {i}: words/labels length mismatch"
            
            # Label values
            for label in item['labels']:
                assert label in (0, 1), f"Line {i}: invalid label {label}"
            
            # Language match
            assert item.get('language') == expected_language, \
                f"Line {i}: wrong language"
```

#### Manual Spot Check
- Review 5% of examples manually
- Check for:
  - Sensible laughter trigger positions
  - Natural language text
  - Proper Hinglish vs Hindi distinction (for Hindi data)

### Quality Metrics

| Dataset | Size | Automated Pass | Manual Pass | Quality Score |
|---------|------|---------------|-------------|---------------|
| Hindi manual | 48 | 100% | 95% | 95% |
| Hindi synthetic | 3,500 | 90% | 80% | 82% |
| Hindi podcasts | 540 | 85% | 75% | 76% |
| Chinese test | 500 | 100% | 90% | 90% |
| StandUp4AI labeled | 3,203 | 100% | 85% | 85% |
| StandUp4AI transcribed | ~1.5M | 95% | N/A (too large) | 95% |

---

## Part 5: Timeline and Resource Allocation

### Master Timeline

```
Week 1:  H1.1-H1.3 (Hindi manual+synth) + S1.1-S1.2 (StandUp4AI setup)
Week 2:  H1.4-H1.6 (Hindi scale) + S2.1-S2.2 (Transcriber setup)
Week 3:  C1-C3 (Chinese test set) + S3.1 (Batch 1 start)
Week 4:  H1.7-H1.9 (Hindi final) + S3.1 (Batch 1 finish)
Week 5:  S3.2 (Batch 2 - Spanish+Italian)
Week 6:  S3.3 (Batch 3 - pt+cs+hu) + S3.4 (Apply model)
Week 7:  S4.1-S4.2 (Merge + final training)
Week 8+: Integration, paper writing, evaluation
```

### Human Hours by Phase

| Phase | Tasks | Human Hours |
|-------|-------|-------------|
| Hindi expansion | H1.1-H1.9 | ~28h |
| Chinese test set | C1-C3 | ~15h |
| StandUp4AI Phase 1-2 | S1.1-S2.2 | ~11h |
| StandUp4AI Phase 3-4 | S3.1-S4.2 | ~33h |
| QA + integration | QA protocols | ~15h |
| **Total human** | | **~102h** |
| **Colab compute** | Transcription | ~100h |

---

## Part 6: Success Metrics

### Hindi Expansion
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Hindi examples | 4,000 | 48 | 🔴 |
| Hindi % of dataset | 40% | 0.5% | 🔴 |
| Laughter rate | 35-40% | 0% (missing) | 🔴 |
| Comedians | 10+ | 1 | 🔴 |

**Target**: All metrics green by Week 4

### Chinese Test Set
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Chinese test examples | 500 | 0 | 🔴 |
| Label quality | 95% | Unknown | ? |

**Target**: 500 verified examples by Week 3

### StandUp4AI
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Languages processed | 7 | 1 (en, fr, es labeled) | 🟡 |
| Videos transcribed | 700+ | 195 (existing) | 🟡 |
| Words with labels | 1.5M+ | 3,203 (pre-labeled) | 🔴 |
| Processed data dir | EXISTS | MISSING | 🔴 |

**Target**: All green by Week 8

### Overall Dataset (Post-Collection)

| Metric | Target | Current |
|--------|--------|---------|
| Total examples | ~44,000 | ~12,000 |
| Languages | 9 | 3 (en, zh, hi) |
| Test languages | 9 | 3 (en, zh, hi) |
| Real labels (manual) | 3,203+ | 3,203 |
| Predicted labels | ~1.5M | 0 |

---

## Part 7: File Manifest

### New Files to Create

| File | Purpose | Source Task |
|------|---------|-------------|
| `training/convert_standup4ai_labels.py` | CSV to JSONL conversion | S1.1 |
| `training/transcribe_standup4ai_batch.py` | Batch transcription | S2.1 |
| `training/apply_laughter_model.py` | Batch inference | S3.4 |
| `training/validate_hindi_dataset.py` | Hindi QC checks | H1.9 |
| `training/semi_supervised_refine.py` | Self-training | H1.8 |
| `data/hindi/synthetic_*.jsonl` | Hindi synthetic data | H1.2, H1.4, H1.7 |
| `data/hindi/podcasts_*.jsonl` | Hindi podcast data | H1.5, H1.6 |
| `data/standup4ai/video_ids/*.txt` | Video ID lists | S2.2 |
| `data/standup4ai/transcripts_batch{1,2,3}/` | Transcribed data | S3.1-S3.3 |
| `data/standup4ai_processed/merged_1.5M.jsonl` | Final merged data | S4.1 |

### Existing Files Referenced

| File | Purpose |
|------|---------|
| `data/v8_1_final/` | Training data split |
| `data/processed/indian_*.jsonl` | Existing Hindi data |
| `experiments/xlmr_standup_baseline_weak_pos5/` | Baseline model |
| `/tmp/standup4ai_dataset/Examples_label/` | Pre-labeled StandUp4AI |
| `/tmp/standup4ai_full/transcripts/` | Existing transcripts |

---

## Appendix A: Comedy Style Prompts for Hindi Synthetic Generation

### Zakir Khan (Observational)
```
Prompt: "Generate 50 Hindi/Hinglish stand-up comedy examples in the style of Zakir Khan. Focus on relatable observations about Indian life - traffic, family gatherings, job interviews, train journeys. Each example should have clear setup-punchline structure with exactly one word marked [LAUGHTER] as the trigger. Make it self-deprecating and warm."
```

### Biswa Kalyan Rath (Sardonic/Intellectual)
```
Prompt: "Generate 50 Hindi/Hinglish stand-up comedy examples in the style of Biswa Kalyan Rath. Focus on logical absurdities, philosophical observations, and nerdy humor. Each example should have exactly one [LAUGHTER] trigger. Dark, intellectual humor."
```

### Kunal Kamra (Dark/Social Commentary)
```
Prompt: "Generate 50 Hindi/Hinglish stand-up comedy examples in the style of Kunal Kamra. Focus on social commentary, politics, and everyday frustrations. Sharp, observational humor with exactly one [LAUGHTER] trigger per example."
```

### Kaneez Surka (Physical/Situational)
```
Prompt: "Generate 50 Hindi/Hinglish stand-up comedy examples in the style of Kaneez Surka. Focus on situational comedy, misunderstandings, and physical humor. Lighter tone with exactly one [LAUGHTER] trigger per example."
```

---

## Appendix B: Whisper Transcription Settings

```python
WHISPER_CONFIG = {
    'model': 'medium',  # Best balance of speed/accuracy
    'language': None,  # Auto-detect, or specify 'hi', 'es', 'fr', etc.
    'task': 'transcribe',
    'word_timestamps': True,  # Required for word-level labels
    'initial_prompt': None,  # Optional context
    'condition_on_previous_text': True,
    'temperature': 0.0,  # Deterministic output
    'compression_ratio_threshold': 2.4,
    'log_prob_threshold': -1.0,
    'no_speech_threshold': 0.6,
}
```

---

## Appendix C: Error Handling

### Transcription Failures
- **yt-dlp fails**: Skip video, log error, continue with next
- **Whisper timeout**: Reduce batch size, retry
- **No audio in video**: Skip, log, continue

### Label Quality Issues
- **Empty labels after weak labeling**: Discard example
- **All labels 0 or all 1**: Discard (no variance)
- **Words/labels length mismatch**: Fix or discard

### Colab Timeouts
- **90 min limit**: Checkpoint every 50 videos
- **Runtime disconnect**: Resume from last checkpoint
- **Out of memory**: Reduce batch size, clear cache

---

**END OF DATA COLLECTION STRATEGY**

*Document Version: 1.0*
*Created: 2026-05-05*
*Status: APPROVED*
*Next Review: Week 4 checkpoint*