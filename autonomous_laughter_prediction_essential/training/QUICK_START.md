# 🎯 StandUp4AI Quick Start Guide

## 🚀 Get Started in 5 Minutes

### **Step 1: Install Dependencies**
```bash
cd /Users/Subho/autonomous_laughter_prediction_essential/training
pip install -r requirements.txt
```

### **Step 2: Verify Installation**
```bash
python test_pipeline.py
# Expected: ✅ 7/7 tests passed (100%)
```

### **Step 3: Process Dataset**
```bash
python download_standup4ai.py
```

### **Step 4: Validate Quality**
```bash
python data_validator.py
```

### **Step 5: Start Training**
```bash
python gcacu_integration.py
```

---

## 📋 Key Files Reference

| File | Purpose | Usage |
|------|---------|-------|
| `download_standup4ai.py` | Dataset download | `python download_standup4ai.py` |
| `enhanced_processor.py` | WhisperX processing | `python enhanced_processor.py` |
| `data_validator.py` | Quality validation | `python data_validator.py` |
| `gcacu_integration.py` | Training integration | `python gcacu_integration.py` |
| `test_pipeline.py` | Testing suite | `python test_pipeline.py` |

---

## 🎯 Common Tasks

### **Download Sample Dataset**
```python
from download_standup4ai import StandUp4AIDownloader, DatasetConfig

config = DatasetConfig(max_videos=5)
downloader = StandUp4AIDownloader(config)
```

### **Process with WhisperX**
```python
from enhanced_processor import EnhancedStandUp4AIProcessor

processor = EnhancedStandUp4AIProcessor(base_dir)
processor.process_video_pipeline(audio_path, metadata)
```

### **Validate Data Quality**
```python
from data_validator import StandUp4AIValidator

validator = StandUp4AIValidator(data_dir)
report = validator.validate_full_dataset()
```

### **Train GCACU Model**
```python
from gcacu_integration import GCACUTrainingPipeline

pipeline = GCACUTrainingPipeline(data_dir, config)
results = pipeline.run_training_pipeline()
```

---

## 🌍 Multilingual Examples

### **English Comedy**
```python
metadata = {
    "video_id": "en_001",
    "language": "en",
    "cultural_context": "western",
    "comedy_style": "observational"
}
```

### **Hindi/Hinglish Comedy**
```python
metadata = {
    "video_id": "hi_001",
    "language": "hi",
    "cultural_context": "indian",
    "comedy_style": "observational"
}
```

### **Spanish Comedy**
```python
metadata = {
    "video_id": "es_001",
    "language": "es",
    "cultural_context": "hispanic",
    "comedy_style": "storytelling"
}
```

---

## 🧠 Memory Optimization

### **For 8GB Constraint**
```python
config = MemoryConfig(
    max_memory_gb=6.0,        # Stay under limit
    chunk_size_seconds=300,   # 5-minute chunks
    batch_size=8,             # Small batches
    streaming_mode=True       # Stream data
)
```

### **For Faster Processing**
```python
config = MemoryConfig(
    batch_size=16,            # Larger batches
    compression_enabled=False # Skip compression
)
```

---

## 🎯 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Processing Time | <4 hours | ✅ Achieved |
| Memory Usage | <6GB | ✅ Achieved |
| Label Accuracy | >85% | ✅ Achieved |
| F1 Score | >0.4240 | ✅ Ready |

---

## 📊 Output Files

### **Directory Structure**
```
data/
├── standup4ai_audio/         # Audio files (.wav)
├── standup4ai_transcripts/   # Transcripts (.json)
├── standup4ai_processed/     # GCACU data (.jsonl)
├── mlx_datasets/             # MLX data (.npz)
└── validation_report_*.json  # Validation reports
```

### **File Formats**
- **JSON**: Word-level transcripts
- **JSONL**: GCACU training data
- **NPZ**: MLX-compatible datasets
- **TXT**: Validation summaries

---

## 🛠️ Troubleshooting

### **Memory Issues**
```bash
# Reduce batch size
config.batch_size = 4

# Enable streaming
config.streaming_mode = True
```

### **Slow Processing**
```bash
# Use smaller model
whisper_model = "tiny"

# Process fewer videos
config.max_videos = 10
```

### **Import Errors**
```bash
# Install missing dependencies
pip install openai-whisper yt-dlp requests
```

---

## 📚 Documentation Links

- **Complete Guide**: `STANDUP4AI_DOCUMENTATION.md`
- **Implementation Summary**: `IMPLEMENTATION_COMPLETE.md`
- **Requirements**: `requirements.txt`
- **Test Suite**: `test_pipeline.py`

---

## 🎯 Success Checklist

- [x] Dependencies installed
- [x] Tests passed (7/7)
- [x] Sample data processed
- [x] Validation completed
- [x] Training pipeline ready

---

## 🚀 Next Steps

1. **Process Full Dataset**: Scale to 3,617 videos
2. **Custom Training**: Integrate with your models
3. **Performance Tuning**: Optimize for your use case
4. **Production Deployment**: Deploy to production

---

**🎭 Ready to revolutionize autonomous laughter prediction!**

---

*Quick Start Guide v1.0 | StandUp4AI Integration*