# Current Status - 2026-05-19

## Pipeline Status

| Component | Status | Count |
|-----------|--------|-------|
| Aligned segments | 389,686 | 3.9% of 10M |
| Laughter labels | 47,642 (12.2%) | Positive class |
| Non-laughter | 342,044 (87.8%) | Negative class |
| Audio files | 1,379 | Tracked in DB |
| Videos aligned | 71 | With segments |
| GDrive backup | 34.9 GB | Backed up |

## Model Performance

| Model | F1 Score | Status |
|-------|----------|--------|
| XLM-R (text only) | 0.82 | Working |
| Audio (pause only) | 0.20 | Weak baseline |
| TF-IDF baseline | 0.73 | Baseline |
| Biosemotic (LLM) | 0.829 | LABEL LEAKAGE |
| Target (prosody) | >0.40 | Testing on Colab |
| Target (text+audio) | >0.87 | Future |

## Research Progress

### CONFIRMED
- H5: Temporal position (p=4e-143)
- H4.6: TF-IDF baseline (F1=0.73)
- H4.5: Split leakage (1.9%)

### REJECTED  
- H1.5: Pause F1≥0.55 (F1=0.20)
- H4.4: Biosemotic leakage (invalid)

### TESTING
- H6.1: F0 DROP at punchline (Colab notebook ready)
- H12: Interaction Model architecture
- H13: MultiLinguahah (BYOL-A)
- H14: Text + Audio fusion

### Key Papers
- Pickering 2009: F0 DROP at punchline
- Purandare 2006: Pause 0.8s before punchline
- Bachorowski 2001: Laughter 250-500Hz
- MultiLinguahah 2026: BYOL-A + Isolation Forest
- Interaction Model: 200ms chunks, no VAD

## Background Agents
1. Download MED tier batch28-29 (running)
2. Transcribe batch24-27 audio (running)

## Files
- H6_Prosody_Test_Colab.ipynb - Ready to run
- aligned_segments.jsonl - On GDrive
- CURRENT_STATUS.md - This file
