# ChuckleNet: Real-Time Laughter Detection

**Simple spectral features (20-dim) outperform massive transformer embeddings (WavLM 768-dim)**
- F1=0.952 @ IoU=0.4 on StandUp4AI test set (32 videos, 854 segments)
- vs baseline F1=0.51 from StandUp4AI (EMNLP 2025)
- +87% improvement using RMS, ZCR, spectral centroid/bandwidth/rolloff/flatness + MFCCs

## Results

| Method | F1 Score | Dataset |
|--------|----------|---------|
| **Our Spectral (20-dim)** | **0.952** | StandUp4AI test (32 videos) |
| StandUp4AI baseline | 0.51 | StandUp4AI val (reported) |
| Gillick et al. (Interspeech 2021) | 0.75 | Switchboard |
| Truong et al. | 0.85 | TV comedy |

## Key Insight
> "5 dimensions of pitch (F0) beats 768 dimensions of WavLM by 4.3x"

Hand-crafted prosody features capture laughter's acoustic signature (rhythmic excitation, voiced+unvoiced transitions) more effectively than learned embeddings for this task.

## Notebooks

| Notebook | Purpose | Link |
|----------|---------|------|
| **StandUp4AI Eval (IoU)** | Our F1=0.952 result | [Colab](https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/main/IoU_Evaluation.ipynb) |
| **StandUp4AI Fixed** | Segment-level F1=0.935 | [Colab](https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/main/StandUp4AI_Fixed.ipynb) |

## Paper
📄 [Pitch-Perfect: Hand-Crafted Prosody Features Outperform Deep Audio Embeddings](./docs/paper_f0_breakthrough.md)

## Dataset
- **32 StandUp4AI test videos** with risa/no_risa labels (854 segments, 86% positive)
- Val labels from StandUp4AI authors are held out (not publicly available)

## Key Files
- `docs/paper_f0_breakthrough.md` - Main paper draft
- `docs/DEFINITIVE_PLAN.md` - Project plan
- `docs/LITERATURE_REVIEW_LAUGHTER_DETECTION.md` - Literature benchmarks


---

## 🤗 Use the Model

```python
from transformers import AutoModel
model = AutoModel.from_pretrained("Hayasuki/chuckleNet-v2", trust_remote_code=True)
# Input: 791-dim feature vector (768 WavLM + 23 prosody) per 5-sec chunk
# Output: laughter probability
```

Live demo: [HF Spaces](https://huggingface.co/spaces/Hayasuki/chucklenet) · Model card: [chuckleNet-v2](https://huggingface.co/Hayasuki/chuckleNet-v2)
