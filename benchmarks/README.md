# Autonomous Laughter Prediction - Benchmark Infrastructure

**Agent 1 Implementation: Universal Data Loading & Preprocessing Framework**

Comprehensive data infrastructure for autonomous laughter prediction research supporting all 9 major academic benchmarks.

## 🎯 Mission Accomplished

✅ **Universal Benchmark Data Loader** - Supports all 9 academic benchmark formats
✅ **Standard Preprocessing Pipeline** - Tokenization, alignment, splitting
✅ **Proper Split Protocols** - Speaker-independent, cross-domain, stratified
✅ **Data Quality Validation** - Comprehensive integrity checks
✅ **Efficient Caching System** - Memory optimization and fast access

## 📊 Supported Academic Benchmarks

1. **StandUp4AI** - Multimodal stand-up comedy laughter detection (~50 hours)
2. **UR-FUNNY** - Large-scale humor detection from jokes (~22K jokes)
3. **TED Laughter Corpus** - Laughter in TED presentations
4. **SCRIPTS** - TV show script humor detection
5. **MHD** - Multimodal humor detection
6. **Kuznetsova** - Cross-domain humor detection
7. **Bertero & Fung** - Conversational humor detection
8. **MuSe-Humor** - Multimodal sentiment and humor
9. **FunnyNet-W** - Web-based humor detection

## 🏗️ Architecture

```
benchmarks/
├── datasets/           # Specific dataset implementations
│   ├── standup4ai.py
│   ├── ur_funny.py
│   ├── ted_laughter.py
│   ├── multimodal_humor.py
│   ├── humor_detection.py
│   └── __init__.py
├── utils/              # Core infrastructure
│   ├── base_dataset.py      # Base dataset class
│   ├── split_manager.py     # Split protocols
│   ├── preprocessing.py     # Preprocessing pipeline
│   ├── validation.py        # Data validation
│   ├── data_manager.py      # Caching system
│   └── __init__.py
├── examples/           # Usage examples
│   └── demo_infrastructure.py
└── __init__.py        # Package initialization
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Import the package
from benchmarks import get_dataset, SplitManager, DataValidator
```

### Basic Usage

```python
from benchmarks import get_dataset, SplitConfig, SplitManager

# Load any benchmark dataset
dataset = get_dataset(
    'standup4ai',
    data_path='/path/to/data',
    split='train'
)

# Create proper splits
split_config = SplitConfig(speaker_independent=True)
split_manager = SplitManager(split_config, 'standup4ai')
train_idx, val_idx, test_idx = split_manager.create_splits(
    dataset.samples,
    speaker_ids=[s.speaker_id for s in dataset.samples],
    labels=[s.label for s in dataset.samples]
)

# Access data
for sample in dataset:
    text = sample.text
    label = sample.label
    # ... use for training
```

## 🔧 Core Components

### 1. Universal Data Loading

```python
from benchmarks import get_dataset, list_datasets

# List available datasets
print(list_datasets())

# Load specific dataset
dataset = get_dataset('standup4ai', data_path='path/to/data')
```

### 2. Advanced Split Protocols

```python
from benchmarks import SplitConfig, SplitManager

# Speaker-independent splits (for comedy datasets)
config = SplitConfig(speaker_independent=True, random_seed=42)
manager = SplitManager(config, 'dataset_name')
train_idx, val_idx, test_idx = manager.create_splits(
    samples, speaker_ids, show_ids, labels
)
```

### 3. Comprehensive Preprocessing

```python
from benchmarks import AudioConfig, VideoConfig, TextConfig
from benchmarks import AudioPreprocessor, VideoPreprocessor, TextPreprocessor

# Audio preprocessing
audio_config = AudioConfig(target_sample_rate=16000, n_mels=128)
audio_proc = AudioPreprocessor(audio_config)
audio_features = audio_proc.preprocess('audio.wav')

# Video preprocessing
video_config = VideoConfig(target_fps=25, target_size=(224, 224))
video_proc = VideoPreprocessor(video_config)
video_features = video_proc.preprocess('video.mp4')

# Text preprocessing
text_config = TextConfig(max_length=512, tokenizer='bert-base-uncased')
text_proc = TextPreprocessor(text_config)
text_features = text_proc.preprocess("Funny joke text")
```

### 4. Data Validation

```python
from benchmarks import DataValidator

# Validate dataset quality
validator = DataValidator('dataset_name', 'path/to/data')
report = validator.validate_all(
    dataset.samples,
    checks=['file_exists', 'label_consistency', 'class_balance']
)

# Check results
print(f"Passed: {report.passed_checks}/{report.total_checks}")
report.save_report('validation_report.json')
```

### 5. Efficient Caching

```python
from benchmarks import CacheConfig, DataManager

# Setup caching
cache_config = CacheConfig(
    enable_cache=True,
    cache_dir='./cache',
    max_cache_size_gb=10.0
)
data_manager = DataManager(cache_config, 'dataset_name')

# Cache will automatically speed up data loading
stats = data_manager.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

## 📈 Features

### Universal Interface
- **Single API** for all 9 benchmarks
- **Consistent data format** across datasets
- **Multimodal support** (text, audio, video)
- **Extensible architecture** for new datasets

### Proper Evaluation Protocols
- **Speaker-independent splits** for comedy datasets
- **Show/comedian-independent splits**
- **Stratified splits** for imbalanced data
- **Cross-domain evaluation** support

### Data Quality Assurance
- **File integrity checks**
- **Label consistency validation**
- **Metadata completeness verification**
- **Audio/video quality assessment**
- **Duplicate detection**
- **Class balance analysis**

### Performance Optimization
- **Intelligent caching** of preprocessed data
- **Parallel preprocessing** with multi-threading
- **Memory-efficient** data loading
- **Automatic cache management**
- **Batch processing** optimization

## 🧪 Validation & Testing

Run the comprehensive demo:

```bash
python benchmarks/examples/demo_infrastructure.py
```

This demonstrates:
- Available datasets and their features
- Split management capabilities
- Preprocessing pipeline
- Data validation system
- Caching infrastructure

## 📊 Dataset Statistics

| Dataset | Type | Modalities | Size | Task |
|---------|------|------------|------|------|
| StandUp4AI | Multimodal | Audio, Video, Text | ~50 hours | Laughter Detection |
| UR-FUNNY | Text | Text | ~22K jokes | Humor Detection |
| TED Laughter | Audio + Text | Audio, Text | Multiple talks | Laughter Detection |
| SCRIPTS | Text | Text | TV excerpts | Humor Detection |
| MHD | Multimodal | Audio, Video, Text | Multimodal samples | Humor Detection |
| Kuznetsova | Text | Text | Various sources | Humor Detection |
| Bertero & Fung | Text | Text | Conversations | Humor Detection |
| MuSe-Humor | Multimodal | Audio, Video, Text | Multimodal samples | Humor Recognition |
| FunnyNet-W | Text | Text | Web content | Humor Detection |

## 🔬 Technical Specifications

### Audio Processing
- **Sample Rate**: 16 kHz (configurable)
- **Features**: Mel spectrograms, MFCC, prosodic features
- **Augmentation**: Time stretching, pitch shifting, noise addition
- **Quality Checks**: Duration, silence detection, format verification

### Video Processing
- **Frame Rate**: 25 FPS (configurable)
- **Resolution**: 224x224 (configurable)
- **Features**: Frame-level visual features
- **Augmentation**: Horizontal flip, brightness adjustment
- **Quality Checks**: Resolution, FPS, duration verification

### Text Processing
- **Tokenization**: BERT-based (configurable)
- **Features**: Linguistic features, laughter indicators
- **Max Length**: 512 tokens (configurable)
- **Quality Checks**: Length validation, encoding checks

## 🎓 Usage for Research

### For Agent 2 (StandUp4AI Implementation)

The infrastructure is ready for immediate use:

```python
from benchmarks import StandUp4AIDataset

# Load StandUp4AI dataset
dataset = StandUp4AIDataset(
    data_path='/path/to/standup4ai',
    split='train',
    use_audio=True,
    use_video=True,
    use_text=True
)

# Access multimodal features
for sample in dataset:
    text_features = sample['text_input_ids']
    audio_features = sample['audio']
    video_features = sample.get('video_frames')
    label = sample['label']
```

### For Other Agents

Each benchmark can be loaded with the same simple API:

```python
from benchmarks import get_dataset

# Load any benchmark
dataset = get_dataset('ur_funny', data_path='path/to/data')
dataset = get_dataset('ted_laughter', data_path='path/to/data')
# ... etc for all 9 benchmarks
```

## 📦 Dependencies

See `requirements.txt` for full list. Key dependencies:

- `torch` - PyTorch for deep learning
- `torchaudio` - Audio processing
- `torchvision` - Video/image processing
- `transformers` - Text tokenization
- `librosa` - Audio feature extraction
- `opencv-python` - Video processing
- `pandas` - Data manipulation
- `scikit-learn` - Split management
- `numpy` - Numerical operations

## 🚧 Project Constraints

- **Total Project Size**: <10GB (respected by caching system)
- **Memory Efficiency**: Optimized for large datasets
- **Cross-Platform**: Works on Linux, macOS, Windows
- **Python Version**: 3.8+

## 📝 Next Steps

1. **Agent 2**: Implement StandUp4AI models using this infrastructure
2. **Agent 3**: Add UR-FUNNY implementations
3. **Agent 4**: Integrate additional benchmarks
4. **Agent 5**: Perform cross-domain evaluation
5. **Agent 6**: Create ensemble methods

## 🏆 Success Criteria - All Met

✅ Universal data loader that can handle all 9 benchmark formats
✅ Standardized preprocessing pipeline operational
✅ Proper split protocols implemented (speaker/show/comedian independent)
✅ Data quality validation passing
✅ All infrastructure ready for Agent 2 (StandUp4AI)

## 📞 Support

For questions or issues:
1. Check the comprehensive examples in `benchmarks/examples/`
2. Review dataset-specific documentation in each dataset file
3. Examine the validation reports for data quality issues

---

**Agent 1 - Data Infrastructure Specialist**
*Foundational work complete. Ready for downstream agents.*