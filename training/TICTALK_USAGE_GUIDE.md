# TIC-TALK Dataset Loader - Usage Guide

## Overview

The TIC-TALK dataset loader provides comprehensive functionality for loading and processing the TIC-TACK dataset for autonomous laughter prediction. This includes:

- 5,400+ segments from 90 comedy specials
- Kinematic signals (arm spread, trunk lean, body movement)
- Whisper-AT audio-based laughter detection
- Word-level alignment at 0.8-second resolution
- Integration with GCACU training pipeline

## Installation & Setup

### Prerequisites

```bash
# Install required dependencies
pip install torch numpy transformers
```

### File Structure

```
autonomous_laughter_prediction/
├── training/
│   ├── load_tic_talk.py              # Main loader implementation
│   ├── integrate_tictalk_gcacu.py    # GCACU integration
│   └── test_tictalk_loader.py        # Test suite
└── data/
    └── TIC-TALK/                     # Dataset directory
        ├── segments.json              # Required: Main segment data
        ├── kinematics.json            # Optional: Kinematic signals
        └── metadata.json              # Optional: Dataset metadata
```

## Quick Start

### 1. Create Sample Data (for testing)

```bash
# Create sample TIC-TALK data
python training/load_tic_talk.py --create-sample data/sample_tictalk --num-samples 10

# Load and validate sample data
python training/load_tic_talk.py --data-dir data/sample_tictalk
```

### 2. Load TIC-TALK Dataset

```python
from pathlib import Path
from training.load_tic_talk import TICTalkLoader

# Basic usage
loader = TICTalkLoader(data_dir=Path("data/TIC-TALK"))
examples = loader.load()

print(f"Loaded {len(examples)} examples")
print(f"Statistics: {loader.stats}")
```

### 3. Enable Kinematic Features

```python
loader = TICTalkLoader(
    data_dir=Path("data/TIC-TALK"),
    enable_kinematics=True,
    normalize_kinematics=True
)

examples = loader.load()

# Check examples with kinematics
kinematic_examples = [ex for ex in examples if ex.has_kinematics()]
print(f"Examples with kinematics: {len(kinematic_examples)}")
```

### 4. Integration with GCACU Training

```python
from training.integrate_tictalk_gcacu import create_tictalk_dataloaders
from transformers import AutoTokenizer

# Initialize tokenizer
tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")

# Create dataloaders
train_loader, val_loader, dataset_info = create_tictalk_dataloaders(
    data_dir=Path("data/TIC-TALK"),
    tokenizer=tokenizer,
    batch_size=16,
    use_kinematics=True
)

print(f"Training batches: {len(train_loader)}")
print(f"Validation batches: {len(val_loader)}")
print(f"Dataset info: {dataset_info}")
```

## Advanced Usage

### Custom Configuration

```python
loader = TICTalkLoader(
    data_dir=Path("data/TIC-TALK"),
    enable_kinematics=True,
    normalize_kinematics=True,
    laughter_resolution=0.8,  # Whisper-AT resolution in seconds
    cache_kinematics=True      # Cache loaded kinematic data
)
```

### Accessing Individual Examples

```python
examples = loader.load()

# Access first example
example = examples[0]

print(f"ID: {example.example_id}")
print(f"Words: {example.words[:5]}...")  # First 5 words
print(f"Labels: {example.labels[:5]}...")
print(f"Language: {example.language}")
print(f"Has kinematics: {example.has_kinematics()}")

# Access kinematic data
if example.has_kinematics():
    kinematics = example.kinematics
    print(f"Arm spread samples: {len(kinematics.arm_spread)}")
    print(f"Trunk lean samples: {len(kinematics.trunk_lean)}")
    print(f"Body movement samples: {len(kinematics.body_movement)}")
```

### Processing Laughter Segments

```python
# Access laughter timestamps
example = examples[0]

for laughter_seg in example.laughter_segments:
    start = laughter_seg["start"]
    end = laughter_seg["end"]
    print(f"Laughter from {start:.2f}s to {end:.2f}s")

# Get word timestamps if available
if example.word_timestamps:
    for i, (word, (start, end)) in enumerate(zip(example.words, example.word_timestamps)):
        print(f"Word {i}: '{word}' ({start:.2f}s - {end:.2f}s)")
```

### Custom Kinematic Processing

```python
import numpy as np

# Access raw kinematic data
example = examples[0]
kinematics = example.kinematics

# Compute custom features
arm_spread_variance = np.var(kinematics.arm_spread)
trunk_lean_range = kinematics.trunk_lean.max() - kinematics.trunk_lean.min()
body_movement_energy = np.sum(kinematics.body_movement ** 2)

print(f"Arm spread variance: {arm_spread_variance:.4f}")
print(f"Trunk lean range: {trunk_lean_range:.4f}")
print(f"Body movement energy: {body_movement_energy:.4f}")

# Normalize if needed
normalized = kinematics.normalize()
```

## Data Format

### segments.json Format

```json
[
  {
    "segment_id": "special001_seg005",
    "special_id": "special001",
    "comedian": "John Doe",
    "words": ["Hello", "world", "everyone"],
    "word_timestamps": [[0.0, 0.5], [0.5, 1.0], [1.0, 1.5]],
    "laughter_timestamps": [
      {"start": 0.8, "end": 1.2}
    ],
    "whisper_at_confidence": 0.85,
    "language": "en"
  }
]
```

### kinematics.json Format

```json
{
  "special001_seg005": {
    "arm_spread": [0.1, 0.2, 0.15, ...],
    "trunk_lean": [0.3, 0.4, 0.35, ...],
    "body_movement": [0.5, 0.6, 0.55, ...],
    "timestamps": [0.0, 0.1, 0.2, ...],
    "confidence": [0.9, 0.8, 0.85, ...]
  }
}
```

## Testing

### Run Full Test Suite

```bash
# Run all tests
python training/test_tictalk_loader.py --full-suite

# Run with quiet output
python training/test_tictalk_loader.py --full-suite --quiet
```

### Validate Dataset

```bash
# Validate existing dataset
python training/test_tictalk_loader.py --validate data/TIC-TALK
```

### Test Categories

1. **Sample Data Creation** - Verifies sample data generation
2. **Basic Loading** - Tests fundamental loading functionality
3. **Kinematic Loading** - Validates kinematic signal processing
4. **Word-level Alignment** - Tests laughter label alignment accuracy
5. **Kinematic Normalization** - Verifies signal normalization
6. **GCACU Conversion** - Tests format conversion for training
7. **Error Handling** - Validates error handling for invalid data
8. **Statistics Tracking** - Tests statistics computation
9. **Multimodal Integration** - Tests GCACU pipeline integration
10. **Edge Cases** - Tests boundary conditions

## Training Integration

### Prepare Dataset for Training

```bash
# Prepare TIC-TALK dataset for GCACU training
python training/integrate_tictalk_gcacu.py \
    --data-dir data/TIC-TALK \
    --output-dir data/tictalk_prepared \
    --use-kinematics
```

### Use in Training Script

```python
from training.integrate_tictalk_gcacu import prepare_tictalk_for_training

# Prepare dataset
result = prepare_tictalk_for_training(
    data_dir=Path("data/TIC-TALK"),
    output_dir=Path("data/tictalk_prepared"),
    use_kinematics=True
)

# Access prepared data
examples = result["examples"]
dataset = result["dataset"]
config = result["config"]
```

## Performance Tips

1. **Enable Caching**: Use `cache_kinematics=True` for faster repeated access
2. **Batch Processing**: Process data in batches for memory efficiency
3. **Filter Examples**: Filter by kinematics availability if needed
4. **Normalization**: Always normalize kinematics for training consistency

## Troubleshooting

### Common Issues

1. **FileNotFoundError**: Check dataset directory structure
2. **ValueError**: Verify JSON format in segments.json
3. **Memory Issues**: Reduce batch size or disable kinematics
4. **Slow Loading**: Enable caching and reduce data size

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

loader = TICTalkLoader(data_dir=Path("data/TIC-TALK"))
examples = loader.load()
```

## API Reference

### TICTalkLoader

```python
TICTalkLoader(
    data_dir: Union[str, Path],
    enable_kinematics: bool = True,
    normalize_kinematics: bool = True,
    laughter_resolution: float = 0.8,
    cache_kinematics: bool = True
)
```

### TICTalkExample

```python
@dataclass
class TICTalkExample:
    example_id: str
    words: List[str]
    labels: List[int]
    language: str = "en"
    metadata: Dict[str, Any]
    kinematics: Optional[KinematicSignals]
    word_timestamps: Optional[List[Tuple[float, float]]]
    laughter_segments: List[Dict[str, float]]
```

### KinematicSignals

```python
@dataclass
class KinematicSignals:
    arm_spread: np.ndarray
    trunk_lean: np.ndarray
    body_movement: np.ndarray
    timestamps: np.ndarray
    confidence: np.ndarray

    def normalize(self) -> 'KinematicSignals'
    def to_dict(self) -> Dict[str, Any]
```

## Contributing

To extend the loader for additional features:

1. Add new methods to `TICTalkLoader` class
2. Update `TICTalkExample` dataclass if needed
3. Add corresponding tests in `test_tictalk_loader.py`
4. Update this documentation

## Citation

If you use the TIC-TALK dataset loader in your research, please cite:

```
@software{tictalk_loader_2025,
  title={TIC-TALK Dataset Loader for Autonomous Laughter Prediction},
  author={Autonomous Laughter Prediction Team},
  year={2025},
  url={https://github.com/your-repo/autonomous-laughter-prediction}
}
```