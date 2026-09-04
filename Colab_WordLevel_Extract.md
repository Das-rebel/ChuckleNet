# Colab T4 GPU Word-Level Extraction

**Goal:** Extract word-level WavLM+prosody features for all 976 videos with audio+labels
**Platform:** Google Colab (free T4 GPU)
**Runtime estimate:** 976 videos × 80s/video = 21.8 hours (too long for one session)
**Better approach:** Process in batches of 50-100, checkpoint to Google Drive

## Colab vs Kaggle Comparison

| Factor | Colab T4 | Kaggle P100 | Winner |
|--------|-----------|-------------|--------|
| GPU | T4 (sm_75) | P100 (sm_60) | Tie (T4 more modern) |
| PyTorch compatibility | ✅ Native | ❌ CUDA mismatch | **Colab** |
| Time per video | ~80s | ~80s | Tie |
| Session limit | 12 hours | 9 hours | Tie |
| Checkpointing | Google Drive | Dataset upload | **Colab** |
| Reliability | Can disconnect | More stable | Kaggle |

## Plan: Colab Batch Processing

### Batch Strategy
- **100 videos per Colab session** (~2.2 hours)
- **10 sessions needed** to process all 976 videos
- Features saved to Google Drive: `MyDrive/standup4ai/word_level_features/`
- Checkpoint file: `MyDrive/standup4ai/word_level_checkpoint.json`

### Session Plan
| Session | Videos | Time | Cumulative |
|---------|--------|------|------------|
| 1 | 0-99 | 2.2h | 2.2h |
| 2 | 100-199 | 2.2h | 4.4h |
| 3 | 200-299 | 2.2h | 6.6h |
| 4 | 300-399 | 2.2h | 8.8h |
| 5 | 400-499 | 2.2h | 11h |
| 6 | 500-599 | 2.2h | 13.2h |
| 7 | 600-699 | 2.2h | 15.4h |
| 8 | 700-799 | 2.2h | 17.6h |
| 9 | 800-899 | 2.2h | 19.8h |
| 10 | 900-975 | 1.7h | 21.5h |

### One-Click Colab Links

**Session 1 (videos 0-99):**
https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Colab_WordLevel_Extract.ipynb

**After each session:** Save checkpoint to Google Drive, then start next session.

## Key Features of Colab Notebook
1. **Auto-resume**: Reads checkpoint from Drive, skips already-done videos
2. **WavLM on GPU**: ~80s per video (vs 5-10 min on CPU)
3. **Batch saves**: Every 10 videos saved to Drive
4. **Progress tracking**: Shows ETA and videos remaining
5. **Error recovery**: Skips failed videos, continues with next

## How to Run
1. Open the Colab notebook link
2. Runtime → Change runtime type → **GPU** (T4)
3. Run all cells
4. When session ends (12h), re-open and run again (auto-resumes from checkpoint)
5. After 10 sessions, all 976 videos will be extracted

## Features Saved
Each video produces 3 files on Google Drive:
- `{vid}_features.npy` — 791-dim WavLM+prosody features per word
- `{vid}_labels.npy` — Binary labels (1=laugh, 0=non)
- `{vid}_timestamps.npy` — Word timestamps (start, end)
