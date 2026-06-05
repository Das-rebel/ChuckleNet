# Implementation Plan: Reinforcement Learning for Multilingual Laughter Prediction
**Version**: 1.0
**Status**: APPROVED
**Start Date**: 2026-05-11
**End Date**: 2026-08-03 (12 weeks)
**Project**: autonomous_laughter_prediction_essential

---

## Executive Summary

This plan details a 12-week implementation of RL-based multilingual laughter prediction, building on the V8.1 baseline (Val F1=0.785, Test F1=0.819). The plan addresses the critical gaps identified in the SOTA PRD: teacher refinement failure (F1 0.078), missing Hindi test set, missing Chinese test set, and StandUp4AI 7-language processing.

**Key Milestones:**
- Week 4: RL trainer Phase 1 (supervised pretraining) complete, Hindi test set created
- Week 8: RL fine-tuning operational, Chinese test set created, StandUp4AI Phase 1 done
- Week 12: Paper draft complete, final model trained, all 7 languages processed

---

## Phase 0: Preparation (Week 0)
**Dates**: 2026-05-05 to 2026-05-10
**Goal**: Fix blocking issues before RL implementation begins

### Tasks

#### Task 0.1: Fix Teacher Refinement Bug (CRITICAL BLOCKER)
**Owner**: Research Team
**Time**: 4-6 hours
**Files**: 
- `training/refine_weak_labels_nemotron.py`
- `experiments/xlmr_standup_baseline_weak_pos5/` (current working model)

**Problem**: Teacher refinement produces F1=0.078 (10x worse than baseline). Root cause: parsing bug causes 0% laughter in refined labels.

**Actions**:
1. Add debug logging to `refine_weak_labels_nemotron.py` line 89-120
2. Print raw LLM output before parsing
3. Validate parsed labels match original word boundaries
4. Test on 100-example subset before full run

**Validation**: Refined model achieves F1 >= 0.70 (within 10% of baseline)

**Success Metric**: Teacher refinement bug fixed, not re-enabled until validated

---

#### Task 0.2: Archive Legacy Files
**Owner**: Research Team
**Time**: 1 hour
**Files to Archive**:
- `train.py` (552 lines, NOT working - per ADR-001)
- `training/old_trainer.py`
- `core/trainer_v7.py`
- `experiments/teacher_refinement_run/` (catastrophic results)

**Action**: Move to `archive/legacy/` directory

**Success Metric**: No training script references archive files

---

#### Task 0.3: Verify V8.1 Baseline Checkpoint
**Owner**: Research Team
**Time**: 30 minutes
**Files**:
- `experiments/xlmr_standup_baseline_weak_pos5/`
- `training/V8_1_FIXED_SCRIPT.py`

**Validation Commands**:
```bash
cd /Users/Subho/autonomous_laughter_prediction_essential
python -c "import torch; m=torch.load('experiments/xlmr_standup_baseline_weak_pos5/pytorch_model.bin'); print('Model loads OK')"
```

**Success Metric**: Baseline model loads without errors, F1=0.819 confirmed

---

## Phase 1: RL Foundation (Weeks 1-4)
**Dates**: 2026-05-11 to 2026-06-07
**Goal**: Implement RL trainer Phase 1, create missing test sets

### Week 1: RL Trainer Core Implementation

#### Task 1.1: Create LaughterRLTrainer Class
**Owner**: Research Team
**Time**: 8 hours
**File**: `training/rl_laughter_trainer.py` (NEW)

**Implementation**:
```python
class LaughterRLTrainer:
    """RL trainer for laughter prediction"""
    
    def __init__(self, config: RLConfig):
        self.actor = LaughterActor(config)      # XLM-R based
        self.critic = LaughterCritic(config)     # Value estimator
        self.reward_model = None                  # Trained in Phase 2
        self.config = config
        
    def pretrain_supervised(self, dataset, epochs=10):
        """Phase 1: Supervised baseline (like V8.1)"""
        # Use CrossEntropyLoss, produce F1 > 0.75
        
    def collect_preferences(self, samples, human_evaluator):
        """Phase 2: Collect human preference data"""
        
    def train_reward_model(self, preferences):
        """Phase 3: Train Bradley-Terry reward model"""
        
    def rl_finetune(self, dataset, reward_model):
        """Phase 4: PPO fine-tuning"""
        
    def evaluate(self, test_set):
        """Multi-objective: F1, Precision, Recall, IoU-F1"""
```

**Dependencies**: None
**Success Metric**: `python training/rl_laughter_trainer.py --test` runs without error

---

#### Task 1.2: Implement Reward Function
**Owner**: Research Team
**Time**: 4 hours
**File**: `training/rl_laughter_trainer.py` (add to class)

**Reward Function Specification**:
```python
def compute_reward(predicted: Action, ground_truth: Label, context: Context) -> float:
    """
    Multi-objective reward for laughter prediction.
    
    Components:
    - base: 1.0 if pred == gt else -1.0
    - temporal: +0.5 if matches adjacent predictions (coherence bonus)
    - intensity_calibration: +0.3 if intensity matches audience energy
    - cultural_adaptation: +0.2 if matches cultural pattern
    - fp_penalty: -0.5 for false positive (non-laugh predicted as laugh)
    """
    base = 1.0 if predicted.laugh_label == ground_truth else -1.0
    temporal = 0.5 if predicted.matches_neighbor else 0.0
    intensity_bonus = 0.3 * (1.0 - abs(predicted.intensity - context.audience_energy))
    cultural_bonus = 0.2 if predicted.cultural_correct else 0.0
    fp_penalty = -0.5 if (predicted.laugh_label == 1 and ground_truth == 0) else 0.0
    return base + temporal + intensity_bonus + cultural_bonus + fp_penalty
```

**Dependencies**: Task 1.1
**Success Metric**: Reward function produces values in range [-1.5, 2.0]

---

#### Task 1.3: Implement State and Action Spaces
**Owner**: Research Team
**Time**: 4 hours
**Files**: 
- `training/rl_config.py` (NEW)
- `training/rl_laughter_trainer.py`

**State Space**:
```python
state = {
    "word_embedding": torch.Tensor,        # [seq_len, 768] XLM-R output
    "pos_encoding": torch.Tensor,          # [seq_len] position IDs
    "speaker_context": str,                 # "opening_joke" / "punchline" / "callback"
    "audience_response": float,            # [-1, 1] from audio analysis (or 0 if N/A)
    "cultural_background": str,             # en / zh / hi / es / fr / it / pt
    "prev_laughter_probs": List[float],     # Last 5 word laughter probs
    "conversation_turn": int,              # Joke # in set
    "duchenne_score": float,               # [0, 1] from biosemotic
    "incongruity_score": float,            # [0, 1]
    "tom_score": float,                    # [0, 1]
}
```

**Action Space**:
```python
action = {
    "laugh_label": 0 | 1,                  # Binary laughter prediction
    "confidence": float,                   # [0, 1] certainty
    "laughter_type": "micro" | "burst" | "solo" | "群体",  # if laugh=1
    "intensity": 0.0 | 0.33 | 0.66 | 1.0
}
```

**Dependencies**: Task 1.1
**Success Metric**: State/action serialization works for batch size 8

---

### Week 2: Human Preference Collection Framework

#### Task 1.4: Implement Preference Collection Interface
**Owner**: Research Team
**Time**: 6 hours
**Files**: 
- `training/preference_collector.py` (NEW)
- `training/preference_dataset.jsonl` (output)

**Interface Design**:
```python
class PreferenceCollector:
    """
    Collects human preferences between pairs of model predictions.
    
    Workflow:
    1. Select sample from validation set
    2. Generate 2 candidate predictions (different model configs)
    3. Present to human: "Which prediction better matches expected laughter?"
    4. Record preference: A / B / Same
    """
    
    def __init__(self, output_path: str):
        self.preferences = []
        
    def generate_candidates(self, sample, model_a, model_b):
        """Generate 2 candidate predictions for same input"""
        
    def present_to_human(self, sample, cand_a, cand_b):
        """Display candidates and collect preference"""
        
    def save(self):
        """Save to JSONL format"""
```

**Preference Data Format**:
```jsonl
{"sample_id": "xxx", "text": "...", "gt_label": 1, "cand_a": {...}, "cand_b": {...}, "preference": "A", "annotator": "human1"}
```

**Dependencies**: Task 1.1
**Success Metric**: Interface presents 10 samples without error

---

#### Task 1.5: Collect 500 Preference Samples (English)
**Owner**: Research Team
**Time**: 4 hours (500 samples at ~30 sec/sample)
**Output**: `data/preferences/en_preferences_500.jsonl`

**Process**:
1. Select 500 diverse samples from validation set (stratified by laughter label)
2. Generate candidate predictions using 2 model variants (pos_weight=4 vs pos_weight=6)
3. Present to human evaluator
4. Record preference

**Success Metric**: 500 preferences collected, inter-annotator agreement > 70%

---

#### Task 1.6: Create Hindi Test Set (CRITICAL GAP)
**Owner**: Research Team
**Time**: 8 hours (manual annotation)
**Output**: `data/test/hindi_test_500.jsonl`

**Current State**: Hindi has 0 examples in test set (per STATUS_REPORT_2026_05_04.md)

**Annotation Process**:
1. Use existing 48 Vir Das examples (word-level)
2. Manually annotate additional 452 examples from Vir Das audio
3. Mark laughter trigger words with label=1

**Format**:
```jsonl
{"words": ["word1", "word2", ...], "labels": [0, 1, 0, ...], "language": "hi-latn", "source": "vir_das_manual"}
```

**Success Metric**: 500 Hindi test examples with verified laughter labels

---

### Week 3: Reward Model Training

#### Task 1.7: Implement Bradley-Terry Reward Model
**Owner**: Research Team
**Time**: 6 hours
**File**: `training/reward_model.py` (NEW)

**Implementation**:
```python
class RewardModel:
    """
    Bradley-Terry model for preference probabilities.
    
    P(preferred | A, B) = sigmoid(reward(A) - reward(B))
    """
    
    def __init__(self, encoder: XLM-REncoder):
        self.encoder = encoder
        self.reward_head = nn.Linear(768, 1)
        
    def forward(self, sample):
        """Compute reward score for a prediction"""
        encoding = self.encoder(sample)
        return self.reward_head(encoding)
    
    def compute_loss(self, preferences):
        """
        Bradley-Terry loss:
        L = -sum(log sigmoid(reward(A) - reward(B))) for preferred A
        """
        
    def train(self, preferences, epochs=10):
        """Train on preference data"""
```

**Dependencies**: Tasks 1.4, 1.5
**Success Metric**: Reward model converges, reward predictions correlate with preferences

---

#### Task 1.8: Create Chinese Test Set (CRITICAL GAP)
**Owner**: Research Team
**Time**: 8 hours (manual annotation)
**Output**: `data/test/chinese_test_500.jsonl`

**Current State**: Chinese has 0 examples in test set

**Source**: Use existing zh examples from V8.1 dataset, split 500 for test

**Success Metric**: 500 Chinese test examples with verified labels

---

### Week 4: Phase 1 Completion + StandUp4AI Phase 1

#### Task 1.9: Phase 1 Supervised Pretraining Validation
**Owner**: Research Team
**Time**: 4 hours
**File**: `training/rl_laughter_trainer.py`

**Validation Commands**:
```bash
cd /Users/Subho/autonomous_laughter_prediction_essential
python training/rl_laughter_trainer.py \
  --phase 1 \
  --base_model FacebookAI/xlm-roberta-base \
  --data data/v8_1_final/ \
  --output experiments/rl_phase1 \
  --epochs 10
```

**Expected Results**:
- Val F1 >= 0.75 (within 5% of V8.1 baseline)
- IoU-F1 >= 0.75
- Training loss < 0.1

**Success Metric**: Phase 1 produces working supervised baseline

---

#### Task 1.10: StandUp4AI Phase 1 - Train on Pre-labeled Data
**Owner**: Research Team
**Time**: 6 hours
**Files**:
- `/tmp/standup4ai_dataset/Examples_label/` (4 CSV files, 3,203 words)
- `training/convert_standup4ai_labels.py` (NEW)

**Convert StandUp4AI CSV to Training Format**:
```python
# Input: /tmp/standup4ai_dataset/Examples_label/-1FrUOEswOk.csv
# Format: text,timestamp,label (L/O)
# Output: {words: [], labels: [], language: 'fr', video_id: '...'}

def convert_standup4ai_csv(csv_path):
    """Convert StandUp4AI CSV to training JSONL"""
    df = pd.read_csv(csv_path)
    words = []
    labels = []
    for _, row in df.iterrows():
        word = row['text'].split()  # Split on whitespace
        label = 1 if row['label'] == 'L' else 0
        words.extend(word)
        labels.extend([label] * len(word))
    return {'words': words, 'labels': labels, ...}
```

**Training Command**:
```bash
python training/rl_laughter_trainer.py \
  --phase 1 \
  --data /tmp/standup4ai_dataset/Examples_label/ \
  --output experiments/standup4ai_phase1 \
  --epochs 10
```

**Success Metric**: Model trained on 3,203 StandUp4AI words, Val F1 >= 0.70

---

#### Task 1.11: Checkpoint - Phase 1 Complete
**Owner**: Research Lead
**Time**: 1 hour
**Review Criteria**:
- [ ] RL trainer Phase 1 implemented
- [ ] Reward function working
- [ ] 500 English preferences collected
- [ ] Hindi test set (500 examples) created
- [ ] Chinese test set (500 examples) created
- [ ] StandUp4AI Phase 1 trained

**Go/No-Go**: Proceed to Phase 2 only if all items checked

---

## Phase 2: RL Fine-tuning (Weeks 5-8)
**Dates**: 2026-06-08 to 2026-07-05
**Goal**: Implement PPO fine-tuning, expand to all StandUp4AI languages

### Week 5: PPO Implementation

#### Task 2.1: Implement PPO Fine-tuning
**Owner**: Research Team
**Time**: 8 hours
**File**: `training/rl_laughter_trainer.py` (add PPO methods)

**PPO Implementation**:
```python
class LaughterRLTrainer:
    def rl_finetune(self, dataset, reward_model, epochs=10):
        """
        PPO fine-tuning with KL divergence penalty.
        
        L = E[r] - beta * KL(pi_new || pi_old)
        
        With KL annealing schedule:
        - Early: high beta (conservative updates)
        - Late: low beta (more exploration)
        """
        beta = 0.1  # Initial KL penalty
        beta_schedule = linear_anneal(beta, 0.01, epochs)
        
        for epoch in epochs:
            for batch in dataset:
                # Compute advantages via reward model
                rewards = reward_model(batch)
                
                # PPO clipped objective
                ratio = torch.exp(log_probs_new - log_probs_old)
                clipped = torch.clamp(ratio, 1-eps, 1+eps)
                policy_loss = -min(ratio * advantages, clipped * advantages)
                
                # KL penalty
                kl = kl_divergence(pi_new, pi_old)
                
                total_loss = policy_loss + beta * kl
                
    def linear_anneal(self, start, end, steps):
        """Linear annealing schedule"""
        return [start + (end - start) * i / steps for i in range(steps)]
```

**Dependencies**: Tasks 1.7, 1.9
**Success Metric**: PPO training runs without NaN/Inf losses

---

#### Task 2.2: Multi-objective Evaluation Framework
**Owner**: Research Team
**Time**: 4 hours
**File**: `training/evaluate_multilingual.py` (NEW)

**Metrics by Language**:
```python
def evaluate_multilingual(model, test_sets):
    """
    Multi-objective evaluation across all languages.
    
    Returns:
    {
        'en': {'f1': 0.82, 'precision': 0.78, 'recall': 0.86, 'iou_f1': 0.84},
        'zh': {'f1': 0.75, 'precision': 0.72, 'recall': 0.78, 'iou_f1': 0.77},
        'hi': {'f1': 0.70, 'precision': 0.68, 'recall': 0.72, 'iou_f1': 0.71},
        ...
    }
    """
```

**Dependencies**: Tasks 1.6, 1.8
**Success Metric**: Evaluation runs on all 3 languages (en, zh, hi)

---

### Week 6: StandUp4AI Language Expansion

#### Task 2.3: StandUp4AI Phase 2 - Apply Model to Existing Transcripts
**Owner**: Research Team
**Time**: 4 hours
**Files**:
- `/tmp/standup4ai_full/transcripts/` (195 transcripts)
- `experiments/standup4ai_phase1/` (trained model)

**Process**:
```bash
python training/apply_laughter_model.py \
  --model experiments/standup4ai_phase1/best_model \
  --input /tmp/standup4ai_full/transcripts/ \
  --output data/standup4ai_processed/transcripts_with_labels.jsonl
```

**Expected Output**: ~50,000 words with predicted laugh labels

**Success Metric**: 195 transcripts processed, labels added

---

#### Task 2.4: StandUp4AI 7-Language Transcription Setup
**Owner**: Research Team
**Time**: 8 hours
**Files**:
- `training/transcribe_standup4ai_batch.py` (NEW)
- `/tmp/standup4ai_dataset/` (3,617 videos)

**Language Coverage**:
| Language | Code | Videos | Hours | Pre-labeled |
|----------|------|--------|-------|-------------|
| Spanish | es | 1,375 | 77h | No |
| French | fr | 652 | 86h | Yes (1 CSV) |
| English | en | 582 | 70h | Yes (2 CSVs) |
| Italian | it | 567 | 55h | No |
| Portuguese | pt | 245 | 23h | No |
| Czech | cs | 123 | 12h | No |
| Hungarian | hu | 73 | 11h | No |

**Transcription Strategy**:
1. Use Whisper for batch transcription (handle multiple languages)
2. Process in batches of 50 videos to avoid Colab timeout
3. Checkpoint every 100 videos

**Success Metric**: Transcription pipeline runs on 100 videos without error

---

#### Task 2.5: StandUp4AI Transcription Batch 1 (English + French)
**Owner**: Research Team (Colab)
**Time**: 12 hours (Colab compute)
**Scope**: 200 videos (en: 100, fr: 100)

**Commands**:
```bash
# Run in Colab
python training/transcribe_standup4ai_batch.py \
  --languages en,fr \
  --max_videos 200 \
  --output data/standup4ai_transcribed_batch1/
```

**Success Metric**: 200 videos transcribed, ~1M words added

---

### Week 7: StandUp4AI Full Processing

#### Task 2.6: StandUp4AI Transcription Batch 2 (Spanish + Italian)
**Owner**: Research Team (Colab)
**Time**: 12 hours
**Scope**: 300 videos (es: 175, it: 125)

**Success Metric**: 300 videos transcribed

---

#### Task 2.7: StandUp4AI Transcription Batch 3 (Portuguese + Czech + Hungarian)
**Owner**: Research Team (Colab)
**Time**: 8 hours
**Scope**: 200 videos (pt: 100, cs: 60, hu: 40)

**Success Metric**: 200 videos transcribed

---

#### Task 2.8: Apply Laughter Model to All Transcribed Data
**Owner**: Research Team
**Time**: 4 hours
**Input**: `data/standup4ai_transcribed_batch{1,2,3}/`
**Output**: `data/standup4ai_processed/all_with_labels.jsonl`

**Command**:
```bash
python training/apply_laughter_model.py \
  --model experiments/rl_phase1/best_model \
  --input data/standup4ai_transcribed_batch1/ \
  --input data/standup4ai_transcribed_batch2/ \
  --input data/standup4ai_transcribed_batch3/ \
  --output data/standup4ai_processed/all_with_labels.jsonl
```

**Success Metric**: ~1.5M words with predicted laugh labels

---

### Week 8: Phase 2 Completion

#### Task 2.9: Retrain on Expanded StandUp4AI Data
**Owner**: Research Team
**Time**: 8 hours
**Input**: Combined real labels (3,203) + predicted labels (~1.5M)

**Command**:
```bash
python training/rl_laughter_trainer.py \
  --phase 1 \
  --data data/standup4ai_processed/all_with_labels.jsonl \
  --output experiments/standup4ai_full \
  --epochs 10
```

**Success Metric**: Final model trained on expanded dataset

---

#### Task 2.10: Checkpoint - Phase 2 Complete
**Owner**: Research Lead
**Review Criteria**:
- [ ] PPO fine-tuning implemented
- [ ] Multi-objective evaluation working
- [ ] 700+ videos transcribed (en, fr, es, it, pt, cs, hu)
- [ ] ~1.5M words with predicted labels
- [ ] Final model retrained on expanded data

**Go/No-Go**: Proceed to Phase 3 and paper writing

---

## Phase 3: Evaluation and Publication (Weeks 9-12)
**Dates**: 2026-07-06 to 2026-08-03
**Goal**: Complete evaluation, write paper, submit

### Week 9: Final Evaluation

#### Task 3.1: Comprehensive Evaluation on All Languages
**Owner**: Research Team
**Time**: 6 hours
**Output**: `docs/EVALUATION_RESULTS.md`

**Evaluation Matrix**:
| Language | Test Set | F1 | Precision | Recall | IoU-F1 | N |
|---------|----------|-----|-----------|--------|--------|---|
| English | 4,124 | 0.82 | 0.79 | 0.85 | 0.88 | 4,124 |
| Chinese | 500 | TBD | TBD | TBD | TBD | 500 |
| Hindi | 500 | TBD | TBD | TBD | TBD | 500 |
| Spanish | 800 | TBD | TBD | TBD | TBD | 800 |
| French | 800 | TBD | TBD | TBD | TBD | 800 |
| Italian | 500 | TBD | TBD | TBD | TBD | 500 |
| Portuguese | 250 | TBD | TBD | TBD | TBD | 250 |
| Czech | 150 | TBD | TBD | TBD | TBD | 150 |
| Hungarian | 100 | TBD | TBD | TBD | TBD | 100 |

**Success Metric**: All metrics computed, results documented

---

#### Task 3.2: Ablation Study (RL vs Supervised)
**Owner**: Research Team
**Time**: 8 hours
**Comparison**:
- Supervised baseline (V8.1): pos_weight=5.0, no RL
- RL fine-tuned (Phase 2): PPO with human feedback

**Results Format**:
```python
{
    'supervised_val_f1': 0.785,
    'rl_val_f1': 0.XXX,  # To be determined
    'improvement': 0.XXX,
    'p_value': 0.XXX,  # Statistical significance
}
```

**Success Metric**: Ablation results show +/- 5% from baseline

---

### Week 10: Paper Writing

#### Task 3.3: Write Paper Draft - Introduction + Abstract
**Owner**: Research Team
**Time**: 6 hours
**File**: `docs/PAPER_DRAFT.md`

**Abstract Outline** (250 words):
1. **Problem**: Word-level laughter prediction in multilingual comedy
2. **Gap**: Limited labeled data, no multilingual baseline
3. **Contribution**: 
   - RL-based multilingual laughter prediction
   - XLM-R backbone with biosemotic features
   - 7-language StandUp4AI processing
   - New Hindi and Chinese test sets

**Success Metric**: Abstract accepted by advisor review

---

#### Task 3.4: Write Paper Draft - Related Work + Methodology
**Owner**: Research Team
**Time**: 8 hours

**Related Work Sections**:
1. Humor detection in NLP (survey 10 papers)
2. Multilingual sequence labeling (survey 10 papers)
3. RL in NLP (survey 5 papers)
4. Comedy dataset surveys

**Methodology Sections**:
1. Task definition (word-level laughter prediction)
2. Model architecture (XLM-R + RL)
3. Reward function design
4. Training procedure

**Success Metric**: Related work covers 25+ papers, methodology complete

---

#### Task 3.5: Write Paper Draft - Experiments + Results
**Owner**: Research Team
**Time**: 6 hours

**Experiments Section**:
1. Datasets (en, zh, hi test sets + StandUp4AI)
2. Baselines (V8.1 supervised, random, keyword)
3. Ablation study (RL components)
4. Per-language breakdown

**Results Section**:
1. Main results table
2. Statistical significance
3. Error analysis
4. Failure cases

**Success Metric**: Experiments reproducible from described procedure

---

#### Task 3.6: Write Paper Draft - Conclusion + Future Work
**Owner**: Research Team
**Time**: 4 hours

**Conclusion Points**:
1. RL-based multilingual laughter prediction works
2. Achieved F1=0.XX on 7 languages
3. StandUp4AI dataset expanded
4. Future: more languages, better audio integration

**Success Metric**: Conclusion < 500 words, no new claims

---

### Week 11: Paper Revision + Submission Prep

#### Task 3.7: Paper Revision Round 1
**Owner**: Research Team
**Time**: 8 hours
**Input**: `docs/PAPER_DRAFT.md`
**Output**: `docs/PAPER_REVISION_1.md`

**Revision Checklist**:
- [ ] All claims backed by experiments
- [ ] Tables/figures have captions
- [ ] Citations complete
- [ ] Appendices for supplementary material

**Success Metric**: Paper passes internal review

---

#### Task 3.8: Create Supplementary Materials
**Owner**: Research Team
**Time**: 4 hours
**Output**: `docs/paper_supplementary.pdf`

**Contents**:
1. A: Full evaluation metrics by language
2. B: Hyperparameter sensitivity analysis
3. C: Error analysis examples
4. D: Code documentation

**Success Metric**: Supplementary materials complete

---

#### Task 3.9: Format for ACL/EMNLP
**Owner**: Research Team
**Time**: 4 hours

**Format Requirements**:
- ACL/EMNLP 2026 style file
- PDF submission
- 8 pages + 2 references
- Anonymized for review

**Success Metric**: Paper compiles with official style file

---

### Week 12: Submission

#### Task 3.10: Final Review + Submission
**Owner**: Research Lead
**Time**: 4 hours
**Target**: ACL/EMNLP 2026

**Submission Checklist**:
- [ ] Paper formatted correctly
- [ ] Supplementary materials ready
- [ ] Code released (GitHub)
- [ ] Model weights released (HuggingFace)
- [ ] Anonymous submission submitted

**Success Metric**: Paper submitted before deadline

---

#### Task 3.11: Archive Results
**Owner**: Research Team
**Time**: 2 hours
**Output**: `experiments/final_results/`

**Contents**:
- Trained models
- Evaluation results
- Paper drafts
- Datasets (if releasable)

**Success Metric**: All artifacts archived

---

## Resource Requirements Summary

### Compute Resources

| Phase | Task | GPU Hours | Notes |
|-------|------|-----------|-------|
| Phase 1 | RL trainer development | 20 | Development/testing |
| Phase 1 | Phase 1 training | 40 | 10 epochs x 4 configs |
| Phase 2 | PPO fine-tuning | 60 | 10 epochs x 6 configs |
| Phase 2 | StandUp4AI transcription | 100 | Colab (free tier) |
| Phase 2 | Final training | 30 | On expanded data |
| Phase 3 | Evaluation | 10 | 9 languages x multiple metrics |
| **TOTAL** | | **260 hours** | |

### Human Resources

| Role | Tasks | Time Commitment |
|------|-------|-----------------|
| Research Lead | All tasks | 20 hrs/week |
| Research Team | Tasks 1.4-1.5, 1.6, 1.8 | 10 hrs/week |
| Annotators (2) | Preference collection | 4 hrs/week |

### External Resources

| Resource | Purpose | Cost |
|----------|---------|------|
| Colab Pro | StandUp4AI transcription | ~$10/month |
| HuggingFace | Model hosting | Free |
| GitHub | Code release | Free |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Colab timeout during transcription | High | Medium | Checkpoint every 100 videos |
| RL training instability | Medium | High | Use KL annealing, gradient clipping |
| Hindi test set quality | Medium | High | Double-annotation, 2 annotators |
| Paper rejected | Medium | Medium | Submit to workshop first |
| Teacher refinement bug persists | Low | High | Disable until fixed |

---

## Success Metrics - Final

| Metric | Target | Baseline |
|--------|--------|----------|
| Val F1 (en) | >= 0.78 | 0.785 |
| Test F1 (en) | >= 0.82 | 0.819 |
| Test F1 (zh) | >= 0.70 | N/A (0 test examples) |
| Test F1 (hi) | >= 0.65 | N/A (0 test examples) |
| Languages processed | 7 | 2 |
| RL vs supervised delta | +/- 5% | N/A |
| Paper submitted | Yes | No |

---

## Appendix A: File Inventory

### New Files to Create

| File | Purpose | Task |
|------|---------|------|
| `training/rl_laughter_trainer.py` | RL trainer core | 1.1 |
| `training/rl_config.py` | Configuration dataclasses | 1.3 |
| `training/reward_model.py` | Bradley-Terry reward model | 1.7 |
| `training/preference_collector.py` | Human preference UI | 1.4 |
| `training/evaluate_multilingual.py` | Multi-objective evaluation | 2.2 |
| `training/convert_standup4ai_labels.py` | CSV to JSONL conversion | 1.10 |
| `training/apply_laughter_model.py` | Batch inference | 2.3 |
| `training/transcribe_standup4ai_batch.py` | StandUp4AI transcription | 2.4 |
| `docs/PAPER_DRAFT.md` | Paper draft | 3.3-3.6 |

### Existing Files to Modify

| File | Change | Task |
|------|--------|------|
| `training/V8_1_FIXED_SCRIPT.py` | Reference in RL trainer | 1.1 |
| `experiments/xlmr_standup_baseline_weak_pos5/` | Load as base model | 1.1 |

### Files to Archive

| File | Reason |
|------|--------|
| `train.py` | NOT working (ADR-001) |
| `core/trainer_v7.py` | Legacy |
| `experiments/teacher_refinement_run/` | Catastrophic results |

---

## Appendix B: Timeline Gantt

```
Week 0:  [0.1 Fix Teacher Refinement] [0.2 Archive Files] [0.3 Verify Baseline]
Week 1:  [1.1 RL Trainer Core] [1.2 Reward Function] [1.3 State/Action Spaces]
Week 2:  [1.4 Preference UI] [1.5 Collect 500 Prefs] [1.6 Hindi Test Set]
Week 3:  [1.7 Reward Model] [1.8 Chinese Test Set]
Week 4:  [1.9 Phase 1 Validation] [1.10 StandUp4AI Phase 1] [1.11 CHECKPOINT]
Week 5:  [2.1 PPO Implementation] [2.2 Multi-obj Evaluation]
Week 6:  [2.3 Apply to Transcripts] [2.4 Transcriber Setup] [2.5 Batch 1 (en+fr)]
Week 7:  [2.6 Batch 2 (es+it)] [2.7 Batch 3 (pt+cs+hu)] [2.8 Apply Model All]
Week 8:  [2.9 Retrain Full] [2.10 CHECKPOINT]
Week 9:  [3.1 Full Evaluation] [3.2 Ablation Study]
Week 10: [3.3 Abstract+Intro] [3.4 Related+Methods] [3.5 Experiments] [3.6 Conclusion]
Week 11: [3.7 Revision 1] [3.8 Supplementary] [3.9 Format]
Week 12: [3.10 Final Review+Submit] [3.11 Archive]
```

---

**END OF IMPLEMENTATION PLAN**

*Document Version: 1.0*
*Created: 2026-05-05*
*Status: APPROVED*