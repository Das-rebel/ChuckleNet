# Hybrid Training Approach PRD - ChuckleNet Project

**Date**: 2026-04-17
**Version**: 2.0
**Status**: CRITICAL RESTRUCTURE

## Executive Summary

Training #39 has been **abandoned** due to multiple critical failures (NaN losses, unvalidated labels, missing quantization). This PRD outlines a **hybrid parallel approach** to achieve publication-ready results with scientific rigor.

## Problem Statement

### Crisis 1: Biosemotic Label Validity (UNVALIDATED)
- **Issue**: Duchenne, ToM, and Incongruity labels are heuristic approximations with no human validation
- **Impact**: Cannot publish without construct validity (Fleiss' κ, Pearson r)
- **Probability of Validity**: ~30% (based on label quality audit)

### Crisis 2: Missing Proven Techniques (CRITICAL)
- **Issue**: Training #39 uses NONE of the techniques that achieved 0.92 F1
- **Missing**: QLoRA, TurboQuant, LoRA, class weighting, gradient clipping
- **Result**: Numerical instability (NaN) and memory crisis

### Crisis 3: NaN Loss Crisis (BLOCKER)
- **Issue**: All 4 loss components returning NaN
- **Root Cause**: No gradient clipping, full float32, no class weighting
- **Status**: Training #39 completely non-functional

## Solution: Hybrid Parallel Approach

### Track 1: Human Validation Study (Week 1-2)
**Objective**: Determine scientific validity of biosemotic labels

**Phase 1A: Annotation Setup** (Day 1-2)
- Sample 300 examples stratified by laughter label
- Create annotation CSV with clear instructions
- Set up HumanAnnotationProtocol with rating scales (1-7)
- Target: 3-5 annotators with psychology/linguistics background

**Phase 1B: Annotation Collection** (Day 3-10)
- Recruit annotators (preferably domain experts)
- Collect ratings for all constructs:
  - Duchenne: Genuine laughter potential
  - Incongruity: 3 dimensions (semantic, expectation, resolution)
  - ToM: 3 dimensions (intent, perspective, context)
- Monitor inter-annotator agreement in real-time

**Phase 1C: Validation Analysis** (Day 11-14)
- Compute Fleiss' κ for inter-annotator agreement
- Compute Pearson r for construct validity
- Generate comprehensive validation report
- **Decision Point**:
  - VALID (κ ≥ 0.60, r ≥ 0.50): Proceed with multi-task learning
  - INVALID (κ < 0.40, r < 0.30): Abandon biosemotic labels, use self-supervised

**Deliverables**:
- Annotation CSV with 900+ ratings (300 examples × 3 annotators)
- Inter-annotator agreement report (Fleiss' κ)
- Construct validity report (Pearson r, 95% CI)
- Go/No-Go decision for biosemotic labels

---

### Track 2: Quantized Training (Week 1)
**Objective**: Replicate 0.92 F1 success with proven quantization stack

**Phase 2A: Script Integration** (Day 1)
- Create `train_xlmr_quantized_v1.py` with ALL proven techniques:
  - QLoRA 4-bit quantization (BitsAndBytes)
  - TurboQuant 3-bit KV cache compression
  - LoRA adapters (parameter-efficient)
  - Mixed precision (float16)
  - Class weighting (5x positive)
  - Gradient clipping (max_norm=1.0)
  - Differential learning rates (10x classifier)
  - Layer freezing strategy

**Phase 2B: Small-Scale Validation** (Day 2)
- Test on 100 examples for 1 epoch
- Verify no NaN losses
- Check memory usage < 5GB
- Confirm training speed < 10s/batch
- **Success Criteria**: All checks pass

**Phase 2C: Full Training** (Day 3-7)
- Train on full dataset (630 examples)
- Target: 0.92+ F1 (binary laughter)
- Expected time: 6-8 hours
- Memory: < 5GB on 8GB Mac M2
- Early stopping with patience=3

**Deliverables**:
- Trained model with 0.92+ F1
- Training logs with no NaN
- Memory usage metrics
- Validation on external benchmarks

---

### Integration Phase (Week 2-3)

#### Scenario A: Biosemotic Labels VALIDATED
**Action**: Add multi-task learning to quantized model

**Implementation**:
- Extend quantized model with biosemotic heads
- Multi-task loss with validated weights
- Train with joint supervision (binary laughter + biosemotic)
- Target: 0.95+ F1 (improved over binary)

**Validation**:
- Per-task metrics (laugh, Duchenne, Incongruity, ToM)
- Correlation with human judgments (r ≥ 0.50)
- Ablation studies for component contributions

**Publication**: NeurIPS 2026 (revolutionary claims)

#### Scenario B: Biosemotic Labels INVALID
**Action**: Self-supervised biosemotic learning

**Implementation**:
- Use binary laughter model as base
- Add self-supervised biosemotic proxies:
  - Laughter density → Duchenne proxy
  - Semantic shift → Incongruity proxy
  - Social presence → ToM proxy
- Learn biosemotic representations from laughter patterns

**Validation**:
- Emergent biosemotic understanding
- Cluster analysis of learned representations
- Qualitative analysis of proxy dimensions

**Publication**: ACL/EMNLP 2026 (efficiency focus)

---

### Week 4: Validation & Publication

**Phase 4A: Benchmark Evaluation**
- StandUp4AI: Word-level laughter detection
- UR-FUNNY: Humor recognition
- WESR-Bench: Vocal event detection
- Internal test set: Final validation

**Phase 4B: Statistical Validation**
- Bootstrap confidence intervals (1000 resamples)
- Statistical significance testing (p < 0.05)
- Inter-annotator agreement (Fleiss' κ)
- Construct validity (Pearson r)

**Phase 4C: Ablation Studies**
- Systematic ablation of each component:
  - QLoRA removal impact
  - TurboQuant removal impact
  - LoRA removal impact
  - Class weighting impact
  - Gradient clipping impact

**Phase 4D: Publication Preparation**
- Paper draft for target venue
- Supplementary materials with code
- Data availability statements
- Ethics approval (if human subjects)

## Technical Specifications

### Model Architecture
```
XLM-RoBERTa-base (270M params)
├── QLoRA 4-bit quantization (8x compression)
├── TurboQuant 3-bit KV cache (6x compression)
├── LoRA adapters (0.1% params trainable)
├── Laughter classification head (2 classes)
├── Duchenne regression head (1 dimension)
├── Incongruity regression head (3 dimensions)
└── ToM regression head (3 dimensions)
```

### Training Configuration
```yaml
Quantization:
  qlora: true
  qlora_bits: 4
  turboquant: true
  turboquant_bits: 3
  compression_ratio: 6.0
  lora: true
  lora_r: 16
  lora_alpha: 32

Training:
  epochs: 10
  batch_size: 16
  learning_rate: 2e-5
  classifier_lr: 1e-4
  max_grad_norm: 1.0
  warmup_ratio: 0.1
  gradient_accumulation: 1

Optimization:
  freeze_encoder_epochs: 1
  unfreeze_last_n_layers: 2
  class_weights: [1.0, 5.0]
  early_stopping_patience: 3

Hardware:
  device: auto (cuda/mps/cpu)
  mixed_precision: true
  target_memory: < 5GB
  target_time: < 10 hours
```

## Success Metrics

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Laughter F1 | > 0.92 | sklearn.metrics.f1_score |
| Training Time | < 10 hours | time.time() |
| Memory Usage | < 5GB | torch.cuda.memory_allocated() |
| NaN Losses | 0% | torch.isnan(loss).any() |

### Scientific Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Inter-Annotator Agreement (κ) | > 0.60 | stats.fleiss_kappa |
| Construct Validity (r) | > 0.50 | scipy.stats.pearsonr |
| Statistical Significance (p) | < 0.05 | scipy.stats.ttest_ind |
| 95% CI Width | < 0.05 | numpy.percentile |

### Publication Metrics
| Metric | Target | Venue |
|--------|--------|-------|
| External Benchmarks | 2+ | StandUp4AI, UR-FUNNY |
| Ablation Studies | Complete | Systematic component removal |
| Statistical Validation | Complete | Bootstrapping, significance |
| Code Availability | Public | GitHub + supplementary |

## Risk Mitigation

### Risk 1: Biosemotic Labels Invalid (Probability: 70%)
**Mitigation**:
- Parallel Track 2 ensures baseline success
- Self-supervised approach ready if labels fail
- Publication narrative adaptable

**Fallback**: Publish binary results + self-supervised analysis

### Risk 2: Quantization Artifacts (Probability: 20%)
**Mitigation**:
- Proven in earlier trainings (0.92 F1)
- Small-scale validation before full training
- Multiple quantization levels tested

**Fallback**: Reduce to 8-bit quantization

### Risk 3: Memory Constraints (Probability: 10%)
**Mitigation**:
- 48x total compression
- Gradient checkpointing available
- CPU fallback functional

**Fallback**: Google Colab GPU (free tier)

## Timeline

### Week 1: Foundation
- Day 1-2: Annotation setup + Script integration
- Day 3-7: Annotation collection + Small validation
- Day 8-14: Validation analysis + Full training

### Week 2-3: Integration
- Biosemotic integration (if valid) OR Self-supervised learning
- Multi-task training OR Proxy learning
- Validation and iteration

### Week 4: Publication
- Benchmark evaluation
- Statistical validation
- Ablation studies
- Paper submission

## Acceptance Criteria

### Track 1: Human Validation
✅ 300 examples annotated by 3+ annotators
✅ Inter-annotator agreement computed (Fleiss' κ)
✅ Construct validity computed (Pearson r, 95% CI)
✅ Go/No-Go decision documented

### Track 2: Quantized Training
✅ Training script with ALL proven techniques
✅ No NaN losses in any batch
✅ Memory usage < 5GB
✅ F1 > 0.92 on validation set
✅ Training time < 10 hours

### Integration Phase
✅ Multi-task model (if valid) OR Self-supervised model (if invalid)
✅ Per-task metrics computed and validated
✅ Ablation studies completed
✅ External benchmarks validated

### Publication Ready
✅ Paper draft for target venue
✅ Statistical validation complete
✅ Code available publicly
✅ Supplementary materials complete

## Dependencies

### External Dependencies
- bitsandbytes >= 0.41.0 (QLoRA)
- peft >= 0.7.0 (LoRA)
- transformers >= 4.35.0
- torch >= 2.0.0
- scipy >= 1.11.0 (statistical validation)

### Internal Dependencies
- memory/turboquant/turboquant.py (TurboQuant)
- src/biosemoticai/validation/label_validation.py (validation framework)
- training/train_xlmr_quantized_v1.py (quantized training)
- data/training/final_multilingual_v3/*.jsonl (datasets)

## Open Questions

1. **Annotator Recruitment**: Where to find 3-5 annotators with psychology/linguistics background?
2. **Incentive Structure**: How to compensate annotators (payment, credit, etc.)?
3. **Quality Control**: How to ensure annotation quality during collection?
4. **Timeline Pressure**: Can validation study complete in 2 weeks?

## Next Steps

1. ✅ **IMMEDIATE**: Stop Training #39
2. ✅ **IMMEDIATE**: Launch quantized training test (100 examples)
3. ✅ **TODAY**: Create human validation study setup
4. ✅ **THIS WEEK**: Complete both Track 1 and Track 2
5. ✅ **WEEK 2-3**: Integration based on validation results
6. ✅ **WEEK 4**: Publication preparation and submission

## Success Definition

**Minimum Viable Success**: 0.92+ F1 with binary laughter prediction + publication in tier-2 venue

**Target Success**: 0.95+ F1 with validated biosemotic understanding + publication in tier-1 venue (NeurIPS)

**Stretch Success**: Revolutionary self-supervised biosemotic framework + multiple venue acceptances
