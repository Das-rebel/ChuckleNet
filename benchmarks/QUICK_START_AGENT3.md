# Agent 3: Academic Metrics Framework - Quick Start Guide

## 🚀 GETTING STARTED IN 5 MINUTES

### Installation & Setup

```bash
# Navigate to project directory
cd ~/autonomous_laughter_prediction

# Verify installation
python3 -c "from benchmarks.academic_metrics_framework import AcademicMetricsFramework; print('✅ Agent 3 ready!')"

# Run validation tests
cd benchmarks && python3 standalone_validation.py
```

### Basic Usage Examples

#### 1. Classification Metrics
```python
from benchmarks.academic_metrics_framework import AcademicMetricsFramework
import numpy as np

# Initialize framework
framework = AcademicMetricsFramework()

# Your predictions
y_true = np.array([0, 1, 0, 1, 0, 1])
y_pred = np.array([0, 1, 0, 1, 0, 0])

# Calculate metrics
results = framework.classification_metrics(y_true, y_pred)

# Access results
print(f"Accuracy: {results['accuracy'].value:.4f}")
print(f"F1 Score: {results['f1'].value:.4f}")
print(f"Macro-F1: {results['f1_macro'].value:.4f}")
```

#### 2. Temporal IoU Metrics
```python
# Ground truth and predicted segments
gt_segments = [{'start': 1.0, 'end': 2.5}, {'start': 5.0, 'end': 7.0}]
pred_segments = [{'start': 1.2, 'end': 2.7}, {'start': 5.5, 'end': 6.8}]

# Calculate IoU metrics
iou_results = framework.iou_based_detection_metrics(gt_segments, pred_segments)

# Access results
print(f"IoU@0.2 F1: {iou_results['f1_iou_20'].value:.4f}")
print(f"IoU@0.3 F1: {iou_results['f1_iou_30'].value:.4f}")
print(f"IoU@0.5 F1: {iou_results['f1_iou_50'].value:.4f}")
```

#### 3. Cross-Domain Evaluation
```python
# Source domain (e.g., TED talks)
source_y_true = np.array([0, 1, 0, 1])
source_y_pred = np.array([0, 1, 0, 1])  # Perfect

# Target domain (e.g., stand-up comedy)
target_y_true = np.array([0, 1, 0, 1])
target_y_pred = np.array([0, 1, 0, 0])  # Some errors

# Calculate cross-domain metrics
cross_domain = framework.cross_domain_metrics(
    (source_y_true, source_y_pred),
    (target_y_true, target_y_pred)
)

# Access results
print(f"Transfer Ratio: {cross_domain['transfer_ratio'].value:.4f}")
print(f"Performance Drop: {cross_domain['transfer_performance_drop'].value:.4f}")
```

---

## 📊 AVAILABLE METRICS

### Classification Metrics
- **Accuracy**: Overall correctness
- **Precision**: True positive rate
- **Recall**: Positive instance identification
- **F1 Score**: Harmonic mean of precision and recall
- **Macro-F1**: Averaged F1 across classes (for imbalanced data)
- **Per-class metrics**: Individual class performance

### Temporal Metrics (IoU-based)
- **IoU@0.2**: Intersection over Union at 0.2 threshold
- **IoU@0.3**: Intersection over Union at 0.3 threshold
- **IoU@0.5**: Intersection over Union at 0.5 threshold
- **Precision@IoU**: Precision at specific IoU threshold
- **Recall@IoU**: Recall at specific IoU threshold
- **F1@IoU**: F1 score at specific IoU threshold

### Cross-Domain Metrics
- **Source F1**: Performance on source domain
- **Target F1**: Performance on target domain
- **Transfer Ratio**: Target/Source performance ratio
- **Performance Drop**: Source - Target performance difference
- **Statistical Significance**: p-value for transfer significance

### Statistical Features
- **Bootstrap Confidence Intervals**: 95% CI for all metrics
- **Statistical Significance Testing**: McNemar's test p-values
- **Sample Size Tracking**: Proper statistical reporting
- **Publication-Ready Formatting**: LaTeX table generation

---

## 🎯 USE CASES

### Use Case 1: StandUp4AI Evaluation
```python
from benchmarks.benchmark_integration import BenchmarkIntegration

# Initialize integration
integration = BenchmarkIntegration()

# Evaluate on StandUp4AI benchmark
results = integration.evaluate_standup4ai_benchmark(model, 'test')

# Compare with published baseline
baseline = 0.58  # From StandUp4AI paper
our_f1 = results['word_f1'].value
improvement = ((our_f1 - baseline) / baseline) * 100

print(f"Published Baseline: {baseline:.4f}")
print(f"Our Method: {our_f1:.4f}")
print(f"Improvement: {improvement:+.2f}%")
```

### Use Case 2: Multiple Benchmark Comparison
```python
# Run full benchmark suite
all_results = integration.run_full_benchmark_suite(model)

# Generate publication table
table = integration.generate_publication_table(all_results)
print(table)

# Save results
integration.save_all_results(all_results, "./results")
```

### Use Case 3: Model Selection
```python
# Compare multiple models
models = {
    'baseline': baseline_model,
    'improved': improved_model,
    'ensemble': ensemble_model
}

results = {}
for model_name, model in models.items():
    model_results = integration.evaluate_standup4ai_benchmark(model, 'test')
    results[model_name] = model_results['word_f1'].value

# Find best model
best_model = max(results, key=results.get)
print(f"Best model: {best_model} with F1={results[best_model]:.4f}")
```

---

## 🔧 CONFIGURATION OPTIONS

### Bootstrap Settings
```python
# More accurate confidence intervals (slower)
framework = AcademicMetricsFramework(
    bootstrap_samples=2000,  # More samples
    confidence_level=0.99     # 99% CI
)

# Faster evaluation (less accurate)
framework = AcademicMetricsFramework(
    bootstrap_samples=500,   # Fewer samples
    confidence_level=0.95     # 95% CI
)
```

### Custom IoU Thresholds
```python
# Evaluate at specific IoU thresholds
iou_results = framework.iou_based_detection_metrics(
    gt_segments, pred_segments,
    iou_thresholds=[0.1, 0.2, 0.3, 0.5, 0.7, 0.9]  # Custom thresholds
)
```

### Classification Averaging
```python
# Different averaging methods
results_binary = framework.classification_metrics(y_true, y_pred, average='binary')
results_macro = framework.classification_metrics(y_true, y_pred, average='macro')
results_micro = framework.classification_metrics(y_true, y_pred, average='micro')
```

---

## 📈 OUTPUT FORMATS

### Console Output
```
🎯 Evaluating StandUp4AI Benchmark (EMNLP 2025)
--------------------------------------------------------------------------------
  Word-level F1: 0.6500
  IoU@0.2 F1: 0.7200
  IoU@0.3 F1: 0.6800

  📊 Comparison with published baseline:
     Published: 0.5800
     Our Method: 0.6500
     Improvement: +12.07%
```

### JSON Output
```json
{
  "accuracy": {
    "metric_name": "Accuracy",
    "value": 0.7500,
    "confidence_interval": [0.6500, 0.8500],
    "sample_size": 100
  },
  "f1": {
    "metric_name": "F1",
    "value": 0.7222,
    "confidence_interval": [0.6200, 0.8200],
    "sample_size": 100
  }
}
```

### LaTeX Table Output
```latex
\begin{table}[t]
\centering
\caption{Evaluation Results}
\label{tab:results}
\begin{tabular}{lccc}
\toprule
Metric & Value & 95\% CI & Sample Size \\
\midrule
Accuracy & 0.7500 & [0.6500, 0.8500] & 100 \\
F1 & 0.7222 & [0.6200, 0.8200] & 100 \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

**Issue 1: Import Errors**
```bash
# Solution: Ensure project path is correct
cd ~/autonomous_laughter_prediction
python3 -c "import sys; sys.path.insert(0, '.'); from benchmarks.academic_metrics_framework import AcademicMetricsFramework"
```

**Issue 2: Sklearn Not Found**
```bash
# Solution: Install dependencies
pip install scikit-learn scipy numpy
```

**Issue 3: Confidence Intervals Too Wide**
```python
# Solution: Increase bootstrap samples
framework = AcademicMetricsFramework(bootstrap_samples=2000)
```

**Issue 4: IoU Calculation Errors**
```python
# Solution: Ensure segments have 'start' and 'end' keys
# Correct format:
segments = [{'start': 1.0, 'end': 2.5}, {'start': 5.0, 'end': 7.0}]

# Wrong format (will cause errors):
segments = [[1.0, 2.5], [5.0, 7.0]]  # ❌ Missing keys
```

---

## 📚 RESOURCES

### Documentation Files
- **AGENT3_COMPLETION_REPORT.md**: Comprehensive technical details
- **INTEGRATION_GUIDE.md**: Integration with Agent 1 & Agent 2
- **academic_metrics_framework.py**: Core implementation
- **benchmark_integration.py**: External benchmark integration

### Validation
- **standalone_validation.py**: Run validation tests
- **validation_report.json**: Validation results

### Examples
- **usage_example.py**: Basic usage examples
- **complete_evaluation.py**: End-to-end pipeline

---

## 🎯 QUICK VALIDATION

Run this to verify Agent 3 is working correctly:

```python
# Quick validation script
from benchmarks.academic_metrics_framework import AcademicMetricsFramework
import numpy as np

print("🔍 Quick Validation of Agent 3")

# Test 1: Classification
framework = AcademicMetricsFramework()
y_true = np.array([0, 1, 0, 1])
y_pred = np.array([0, 1, 0, 1])
results = framework.classification_metrics(y_true, y_pred)
assert results['accuracy'].value == 1.0, "Classification test failed"
print("✅ Classification metrics working")

# Test 2: IoU calculation
seg1 = {'start': 0.0, 'end': 10.0}
seg2 = {'start': 0.0, 'end': 10.0}
iou = framework.calculate_iou(seg1, seg2)
assert abs(iou - 1.0) < 1e-6, "IoU calculation failed"
print("✅ IoU calculation working")

# Test 3: Temporal metrics
gt_segments = [{'start': 1.0, 'end': 2.0}]
pred_segments = [{'start': 1.0, 'end': 2.0}]
iou_results = framework.iou_based_detection_metrics(gt_segments, pred_segments)
assert iou_results['f1_iou_20'].value == 1.0, "Temporal metrics failed"
print("✅ Temporal metrics working")

print("\n🎉 All validation tests passed! Agent 3 is ready to use.")
```

---

## 🚀 NEXT STEPS

1. **Run Validation**: `python3 benchmarks/standalone_validation.py`
2. **Try Examples**: `python3 benchmarks/usage_example.py`
3. **Read Integration Guide**: Check `INTEGRATION_GUIDE.md`
4. **Connect Your Model**: Update `_get_model_prediction()` methods
5. **Run Benchmarks**: `python3 benchmarks/benchmark_integration.py`

---

**Agent 3 Status**: ✅ OPERATIONAL
**Validation**: 100% Pass Rate
**Ready for Integration**: YES
**Production Ready**: YES

*Quick Start Guide v1.0 - Last Updated: 2026-03-29*