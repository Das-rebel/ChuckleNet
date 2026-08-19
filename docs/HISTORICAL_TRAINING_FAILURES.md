# Historical Training Failures — Triple-Check Analysis

## Pattern 1: Label Sparsity Catastrophe
| Dataset | Positive Rate | F1 Achieved | Result |
|---------|-------------|-------------|--------|
| F0 668 videos | 1.2% | ~0 | **COLLAPSE** |
| Gillick 272 | 2.2% | 0.04 | **COLLAPSE** |
| FINAL_500plus | 4.4% | N/A | **DEAD** |
| combined_f0_pseudo | N/A | N/A | **DEAD** |

**ROOT CAUSE**: At <5% positive rate, gradients from negatives drown the positive signal. 
The model learns "predict non-laugh always" as optimal and can't escape.

**PREVENT**: Only train on data with >15% positive rate. Never pseudo-label from sparse source.

---

## Pattern 2: Model Saturation (pos_weight=5.0)
**SYMPTOM**: top200_prosody_model.pt outputs ALL probs = 1.0
**ROOT CAUSE**: pos_weight=5.0 over-upweighted positives → model predicts laugh for every segment
**EVIDENCE**: min=1.0, max=1.0, mean=1.0, std=0.0 on 10-vide EMNLP test
**LESSON**: Never use pos_weight > 3.0 without validation. Start low.

---

## Pattern 3: Word-Level Boundary Problem
**APPROACH**: XLM-R sequence labeling at word level
**RESULT**: IoU-F1 = 0.50 stuck (can't break 0.5)
**ROOT CAUSE**: Single classification head must do TWO tasks:
  1. BIO sequence labeling (which words are in a laugh region?)
  2. Boundary detection (where exactly does laugh START and END?)
**LESSON**: These need SEPARATE mechanisms. Single head can't solve both.

---

## Pattern 4: Teacher Refinement Hurt Performance
**APPROACH**: Use qwen2.5-coder:1.5b to refine weak labels
**RESULT**: Refined-label XLM-R → val F1=0.0784, test F1=0.1231
**COMPARISON**: Weak-label XLM-R → val F1=0.7850, test F1=0.8194
**ROOT CAUSE**: Teacher introduced more errors than it fixed. The "refinement" corrupted labels.
**LESSON**: Don't refine already-labeled data with an imperfect teacher. Trust original labels.

---

## Pattern 5: Hyperparameter Variants Lost to Baseline
**TESTED**: pos4 (pos_weight=4.0), pos6 (pos_weight=6.0)
**RESULT**: Both lost to pos5 baseline in autonomous research loop
**LESSON**: The pos5 configuration was already optimal. Don't chase hyperparams without major data change.

---

## Pattern 6: Pseudo-Labeling Amplified Noise
**APPROACH**: Use F0 model (1.2% positive) to pseudo-label more data
**RESULT**: Model learned garbage from garbage-in
**ROOT CAUSE**: Pseudo-labels from a broken model are worse than no labels
**LESSON**: Only pseudo-label with a model that already works (F1 > 0.9).

---

## Working Results (What NOT to Break)

| Model | F1 | Data | Positive Rate |
|-------|-----|------|--------------|
| best_fusion_model.pt | 0.975 | 87 videos, 21K utt | 22.7% ✅ |
| fusion_results | 0.973 | same | 22.7% ✅ |
| video_holdout | 0.960 | 18 held-out videos | 12.3% test ✅ |
| prosody_300videos | 0.992 train | 300 videos | 16.8% train ⚠️ |

**The working models all have one thing in common**: >15% positive rate in training data.

---

## Critical Rules for Any New Training

1. **Minimum 15% positive rate** — reject or don't count data below this
2. **pos_weight ≤ 3.0** — validate at each step, check prob distribution
3. **Don't refine good labels** — teacher models introduce noise
4. **Pseudo-label only from working models** — F1 > 0.9 required
5. **Separate boundary from classification** — don't use single head for both
6. **Don't chase hyperparams** — only major data changes improve results
