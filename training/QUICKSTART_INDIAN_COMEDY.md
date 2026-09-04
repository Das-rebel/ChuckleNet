# Quick Start: Indian Comedy Data Collection

## 🚀 5-Minute Quick Start

### Step 1: Search for Videos (1 min)
```bash
cd training

# Search for a comedian
python3 search_youtube_videos.py --comedian "Vir Das" --max 3 --output vir_das.json
```

### Step 2: Collect Transcripts (3-5 min per video)
```bash
# Collect using Whisper (recommended)
python3 collect_indian_comedy.py --config vir_das.json --strategy whisper
```

### Step 3: Process to Training Format (30 sec)
```bash
python3 process_youtube_transcripts.py --comedian all
```

### Step 4: Check Results
```bash
# Count examples
wc -l data/processed/combined/train.jsonl

# View sample
head -1 data/processed/combined/train.jsonl | jq .
```

---

## 📊 Demo Results (Already Collected)

✅ **2 Vir Das videos collected**
- Video 1: 925 words (~2 min)
- Video 2: 1,402 words (~5 min)
- **Total: 2,327 words** (exceeds 1,000 target!)

Location:
- Transcripts: `data/audio_comedy/transcripts/unknown/`
- Training data: `data/processed/unknown/train.jsonl`

---

## 🎯 Full Collection Commands

### Collect All Hindi/Hinglish Comedians
```bash
# Search for all
python3 search_youtube_videos.py --max 5 --output hindi_videos.json

# Batch collect with report
python3 batch_collect_indian_comedy.py --language hindi_hinglish --config hindi_videos.json --strategy whisper --report hindi_report.json
```

### Collect Bengali Comedians
```bash
# Search for Bengali comedians
python3 search_youtube_videos.py --comedian "Mir Afsar Ali" --max 5 --output bengali_videos.json
python3 search_youtube_videos.py --comedian "Sourav Ghosh" --max 3 --output sourav.json

# Merge and collect
cat bengali_videos.json sourav.json | jq -s 'add' > all_bengali.json
python3 batch_collect_indian_comedy.py --language bengali --config all_bengali.json --strategy whisper --report bengali_report.json
```

### Collect Everything at Once
```bash
# Search all comedians
python3 search_youtube_videos.py --max 5 --output all_videos.json

# Collect all with full report
python3 batch_collect_indian_comedy.py --config all_videos.json --strategy whisper --report full_report.json

# Process all to training format
python3 process_youtube_transcripts.py --comedian all
```

---

## 📁 What Gets Created

### Raw Transcripts
```
data/audio_comedy/transcripts/
├── vir_das/
│   ├── VIDEO1_transcript.json
│   └── VIDEO2_transcript.json
├── zakir_khan/
│   └── VIDEO3_transcript.json
└── mir_afsar_ali/
    └── VIDEO4_transcript.json
```

### Training Data
```
data/processed/
├── vir_das/
│   ├── train.jsonl
│   └── val.jsonl
├── zakir_khan/
│   ├── train.jsonl
│   └── val.jsonl
└── combined/
    ├── train.jsonl
    └── val.jsonl
```

---

## 🔧 Troubleshooting

### YouTubeTranscriptApi blocked?
**Normal!** Use `--strategy whisper` instead (more reliable anyway).

### Slow transcription?
Expected! Whisper takes ~1-2 min per 10 min video.

### Out of memory?
Use smaller model:
```python
# In collect_indian_comedy.py, change:
whisper_model = whisper.load_model('tiny')  # Instead of 'base'
```

### No word-level timestamps?
Only happens with YouTube API. Use Whisper strategy instead.

---

## 📈 Check Progress

### Count collected videos
```bash
find data/audio_comedy/transcripts -name "*_transcript.json" | wc -l
```

### Count total words
```bash
cat data/processed/combined/train.jsonl | jq -s 'map(.total_words) | add'
```

### View collection report
```bash
cat collection_report.json | jq .
```

### Check language distribution
```bash
cat data/processed/combined/train.jsonl | jq -s 'group_by(.language) | map({language: .[0].language, count: length})'
```

---

## 🎓 Next Steps After Collection

1. **Verify data quality**
   ```bash
   # Check language detection
   cat data/audio_comedy/transcripts/*/*.json | jq -r '.language' | sort | uniq -c
   ```

2. **Run weak label refinement**
   ```bash
   python3 training/refine_weak_labels_nemotron.py \
     --input data/processed/combined/train.jsonl \
     --output data/processed/combined/train_refined.jsonl
   ```

3. **Train multilingual model**
   ```bash
   python3 training/xlmr_standup_word_level.py \
     --train_data data/processed/combined/train_refined.jsonl \
     --val_data data/processed/combined/val.jsonl \
     --languages en,hi-latn,bn
   ```

---

## 📚 Full Documentation

- **Detailed Guide**: `INDIAN_COMEDY_COLLECTION.md`
- **Collection Report**: `COLLECTION_REPORT.md`
- **Script Help**: Each script has `--help` flag

---

## 🎉 Targets

| Language | Target | Command to Check |
|----------|--------|------------------|
| Hindi/Hinglish | 1,000+ words | `cat data/processed/combined/train.jsonl | jq -s 'map(select(.language=="hi-latn") \| .total_words) \| add'` |
| Bengali | 500+ words | `cat data/processed/combined/train.jsonl | jq -s 'map(select(.language=="bn") \| .total_words) \| add'` |

---

**Ready to collect! Start with:**
```bash
python3 search_youtube_videos.py --comedian "Zakir Khan" --max 5 --output zakir.json
```
