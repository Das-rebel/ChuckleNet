# Word-Level Multilingual Features (40 Videos)

## What's Here
- `word_features/*.npy` - Word-level WavLM+prosody features (791-dim per word)
- `word_features/*_labels.npy` - Binary labels (1=laugh, 0=non-laugh)
- `word_features/*_timestamps.npy` - Word timestamps (start, end)
- `labels/*.csv` - EMNLP ground truth labels (B/I/L/O)
- `train_results.json` - Training results (F1=0.21 on 40 videos)
- `train_results.txt` - Full training log

## Data Summary
- **Videos**: 40 unique videos with word-level features
- **Total words**: 31,143
- **Positive rate**: 11.4% (below 15% threshold - model struggles)
- **Feature dim**: 791 (WavLM 768 + prosody 23)

## Results
- OOF Word F1@0.5: 0.2056
- IoU-F1@0.2: 0.1978
- **Problem**: Only 40 videos, 11.4% positive rate (below 15% threshold)

## Next Steps
1. Extract 858 more videos using Kaggle GPU
2. Train on 900+ videos
3. Expected improvement: F1 → 0.50+, IoU → 0.40+
