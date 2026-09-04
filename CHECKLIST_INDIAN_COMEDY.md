# Indian Comedy Data Collection - Final Checklist

## ✅ Tasks Completed

### Pipeline Creation
- [x] Created `search_youtube_videos.py` - Video search tool
- [x] Created `collect_indian_comedy.py` - Individual video collection
- [x] Created `batch_collect_indian_comedy.py` - Batch collection with stats
- [x] Updated `process_youtube_transcripts.py` - Training format conversion (existed)
- [x] Created `indian_comedy_urls.json` - Video URL configuration

### Documentation
- [x] Created `INDIAN_COMEDY_COLLECTION.md` - Detailed user guide
- [x] Created `COLLECTION_REPORT.md` - Full technical report
- [x] Created `QUICKSTART_INDIAN_COMEDY.md` - 5-minute quick start
- [x] Created `INDIAN_COMEDY_SUMMARY.md` - Complete summary
- [x] Created `CHECKLIST_INDIAN_COMEDY.md` - This checklist

### Demo Collection
- [x] Collected 2 Vir Das videos (demo)
- [x] Transcribed with Whisper
- [x] Verified language detection (Hindi)
- [x] Verified word-level timestamps
- [x] Processed to training format
- [x] Verified data quality

---

## 📊 Current Data Status

### Hindi/Hinglish
- [x] **Target**: 1,000+ words
- [x] **Current**: 2,327 words
- [x] **Status**: ✅ EXCEEDED
- [x] **Videos**: 2 (Vir Das)

### Bengali
- [ ] **Target**: 500+ words
- [ ] **Current**: 0 words
- [ ] **Status**: ⚠️ NOT STARTED
- [ ] **Videos**: 0

---

## 🎯 Next Steps (Priority Order)

### Priority 1: Collect Bengali Data (HIGH)
```bash
cd training

# Search for Mir Afsar Ali
python3 search_youtube_videos.py --comedian "Mir Afsar Ali" --max 5 --output mir_afsar.json

# Search for Sourav Ghosh
python3 search_youtube_videos.py --comedian "Sourav Ghosh" --max 3 --output sourav.json

# Collect Bengali videos
python3 batch_collect_indian_comedy.py --language bengali --config mir_afsar.json --strategy whisper
python3 batch_collect_indian_comedy.py --language bengali --config sourav.json --strategy whisper

# Verify
find data/audio_comedy/transcripts -name "*mir_afsar*" -o -name "*sourav*" | wc -l
```

### Priority 2: Expand Hindi/Hinglish Collection
```bash
# Search for Zakir Khan
python3 search_youtube_videos.py --comedian "Zakir Khan" --max 5 --output zakir.json

# Search for Biswa Kalyan Rath
python3 search_youtube_videos.py --comedian "Biswa Kalyan Rath" --max 5 --output biswa.json

# Collect
python3 batch_collect_indian_comedy.py --language hindi_hinglish --config zakir.json --strategy whisper
python3 batch_collect_indian_comedy.py --language hindi_hinglish --config biswa.json --strategy whisper
```

### Priority 3: Process All Data
```bash
# Process all transcripts to training format
python3 process_youtube_transcripts.py --comedian all

# Verify
wc -l data/processed/combined/train.jsonl
wc -l data/processed/combined/val.jsonl
```

### Priority 4: Weak Label Refinement
```bash
# Add laughter labels using teacher model
python3 training/refine_weak_labels_nemotron.py \
  --input data/processed/combined/train.jsonl \
  --output data/processed/combined/train_refined.jsonl \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b
```

### Priority 5: Train Multilingual Model
```bash
# Train XLM-R with English + Hindi + Bengali
python3 training/xlmr_standup_word_level.py \
  --train_data data/processed/combined/train_refined.jsonl \
  --val_data data/processed/combined/val.jsonl \
  --languages en,hi-latn,bn \
  --output_dir experiments/xlmr_multilingual_indian
```

---

## ✅ Verification Commands

### Check Collection Progress
```bash
# Count total videos collected
find data/audio_comedy/transcripts -name "*_transcript.json" | wc -l

# Count by comedian
find data/audio_comedy/transcripts -type d -mindepth 1 -maxdepth 1 | while read dir; do
  echo "$(basename $dir): $(find $dir -name "*_transcript.json" | wc -l)"
done

# Count total words
cat data/processed/combined/train.jsonl | jq -s 'map(.total_words) | add'

# Check language distribution
cat data/processed/combined/train.jsonl | jq -s 'group_by(.language) | map({language: .[0].language, count: length})'
```

### Check Transcript Quality
```bash
# Sample transcript
cat data/audio_comedy/transcripts/*/ufHrTI_E4Kk_transcript.json | jq '.metadata'

# Check language detection
cat data/audio_comedy/transcripts/*/*.json | jq -r '.language' | sort | uniq -c

# Verify word-level timestamps
cat data/audio_comedy/transcripts/*/*.json | jq '.segments[0].words' | grep -q "word" && echo "✅ Word-level timestamps present" || echo "❌ No word-level timestamps"
```

---

## 📈 Target Tracking

| Metric | Target | Current | Command to Check |
|--------|--------|---------|------------------|
| Hindi/Hinglish words | 1,000+ | 2,327 | `cat data/processed/combined/train.jsonl \| jq -s 'map(select(.language=="hi-latn") \|.total_words) \| add'` |
| Bengali words | 500+ | 0 | `cat data/processed/combined/train.jsonl \| jq -s 'map(select(.language=="bn") \|.total_words) \| add'` |
| Total videos | 10-15 | 2 | `find data/audio_comedy/transcripts -name "*_transcript.json" \| wc -l` |
| Languages | 2 (hi, bn) | 1 (hi) | `cat data/processed/combined/train.jsonl \| jq -s 'map(.language) \| unique'` |

---

## 🛠️ Tools Summary

| Tool | Purpose | Status |
|------|---------|--------|
| `search_youtube_videos.py` | Search for videos | ✅ Working |
| `collect_indian_comedy.py` | Download & transcribe | ✅ Working |
| `batch_collect_indian_comedy.py` | Batch collection | ✅ Working |
| `process_youtube_transcripts.py` | Convert to training format | ✅ Working |

---

## 📝 Notes

### What Works Well
- ✅ Whisper transcription is reliable
- ✅ Language detection is accurate
- ✅ Word-level timestamps are precise
- ✅ Batch processing is efficient
- ✅ Error handling is robust

### What to Watch Out For
- ⚠️ YouTubeTranscriptApi often blocked (use Whisper instead)
- ⚠️ Transcription is slow (1-2 min per 5 min video)
- ⚠️ No laughter markers in raw transcripts (need refinement)
- ⚠️ Hinglish detected as Hindi (minor issue)

### Recommendations
1. **Always use Whisper strategy** for Indian content
2. **Collect 3-5 videos per comedian** for good coverage
3. **Run weak label refinement** before training
4. **Mix of short (5-10 min) and long (20-30 min) videos** is ideal
5. **Verify language detection** manually for quality control

---

## 🎉 Success Metrics

### When Complete
- [ ] Hindi/Hinglish: 1,000+ words ✅
- [ ] Bengali: 500+ words
- [ ] Total: 10+ videos
- [ ] All languages: 2+ (hi, bn)
- [ ] All transcripts processed
- [ ] Weak labels refined
- [ ] Model trained

### Quality Checks
- [ ] All transcripts have word-level timestamps
- [ ] Language detection verified manually
- [ ] No duplicate videos
- [ ] Training format validated
- [ ] Laughter labels added

---

## 🚀 Quick Commands Reference

### Search & Collect (One Comedian)
```bash
cd training
python3 search_youtube_videos.py --comedian "NAME" --max 5 --output name.json
python3 batch_collect_indian_comedy.py --config name.json --strategy whisper
```

### Search & Collect (All)
```bash
cd training
python3 search_youtube_videos.py --max 5 --output all.json
python3 batch_collect_indian_comedy.py --config all.json --strategy whisper --report report.json
```

### Process & Train
```bash
python3 process_youtube_transcripts.py --comedian all
python3 training/refine_weak_labels_nemotron.py --input data/processed/combined/train.jsonl --output data/processed/combined/train_refined.jsonl
python3 training/xlmr_standup_word_level.py --train_data data/processed/combined/train_refined.jsonl --val_data data/processed/combined/val.jsonl
```

---

**Created**: 2026-05-03
**Status**: ✅ Pipeline Ready, Hindi Data Collected, Bengali Pending
**Next Priority**: Collect Bengali comedy data
