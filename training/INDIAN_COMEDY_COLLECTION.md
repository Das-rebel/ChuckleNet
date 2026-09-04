# Indian Comedy Data Collection Guide

## Overview

This guide explains how to collect Hindi/Hinglish and Bengali comedy data from YouTube for laughter prediction training.

## Tools

Two main scripts:

1. **`search_youtube_videos.py`** - Search and find video URLs
2. **`collect_indian_comedy.py`** - Download and transcribe videos

## Step 1: Find Videos

### Option A: Search for specific comedian

```bash
cd /Users/Subho/autonomous_laughter_prediction_essential/training
python3 search_youtube_videos.py --comedian "Vir Das" --max 5 --output vir_das_videos.json
```

### Option B: Search all comedians

```bash
python3 search_youtube_videos.py --max 5 --output all_indian_comedy_videos.json
```

### Option C: Custom search

```bash
python3 search_youtube_videos.py --query "Hindi standup comedy full show 2024" --max 10
```

### List available comedians

```bash
python3 search_youtube_videos.py --list
```

## Step 2: Collect Transcripts

### Collect with auto strategy (recommended)

The auto strategy tries YouTubeTranscriptApi first, then falls back to Whisper:

```bash
python3 collect_indian_comedy.py --config all_indian_comedy_videos.json --strategy auto
```

### Collect with Whisper only (more reliable)

```bash
python3 collect_indian_comedy.py --config all_indian_comedy_videos.json --strategy whisper
```

### Collect specific videos

```bash
python3 collect_indian_comedy.py --videos "https://www.youtube.com/watch?v=VIDEO_ID1" "https://www.youtube.com/watch?v=VIDEO_ID2"
```

### Collect by language

```bash
# Hindi/Hinglish only
python3 collect_indian_comedy.py --language hindi_hinglish --config videos.json

# Bengali only
python3 collect_indian_comedy.py --language bengali --config videos.json
```

## Step 3: Process Transcripts

Once transcripts are collected, process them into training format:

```bash
python3 process_youtube_transcripts.py --comedian all
```

This creates JSONL files in `data/processed/` with:
- Word-level data
- Language codes (hi-latn, bn)
- Laughter labels
- Train/validation splits

## Expected Output

### Target Numbers

- **Hindi/Hinglish**: 1,000+ examples (5-10 videos)
- **Bengali**: 500+ examples (3-5 videos)

### File Structure

```
data/
├── audio_comedy/
│   ├── transcripts/
│   │   ├── vir_das/
│   │   │   ├── VIDEO_ID1_transcript.json
│   │   │   └── VIDEO_ID2_transcript.json
│   │   ├── zakir_khan/
│   │   └── mir_afsar_ali/
│   └── audio/
│       ├── VIDEO_ID1.wav
│       └── VIDEO_ID2.wav
└── processed/
    ├── vir_das/
    │   ├── train.jsonl
    │   └── val.jsonl
    └── combined/
        ├── train.jsonl
        └── val.jsonl
```

## Transcript Format

### Raw Transcript JSON

```json
{
  "text": "Full transcript text...",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello everyone",
      "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "everyone", "start": 0.6, "end": 1.2}
      ]
    }
  ],
  "source": "whisper",
  "language": "hi",
  "metadata": {
    "video_id": "VIDEO_ID",
    "comedian": "Vir Das",
    "language_code": "hi-latn",
    "language_name": "Hindi/Hinglish",
    "script": "Latn",
    "collected_at": "2026-05-03 10:30:00"
  }
}
```

### Processed Training JSONL

```json
{
  "example_id": "vir_das_VIDEO_ID_1234",
  "language": "hi-latn",
  "comedian_id": "vir_das",
  "show_id": "VIDEO_ID",
  "words": ["Hello", "everyone", ...],
  "labels": [0, 0, 1, 0, ...],
  "label": 1,
  "laughter_count": 42,
  "total_words": 350,
  "laughter_ratio": 0.12,
  "metadata": {
    "source": "whisper",
    "comedian": "Vir Das",
    "video_id": "VIDEO_ID",
    "collection_type": "youtube_transcript"
  }
}
```

## Language Codes

| Language | Code | Script | Example Comedians |
|----------|------|--------|-------------------|
| Hindi/Hinglish | hi-latn | Latn | Vir Das, Zakir Khan |
| Bengali | bn | Beng | Mir Afsar Ali, Sourav Ghosh |

## Troubleshooting

### YouTubeTranscriptApi blocked

If you see:
```
⚠️ YouTube API failed, trying fallback...
```

This is normal! The script will automatically fall back to Whisper.

### Slow transcription

Whisper transcription takes ~1-2 minutes per 10 minutes of video. Be patient.

### Out of memory

For long videos, use smaller Whisper model:
- Edit `collect_indian_comedy.py`
- Change `load_whisper_model('base')` to `load_whisper_model('tiny')`

### No word-level timestamps

YouTubeTranscriptApi doesn't always provide word-level data. Whisper always does.

## Next Steps After Collection

1. **Verify data quality**:
   ```bash
   python3 -c "import json; data=json.load(open('data/audio_comedy/transcripts/vir_das/VIDEO_ID_transcript.json')); print(len(data['segments']))"
   ```

2. **Process into training format**:
   ```bash
   python3 process_youtube_transcripts.py --comedian all
   ```

3. **Check statistics**:
   ```bash
   wc -l data/processed/combined/train.jsonl
   wc -l data/processed/combined/val.jsonl
   ```

4. **Add to training pipeline**:
   - Update training config to include new language data
   - Adjust language IDs in model
   - Train multilingual model

## Recommended Video Sources

### Hindi/Hinglish

- **Vir Das**: Netflix specials, Amazon Prime
- **Zakir Khan**: Amazon Prime, YouTube originals
- **Biswa Kalyan Rath**: Amazon Prime
- **Kaneez Surka**: YouTube, Comedy Central
- **Atul Khatri**: YouTube, live shows

### Bengali

- **Mir Afsar Ali**: YouTube, TV shows
- **Sourav Ghosh**: YouTube standup
- **Rohit Ghosh**: YouTube comedy
- **Rajat Chakraborty**: Bengali comedy shows

## Notes

- Always respect YouTube's Terms of Service
- Transcripts are for research purposes only
- Consider video length (aim for 10-30 minutes per video)
- More videos = better language coverage
- Mix of studio recordings and live shows is good
