# YouTube Comedy Dataset Quick Start Guide

## Immediate Usage

### 1. Export Production Data
```bash
# Basic export (no augmentation)
cd /Users/Subho/autonomous_laughter_prediction
python3 training/load_youtube_comedy.py \
    --output-dir data/training/youtube_comedy_final \
    --no-augmentation

# Export with augmentation (recommended)
python3 training/load_youtube_comedy.py \
    --output-dir data/training/youtube_comedy_final \
    --augmentation-factor 3
```

### 2. Test the System
```bash
# Run comprehensive test suite
python3 training/test_youtube_comedy_loader.py

# Test with small dataset
python3 training/load_youtube_comedy.py \
    --max-comprehensive 10 \
    --output-dir test_output \
    --verbose
```

## Key Files

- **`training/load_youtube_comedy.py`** - Main loader (866 lines)
- **`training/test_youtube_comedy_loader.py`** - Test suite (21 tests)
- **`data/training/youtube_comedy_final/`** - Production datasets

## Dataset Statistics

**Original**: 30,036 segments (50.7% laughter)
**Augmented**: 52,502 segments (71.8% laughter)
**Words**: 1.2M+ total, 37K+ laughter words

## Revolutionary Features

✅ **YouTube Virality Prediction** - Predict joke performance
✅ **Word-Level Alignment** - Precise laughter labels
✅ **Data Augmentation** - 75% increase in training data
✅ **GCACU Integration** - Ready for existing pipeline
✅ **Production Ready** - 100% test pass rate

## Usage in Training

```python
from training.load_youtube_comedy import YouTubeComedyLoader

loader = YouTubeComedyLoader()
segments = list(loader.load_all_datasets())

# Use with GCACU training pipeline
for segment in segments:
    if segment.has_laughter:
        # Train laughter detection
        pass
```

## Command-Line Options

```bash
--data-dir           # Raw data directory (default: data/raw)
--output-dir         # Output directory (default: data/training/youtube_comedy)
--augmentation-factor # Augmentation factor (default: 3)
--no-augmentation    # Disable augmentation
--max-comprehensive  # Limit comprehensive dataset processing
--verbose            # Enable detailed logging
```

## Test Results

```
Tests run: 21
Successes: 21
Failures: 0
Errors: 0
Status: ✅ PRODUCTION READY
```

## Support

- **Full Documentation**: See `YOUTUBE_COMEDY_INTEGRATION_COMPLETE.md`
- **Test Suite**: Run `python3 training/test_youtube_comedy_loader.py`
- **Issues**: Check logs for detailed error messages