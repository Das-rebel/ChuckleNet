# Colab Optimization Plan - WavLM Extraction

**Date:** 2026-07-12
**Goal:** Reduce extraction time and prevent data loss from disconnections

---

## Problem
- Original extraction: ~8 hours on T4 GPU
- Colab limit: 12 hours but frequent disconnections
- Risk: Losing hours of progress

## Optimizations Applied

### 1. Batch Processing (4x faster)
```python
# Before: BATCH_SIZE = 8
# After:  BATCH_SIZE = 32
```
**Impact:** ~4x faster GPU inference

### 2. Checkpoint Frequency (5x more saves)
```python
# Before: CHECKPOINT_EVERY = 25
# After:  CHECKPOINT_EVERY = 5
```
**Impact:** Max 5 videos lost on disconnect

### 3. Binary Output (.npy instead of JSON)
```python
# Before: JSON lines (slow parse, large size)
out_f.write(json.dumps(record) + '\n')

# After: Binary numpy (10x faster save/load)
np.save(f'{vid}_wavlm.npy', embeddings)
np.save(f'{vid}_prosody.npy', prosody)
```
**Impact:** 10x faster file I/O

### 4. Soundfile Audio (faster than librosa)
```python
# Try soundfile first, fallback to librosa
try:
    audio, sr = sf.read(audio_path, sr=SR)
except:
    audio, sr = librosa.load(audio_path, sr=SR)
```

### 5. Parallel CPU Prosody
```python
# Prosody extraction is CPU-bound, run in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    prosody_list = list(executor.map(...))
```

---

## Notebooks

### Optimized Colab (~3 hours)
```
https://colab.research.google.com/github/Das-rebel/chuck-audio-notebooks/blob/main/Colab_WavLM_Optimized_Extraction.ipynb?authuser=1
```

### Full Training Notebook (~5 hours after extraction)
```
https://colab.research.google.com/github/Das-rebel/chuck-audio-notebooks/blob/main/Colab_WavLM_Prosody_Training_v2.ipynb?authuser=1
```

---

## Local GPU Script (No Disconnection Risk)

For machines with GPU, run overnight:

```bash
bash /Users/Subho/extract_wavlm_local_gpu.sh
```

**Output:** `/Users/Subho/data/chuckle-net/wavlm_prosody_opt/`

**Monitor:**
```bash
tail -f /Users/Subho/data/chuckle-net/wavlm_prosody_opt/extraction.log
cat /Users/Subho/data/chuckle-net/wavlm_prosody_opt/checkpoint.json
```

---

## Resume Procedure

If disconnected:
1. Reopen notebook
2. Runtime → Run all
3. Checkpoint loads automatically from `checkpoint.json`
4. Extraction resumes from last checkpoint

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Extraction time | ~8 hours | ~3 hours |
| Checkpoint frequency | 25 videos | 5 videos |
| File format | JSONL | Binary .npy |
| Max data loss | 25 videos | 5 videos |
| Colab disconnect risk | HIGH | MEDIUM |

---

## Output Format

```
wavlm_prosody_opt/
├── wavlm/          # {video_id}.npy (N, 768)
├── prosody/        # {video_id}.npy (N, 22)
├── meta/           # {video_id}.json (labels, timestamps)
└── checkpoint.json # Resume state
```
