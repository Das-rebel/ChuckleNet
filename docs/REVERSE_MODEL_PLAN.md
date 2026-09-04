# Funny Strength Predictor — Reverse Model Architecture Plan

> **Problem**: ChuckleNet detects laughter POST-HOC (audio → laugh/no-laugh).  
> **Reverse Model**: Predict FUNNY STRENGTH (0-100%) BEFORE audience reacts.  
> **Causal flip**: audience reaction → comedy content properties.

---

## 1. Problem Framing

| ChuckleNet (Forward) | Reverse Model |
|---|---|
| Input: comedy text + audio | Input: comedy text (± audio) |
| Output: binary laugh/no-laugh | Output: continuous funny_strength (0-100%) |
| Target: per-word [laughter] marker | Target: laugh density per segment |
| Task: binary classification | Task: ordinal regression (0-100 continuous) |
| Sits AFTER performance | Sits BEFORE writing/performance |

### Key Hypothesis
**H**: If ChuckleNet learned "this acoustic pattern → laughter", we can invert the mapping: "this text pattern → expected laughter density". The text representations that predict laughter CAN be used to score comedy before audio exists.

---

## 2. Training Target Engineering

### 2A. Primary Target: Laugh Density (Continuous)
```
funny_strength_i = (count of [laughter]/[applause]/[praise] words in segment_i) / (total words in segment_i) × 100
```

- Segment = utterance or fixed 30-second window
- Produces continuous 0-100% score per segment
- Aligned with what we measure post-hoc

### 2B. Aggregation Strategy
| Strategy | Method | Pros | Cons |
|---|---|---|---|
| **Mean** | Average laugh density across segment words | Smooth, interpretable | Loses burst info |
| **Max** | Peak laughter burst | Captures best joke moment | Noisy |
| **Integral** | Sum of laugh density × duration | Physics-correct | Hard to calibrate |
| **Weighted** | Exponential decay from punchline | Theory-aligned | Extra hyperparameter |

**Recommended**: Mean + punchline-weighted hybrid:
```
score = α × mean_laugh_density + (1-α) × max_laugh_density_near_punchline
```

### 2C. Video-Level Supervision (auxiliary)
- YouTube view-to-like ratio as engagement proxy
- Star rating from comedy forums
- Use as auxiliary loss (multi-task learning)

---

## 3. Feature Engineering

### 3A. Text-Based Features (from transcript only — no audio needed)

| Feature | How to Extract | Theory Basis | Humor Relevance |
|---|---|---|---|
| **Incongruity score** | Setup/punchline semantic distance via XLM-R embeddings | Suls 1972 | Punchline subverts setup expectation |
| **Comic timing ratio** | Punchline word count / setup word count | Proportion of setup:punch | Longer setup → bigger payoff |
| **Pause placement** | Silence markers in transcript | Purandare 2006 | Pre-punchline pause creates tension |
| **Interaction pattern** | Monologue vs dialogue vs call-response | Berk 2019 | Call-and-response = 100% laugh |
| **Speaker intent tag** | Playful banter vs setup vs observation | ACT theory | Banter = 93.7% laugh rate |
| **Tension arc** | Rising/falling energy across utterance | Dramatic arc | Tension buildup → release |
| **Surprise lexicals** | Count of surprising words (by XLM-R perplexity) | Incongruity theory | Surprising words signal punchline |
| **Self-deprecation index** | First-person pronoun ratio |心理学 | Self-deprecating humor wins |
| **Taboo/edge score** | LLM-labeled taboo-level (1-5) | Benign Violation Theory | Optimal violation = max laugh |

### 3B. Audio-Based Features (optional, for multimodal)

| Feature | Extract Via | Validation |
|---|---|---|
| **Pause duration** | librosa amplitude threshold | Purandare 2006: most predictive single feature |
| **F0 contour** | librosa.pyin F0 tracking | Pickering 2009: F0 DROP before punchline |
| **Speech rate acceleration** | words/second change | Berk 2019: acceleration before punchline |
| **RMS energy spike** | librosa.feature.rms | Energy correlate with laughter |
| **Duchenne markers** | 250-500Hz spectral energy | Bacharowski 2001 |

### 3C. Multimodal Alignment
- Text timestamp + audio timestamp must align
- Use Whisper word-level timestamps as anchor
- Audio features averaged per text segment

---

## 4. Architecture Options

### Option A: XLM-R Fine-Tune (Text-Only, Fastest 0→1)

```
Text → XLM-R-base → [CLS] token → Linear(768→256) → GELU → Dropout → Linear(256→1) → Sigmoid × 100
Loss: MSE(predicted_score, laugh_density × 100)
```

**Pros**: Fast, no audio needed, leverages XLM-R's implicit humor knowledge  
**Cons**: Ignores prosody, less accurate for implicit humor

**Hyperparameters**:
- LR: 2e-5 (XLM-R), 1e-3 (head)
- Epochs: 3-5
- Pos weight: cap at 5.0
- Warmup: 10% of steps

### Option B: Multimodal Fusion (Best Accuracy)

```
Text → XLM-R-base → [CLS] token (768-dim)
Audio prosody (23-dim) → Linear(23→64) → BN → GELU

[CLS_768 | prosody_64] → concat → MLP(832→256→64→1) → Sigmoid × 100
Loss: MSE + 0.1 × ordinal_CE (see below)
```

**Pros**: Best of both modalities  
**Cons**: Needs aligned audio + text

### Option C: Ordinal Classification (Theoretically Grounded)

Instead of regression, treat as 5-class ordinal:
- 0: Not funny (0-20%)
- 1: Mildly funny (20-40%)
- 2: Funny (40-60%)
- 3: Very funny (60-80%)
- 4: Hilarious (80-100%)

**Loss**: Ordinal Cross-Entropy (CORAL loss):
```python
def coral_loss(logits, labels, num_classes=5):
    # labels are integers 0-4
    return F.binary_cross_entropy_with_logits(
        cumulative_logits.cumsum(dim=-1),  # cumulative
        F.one_hot(labels, num_classes).float()
    )
```

**Advantage**: More stable gradients, natural ordering constraint, interpretable buckets

### Option D: Two-Stage Cascade (Recommended)

```
Stage 1: Is this even comedy? (binary classifier, fast rejection)
Stage 2: How funny? (regression on Stage-1 positives only)
```

**Rationale**: Many segments aren't trying to be funny. Stage 1 filters these. Stage 2 focuses compute on genuine comedy.

---

## 5. Recommended Architecture: Multimodal Cascade

```
Stage 1 (Binary Filter):
  Text → XLM-R → Binary(logistic) → is_comedy?

Stage 2 (Funny Strength — activated only if Stage 1 = True):
  Text → XLM-R [CLS] (768)
  Prosody → Linear(23→64) → BN → GELU (64)
  Concatenate → [832] → MLP → Sigmoid × 100
  Loss: MSE + 0.05 × binary_CE(stage1)
```

**Training**:
1. Train Stage 1 on binary laughter labels (standard ChuckleNet task)
2. Freeze Stage 1 weights
3. Train Stage 2 on laugh_density × 100
4. Joint fine-tune Stage 1 + Stage 2 end-to-end with weighted loss

---

## 6. Training Recipe

### Data Pipeline
```python
class FunnyStrengthDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_len=128):
        self.data = load_jsonl(jsonl_path)
        self.tokenizer = tokenizer
        
    def __getitem__(self, idx):
        item = self.data[idx]
        text = item['text']
        # Aggregate word-level labels to segment-level funny_strength
        n_words = len(item['words'])
        n_laughs = sum(1 for w in item.get('labels', []) if w == 1)
        target = (n_laughs / n_words * 100) if n_words > 0 else 0
        
        enc = self.tokenizer(text, truncation=True, max_length=max_len)
        return {
            'input_ids': enc['input_ids'],
            'attention_mask': enc['attention_mask'],
            'prosody': torch.tensor(item['prosody_mean'][:23]),  # 23-dim
            'target': torch.tensor(target, dtype=torch.float32)
        }
```

### Hyperparameters
| Param | Value | Rationale |
|---|---|---|
| LR (XLM-R) | 2e-5 | Standard for text fine-tuning |
| LR (head) | 1e-3 | Faster adaptation |
| Batch size | 16 | MacBook M3 GPU memory |
| Max length | 128 | Most utterances < 64 words |
| Epochs | 5 | Enough for convergence |
| Warmup ratio | 0.1 | Standard |
| Weight decay | 0.01 | Standard |
| Pos weight cap | 5.0 | From AGENTS.md |

### Training Loop
```python
model = FunnyStrengthModel()
optimizer = AdamW([
    {'params': model.xlmr.parameters(), 'lr': 2e-5},
    {'params': model.prosody_proj.parameters(), 'lr': 1e-3},
    {'params': model.head.parameters(), 'lr': 1e-3},
])
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps, num_steps)

for epoch in range(5):
    model.train()
    for batch in dataloader:
        enc = tokenizer(batch['text'], return_tensors='pt', padding=True, truncation=True, max_length=128)
        prosody = batch['prosody']
        target = batch['target']
        
        pred = model(enc['input_ids'], enc['attention_mask'], prosody)
        loss = F.mse_loss(pred.squeeze(), target)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
```

---

## 7. Validation Strategy

### Primary Metrics
| Metric | Formula | Why |
|---|---|---|
| **Spearman ρ** | rank correlation(pred, target) | Captures ordering, not absolute |
| **MSE** | mean((pred - target)²) | Calibrated accuracy |
| **MAE** | mean(|pred - target|) | Interpretable error |
| **Top-K Recall** | Does top-10% predicted = top-10% actual? | Practical relevance |

### Baselines to Beat
| Baseline | Expected Funny_Strength Score |
|---|---|
| Random | ~50 MSE |
| Word-count heuristic | ~35 MSE |
| XLM-R text-only (no prosody) | ~25 MSE |
| **Multimodal (target)** | **<15 MSE** |

---

## 8. Inference & Deployment

### ONNX Export
```python
model.eval()
torch.onnx.export(
    model, (dummy_ids, dummy_mask, dummy_prosody),
    "funny_strength.onnx",
    input_names=['input_ids', 'attention_mask', 'prosody'],
    output_names=['funny_score'],
    dynamic_axes={...}
)
```

### API Spec
```python
@app.post("/score")
def score_comedy(request: ScoreRequest):
    """
    request.text: str  # comedy transcript
    request.include_prosody: bool  # if True, also extract audio features
    """
    score = model.predict(request.text)
    breakdown = model.explain(request.text)  # feature importance
    return {
        "funny_strength": round(score, 1),  # 0-100
        "bucket": get_bucket(score),  # not_funny/mild/funny/very_funny/hilarious
        "breakdown": breakdown,
        "model_version": "v0.1"
    }
```

---

## 9. Product Spec

### Target Use Cases (ranked)
1. **Comedians**: Pre-test sets before open mic (daily iteration loop)
2. **Content commissioners**: Score script submissions before buying
3. **Social comedy writers**: Rank tweet-thread jokes before posting

### Business Model
| Tier | Price | Limits |
|---|---|---|
| Free | $0 | 10 scores/month |
| Pro | $9.99/mo | 500 scores/month |
| API | $0.01/req | 10K+ |

### Unfair Advantage
- Data flywheel: more predictions → more training signal → better model
- Laughter density database: first dataset mapping text→funny_strength
- Complementary to ChuckleNet: sell as a bundle ("write funny, then verify it lands")

---

## 10. Milestones

| Week | Milestone | Output |
|---|---|---|
| **1** | Data pipeline + target engineering | FunnyStrengthDataset class |
| **2** | XLM-R text-only baseline | Trained model, Spearman ρ baseline |
| **3** | Multimodal fusion + prosody | Trained model, comparison |
| **4** | Cascade architecture | Final model |
| **5** | ONNX export + API | Deployed scoring API |
| **6** | Product demo + landing page | Working product |

---

## 11. Key Decisions Required

1. **Ordinal vs Regression?** → Recommend ordinal (Option C) for interpretability + stable gradients
2. **Text-only vs Multimodal?** → Start with text-only (fastest 0→1), add prosody in week 3
3. **Single-segment vs multi-segment?** → Start single-utterance, aggregate later
4. **Own dataset or leverage existing?** → ChuckleNet's 15K is enough to start; expand via YouTube scraping

---

## Appendix: Vault Memory References

- `laughter.three_products_platform`: three products including Funny Strength Predictor
- `project.laughter.biosemiotic_features`: real vs synthetic features
- `project.laughter.valid_features`: only words/labels/audio are valid, TOM/incongruity/tension are LEAKED
- `chuckle.fusion_breakthrough_20261005`: WavLM+Prosody fusion → F1=0.975
- `project.laughter.acoustic_biosemiotic_theory`: validated acoustic features from literature
