# Extraction Summary - 2026-07-12

## Critical Fix: Utterance-Level Extraction

### The Problem (What Went Wrong)

#### Video-Level Extraction (WRONG - 2026-07-09)
- Extracted **645 .npy files** to `wavlm_all_embeddings/` on Google Drive
- Each file = one 768-dim embedding for **entire video**
- **USELESS** for laughter prediction (can't identify WHICH utterances get laughs)
- Training on video-level: F1=0.0 (model just predicted all zeros)

#### Colab Path Issue (2026-07-10)
- Only searched `chuckle_audio/` (71 files)
- Missed `chuckle_audio_all/audio` (71), `chuckle_audio_all/audio_all` (249), `chuckle_audio_all/audio_final` (429), `chuckle_audio_all/audio_new` (131)
- Result: Found 71 files, extracted 0 utterances

### The Fix (What Works)

#### Correct Approach: Utterance-Level
```python
# For each utterance segment (start_s → end_s):
segment = audio[start_sample:end_sample]  # Just that utterance's audio
inputs = feature_extractor([segment])
outputs = model(**inputs)
emb = attention_pool(outputs.last_hidden_state)  # 768-dim per utterance
```

#### Correct Audio Paths
```python
search_folders = [
    'chuckle_audio',                    # 71 files
    'chuckle_audio_all/audio',         # 71 files  
    'chuckle_audio_all/audio_all',     # 249 files
    'chuckle_audio_all/audio_final',    # 429 files
    'chuckle_audio_all/audio_new',     # 131 files
]
# Total: 741 audio files, 555 with matching utterances
```

### Notebook: Colab_WavLM_Prosody_Training_v2.ipynb

**GitHub:** `https://github.com/Das-rebel/chuck-audio-notebooks/blob/main/Colab_WavLM_Prosody_Training_v2.ipynb`

**Features extracted per utterance:**
| Feature | Dim | Description |
|---------|-----|-------------|
| wavlm | 768 | Attention-pooled WavLM hidden states |
| prosody | 21 | F0(5) + energy(5) + duration(2) + spectral(5) + voice(4) |
| text | 200 chars | Utterance text |
| label | 1 | 0/1 laughter |

**Key code snippet:**
```python
# Attention pooling (NOT mean pooling)
attn_weights = torch.softmax(torch.nn.Linear(768, 1)(hidden).squeeze(-1), dim=-1)
audio_emb = torch.bmm(attn_weights.unsqueeze(1), hidden).squeeze(1)

# Prosody 21-dim (NOT 9-dim)
prosody = [
    f0_mean, f0_std, f0_max, f0_min, voiced_rate,       # 5 pitch
    energy_mean, energy_std, energy_max, energy_min, energy_range,  # 5 energy
    duration_s, speech_rate,                               # 2 duration
    mfcc1, mfcc2, mfcc3, mfcc_delta, spectral_centroid,  # 5 spectral
    zcr, jitter, shimmer_approx, voiced_rate              # 4 voice quality
]
```

### Data Match Status
```
Audio files on Drive:     741 unique
Videos with labels:       626
Matched (audio + labels): 555
Expected utterances:      ~175,000
Expected positive:       ~1,113 (6.1%)
```

### Previous Wrong Extraction Data
```
Location: gdrive:wavlm_all_embeddings/
Files: 645 .npy files
Format: VIDEO-level (one embedding per video)
Status: USELESS for utterance prediction
Action: Ignore, re-extract with correct notebook
```

### Correct Extraction Data (In Progress)
```
Location: gdrive:wavlm_prosody_utterance_v2/
Format: UTTERANCE-level (one embedding per utterance segment)
Checkpoint: Every 25 videos
Status: In progress (~8 hours on T4 GPU)
```
