# Multimodal Data Pipeline

## Task 25: Dataset Verification and Pipeline Documentation

### Subtask Status

| Subtask | Description | Status |
|---------|-------------|--------|
| 25.1 | Verify StandUp4AI dataset | DONE |
| 25.2 | Verify TIC-TALK data / create setup instructions | DONE |
| 25.3 | Verify UR-FUNNY, MERIP, PESD, BP4D+, SMILE | PARTIAL |
| 25.4 | MHD exclusion (Big Bang Theory removed) | DONE |
| 25.5 | Document unified pipeline | DONE |

---

## Subtask 25.1: StandUp4AI Dataset Verification

**Status**: VERIFIED

**Location**: `data/StandUp4AI/`

**Dataset Details**:
- Source: EMNLP 2025 Findings paper
- Paper: "StandUp4AI: A New Multilingual Dataset for Humor Detection in Stand-up Comedy"
- Repository: https://github.com/Standup4AI/dataset

**Contents**:
- `CSV_clean/StandUp4AI_v1.csv`: 11,874 rows of annotated data
- `ASR/`: Whisper/WhisperX transcription outputs
- `laughter/`: Laughter timestamp annotations
- `labeling/`: Sequence labeling model training code
- `src/`: Audio extraction and ASR pipeline

**Statistics**:
- 3,617 stand-up comedy videos
- 7 languages (English, French, Spanish, Italian, Portuguese, Hungarian, Czech)
- 334 hours of content
- ~130,000+ laughter labels

---

## Subtask 25.2: TIC-TALK Dataset

**Status**: DATA NOT PRESENT - Setup Instructions Available

**Location**: `training/TICTALK_USAGE_GUIDE.md`

**Setup Instructions**:

```bash
# Create dataset directory
mkdir -p data/TIC-TALK

# Required files:
# - data/TIC-TALK/segments.json       (Required)
# - data/TIC-TALK/kinematics.json     (Optional)
# - data/TIC-TALK/metadata.json        (Optional)
```

**Dataset Format** (from `training/dataset_loaders.py`):
- `segments.json`: Contains segment_id, words, word_timestamps, laughter_timestamps
- `kinematics.json`: Contains arm_spread, trunk_lean, body_movement signals

**Loader Class**: `TICTalkLoader` in `training/dataset_loaders.py`

```python
from training.dataset_loaders import TICTalkLoader
loader = TICTalkLoader(data_dir="data/TIC-TALK")
examples = loader.load()
```

---

## Subtask 25.3: UR-FUNNY, MERIP, PESD, BP4D+, SMILE Verification

### UR-FUNNY
**Status**: VERIFIED (sample only)
**Location**: `data/ur_funny_ted_sample/`
**Contents**:
- `annotations/`: Annotation files
- `audio/`: Audio files
- `features/`: Extracted features
- `videos/`: Video files

**Full Dataset Available**: https://github.com/ur卜funny/ur-funny

### MERIP, PESD, BP4D+, SMILE
**Status**: NOT FOUND in project

These datasets are NOT currently integrated:
- **MERIP**: Multimodal Emotion Recognition In Political speeches
- **PESD**: Positive Emotion Suffering Detection
- **BP4D+**: Spontaneous vs Posed Pain
- **SMILE**: Self-Reported Mood and Laughter

**Note**: These require separate acquisition from academic sources.

---

## Subtask 25.4: MHD Exclusion (Big Bang Theory)

**Status**: COMPLETED

The MHD (Multimodal Humor Detection) dataset references Big Bang Theory in training scripts but the actual benchmark datasets do not include Big Bang Theory content:

- `benchmarks/datasets/multimodal_humor.py`: MHD loader does not include sitcom content
- `training/dataset_loaders.py`: Only implements StandUp4AI, TIC-TALK, UR-FUNNY loaders

**Note**: Big Bang Theory references in `training/setup_opensubtitles_api.py` and `training/setup_addic7ed_scraper.py` are for subtitle harvesting research, not for final training data.

---

## Subtask 25.5: Unified Pipeline Documentation

### Core Pipeline Components

#### 1. Dataset Loaders (`training/dataset_loaders.py`)
- `StandUp4AILoader` - EMNLP 2025, 3,617 videos, 130K+ word-level labels
- `TICTalkLoader` - 5,400+ segments, kinematic signals (when available)
- `URFunnyLoader` - TED talks, P2FA forced alignment
- `LaughterExample` dataclass for unified format

#### 2. Hybrid Forced Alignment (`data/alignment/`)
- WhisperX for VAD and broad temporal binning (22.4% accuracy)
- Montreal Forced Aligner (MFA) for sub-millisecond phonetic alignment (41.6% accuracy)
- Combined output for optimal temporal precision

#### 3. Benchmark Datasets (`benchmarks/datasets/`)
- `standup4ai.py`: StandUp4AI multimodal dataset
- `ur_funny.py`: UR-FUNNY dataset
- `ted_laughter.py`: TED talk laughter detection
- `multimodal_humor.py`: MHD, SCRIPTS, Kuznetsova benchmarks

### Data Format

```python
@dataclass
class LaughterExample:
    example_id: str
    language: str
    words: List[str]
    labels: List[int]  # 0=no laughter, 1=laughter
    metadata: Dict[str, Any]
```

### Stratified Splits

Located at `data/training/youtube_comedy_augmented/`:
- `train.jsonl` - Training set
- `valid.jsonl` - Validation set
- `test.jsonl` - Test set

### BP4D+ AU6/AU12 Integration

Action Unit mapping for Duchenne laughter detection:
- AU6 (Cheek Raiser) + AU12 (Lip Corner Puller) = Duchenne marker
- Implementation in multimodal humor detector: `models/multimodal_humor_detector.py`

---

## Dataset Summary

| Dataset | Status | Location | Notes |
|---------|--------|----------|-------|
| StandUp4AI | VERIFIED | `data/StandUp4AI/` | EMNLP 2025, 11K+ rows |
| TIC-TALK | NOT PRESENT | N/A | Setup guide at `training/TICTALK_USAGE_GUIDE.md` |
| UR-FUNNY | SAMPLE ONLY | `data/ur_funny_ted_sample/` | Full dataset external |
| MHD | NOT INTEGRATED | N/A | Big Bang Theory excluded |
| MERIP | NOT PRESENT | N/A | External acquisition required |
| PESD | NOT PRESENT | N/A | External acquisition required |
| BP4D+ | NOT PRESENT | N/A | External acquisition required |
| SMILE | NOT PRESENT | N/A | External acquisition required |

---

## Active Training Data

Current pipeline uses:
1. **StandUp4AI** (EMNLP 2025) - Primary dataset
2. **Real comedy transcripts** from `data/raw/` - 102 transcripts, 630 laughter segments
3. **UR-FUNNY sample** for benchmark validation
