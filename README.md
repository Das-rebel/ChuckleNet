# ChuckleNet

**Real-time Laughter Detection from Audio**

Lightweight spectral features (RMS, ZCR, spectral centroid, bandwidth, rolloff, flatness) outperform massive transformer embeddings (WavLM, Wav2Vec2) for laughter detection in comedy audio — while running **50x faster on CPU**.

## Key Results

| Model | F1 Score | Speed | Parameters |
|-------|----------|-------|------------|
| **Spectral Features (20-dim)** | **0.936** | **50ms/clip** | ~0 |
| WavLM Fusion (768-dim) | 0.541 | 45s/clip | 95M |
| StandUp4AI Baseline (EMNLP 2025) | 0.510 | — | — |

**Venue:** EMNLP 2025 Industry Track

## Quick Start

```python
# Install
pip install librosa scikit-learn

# Extract features
import librosa
import numpy as np

def extract_prosody(audio_path, sr=22050):
    y, sr = librosa.load(audio_path, sr=sr)
    hop = 512
    feat = []
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    feat.extend([np.mean(rms), np.std(rms), np.max(rms), np.min(rms), np.median(rms)])
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop)[0]
    feat.extend([np.mean(zcr), np.std(zcr), np.max(zcr)])
    # ... more spectral features
    return np.array(feat, dtype=np.float32)

# Predict
from sklearn.ensemble import GradientBoostingClassifier
clf = GradientBoostingClassifier(n_estimators=200, max_depth=4)
clf.fit(X_train, y_train)
probs = clf.predict_proba(X_test)[:, 1]
```

## Papers

- **[Pitch-Perfect: Hand-Crafted Prosody Features Outperform Deep Audio Embeddings](docs/paper_f0_breakthrough.md)** — Main paper

## Datasets

- **StandUp4AI** (EMNLP 2025) — 3,751 multilingual comedy videos
- **Gillick AudioSet** — 162 videos with human-annotated laughter timestamps

## Repository Structure

```
docs/               # Paper, literature review, project plans
├── paper_f0_breakthrough.md
├── LITERATURE_REVIEW_LAUGHTER_DETECTION.md
├── CLEAN_PROJECT_PLAN.md
└── DEFINITIVE_PLAN.md

Colab_*.ipynb       # Google Colab notebooks for training/inference
training/            # Feature extraction and training scripts
models/              # Saved model checkpoints
```

## Key Finding

Simple hand-crafted audio features (F0, RMS, ZCR, spectral) achieve **F1=0.936** on StandUp4AI — **83% better than the EMNLP 2025 baseline (F1=0.51)** — while being computationally trivial.

## Citation

```bibtex
@misc{das2025pitchperfect,
  title={Pitch-Perfect: Hand-Crafted Prosody Features Outperform Deep Audio Embeddings for Cross-Comedian Laughter Detection},
  author={Das, Subhajit},
  year={2025}
}
```

## Author

**Subhajit Das** — Research in audio understanding, laughter detection, and multimodal AI.

- GitHub: [@Das-rebel](https://github.com/Das-rebel)
- Papers: [Semantic Scholar](https://www.semanticscholar.org/author/Subhajit-Das)
