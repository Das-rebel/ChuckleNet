# Data Directory

This directory contains datasets for training and evaluating the biosemiotic laughter prediction model.

## Dataset Structure

Training data should be in CSV format with the following columns:
- `text`: The input text (joke, pun, or humor content)
- `label`: Binary label (1 = humorous, 0 = not humorous)

Optional columns:
- `score`: Audience engagement score (upvotes, etc.)
- `source`: Dataset source identifier

## Acquiring Datasets

### Reddit Humor Dataset
1. Use Reddit API or PRAW library
2. Filter for posts with humor-related flair
3. Use upvotes as engagement proxy

### SemEval Sarcasm Data
1. Download from SemEval competition page
2. Process multi-language sarcasm annotations

## Preprocessing

```python
import pandas as pd

# Load raw data
df = pd.read_csv("raw_data.csv")

# Basic cleaning
df["text"] = df["text"].str.strip()
df = df[df["text"].str.len() > 0]

# Save in required format
df.to_csv("processed_data.csv", index=False)
```

## Citation

If using external datasets, cite the original sources as specified in their respective licenses.
