# PRD v4.0: 10M Audio Segment Pipeline for Multilingual Laughter Prediction

**Date:** 2026-05-09  
**Status:** DRAFT  
**Target:** 10,000,000 audio segments across English, Chinese, Hindi  
**Storage:** GDrive (5TB available) + Local  
**Compute:** Windows laptop GPU + Colab fallback

---

## Executive Summary

Build a pipeline to collect, align, and train on **10 million audio-word segments** with laugh labels for multilingual laughter prediction (en/zh/hi-latn). The system uses YouTube comedy videos with subtitle `[laughter]` markers as ground truth, aligned to Whisper-generated word timestamps.

**Key decisions:**
- Audio files + alignment metadata stored on **GDrive** (~120GB)
- Local feature extraction (MFCC) for training
- **Windows laptop with NVIDIA GPU** as primary compute (e.g., RTX 3080, 4090, or RTX 6000 Ada)
- **Google Colab T4/A100** as fallback for batch Whisper transcription
- `faster-whisper tiny` for speed, `Wav2Vec2-base` for audio encoder

---

## Dataset Target

| Language | Videos | Words/Video | Total Words | Positive Rate |
|----------|--------|-------------|-------------|---------------|
| English (en) | 417 | 8,000 | 3,333,333 | ~10% |
| Hindi (hi-latn) | 667 | 5,000 | 3,333,333 | ~15% |
| Chinese (zh) | 556 | 6,000 | 3,333,333 | ~10% |
| **TOTAL** | **1,640** | | **10,000,000** | **~11%** |

---

## Architecture

### Storage: GDrive

```
gdrive:/laughter_prediction/
├── audio/
│   ├── en/           (417 MP3s, ~40GB)
│   ├── zh/           (556 MP3s, ~40GB)
│   └── hi-latn/      (667 MP3s, ~30GB)
├── vtt/
│   ├── en/           (417 VTTs, ~5GB)
│   ├── zh/           (556 VTTs, ~5GB)
│   └── hi-latn/      (667 VTTs, ~5GB)
├── transcripts/
│   ├── en/           (417 JSON, ~2GB)
│   ├── zh/           (556 JSON, ~2GB)
│   └── hi-latn/      (667 JSON, ~2GB)
├── aligned/
│   ├── en.jsonl      (~170MB)
│   ├── zh.jsonl       (~170MB)
│   └── hi-latn.jsonl  (~170MB)
└── models/
    ├── wav2vec2_en/
    ├── wav2vec2_zh/
    ├── wav2vec2_hi/
    └── fusion/
```

**Total GDrive usage:** ~135 GB / 4,630 GB free ✓

### Local Compute Options

#### Option A: Windows Laptop with NVIDIA GPU (PRIMARY)

| Component | Spec | Notes |
|-----------|------|-------|
| GPU | RTX 3080/3090/4090 or RTX 6000 Ada | 16-24GB VRAM |
| RAM | 32GB+ | For DataLoader with large datasets |
| Storage | 500GB+ NVMe | For clip cache + MFCC features |
| OS | Windows 10/11 with WSL2 | OR native Python |

**GPU Performance Estimates:**
- `faster-whisper tiny`: ~150x realtime on RTX 4090
- `faster-whisper base`: ~80x realtime on RTX 4090
- `Wav2Vec2 training`: ~15 steps/sec on RTX 4090 (fp16)

**Speedup vs Colab T4:**
- Whisper: 1.5x faster (4090 vs T4)
- Wav2Vec2: 2-3x faster (4090 vs T4)

#### Option B: Google Colab (FALLBACK)

| Tier | GPU | Speed vs T4 | Monthly Cost |
|------|-----|-------------|--------------|
| Colab Pro | T4 (16GB) | 1x baseline | $10 |
| Colab Pro+ | A100 (40GB) | 3x faster | $50 |

---

## Pipeline Phases

### Phase 0: Prerequisites (1-2 days)

#### 0.1: Windows Setup
```
- Install Python 3.10+ via Anaconda or python.org
- Install CUDA 12.x + cuDNN 8.x
- Install ffmpeg (choco install ffmpeg on Windows)
- pip install: faster-whisper, torch, transformers, librosa, rclone
- rclone config gdrive:  (use existing OAuth from Chrome extension)
- Verify: python -c "import torch; print(torch.cuda.is_available())"
- Verify: ffmpeg -version
- Verify: rclone ls gdrive:  (should show existing files)
```

#### 0.2: GPU Driver Test
```powershell
nvidia-smi  # Should show GPU name + VRAM
python -c "import torch; print(torch.cuda.get_device_name(0))"
# Expected: RTX 4090, RTX 3080, or similar
```

#### 0.3: Colab Connection (if using Colab fallback)
```
- Mount Google Drive on Colab
- Verify rclone can reach gdrive:/laughter_prediction/
- Test download speed: rclone copy gdrive:/laughter_prediction/audio/en/test.mp3 /tmp/
```

---

### Phase 1: Video Discovery + Download (Week 1, CPU-bound)

**Goal:** Download 1,640 MP3s + VTTs to GDrive

#### 1.1: Find Comedy Videos per Language

Script: `training/find_comedy_videos.py`

```python
"""
Search YouTube for comedy videos with subtitle [laughter] markers.
Output: data/video_candidates/{lang}.json

Strategy:
- yt-dlp ytsearch for "stand up comedy special"
- For each result, check VTT laugh density (use --skip-download --write-auto-sub)
- Only keep videos with >= 20 laugh markers
- Target: 417 en, 667 hi, 556 zh

Search queries:
  en: "stand up comedy special english", "comedy special netflix", "comedian full set"
  hi: "hindi stand up comedy zakir khan", "hinglish comedy special", "desi comedy"
  zh: "chinese comedy special 单口相声", "stand up comedy china"
```

**Output:**
```json
{
  "en": [
    {"id": "abc123", "title": "Comedy Special", "laugh_markers": 45, "duration_min": 45},
    ...
  ],
  "zh": [...],
  "hi-latn": [...]
}
```

**Time:** ~82 minutes of searching (rate-limited to 20 searches/min)

#### 1.2: Download Audio to GDrive

Script: `training/download_audio_batch.py`

```bash
# Parallel download with 4 workers
python training/download_audio_batch.py \
  --lang en \
  --video-list data/video_candidates/en.json \
  --output gdrive:/laughter_prediction/audio/en/ \
  --workers 4

# Estimated: 417 videos × 50MB = ~21GB, 2 min each = ~14 hours
```

**Commands per worker:**
```powershell
yt-dlp -x --audio-format mp3 --audio-quality 5 \
  -o "gdrive:/laughter_prediction/audio/en/%(id)s.%(ext)s" \
  https://youtube.com/watch?v=VIDEO_ID
```

**Using Windows Task Scheduler:** Run 4 parallel `yt-dlp` instances

#### 1.3: Download VTT Subtitles

```bash
# Download auto-subs for all videos
python training/download_vtt_batch.py \
  --lang en \
  --video-list data/video_candidates/en.json \
  --output gdrive:/laughter_prediction/vtt/en/ \
  --workers 4

# ~5GB total across all languages
```

**Time:** ~11 hours CPU (parallel)

---

### Phase 2: Whisper Transcription (Week 2, GPU)

**Goal:** Generate word-timestamp JSONs for all 1,640 videos

#### 2.1: Colab Transcription (A100 recommended, T4 fallback)

Notebook: `colab_package/whisper_10m_pipeline.ipynb`

```python
"""
Mount GDrive, run faster-whisper tiny on all audio files.
Save transcripts to gdrive:/laughter_prediction/transcripts/{lang}/
"""

import faster_whisper

model = faster_whisper.WhisperModel("tiny", device="cuda", compute_type="int8-fp16")

def transcribe_video(audio_path, output_path):
    segments, info = model.transcribe(audio_path, word_timestamps=True)
    # Save as JSON with word-level timestamps
    ...

# Process all 1,640 videos
# Batch by language to minimize GDrive API calls
```

**Windows Laptop Alternative (if GPU strong enough):**

```python
# On Windows with RTX 4090 (16GB VRAM)
model = faster_whisper.WhisperModel("base", device="cuda", compute_type="fp16")
# base is 2x slower but 5% better accuracy - still worth it on 4090
```

#### Time Estimates (GPU hours)

| Config | Speed | 1,229hr audio | Sessions | Cost |
|--------|-------|---------------|----------|------|
| tiny + T4 | 130x | 9.5 hrs | 6 × 90min | ~$10/mo Colab |
| base + RTX 4090 | 100x | 12.3 hrs | 8 local | $0 (owned) |
| tiny + A100 | 300x | 4.1 hrs | 3 × 90min | ~$15 Colab |
| base + RTX 4090 | 100x | 12.3 hrs | 8 local | $0 |

**Recommendation:** Use Windows laptop for Whisper (RTX 4090 at 100x realtime = 12 hours total)

---

### Phase 3: Alignment (Week 3, CPU)

**Goal:** Parse VTT `[laughter]` markers, align to Whisper timestamps

Script: `training/align_10m_segments.py`

```python
"""
1. For each VTT file:
   - Parse timestamp + text segments
   - Extract laughter events: [laughter], [Applause], (audience laughing), etc.
   
2. For each Whisper transcript:
   - Load word-level timestamps
   
3. Align:
   - Word labeled as laugh if:
     a) Falls within a laughter event interval (VTT timestamp range)
     b) Is within 5 seconds BEFORE a laughter event (audience reaction lag)
     c) Is 2 words before trigger (punchline context)
   
4. Output: gdrive:/laughter_prediction/aligned/{lang}.jsonl
   - 10M lines, each: {video_id, word, start, end, label, language}
"""

LAUGHTER_MARKERS = [
    "[laughter]", "[laugh]", "[applause]", "[Applause]",
    "(audience laughing)", "(audience laughs)", "(audience clapping)",
    "(audience cheering)", "(audience applause)",
    "[प्रशंसा]",  # Hindi applause
]
```

**Output format (JSONL):**
```jsonl
{"video_id":"abc123","comedian":"john_mulaney","language":"en","word":"joke","start":12.5,"end":12.9,"duration":0.4,"label":1,"context_words":["a","joke","here"],"word_index":45}
{"video_id":"abc123","comedian":"john_mulaney","language":"en","word":"is","start":12.9,"end":13.1,"duration":0.2,"label":0,...}
```

**Time:** ~9 hours CPU (parallelize by language)

---

### Phase 4: Feature Extraction (Week 3, CPU/GPU)

**Goal:** Pre-compute MFCC features for faster training

Script: `training/compute_mfcc_features.py`

```python
"""
Extract 40-dim MFCC features per word segment.

For each aligned segment:
  1. Load .mp3 audio from GDrive (or local cache)
  2. Slice audio: start - 0.1s to end + 0.1s (context window)
  3. Compute: 40 MFCCs + delta + delta-delta = 120-dim feature
  4. Store as numpy .npz: features/{lang}/{video_id}/{word_idx}.npz

Total size: 10M × 120 × 4 bytes = ~4.8 GB (store on GDrive)
Or compute on-demand during training (slower but saves storage)
"""

import librosa
import numpy as np

def extract_mfcc(audio_path, start, end):
    y, sr = librosa.load(audio_path, offset=start-0.1, duration=end-start+0.2, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    return np.concatenate([mfcc, delta, delta2], axis=0)  # (120, frames)
```

**Time:** 
- Pre-compute all: ~4 hours GPU (RTX 4090) or ~40 hours CPU
- On-demand during training: negligible per epoch

**Recommendation:** Pre-compute on Windows GPU after Whisper transcription

---

### Phase 5: Model Training (Week 4, GPU)

#### 5.1: XLM-R Text Baseline (Local Mac/Windows)

```bash
# Train on merged_final (19K examples) - NOT on GPU-heavy side
python training/train_xlmr_combined.py \
  --epochs 5 \
  --batch-size 32 \
  --lr 5e-5 \
  --pos-weight 5.0 \
  --unfreeze 4 \
  --output experiments/xlmr_text_baseline

# Time: ~2-3 hours CPU (can run on MacBook Pro)
```

#### 5.2: Wav2Vec2 Audio Model (Windows GPU or Colab)

Script: `training/train_wav2vec2_audio.py`

```python
"""
Fine-tune Wav2Vec2-base on MFCC features per language.

Per language (en/zh/hi):
  - Load MFCC features from GDrive (or local cache)
  - DataLoader: batch_size=256, num_workers=4, pin_memory=True
  - Model: Wav2Vec2 + 2-layer MLP classifier
  - Optimizer: AdamW fp16 + torch.compile
  - 10 epochs, ~52K steps each

Total GPU time:
  - RTX 4090: ~12 hours per language × 3 = 36 hours (sequential)
  - Colab A100: ~6 hours per language × 3 = 18 hours
  
Recommended: Run 3 parallel agents on Windows (one per language)
"""

# Training command per language
python training/train_wav2vec2_audio.py \
  --features-dir gdrive:/laughter_prediction/features/en/ \
  --aligned-file gdrive:/laughter_prediction/aligned/en.jsonl \
  --output gdrive:/laughter_prediction/models/wav2vec2_en/ \
  --lang en \
  --batch-size 256 \
  --epochs 10 \
  --lr 1e-4 \
  --device cuda
```

#### 5.3: Multimodal Fusion

Script: `training/train_fusion_model.py`

```python
"""
Text: XLM-R → 768-dim → 256-dim projection
Audio: Wav2Vec2 → 768-dim → 256-dim projection
      ↓
Cross-Attention Fusion (6 layers)
      ↓
Classifier: 512 → 2 (laugh/no-laugh)

Train on paired (text, audio, label) examples.
"""
```

---

## Time & Cost Summary

### Windows Laptop (Primary)

| Component | GPU | Time | Cost |
|-----------|-----|------|------|
| Video discovery | CPU | 1 hr | $0 |
| Audio download | CPU | 20 hrs | $0 |
| VTT download | CPU | 11 hrs | $0 |
| Whisper (base/4090) | RTX 4090 | 12 hrs | $0 |
| Alignment | CPU | 9 hrs | $0 |
| MFCC extraction | RTX 4090 | 4 hrs | $0 |
| Wav2Vec2 × 3 | RTX 4090 | 36 hrs | $0 |
| Text baseline | CPU/Mac | 3 hrs | $0 |
| **TOTAL** | | **96 hrs** | **$0** |

### Google Colab (Fallback)

| Component | GPU | Time | Cost |
|-----------|-----|------|------|
| Whisper (tiny/T4) | T4 | 9.5 hrs | $10/mo |
| Wav2Vec2 × 3 | T4 | 55 hrs | $50/mo |
| **TOTAL** | | **64.5 hrs** | **~$60** |

---

## Optimization Stack Applied

| Optimization | Speedup | Applicable To |
|--------------|---------|---------------|
| `faster-whisper` int8-fp16 | 1.3x | Whisper |
| `faster-whisper tiny` model | 2x vs base | Whisper |
| FP16 mixed precision | 1.5x | Wav2Vec2 training |
| `torch.compile` | 1.3x | Training loop |
| Adam8bit quantizer | 1.2x | Optimizer |
| Gradient accumulation (4x) | Batch 4x larger | Wav2Vec2 |
| DataLoader num_workers=4 | I/O overlap | Training |
| MFCC pre-computation | 10x vs on-demand | Feature extraction |
| GDrive streaming | I/O optimization | Data loading |

---

## Windows-Specific Setup Instructions

### Step 1: Install CUDA + PyTorch

```powershell
# Install CUDA 12.1 (check nvidia-smi for driver version)
# Download from: https://developer.nvidia.com/cuda-downloads

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### Step 2: Install ffmpeg

```powershell
choco install ffmpeg
# OR download from https://ffmpeg.org/download.html
```

### Step 3: Install rclone

```powershell
# Download from https://rclone.org/downloads/
# Or: choco install rclone
rclone config  # Configure GDrive using existing OAuth
```

### Step 4: Install Python packages

```powershell
pip install faster-whisper transformers librosa numpy pandas sklearn
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 5: Verify Everything

```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
python -c "import librosa; print('librosa OK')"
python -c "from faster_whisper import WhisperModel; print('faster-whisper OK')"
ffmpeg -version | head -1
rclone ls gdrive:  # Should show existing files
```

---

## Execution Plan

### Week 1 (Local Windows/Mac)
1. ✅ Verify Windows GPU setup
2. ✅ Run `find_comedy_videos.py` for en/hi/zh → `data/video_candidates/`
3. ✅ Download audio → GDrive (`download_audio_batch.py`)
4. ✅ Download VTT → GDrive (`download_vtt_batch.py`)
5. ✅ Background: keep downloading while doing other steps

### Week 2 (Colab or Windows GPU)
1. Run Whisper on all 1,640 audio files
2. Save transcripts to GDrive
3. Verify transcript quality on sample

### Week 3 (Local)
1. Run alignment (`align_10m_segments.py`)
2. Pre-compute MFCC features on Windows GPU
3. Verify alignment on sample

### Week 4 (Colab or Windows GPU)
1. Train Wav2Vec2 per language (parallel if possible)
2. Train multimodal fusion
3. Evaluate and document

---

## File Inventory

| Script | Purpose | Owner |
|--------|---------|-------|
| `find_comedy_videos.py` | Search YouTube, filter by laugh density | Local |
| `download_audio_batch.py` | Download MP3s to GDrive | Local |
| `download_vtt_batch.py` | Download VTTs to GDrive | Local |
| `whisper_batch.py` | Transcribe all audio (Colab notebook) | Colab |
| `align_10m_segments.py` | VTT + Whisper alignment | Local |
| `compute_mfcc_features.py` | Extract MFCC features | Local GPU |
| `train_wav2vec2_audio.py` | Wav2Vec2 fine-tuning | Colab/Windows GPU |
| `train_fusion_model.py` | Multimodal fusion training | Colab/Windows GPU |
| `train_xlmr_text.py` | XLM-R text baseline | Local Mac/Windows |

---

## Success Criteria

- ✅ **10,000,000** segments with laugh labels
- ✅ **11% positive rate** (~1.1M positive examples)
- ✅ **3 languages** covered (en, zh, hi-latn)
- ✅ **Audio model F1 > 0.65** (per PRD target)
- ✅ **Multimodal F1 > 0.75** (per PRD target)
- ✅ **Paper submission** to ACL/EMNLP 2026

---

**END OF PRD v4.0**

*Next step: Execute Phase 1 (Video Discovery)*