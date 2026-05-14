# Data Collection Status Report
**Project:** autonomous_laughter_prediction_essential
**Generated:** 2026-05-02
**Working Directory:** /Users/Subho/autonomous_laughter_prediction_essential

---

## 1. Audio Comedy Collection

### Collected Comedians

| Comedian | Audio Files | Transcripts | Total Audio Size |
|----------|-------------|-------------|------------------|
| Ali Wong | 3 | 3 | ~46 MB |
| Dave Chappelle | 1 | 0 | ~98 MB |
| John Mulaney | 2 | 0 | ~113 MB |

**Status:** Audio collected for 3 comedians (6 total videos), but **transcripts only for Ali Wong**.

### Data Locations
- Audio: `data/audio_comedy/audio/{comedian}/`
- Transcripts: `data/audio_comedy/transcripts/{comedian}/`
- Manifest: `data/audio_comedy/ali_wong_manifest.json`

---

## 2. JSONL Data Files

### Local Project Files (data/)

| File | Lines | Status |
|------|-------|--------|
| `enhanced_comedy_large.jsonl` | 0 | EMPTY |
| `enhanced_comedy_medium.jsonl` | 0 | EMPTY |
| `enhanced_comedy_small.jsonl` | 0 | EMPTY |
| `integrated_comedy_data.jsonl` | 0 | EMPTY |
| `sample_transcripts.jsonl` | 16 | Synthetic examples |
| `standup_transcript_examples.jsonl` | 16 | Synthetic examples |

**Total usable local text data: 32 lines (synthetic only)**

### Real Training Data (run_42_transfer_minimal/data/)

| File | Lines | Description |
|------|-------|-------------|
| `train_merged.jsonl` | 1515 | Real transcribed comedy |
| `valid_merged.jsonl` | 306 | Validation set |
| `test_merged.jsonl` | 69 | Test set |

**This is the actual working dataset.** Contains word-level labeled data with laughter annotations.

---

## 3. Subtitle Harvester Analysis

**Location:** `data/harvesters/subtitle_harvester.py`

### Integrated Sources
1. **OpenSubtitles API** - Requires API key, searches for subtitles
2. **Scraps from the Loft** - Web scraping of text transcripts
3. **Addic7ed** - Not fully implemented in code

### Missing: YouTubeTranscriptApi Integration

The harvester does **NOT** have `youtube-transcript-api` integration. This is a critical gap since:
- Most standup comedy specials are on YouTube
- YouTube provides automatic captions with timestamps
- Timestamps are essential for laughter detection training

**Recommendation:** Add `youtube-transcript-api` support for automated subtitle collection.

---

## 4. Data Quality Issues

### Identified Problems

1. **Missing Transcripts for Dave Chappelle & John Mulaney**
   - 3 out of 6 audio files lack transcripts
   - Cannot use for training without text

2. **Empty Enhanced JSONL Files**
   - 4 JSONL files exist but contain zero records
   - Pipeline not producing output

3. **Synthetic Data Only in Local Project**
   - 32 lines of synthetic standup examples
   - Insufficient for real training

4. **No Timestamps on Local Data**
   - Transcripts lack precise timing information
   - Limits utility for audio-aligned training

---

## 5. Priority Comedians NOT Yet Collected

### High Priority (Standalone Specials Available)
- **Kevin James** - Many full specials
- **Jim Gaffigan** - Well-documented specials
- **Robin Williams** - Classic material
- **Jerry Seinfeld** - Clean delivery patterns
- **Dave Chappelle** - Already have audio, need transcripts
- **John Mulaney** - Already have audio, need transcripts

### Medium Priority
- **Amy Schumer** - Popular specials
- **Ali Wong** - Already collected (2 more specials available)
- **Ricky Gervais** - Multiple specials

### Lower Priority
- **John Oliver** - More structured/less spontaneous
- **George Carlin** - Estate issues possible

---

## 6. Recommended Next Collection Targets

### Immediate Actions

1. **Complete Transcript Collection for Existing Audio**
   - Dave Chappelle: 1 video needs transcript
   - John Mulaney: 2 videos need transcripts

2. **Add YouTubeTranscriptApi to Harvester**
   ```bash
   pip install youtube-transcript-api
   ```
   - Enables automatic caption fetching
   - Provides timestamps for alignment

3. **Expand Comedian Collection**
   - Target: Jerry Seinfeld (clean patterns)
   - Target: Jim Gaffigan (reliable transcripts)
   - Target: Kevin James (audio quality good)

### Data Pipeline Improvements

1. **Populate Enhanced JSONL Files**
   - Process existing audio/transcripts
   - Generate word-level labeled training data

2. **Integrate with run_42_transfer_minimal/data/**
   - Consider merging into unified dataset
   - Cross-reference available comedians

---

## 7. Available Data Sources Summary

| Source | Type | Status | Notes |
|--------|------|--------|-------|
| Audio files | Audio | 6 videos, 3 comedians | Need transcripts for 3 |
| Ali Wong transcripts | Text | 3 complete | Best quality |
| Synthetic JSONL | Text | 32 lines | Insufficient |
| run_42 train data | Text+Labels | 1890 lines | Main training set |
| OpenSubtitles | Subtitles | API key needed | Limited comedy |
| Scraps from Loft | Transcripts | 3 comedians scraped | Web scraping |
| YouTube Captions | Subtitles | NOT INTEGRATED | Critical gap |

---

## 8. Priority Recommendations

1. **HIGH:** Add YouTubeTranscriptApi to subtitle_harvester.py
2. **HIGH:** Complete transcript collection for existing audio (Dave Chappelle, John Mulaney)
3. **MEDIUM:** Process audio files to generate training data in enhanced JSONL format
4. **MEDIUM:** Collect new comedian data (Jerry Seinfeld, Jim Gaffigan)
5. **LOW:** Clean up empty JSONL files or populate them