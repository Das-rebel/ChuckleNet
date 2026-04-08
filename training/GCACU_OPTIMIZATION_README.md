# GCACU Hyperparameter Optimization System

## Overview

Comprehensive hyperparameter optimization system for GCACU (Gated Contrast-Attention Contextualized-Understanding) networks, specifically designed to address the performance issues identified in multilingual laughter prediction experiments.

## Problem Statement

### Current Performance Issues
The multilingual experiment revealed significant performance degradation:
- **Validation F1: 0.5929** (vs 0.6667 baseline) - 10.9% decrease
- **Test F1: 0.3771** (vs 0.7222 baseline) - 47.8% decrease
- **Language variance**: Czech (0.6231), English (0.2771), Spanish (0.4667), French (0.3389)

### Root Causes Identified
1. **Overfitting** on small multilingual dataset (4 examples)
2. **Hyperparameter mismatch** for multilingual scenarios
3. **Insufficient regularization** for tiny datasets
4. **No adaptation** for language-specific patterns
5. **Fixed architecture** regardless of dataset size

## Revolutionary Features

### 1. Adaptive GCACU
Automatically adjusts model complexity based on dataset characteristics:
- **Tiny datasets** (< 100 examples): Smaller models, strong regularization
- **Small datasets** (100-500): Balanced complexity
- **Medium datasets** (500-2000): Full GCACU capacity
- **Large datasets** (> 2000): Enhanced capacity and features

### 2. Bayesian Optimization
Efficient hyperparameter search using Thompson Sampling:
- **Exploration phase**: Random sampling for initial trials
- **Exploitation phase**: Guided search around best parameters
- **Adaptive balance**: Automatically adjusts exploration/exploitation ratio

### 3. Language-Specific Tuning
Per-language hyperparameter optimization:
- **Morphological complexity** awareness
- **Word order** characteristics
- **Language-specific** dropout and learning rates

### 4. Small Data Adaptation
Specialized techniques for tiny datasets:
- **Strong regularization** (dropout up to 0.5)
- **Data augmentation** (token dropout, synonym replacement)
- **Cross-validation** for robust evaluation
- **Ensemble methods** for stability

### 5. Comprehensive Validation
Robust evaluation framework:
- **K-fold cross-validation** for statistical reliability
- **Overfitting detection** with early stopping
- **Statistical significance testing** for comparisons
- **Per-language performance** tracking

## System Architecture

```
gcacu_optimizer.py              # Main optimization engine
├── BayesianOptimizer            # Efficient hyperparameter search
├── DataAugmentor                # Small data augmentation
├── LanguageSpecificTuner        # Per-language optimization
└── GCACUOptimizer               # Main orchestrator

gcacu_validation_framework.py   # Validation and testing
├── CrossValidator               # K-fold cross-validation
├── OverfittingDetector          # Overfitting detection
├── StatisticalValidator         # Statistical testing
├── PerformanceTracker           # Performance comparison
└── EarlyStoppingValidator       # Enhanced early stopping

adaptive_gcacu.py               # Adaptive configuration
├── DatasetAnalyzer              # Dataset characteristic analysis
├── AdaptiveGCACUController      # Automatic complexity adjustment
└── AdaptiveTrainer              # Adaptive training orchestration

run_gcacu_optimization.py       # Complete pipeline
└── GCACUOptimizationPipeline    # End-to-end optimization
```

## Installation

### Requirements
```bash
pip install torch transformers numpy scipy scikit-learn
```

### Files Required
- `gcacu_optimizer.py` - Main optimization system
- `gcacu_validation_framework.py` - Validation framework
- `adaptive_gcacu.py` - Adaptive configuration
- `run_gcacu_optimization.py` - Execution pipeline
- `gcacu_network.py` - GCACU model architecture

## Usage

### Basic Usage

```bash
python run_gcacu_optimization.py \
    --train-file data/training/multilingual.jsonl \
    --valid-file data/training/multilingual_valid.jsonl \
    --test-file data/training/multilingual_test.jsonl \
    --output-dir optimization_results \
    --trials 50
```

### Advanced Usage

```bash
# With cross-validation (recommended for small datasets)
python run_gcacu_optimization.py \
    --train-file data/training/multilingual.jsonl \
    --valid-file data/training/multilingual_valid.jsonl \
    --test-file data/training/multilingual_test.jsonl \
    --output-dir optimization_results \
    --trials 100

# Using specific model
python run_gcacu_optimization.py \
    --train-file data/training/multilingual.jsonl \
    --valid-file data/training/multilingual_valid.jsonl \
    --test-file data/training/multilingual_test.jsonl \
    --model-name FacebookAI/xlm-roberta-base \
    --output-dir optimization_results \
    --trials 50

# Quick test (fewer trials, no cross-validation)
python run_gcacu_optimization.py \
    --train-file data/training/multilingual.jsonl \
    --valid-file data/training/multilingual_valid.jsonl \
    --test-file data/training/multilingual_test.jsonl \
    --output-dir quick_test \
    --trials 10 \
    --no-cv
```

### Programmatic Usage

```python
from pathlib import Path
from run_gcacu_optimization import GCACUOptimizationPipeline

# Create pipeline
pipeline = GCACUOptimizationPipeline(
    train_file="data/training/multilingual.jsonl",
    valid_file="data/training/multilingual_valid.jsonl",
    test_file="data/training/multilingual_test.jsonl",
    model_name="FacebookAI/xlm-roberta-base",
    output_dir="optimization_results"
)

# Run optimization
report = pipeline.run_complete_optimization(
    n_trials=50,
    use_cross_validation=True
)

# Access results
best_params = report['production_config']
recommendations = report['recommendations']
```

## Output and Reports

### Optimization Report Structure

```json
{
  "metadata": {
    "timestamp": "2025-01-15T10:30:00",
    "model_name": "FacebookAI/xlm-roberta-base",
    "dataset_info": {
      "languages": ["cs", "en", "es", "fr"],
      "scenario": "tiny_multilingual",
      "dataset_size": 4,
      "n_languages": 4
    }
  },
  "adaptive_configuration": {
    "scenario": "tiny_multilingual",
    "adaptive_config": {
      "gcacu_dim": 48,
      "num_heads": 2,
      "dropout": 0.5,
      "learning_rate": 8e-6
    }
  },
  "optimization_results": {
    "best_valid_f1": 0.6842,
    "best_parameters": { ... },
    "all_trials": [ ... ]
  },
  "validation_results": {
    "valid_f1_mean": 0.6523,
    "valid_f1_std": 0.0234,
    "test_f1_mean": 0.4456,
    "test_f1_std": 0.0345
  },
  "recommendations": {
    "hyperparameter_recommendations": [ ... ],
    "training_recommendations": [ ... ],
    "deployment_recommendations": [ ... ]
  },
  "production_config": { ... }
}
```

## Key Parameters

### Search Space Configuration

```python
@dataclass
class OptimizationConfig:
    # Architecture
    gcacu_dim_range: Tuple[int, int] = (64, 256)
    num_heads_range: Tuple[int, int] = (2, 8)

    # Training
    learning_rate_range: Tuple[float, float] = (1e-6, 1e-3)
    batch_size_range: Tuple[int, int] = (4, 32)
    epochs_range: Tuple[int, int] = (3, 10)

    # Regularization
    dropout_range: Tuple[float, float] = (0.1, 0.5)
    weight_decay_range: Tuple[float, float] = (0.001, 0.1)
    label_smoothing_range: Tuple[float, float] = (0.0, 0.3)

    # Loss function
    focal_gamma_range: Tuple[float, float] = (1.0, 4.0)
    positive_class_weight_range: Tuple[float, float] = (1.0, 8.0)
```

### Adaptive Scenarios

| Scenario | Dataset Size | Languages | GCACU Dim | Dropout | Learning Rate |
|----------|-------------|-----------|-----------|---------|---------------|
| tiny_monolingual | < 100 | 1 | 64 | 0.4 | 1e-5 |
| tiny_multilingual | < 100 | >1 | 48 | 0.5 | 8e-6 |
| small_monolingual | 100-500 | 1 | 96 | 0.3 | 1.5e-5 |
| small_multilingual | 100-500 | >1 | 80 | 0.35 | 1.2e-5 |
| medium_monolingual | 500-2000 | 1 | 128 | 0.2 | 2e-5 |
| medium_multilingual | 500-2000 | >1 | 112 | 0.25 | 1.8e-5 |
| large_monolingual | > 2000 | 1 | 192 | 0.15 | 3e-5 |
| large_multilingual | > 2000 | >1 | 176 | 0.18 | 2.5e-5 |

## Performance Expectations

### Improvement Targets

Based on the optimization system:

1. **Small Datasets** (< 100 examples):
   - Expected improvement: 15-25% over baseline
   - Key techniques: Strong regularization, data augmentation
   - Validation method: Cross-validation essential

2. **Multilingual Scenarios**:
   - Expected improvement: 10-20% over baseline
   - Key techniques: Language-specific tuning, adaptive dropout
   - Expected language balance: Reduced variance

3. **Combined Challenges** (small + multilingual):
   - Expected improvement: 20-30% over baseline
   - Key techniques: All adaptive features
   - Validation method: Rigorous cross-validation

## Troubleshooting

### Common Issues

**Issue**: Overfitting detected
- **Solution**: Increase dropout (0.4-0.5), reduce model complexity, add more data

**Issue**: Poor performance on specific language
- **Solution**: Use language-specific tuning, adjust learning rate per language

**Issue**: High variance across folds
- **Solution**: Increase cross-validation folds, use more aggressive regularization

**Issue**: Optimization takes too long
- **Solution**: Reduce trials, disable cross-validation for initial testing

### Monitoring

Key metrics to monitor during optimization:
1. **Overfitting score**: Should be < 0.3
2. **Per-language F1**: Variance should decrease with optimization
3. **Cross-validation stability**: Standard deviation should be < 0.05

## Integration with Existing Pipeline

### Using Optimized Parameters

```python
# Load optimized configuration
import json
with open('optimization_results/final_optimization_report_*.json') as f:
    report = json.load(f)

# Extract production config
production_config = report['production_config']

# Use in training
from gcacu_network import create_gcacu_model, GCACUConfig

config = GCACUConfig(
    gcacu_dim=production_config['gcacu_dim'],
    num_heads=production_config['num_heads'],
    dropout=production_config['dropout'],
    # ... other parameters
)
```

## Advanced Features

### Custom Search Spaces

```python
# Define custom search space
custom_space = {
    'learning_rate': (5e-6, 5e-5),  # Narrower range
    'dropout': (0.2, 0.4),          # Focused search
    'gcacu_dim': [64, 96, 128]      # Discrete options
}

# Use in optimizer
optimizer = GCACUOptimizer(custom_search_space=custom_space)
```

### Multi-Objective Optimization

```python
# Optimize for both F1 and inference speed
multi_objective = {
    'metrics': ['f1', 'inference_time'],
    'weights': [0.8, 0.2]  # Prioritize F1
}

report = pipeline.run_multi_objective_optimization(multi_objective)
```

## Citation and References

If you use this optimization system, please cite:

```
GCACU Hyperparameter Optimization System for Multilingual Laughter Prediction
Adaptive GCACU: Automatic Complexity Adjustment for Varying Dataset Sizes
Bayesian Optimization for Small Data NLP Tasks
```

## License

This optimization system is part of the Autonomous Laughter Prediction project.

## Contact and Support

For questions, issues, or contributions, please refer to the main project documentation.

---

**Note**: This system is designed to address the specific challenges identified in multilingual laughter prediction experiments. The adaptive features and optimization strategies are particularly important for small datasets and multilingual scenarios.