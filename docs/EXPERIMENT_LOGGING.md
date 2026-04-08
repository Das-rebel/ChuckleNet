# Experiment Logging Guide

This document describes the experiment logging infrastructure for the Autonomous Laughter Prediction project.

---

## 1. Configuration Logging

Every experiment run must log the following configuration parameters:

### Core Config
```python
{
    "experiment_id": "exp_YYYYMMDD_HHMMSS",
    "timestamp": "ISO8601 timestamp",
    "git_commit": "current git SHA",
    "python_version": "3.x.x",
    "platform": "darwin/arm64",  # macOS M2
}
```

### Model Configuration
```python
{
    "model_name": "model identifier",
    "model_hash": "SHA256 of model weights",
    "vocab_size": number,
    "hidden_size": number,
    "num_layers": number,
    "num_attention_heads": number,
}
```

### Quantization Config
```python
{
    "qlora_bits": 4,
    "qlora_block_size": 64,
    "turboquant_enabled": True,
    "turboquant_bits": 3,
    "memory_compression_ratio": 6.0,
}
```

---

## 2. Dataset Versioning

All datasets must be versioned and logged:

```python
{
    "dataset_version": "v1.0.0",
    "datasets": [
        {
            "name": "standup4ai",
            "version": "1.0.0",
            "num_samples": 130000,
            "hash": "SHA256 of dataset",
        },
        {
            "name": "ur-funny",
            "version": "1.0.0",
            "num_samples": 5000,
            "hash": "SHA256 of dataset",
        },
        # ... other datasets
    ],
    "split_ratios": {
        "train": 0.8,
        "val": 0.1,
        "test": 0.1
    }
}
```

---

## 3. Model Hash Tracking

### Weight Hash
```bash
# Generate model weight hash
sha256sum models/*.safetensors > model_hashes.txt
```

### Configuration Hash
```python
import hashlib
import json

def compute_config_hash(config):
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]
```

---

## 4. Memory Profiling

Log peak memory usage during training:

```python
{
    "memory_profile": {
        "peak_ram_mb": 6144,
        "peak_vram_mb": 0,  # M2 uses unified memory
        "ssd_cache_hits": 1234,
        "ssd_cache_misses": 56,
        "kv_cache_compression_ratio": 6.0,
        "qlora_compression_ratio": 4.0,
    }
}
```

### Memory Tracking Script
```python
import psutil
import os

def log_memory_profile():
    process = psutil.Process(os.getpid())
    return {
        "peak_ram_mb": process.memory_info().rss / 1024 / 1024,
        "available_ram_mb": psutil.virtual_memory().available / 1024 / 1024,
    }
```

---

## 5. Benchmark Results

Log all benchmark metrics:

```python
{
    "benchmarks": {
        "word_level_laughter_f1": {
            "score": 0.7222,
            "target": 0.7222,
            "status": "PASS",
        },
        "textual_incongruity_f1": {
            "score": 0.77,
            "target": 0.77,
            "status": "PASS",
        },
        "vocal_event_detection": {
            "score": 0.38,
            "target": 0.38,
            "status": "PASS",
        },
        "sincerity_detection": {
            "score": 0.821,
            "target": 0.821,
            "status": "PASS",
        },
        "memory_compression": {
            "ratio": 6.0,
            "target": 6.0,
            "status": "PASS",
        }
    }
}
```

---

## 6. Logging Implementation

### File Structure
```
experiments/
  exp_20260403_120000/
    config.json           # Full configuration
    model_hash.txt        # Model weight hash
    memory_profile.json   # Memory usage data
    benchmarks.json       # Benchmark results
    training_log.txt      # Training output
  exp_20260403_130000/
    ...
```

### Logging Decorator
```python
import logging
import json
from pathlib import Path
from datetime import datetime

def setup_experiment_logging(exp_dir):
    exp_dir = Path(exp_dir)
    exp_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(exp_dir / 'training_log.txt'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
```

### Context Manager for Experiments
```python
from contextlib import contextmanager

@contextmanager
def experiment_context(experiment_id):
    exp_dir = Path(f"experiments/{experiment_id}")
    exp_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now().isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
    }

    with open(exp_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    try:
        yield exp_dir
    finally:
        logging.info(f"Experiment {experiment_id} completed")
```

---

## 7. Reproducibility Checklist

Before running any experiment, verify:

- [ ] `PYTHONHASHSEED=42` set
- [ ] `RANDOM_SEED=42` set
- [ ] `MLX_DETERMINISTIC=1` set (or equivalent for MLX)
- [ ] Dataset hashes verified
- [ ] Model weights hash computed
- [ ] Configuration saved to experiment directory
- [ ] No non-deterministic operations in data loading

---

## 8. Example Run

```bash
# Set seeds
export PYTHONHASHSEED=42
export RANDOM_SEED=42
export MLX_DETERMINISTIC=1

# Run experiment
python train.py --config configs/gcacu_base.yaml

# Results logged to
# experiments/exp_20260403_120000/
```
