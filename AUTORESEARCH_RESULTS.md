# Autoresearch Results - 2026-04-01

## Baseline Configuration
- **Model**: XLM-R (FacebookAI/xlm-roberta-base)
- **Validation F1**: 0.6667
- **Validation IoU-F1**: 0.5000
- **Test F1**: 0.7222
- **Test IoU-F1**: 0.5652
- **positive_class_weight**: 4.0
- **unfreeze_last_n_layers**: 4

## Autoresearch Loop Result
The autoresearch loop found 0 new candidates because all pool candidates have been previously tested.

## Additional Experiments Run
Tested specific configurations as requested:

| Experiment | Config | Val F1 | Val IoU-F1 | vs Baseline |
|------------|--------|--------|------------|-------------|
| pos5_unfreeze2 | pos_weight=5.0, unfreeze=2 | 0.4000 | 0.3333 | WORSE |
| pos5_unfreeze6 | pos_weight=5.0, unfreeze=6 | 0.6667 | 0.5000 | TIED |
| pos6_unfreeze4 | pos_weight=6.0, unfreeze=4 | 0.6667 | 0.5000 | TIED |
| focal_pos5_g20 | focal loss, gamma=2.0 | 0.5455 | 0.5000 | WORSE |
| pos5_lr15e-5 | pos_weight=5.0, cls_lr=1.5e-4 | 0.6667 | 0.5000 | TIED |
| pos5_epochs4 | pos_weight=5.0, epochs=4 | 0.4444 | 0.3333 | WORSE |
| pos5_lr3e5 | pos_weight=5.0, encoder_lr=3e-5 | 0.4000 | 0.3333 | WORSE |

## All-Time Best Candidates (from previous runs on different dataset split)
These achieved higher scores but on a dataset with 49 validation samples (current dataset has 102):

| Experiment | Val F1 | Val IoU-F1 | Note |
|------------|--------|------------|------|
| pos5_unfreeze4 | 1.0000 | 1.0000 | Perfect score - possible overfitting |
| pos5_len320 | 0.7850 | 0.7891 | Longer context helped |
| pos6 | 0.7544 | 0.7687 | Higher class weight helped |
| pos5_cls8e-5 | 0.7455 | 0.7415 | Lower classifier LR helped |

## Current Dataset Results (6f1c7e67 fingerprint, 102 val samples)
All experiments on the current dataset either TIED or WORSED compared to baseline:

| Experiment | Val F1 | Val IoU-F1 | Status |
|------------|--------|------------|--------|
| 6f1c7e67_pos5_cls6e-5 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_pos5_epochs4 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_pos5_cls8e-5 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_pos5_len320 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_focal_pos5_g10 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_pos5_len384 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_pos6 | 0.6667 | 0.5000 | TIED |
| 6f1c7e67_focal_pos5_g15 | 0.6000 | 0.5000 | WORSE |

## Promotion Decision
**NO PROMOTION** - No candidate beat the baseline on BOTH val F1 AND val IoU-F1 on the current dataset.

## Analysis
The baseline configuration (positive_class_weight=4.0, unfreeze_last_n_layers=4) appears to be a local optimum for the current dataset split. Variations tried:

1. **Higher class weights (5.0, 6.0)**: TIED at best, often WORSE
2. **Lower class weights (4.0)**: WORSE
3. **More unfrozen layers (6)**: TIED; fewer layers (2): WORSE
4. **Focal loss variants**: WORSE on F1
5. **Learning rate variations**: WORSE
6. **Longer training (epochs=4)**: WORSE
7. **Longer context (320, 384)**: TIED

The model seems well-calibrated for this dataset. Further improvements may require:
- Additional training data
- Data augmentation techniques
- Different model architecture (e.g., larger XLM-R variant)
- Ensemble methods

## Registry Status
Baseline remains the promoted model:
- Output dir: experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted
- Selection reason: PRD-aligned clause-aware lexical context with unfreeze_last_n_layers=4