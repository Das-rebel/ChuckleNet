# Colab Setup for Prosody Extraction

## Quick Start

1. **Upload this notebook to Google Colab**
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Upload `colab_prosody_extraction.ipynb`

2. **Upload aligned_segments.jsonl**
   - Upload from `data/audio_comedy/aligned_segments.jsonl`

3. **Upload audio files** (in batches)
   - Create folder structure: `data/audio_comedy/audio/batch{N}/`
   - Upload batch1 first (5 files, ~400MB)
   - Or upload batch24-27 (75 files, ~900MB total)

4. **Run cells in order**

## Alternative: Direct Upload

If you have the files already, you can:

```python
# Upload aligned segments
from google.colab import files
uploaded = files.upload()

# For audio, upload zip file and unzip
!mkdir -p data/audio_comedy/audio
!cd data/audio_comedy/audio && unzip -q uploaded_file.zip
```

## Processing More Videos

To process all 388 audio files:
1. Upload audio files in batches (zip each batch folder)
2. Run the extraction cell multiple times
3. Download `prosody_features.csv` after each batch
4. Combine locally

## Kaggle Alternative

On Kaggle:
1. Create new notebook
2. Upload dataset (aligned_segments.jsonl + audio files)
3. Set accelerator to GPU for faster processing
4. Run same code

## Output

The notebook will:
1. Extract F0, energy, pause, duration features
2. Train audio-only classifier
3. Test H6.1 (F0 DROP at punchline)
4. Output F1 score comparing to baseline (F1=0.20)

## Expected Results

| Feature Set | Expected F1 |
|-------------|-------------|
| Simple pause only | 0.20 (baseline) |
| Prosody (F0+energy+pause) | 0.40-0.60 |
| Prosody + text (XLM-R) | 0.85-0.87 |

## H6.1 Validation

If F0 DROP is confirmed (laughter F0 < non-laugh F0):
- Supports Pickering 2009 findings
- Laughter words have lower pitch than non-laugh words
- Consistent with "setup-punchline" structure where punchline has falling intonation