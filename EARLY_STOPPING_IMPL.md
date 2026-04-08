# Early Stopping Implementation

## Overview

Early stopping has been added to the XLM-R word-level laughter prediction training to prevent overfitting and reduce training time.

## Implementation Details

### Configuration

- **Field**: `early_stopping_patience` in `XLMRStandupConfig`
- **Default**: 2 epochs
- **CLI Flag**: `--early-stopping-patience`

### Logic

1. **Metric Monitored**: Validation IoU-F1 (`iou_f1`)
2. **Patience**: Training stops if no improvement for N consecutive epochs (default: 2)
3. **Best Model**: Best model (based on IoU-F1) is saved after each improvement

### Code Changes

#### 1. Config Dataclass (line 115)
```python
early_stopping_patience: int = 2
```

#### 2. Training Loop Variables (lines 1281-1282)
```python
best_iou_f1: float = -1.0
epochs_without_improvement: int = 0
```

#### 3. Early Stopping Logic (lines 1407-1418)
```python
current_iou_f1 = float(metrics["iou_f1"])
if current_iou_f1 > best_iou_f1:
    best_iou_f1 = current_iou_f1
    best_metrics = dict(metrics)
    epochs_without_improvement = 0
    save_model(model, tokenizer, output_dir / "best_model", config)
else:
    epochs_without_improvement += 1

if epochs_without_improvement >= config.early_stopping_patience:
    print(f"Early stopping triggered after {epoch + 1} epochs with no improvement in IoU-F1.")
    break
```

#### 4. CLI Argument (line 1507)
```python
parser.add_argument("--early-stopping-patience", type=int, default=2,
    help=" epochs with no IoU-F1 improvement before early stopping.")
```

### Summary Output

The training summary includes early stopping information:
```json
{
  "early_stopping": {
    "patience": 2,
    "best_iou_f1": 0.45,
    "epochs_without_improvement": 0
  }
}
```

## Usage

```bash
python training/xlmr_standup_word_level.py \
  --train-file data/train.jsonl \
  --valid-file data/valid.jsonl \
  --output-dir output/ \
  --epochs 10 \
  --early-stopping-patience 2
```

## Behavior

- With `--epochs 10 --early-stopping-patience 2`: Training runs for up to 10 epochs but stops early if IoU-F1 doesn't improve for 2 consecutive epochs
- Best model is always saved to `output_dir/best_model/` when improvement occurs
- The printed message when early stopping triggers: `"Early stopping triggered after N epochs with no improvement in IoU-F1."`
