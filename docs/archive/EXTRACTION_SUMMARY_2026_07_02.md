# WavLM Extraction Summary - 2026-07-02

## Status: COMPLETE

Extracted WavLM embeddings for 36 additional videos (71 → 107).

## What Was Done

1. **Identified data gap**: 41 videos had audio but no WavLM embeddings
2. **Skipped 5 long videos** (>60 min): 43O5Y6KXu0E, 36NLny9UG_o, 3ypZxO0Cht0, 2NvLyFoTILI, 4IWPavFgVn0
3. **Extracted 36 videos** in ~40 minutes on CPU

## Final Data Summary

| Metric | Count |
|--------|-------|
| Total WavLM files | 107 |
| Original collection (aligned_utterances) | 71 |
| New from manifest | 36 |
| In manifest with laughter | 178 |
| Remaining to extract | 71 |

## Extraction Details

- **Processing time**: 38.6 minutes total
- **Success rate**: 36/36 (100%)
- **Average per video**: ~1 minute (varied by length)
- **Format**: Chunked 30s processing to handle long videos

## Files Created

All embeddings saved to: `/Users/Subho/data/chuckle-net/wavlm_embeddings/`

Each file contains:
```json
{
  "video_id": "xxx",
  "embedding": [768 floats...]
}
```

## Next Steps

1. Combine with original 71 videos for training
2. Verify data integrity
3. Train model on expanded dataset
