# ZAI V9 MASTER PLAN - Corrected 2026-04-27

## CRITICAL LESSON LEARNED
- **Data format matters**: GitHub data is `words/labels` (word-level), code must convert to `text/label` (sentence-level)
- All future scripts MUST include data format detection + conversion

---

## PHASE 1: V8 BASELINE (Priority - Fix Now)

### Issue: Current V8 gives ValF1=0.0000
**Root cause**: Data has `words + labels` but code expects `text + label`

### Fix: Include conversion in all scripts
```python
def load_data(path, tokenizer):
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            # Auto-detect format
            if 'text' in d:
                text, label = d['text'], d['label']
            elif 'words' in d:
                text = ' '.join(d['words'])
                label = 1 if any(l == 1 for l in d.get('labels', [])) else 0
            else:
                continue
            yield text, label, tokenizer
```

### Experiments: 14 runs (7 task groups × 2 biosemotic variants)
- Task groups: MHD, MELD, IEMOCAP, UR-FUNNY, STANDUP4AI, VINEGAR, MULTILINGUAL
- 2 variants: standard vs enhanced class weights
- Target: ValF1 > 0.72

### Canonical path:
1. `convert_standup_raw_to_word_level.py` 
2. `refine_weak_labels_nemotron.py`
3. `xlmr_standup_word_level.py`
4. `run_xlmr_standup_pipeline.py`

---

## PHASE 2: V9 MULTIMODAL FUSION (After V8)

### Architecture
```
Text Branch:  XLM-R 768-dim → Biosemotic 256-dim
Audio Branch: Wav2Vec2 → Audio 512-dim  
Fusion:       [text_emb, audio_emb] → CrossAttention → Final Classifier
```

### Components
1. **Text Model**: XLM-R fine-tuned on V8 baseline
2. **Audio Model**: Wav2Vec2 fine-tuned on laughter audio
3. **Fusion**: Multimodal cross-attention layer

### Training Data (need to create)
```python
{
    "text": "funny text here",
    "audio_path": "/data/audio/funny.wav", 
    "label": 1,
    "language": "en"
}
```

### Scripts to build:
- `training/audio_wav2vec_train.py` - audio-only baseline
- `training/fusion_crossmodal_train.py` - full multimodal
- `training/multilingual_audio_collector.py` - collect data

---

## PHASE 3: V9 AUTONOMOUS RESEARCH LOOP

After V8+9 baselines established, run autonomous hyperparameter search.

### Pipeline:
1. Generate experiment configs
2. Run parallel experiments (V8 text + V9 audio + V9 fusion)
3. Evaluate results
4. Generate hypotheses
5. Run next batch
6. Auto-promote best model

---

## METRICS TARGETS

| Model | ValF1 | IoU-F1 | Use Case |
|-------|-------|--------|----------|
| V8 Text | >0.72 | >0.75 | Baseline, multilingual |
| V9 Audio | >0.65 | >0.70 | Audio-only scenes |
| V9 Fusion | >0.78 | >0.80 | Full multimodal |

---

## IMMEDIATE ACTIONS

### Step 1: Fix V8 script (DONE)
- Created `train_v8_fixed.py` with data conversion
- Push to GitHub

### Step 2: Run fixed V8 on Colab
- Stop current run
- Run: `!curl -sL "https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/train_v8_fixed.py" -o /tmp/v8.py && python3 /tmp/v8.py`

### Step 3: After V8 completes, build V9 audio
- Collect audio data from multilingual comedy sources
- Train Wav2Vec2 baseline
- Measure audio-only performance

### Step 4: Build V9 fusion
- Combine V8 text + V9 audio
- Cross-attention fusion layer
- Full training pipeline
