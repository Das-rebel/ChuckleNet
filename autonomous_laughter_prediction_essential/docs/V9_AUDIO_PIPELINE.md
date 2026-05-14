# V9 Multimodal Audio Pipeline - Implementation Complete

## 📁 Scripts Created

### 1. `audio_data_collector.py` - Collect Comedy Audio from YouTube
Downloads stand-up comedy videos from YouTube, extracts MP3 audio, and transcribes with Whisper.

**Usage:**
```bash
python training/audio_data_collector.py --comedian "Dave Chappelle" --max_videos 5
```

**Workflow:**
1. Search YouTube for comedian + "stand-up comedy"
2. Download audio (MP3, best quality)
3. Transcribe with Whisper (word-level timestamps)
4. Save JSON manifest with word alignments

**Dependencies:**
- `ffmpeg` (brew install ffmpeg)
- `yt-dlp` (brew install yt-dlp)
- `openai-whisper` (pip install openai-whisper)

---

### 2. `audio_wav2vec_train.py` - Audio-Only Baseline
Trains Wav2Vec2 on comedy audio for laughter detection. Target: Val F1 > 0.65

**Usage:**
```bash
python training/audio_wav2vec_train.py \
    --train data/audio_train.jsonl \
    --val data/audio_val.jsonl \
    --output experiments/wav2vec_audio \
    --epochs 10
```

**Dataset Format:**
```json
{"audio_path": "/path/to/audio.wav", "words": [{"word": "funny", "start": 1.2, "end": 1.5}], "label": 1}
```

---

### 3. `fusion_crossmodal_train.py` - Multimodal Fusion (Text + Audio)
Combines XLM-R text branch with Wav2Vec2 audio branch via cross-attention.

**Architecture:**
```
Text Input → XLM-R → text_proj(768→256) → [T, 256]
Audio Input → Wav2Vec2 → audio_proj(768→256) → [A, 256]
                         ↓
            CrossAttention → fusion_emb
                         ↓
            [fusion_emb] → classifier → laughter_prob
```

**Target Metrics:**
| Model | ValF1 | IoU-F1 |
|-------|-------|--------|
| V9 Audio | >0.65 | >0.70 |
| V9 Fusion | >0.78 | >0.80 |

**Usage:**
```bash
python training/fusion_crossmodal_train.py \
    --train data/multimodal_train.jsonl \
    --val data/multimodal_val.jsonl \
    --output experiments/v9_fusion \
    --epochs 10 \
    --aux_weight 0.3
```

---

### 4. `run_audio_collection.sh` - Quick Start Script
Bash wrapper for quick audio collection.

```bash
bash training/run_audio_collection.sh "Dave Chappelle" 5
```

---

## 📊 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│ V9 MULTIMODAL PIPELINE                                      │
└─────────────────────────────────────────────────────────────┘

[Audio Collection]          [Text Pipeline (V8)]      [Output]
      ↓                            ↓
yt-dlp + Whisper         XLM-R + Word-Level    [Multimodal Fusion]
      ↓                            ↓              CrossAttention
Audio Files +                  Text Embeddings        ↓
Transcripts                    [768-dim]         Final Classifier
      ↓                            ↓              ValF1 > 0.78
[Wav2Vec2 Training]              ↓
Audio Embeddings           [256-dim proj]
[512-dim]                       ↓
      ↓                         ↓
Audio-Only Baseline      [Fused Text+Audio] ←── Cross-Modal Fusion
Val F1 > 0.65                    ↓
                           laughter_prob
```

---

## 🎯 Next Steps

### Immediate (Before V9 Audio Training)
1. [ ] Run audio collection for 3-5 comedians
   ```bash
   bash training/run_audio_collection.sh "Dave Chappelle" 5
   bash training/run_audio_collection.sh "Ali Wong" 3
   bash training/run_audio_collection.sh "John Mulaney" 3
   ```

2. [ ] Create word-level aligned labels (laughter timestamps)

3. [ ] Generate train/val JSONL manifests

### After Audio Collection
4. [ ] Train Wav2Vec2 audio-only baseline
   ```bash
   python training/audio_wav2vec_train.py --train train.jsonl --val val.jsonl
   ```

5. [ ] If audio F1 > 0.65, proceed to fusion

6. [ ] Train multimodal fusion
   ```bash
   python training/fusion_crossmodal_train.py --train train.jsonl --val val.jsonl
   ```

---

## 📁 Data Directory Structure

```
data/
├── audio_comedy/
│   ├── audio/
│   │   ├── dave_chappelle/
│   │   │   ├── video1.mp3
│   │   │   └── video2.mp3
│   │   └── ali_wong/
│   │       └── video1.mp3
│   └── transcripts/
│       ├── dave_chappelle/
│       │   └── video1_transcript.json
│       └── ali_wong/
│           └── video1_transcript.json
└── multimodal/
    ├── train.jsonl
    └── val.jsonl
```

---

## 🔧 Troubleshooting

### yt-dlp fails to download
```bash
# Update yt-dlp
yt-dlp --update-to-stable

# Try with cookies (if age-restricted)
yt-dlp --cookies-from-browser chrome URL
```

### Whisper transcription slow
- Use `model="tiny"` for fast testing
- Use `model="base"` for balanced speed/accuracy
- Use `model="large"` for best quality (slower)

### Audio quality issues
```bash
# Re-extract with higher quality
yt-dlp -x --audio-format wav --audio-quality 0 URL
```
