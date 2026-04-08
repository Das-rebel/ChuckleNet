# Biosemiotic Laughter Prediction

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-Pending-brightgreen.svg)](https://arxiv.org/abs/XXXX.XXXXX)

**The first biosemiotic framework for computational humor recognition, integrating evolutionary theories of laughter with transformer-based machine learning.**

---

## Architecture

![Biosemiotic Framework Architecture](docs/architecture.svg)

### Core Components

| Component | Description | Performance |
|-----------|-------------|-------------|
| **Duchenne Marker** | Spontaneous vs volitional laughter classification | F1: 0.83 |
| **GCACU Incongruity** | Semantic conflict detection | Acc: 75% |
| **Theory of Mind** | Mental state & audience modeling | R²: 0.68 |
| **Cultural Adapter** | Cross-regional comedy patterns | Nuance: 75.9% |

### Key Innovation: Biosemiotic Integration

Unlike traditional NLP approaches that rely purely on linguistic features, our framework integrates:

1. **Duchenne vs. Volitional Laughter** - Distinguishing spontaneous brainstem-generated laughter from deliberate volitional laughter
2. **Incongruity-Based Sarcasm Detection** - GCACU-inspired semantic conflict analysis
3. **Theory of Mind Modeling** - Mental state trajectory for humor appreciation
4. **Cross-Cultural Nuance Detection** - Adaptive threshold systems

---

## Key Results

### Humor Recognition (Reddit)
| Model | Accuracy | Pun Detection | Audience Prediction (R²) |
|-------|----------|---------------|--------------------------|
| **Biosemiotic Framework** | **75%** | **83%** | **0.68** |
| XLM-RoBERTa (baseline) | 71% | 71% | 0.59 |
| Previous SOTA | 71% | - | - |

### Cross-Cultural Sarcasm Detection
| Model | Accuracy | Cultural Nuance | Consistency |
|-------|----------|-----------------|-------------|
| **Biosemiotic Framework** | **75%** | **75.9%** | **73%** |
| Language-Specific | 71% | 67% | 62% |
| Universal Embeddings | 68% | 61% | 57% |

---

## Training Insights

### Critical Findings from Optimization

| Parameter | Previous (Failed) | Current (Optimal) |
|-----------|------------------|-------------------|
| **Learning Rate** | 1e-4 | 2e-5 |
| **Warmup Steps** | None | 500 |
| **Early Stopping** | None | Patience=2 |

### Loss Trajectory Comparison

```
LR=1e-4 (Overfitting):     LR=2e-5 (Optimal):
0.27 → 0.15 → 0.49 ✗      0.27 → 0.15 → 0.10 ✓
     ↑ spike at 35K              ↑ steady decrease
```

**Key Learning:** Lower LR with warmup prevents the loss spike that occurs around 35K samples when using higher learning rates.

---

## Installation

```bash
git clone https://github.com/yourusername/biosemioticai.git
cd biosemioticai
pip install -r requirements.txt
```

## Quick Start

### Train the Model

```bash
python training/finetune_biosemotic_humor_bert.py \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5 \
    --warmup-steps 500 \
    --early-stopping-patience 2
```

### Evaluate

```bash
python -m biosemioticai.evaluate \
    --model experiments/biosemotic_humor_bert_lr2e5 \
    --data data/training/reddit_jokes/test.csv
```

### Reproduce Results

```bash
python reproduce_results.py
```

---

## Project Structure

```
biosemioticai/
├── README.md                      # This file
├── LICENSE                       # MIT License
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
├── reproduce_results.py          # One-command reproduction
├── src/
│   └── biosemioticai/            # Main package
│       ├── __init__.py
│       ├── evaluate.py            # Evaluation script
│       ├── models/
│       │   ├── __init__.py
│       │   └── biosemiotic_classifier.py
│       └── data/
│           ├── __init__.py
│           └── dataset.py
├── training/
│   └── finetune_biosemotic_humor_bert.py  # Training script
├── experiments/                  # Model checkpoints
├── data/                        # Dataset directory
└── docs/
    ├── architecture.svg          # Architecture diagram
    └── PAPER_DRAFT.md           # Full paper draft
```

---

## Datasets

The model is trained on:
- **Reddit Humor Dataset** - 120,000+ posts with humor labels and audience metrics
- **SemEval Historical Data** - Multi-language sarcasm detection benchmarks

See `data/README.md` for dataset acquisition instructions.

---

## Citation

If you use this research in your work, please cite:

```bibtex
@article{biosemiotic_laughter_2026,
  title={Biosemiotic Laughter Prediction: Integrating Evolutionary Laughter Theory with Transformer-Based Humor Recognition},
  author={[Your Name]},
  booktitle={ACL/EMNLP 2026},
  year={2026}
}
```

See [CITATION.md](CITATION.md) for additional citation formats.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Reddit for dataset access
- Hugging Face for transformer infrastructure
- XLM-RoBERTa model developers
- Biosemotic theory research community
