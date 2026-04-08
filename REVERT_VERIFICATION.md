# Revert Verification Report

## Date: 2026-04-01

## Summary
The label fix revert was verified successfully. F1 returned to expected levels after reverting incorrect label changes.

## Label Verification
Top positive tokens after revert:
- `"`: 162 occurrences
- `!`: 161 occurrences
- `?`: 81 occurrences

These punctuation marks correctly indicate discourse boundaries where laughter occurs.

## Training Results

### Best Validation Metrics (Epoch 3)
| Metric | Value | Target |
|--------|-------|--------|
| F1 | 0.6667 | >= 0.6667 |
| IoU-F1 | 0.5000 | >= 0.5000 |
| Precision | 1.0000 | - |
| Recall | 0.5000 | - |

### Test Metrics (Epoch 5)
| Metric | Value |
|--------|-------|
| F1 | 0.7222 |
| IoU-F1 | 0.5652 |
| Precision | 1.0000 |
| Recall | 0.5652 |

## Conclusion
- Training completed successfully without errors
- Validation F1 = 0.6667 meets target (>= 0.6667)
- IoU-F1 = 0.5000 meets target (>= 0.5000)
- The original labels were correct; the "label fix" was the error
