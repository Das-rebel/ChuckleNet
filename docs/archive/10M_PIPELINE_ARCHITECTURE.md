# 10M Audio Segment Pipeline - Architecture v1.0

**Date:** 2026-05-09  
**Status:** APPROVED  
**Storage:** GDrive (5TB available, ~120GB needed)  
**Target:** 10,000,000 segments across en/zh/hi-latn

---

## Architecture

```
GDrive: gdrive:/laughter_prediction/
├── audio/en/           # 417 MP3 files, ~40GB
├── audio/zh/           # 556 MP3 files, ~40GB  
├── audio/hi-latn/       # 667 MP3 files, ~30GB
├── transcripts/        # Whisper JSON per video
├── aligned/            # Alignment JSONL per language
└── models/             # Trained checkpoints

LOCAL: 
├── data/audio_comedy/aligned_segments.jsonl  # Current 50K
└── data/audio_comedy/extracted_clips/       # Local clip cache (optional)
```

---

## Pipeline Phases

### Phase 1: Video Discovery & Download (Week 1)
**Who:** CPU/local (yt-dlp + Chrome cookies for auth)

Tasks:
1. Search YouTube for 417 EN comedy videos (stand-up, [laughter] subs)
2. Search for 667 HI/Hinglish comedy videos
3. Search for 556 ZH comedy videos
4. Download audio MP3s → GDrive audio/{lang}/
5. Download VTT subtitles → GDrive vtt/{lang}/

**Output:** 1,640 audio files on GDrive (~120GB)

### Phase 2: Whisper Transcription (Week 2)
**Who:** Colab T4 GPU

Tasks:
1. Mount GDrive on Colab
2. Batch process each language with faster-whisper tiny
3. Save transcripts JSON → GDrive transcripts/{lang}/
4. ~8 Colab sessions × 90 min each = ~12 GPU hours

**Output:** 1,640 transcript JSON files with word timestamps

### Phase 3: Alignment (Week 3)
**Who:** CPU (Colab or local)

Tasks:
1. Parse VTT for [laughter]/[Applause]/[laughing]/etc markers
2. Align laughter events with Whisper word timestamps (5s window)
3. Export per-video alignment JSONL → GDrive aligned/{lang}/
4. Merge into single aligned_segments.jsonl (~500MB)

**Output:** 10M segments with audio_file, word, start, end, label

### Phase 4: Training (Week 4)
**Who:** Colab GPU

Tasks:
1. Wav2Vec2 fine-tuning on each language
2. XLM-R text baseline on merged_final (19K)
3. Multimodal fusion
4. Evaluation

**Output:** Trained models on GDrive

---

## Storage Estimates

| Component | Size | Location |
|-----------|------|----------|
| Audio (1,640 MP3s, 1,500hr) | ~120 GB | GDrive audio/ |
| VTT subtitles | ~10 GB | GDrive vtt/ |
| Transcripts JSON | ~5 GB | GDrive transcripts/ |
| Alignment JSONL (10M × 50B) | ~500 MB | GDrive aligned/ |
| **Total** | **~135 GB** | |

**GDrive used:** 135 GB / 4,630 GB free ✓

---

## Cost Analysis

| Phase | Compute | Time | Cost |
|-------|---------|------|------|
| Video download | CPU | ~20 hrs | $0 (local) |
| Whisper (T4) | GPU | ~12 hrs | ~$10 (Colab Pro mo) |
| Alignment | CPU | ~9 hrs | $0 (Colab) |
| Wav2Vec2 training | GPU | ~6 hrs | ~$10 (Colab Pro mo) |
| **Total** | | **~47 hrs** | **~$20/month** |

---

## Language Distribution

| Language | Videos | Words/Video | Total Words | Positive Rate |
|----------|--------|-------------|-------------|---------------|
| English (en) | 417 | 8,000 | 3,333,333 | ~5-15% |
| Hindi (hi-latn) | 667 | 5,000 | 3,333,333 | ~10-20% |
| Chinese (zh) | 556 | 6,000 | 3,333,333 | ~5-15% |

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `training/scale_to_1m_segments.py` | Master orchestrator |
| `training/align_whisper_to_vtt.py` | VTT + Whisper alignment |
| `training/expand_audio_dataset.py` | Download audio + VTT |
| `training/extract_audio_clips.py` | Extract .wav clips (optional cache) |

---

## Execution Plan

### Immediately (this session)
1. ✅ `align_whisper_to_vtt.py` — updated with all laugh markers
2. ✅ `expand_audio_dataset.py` — audio + VTT download
3. 🔄 Background: Clip extraction + Whisper transcription (running)

### This Week
1. Create Colab notebook for batch Whisper transcription
2. Write video search script for en/hi/zh comedy
3. Begin downloading first batch of videos to GDrive

### Next Week
1. Run Whisper on Colab (8 sessions)
2. Align all transcripts
3. Verify 10M segments target

---

*Last updated: 2026-05-09*