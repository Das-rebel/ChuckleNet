# PRD v3.0: Audio-First Laughter Prediction - Paper + API

**Updated:** 2026-05-09  
**See also:** `docs/PRD_V4_10M_PIPELINE.md` for the 10M segment pipeline (Windows GPU + GDrive).  

**Focus:** Audio model training, ACL/EMNLP paper, production API

---

**NOTE: This PRD describes the ORIGINAL 10K target. The pipeline has been redesigned for 10M segments, Windows GPU + GDrive storage. See `docs/PRD_V4_10M_PIPELINE.md` for the updated plan.**

---

## Executive Summary

Build a **multilingual audio-based laughter prediction API** and publish results at ACL/EMNLP 2026.

**Core deliverables:**
1. Trained audio model (Wav2Vec2 + Gillick CNN) with word-level laugh detection
2. Paper submission to ACL/EMNLP 2026
3. Deployed REST API

---

## Current State (Honest)

### What Works
| Component | Location | Status |
|-----------|----------|--------|
| Text data (19,109 train) | `data/merged_final/` | ✅ Verified |
| YouTube scraped (8,637 words) | `data/youtube_scraped/` | ✅ Verified, labels fixed |
| StandUp4AI model (F1=0.744) | `gdrive:standup4ai_models/` | ✅ Trained |
| Audio files (15 videos, 849MB) | Google Drive | ✅ Collected |
| Bengali labels fixed | `hi_bn_records.jsonl` | ✅ 1068→143 |
| PRD + Paper outline | `docs/` | ✅ Updated |

### What Doesn't Work
| Component | Status | Blocker |
|-----------|--------|---------|
| Text baseline training | ❌ 4 failed attempts | Colab path issues |
| Audio timestamps | ❌ Not started | Need Whisper |
| Audio segments | ❌ Not started | Blocked by timestamps |
| Audio model | ❌ Not started | Blocked by segments |
| Multimodal model | ❌ Not started | Blocked by audio |
| API | ❌ Not started | Blocked by models |

### What We Have Too Much Of
| Category | Count | Actually Used |
|----------|-------|---------------|
| Training scripts | 44 Python files | ~5 used |
| Data directories | 15+ | 3 matter (merged_final, youtube_scraped, audio_comedy) |
| Notebooks created | 10+ | 0 ran successfully |
| Doc files | 28 MD files | Most outdated |

---

## Dataset Inventory (What Actually Matters)

### Text Data
| Dataset | Path | Train | Valid | Test | Languages | Use |
|---------|------|-------|-------|------|-----------|-----|
| **merged_final** | `data/merged_final/` | 19,109 | 2,989 | 1,790 | en,zh,hi-latn,bn,fr,es,hi | **PRIMARY** |
| youtube_scraped | `data/youtube_scraped/` | 8,637 | - | - | hi-latn,bn | Audio alignment |
| v8_1_final | `data/v8_1_final/` | 9,638 | 1,805 | 605 | en,zh,hi-latn | Legacy |
| combined | `data/combined/` | 12,200 | 2,125 | 926 | en,zh,hi-latn,fr,es | Legacy |

### Audio Data
| Language | Files | Duration | Location |
|----------|-------|----------|----------|
| EN | 3 (mulaney, chappelle, wong) | 1.5 hrs | `gdrive:audio_en/` |
| ZH | 2 (hehuang, jimmyoyang) | 1.6 hrs | `gdrive:audio_zh/` |
| HI | 4 (zakir khan specials) | 3.5 hrs | `gdrive:multimodal_audio/hindi/` |
| BN | 4 (anirban, shiladitya, rohit) | 2.0 hrs | `gdrive:multimodal_audio/bengali/` |
| FR | 1 (herve kimenyi) | 9 min | `gdrive:audio_fr_es/` |
| ES | 1 (franco escamilla) | 11 min | `gdrive:audio_fr_es/` |
| **Total** | **15** | **8.7 hrs** | |

### Pre-trained Models Available
| Model | Source | Use |
|-------|--------|-----|
| StandUp4AI best.pt (1GB) | Earlier training | Text baseline F1=0.744 |
| Gillick's CNN checkpoint | jrgillick/laughter-detection | Audio laugh detection backbone |
| Wav2Vec2-base | facebook/wav2vec2-base | Audio encoder |

---

## Architecture (Final)

```
INPUT: Audio OR Text OR Both
        ↓
┌───────────────────────────────────────┐
│         LAUGHTER PREDICTION API        │
├───────────────────────────────────────┤
│                                        │
│  Text: words → XLM-R → 768 → 256     │
│  Audio: wav → Wav2Vec2/Gillick → 256  │
│  Fusion: CrossAttention → classifier  │
│                                        │
├───────────────────────────────────────┤
│  POST /predict-text                    │
│  POST /predict-audio                   │
│  POST /predict-multimodal              │
└───────────────────────────────────────┘
```

---

## Biosemotic Feature Integration (CRITICAL ENHANCEMENT)

### Analysis Results

We have 13 biosemotic features already present in merged_final data that are completely ignored by current training. Analysis of 19,109 training examples shows:

**Highly Discriminative Numeric Features (delta > 0.10):**

| Feature | Laugh Mean | No-Laugh Mean | Delta | Direction |
|---------|-----------|---------------|-------|-----------|
| tom_character_interaction_score | 0.831 | 0.580 | +0.252 | Higher = more laugh |
| incongruity_expectation_violation | 0.229 | 0.428 | -0.199 | Lower = more laugh |
| incongruity_humor_complexity | 0.250 | 0.436 | -0.186 | Lower = more laugh |
| duchenne_setup_punchline_structure | 0.728 | 0.556 | +0.173 | Higher = more laugh |
| tom_speaker_intent_confidence | 0.723 | 0.553 | +0.170 | Higher = more laugh |
| duchenne_spontaneous_laughter_markers | 0.066 | 0.213 | -0.148 | Lower = more laugh |
| incongruity_resolution_time | 0.337 | 0.451 | -0.114 | Lower = more laugh |
| tom_audience_perspective_score | 0.351 | 0.462 | -0.110 | Lower = more laugh |
| duchenne_joy_intensity | 0.182 | 0.286 | -0.105 | Lower = more laugh |

**Categorical Features:**

Speaker Intent → Laugh Rate:
- playful_banter: 93.7% (697/744)
- humor_expression: 79.7% (2671/3352)
- comic_observation: 100% (13/13)
- joke_delivery: 100% (8/8)
- setup: 52.5% (1190/2267)
- other: 53.5% (729/1362)
- informative: 6.5% (616/9471)

Interaction Pattern → Laugh Rate:
- call_and_response: 100% (8/8)
- reported_dialogue: 100% (8/8)
- monologue: 68.5% (5273/7701)
- dialogue_exchange: 70.6% (24/34)
- dialogue: 2.7% (184/6909)

### Enhanced Architecture

```
CURRENT (ignoring biosemotic):
  words → XLM-R (768-dim) → classifier → F1 ~0.75

ENHANCED (using biosemotic):
  words → XLM-R (768-dim) ─┐
  11 numeric features → FC (32-dim) ─┤→ concat (800) → classifier → F1 ~0.80+
  2 categorical → embed (16-dim) ────┘
```

### Implementation

```python
class EnhancedXLMR(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Text branch
        self.xlmr = AutoModel.from_pretrained('xlm-roberta-base')
        
        # Biosemotic branch (11 numeric + 2 categorical)
        self.bio_numeric = torch.nn.Sequential(
            torch.nn.Linear(11, 32),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.1)
        )
        self.intent_embed = torch.nn.Embedding(10, 8)  # 10 intent types
        self.pattern_embed = torch.nn.Embedding(8, 8)   # 8 pattern types
        
        # Classifier
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(768 + 32 + 8 + 8, 256),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(256, 2)
        )
    
    def forward(self, input_ids, attention_mask, bio_numeric, intent_id, pattern_id):
        # Text encoding
        text_out = self.xlmr(input_ids=input_ids, attention_mask=attention_mask)
        text_emb = text_out.last_hidden_state[:, 0]  # [CLS] token, 768-dim
        
        # Biosemotic encoding
        bio_emb = self.bio_numeric(bio_numeric)  # 32-dim
        intent_emb = self.intent_embed(intent_id)  # 8-dim
        pattern_emb = self.pattern_embed(pattern_id)  # 8-dim
        
        # Concatenate all features
        combined = torch.cat([text_emb, bio_emb, intent_emb, pattern_emb], dim=1)
        return self.classifier(combined)
```

### Expected Impact

From the existing ablation study (V8.1 paper draft):
- Removing all cognitive features: -0.008 F1
- But that was on 12K examples. With 19K examples, signal should be stronger.
- Top features (tom_character_interaction +0.25 delta) alone should add +0.02-0.05 F1
- Combined effect: estimated **F1 improvement of +0.03 to +0.05**

### Updated Task List

Add before Phase 1 training:
- **0.1**: Extract biosemotic features from merged_final into training tensors
- **0.2**: Build enhanced model with biosemotic branch
- **0.3**: Train and compare: vanilla XLM-R vs enhanced XLM-R

---

## Task List (Execution Order)

### Phase 1: Get Text Baseline Working (Day 1)

| Task | What | Where | Est. Time |
|------|------|-------|-----------|
| **1.1** | Train XLM-R on merged_final (19K) | **LOCAL** (Mac CPU) | 2-4 hrs |
| **1.2** | Evaluate per-language F1 | Local | 5 min |
| **1.3** | Save model + results | Local → GDrive | 5 min |

**Why LOCAL:** Eliminates all Colab/Drive path issues. Mac has PyTorch installed.

### Phase 2: Audio Pipeline (Day 2-3)

| Task | What | Where | Est. Time |
|------|------|-------|-----------|
| **2.1** | Run Whisper large-v2 on all 15 videos | Colab (GPU) | 2-3 hrs |
| **2.2** | Extract word-level audio segments | Colab | 1 hr |
| **2.3** | Align text laugh labels to audio segments | Colab | 30 min |
| **2.4** | Verify 10K+ aligned segments | Colab | 15 min |

### Phase 3: Audio Model (Day 3-4)

| Task | What | Where | Est. Time |
|------|------|-------|-----------|
| **3.1** | Download Gillick's pretrained model | Colab | 10 min |
| **3.2** | Fine-tune on our 10K segments | Colab (GPU) | 1-2 hrs |
| **3.3** | Evaluate audio-only F1 | Colab | 10 min |

### Phase 4: Multimodal (Day 4-5)

| Task | What | Where | Est. Time |
|------|------|-------|-----------|
| **4.1** | Combine text encoder + audio encoder | Colab | 30 min |
| **4.2** | Train cross-attention fusion | Colab (GPU) | 1-2 hrs |
| **4.3** | Evaluate multimodal F1 | Colab | 10 min |

### Phase 5: Scale + Polish (Day 5-7)

| Task | What | Where | Est. Time |
|------|------|-------|-----------|
| **5.1** | If segments < 10K, download more videos | Local/Colab | 2-4 hrs |
| **5.2** | Retrain with scaled data | Colab | 1-2 hrs |
| **5.3** | Add pause/timing features | Colab | 1 hr |

### Phase 6: Paper (Day 7-10)

| Task | What | Est. Time |
|------|------|-----------|
| **6.1** | Write abstract + intro | 2 hrs |
| **6.2** | Write methodology | 2 hrs |
| **6.3** | Create results tables + figures | 2 hrs |
| **6.4** | Write experiments section | 3 hrs |
| **6.5** | Write conclusion + related work | 2 hrs |
| **6.6** | Internal review + revision | 3 hrs |

### Phase 7: API (Day 10-12)

| Task | What | Est. Time |
|------|------|-----------|
| **7.1** | Build FastAPI wrapper | 2 hrs |
| **7.2** | Deploy to Modal.com | 2 hrs |
| **7.3** | Test endpoints | 1 hr |
| **7.4** | Documentation | 1 hr |

---

## Target Metrics

| Model | F1 Target | Current |
|-------|-----------|---------|
| Text-only (XLM-R) | ≥ 0.75 | 0.744 (close) |
| Audio-only (Gillick/Wav2Vec2) | ≥ 0.65 | N/A |
| Multimodal (Fusion) | ≥ 0.78 | N/A |
| API latency | < 100ms | N/A |

---

## Paper Claims (Honest)

**We claim:**
- Multilingual word-level laughter prediction (6 languages)
- Audio-enhanced detection using pretrained CNN + Wav2Vec2
- 10K+ aligned audio segments with laugh labels
- Deployed API with < 100ms latency
- Cross-attention multimodal fusion architecture

**We do NOT claim:**
- 100+ languages (only 6)
- SOTA on all benchmarks
- Production-scale deployment (prototype only)

---

## File Cleanup Needed

### Keep (active files)
```
data/merged_final/          # Primary text data
data/youtube_scraped/       # Audio-aligned text
data/audio_comedy/          # Audio + transcripts
docs/SOTA_PRD*.md           # This PRD
docs/PAPER_OUTLINE*.md      # Paper draft
training/audio_*.py         # Audio scripts
training/xlmr_standup*.py   # Text training
```

### Archive (outdated/superseded)
```
data/enhanced_comedy_*      # Corrupted (0 lines)
data/integrated_comedy_*    # Empty
data/reddit_hindi_jokes/    # Empty
data/synthetic_hindi/       # Superseded by merged_final
data/expanded_10k/          # Superseded by merged_final
data/combined_multilingual/ # Superseded by merged_final
training/generate_hindi_*.py # 8 variants, all superseded
```

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Local training too slow (no GPU) | Medium | Delays Phase 1 | Use Colab with fixed notebook |
| Whisper poor on Hindi/Bengali | Medium | Bad timestamps | Use faster-whisper with VAD |
| < 10K segments extracted | Low | Less training data | Download more videos |
| Audio model F1 < 0.65 | Medium | Weak paper claim | Use Gillick pretrained backbone |
| Paper rejected | Medium | No publication | Submit to workshop first |

---

**END OF PRD v3.0**

*Focused on execution: audio model → paper → API*
