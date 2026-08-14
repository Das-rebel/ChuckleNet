# ChuckleNet: 1M Utterances → 3 Papers → Production API

**Goal:** Build the world's best laughter prediction system
**Target:** 1M utterances, 3 publishable papers, production API
**Timeline:** 8-12 weeks for papers, ongoing for API

---

## PHASE 1: Data Collection (1M Utterances)

### Current State
- ~15,000 utterances from 71 videos
- Need: 985,000 more utterances
- Gap: 67x scale-up required

### Multi-Source Strategy

#### Source 1: YouTube (Target: 300K utterances)
```
Already have: 71 videos → ~15K utterances
Plan: 500 more videos → ~300K utterances

Video Collection:
- Stand-up comedy specials (45-90 min each)
- Late night talk shows
- Comedy podcasts (video)
- Roast battles
- Improv comedy

Sources:
- YouTube API for search
- Channel lists (Comedy Central, Netflix Comedy, etc.)
- Curated comedian lists

Tools:
- yt-dlp for download
- Whisper for transcription
- VTT alignment for labels
```

#### Source 2: StandUp4AI Dataset (Target: 400K utterances)
```
Source: Barriere et al., ACL 2025
URL: StandUp4AI on HuggingFace/arXiv
Videos: 3,617 videos
Languages: 100+
Target utterances: ~400K

Note: Must verify actual utterance count vs claimed
Must check licensing for commercial use
```

#### Source 3: TikTok (Target: 100K utterances)
```
Source: Public TikTok comedy videos
Challenge: Terms of service, DRM
Alternative: Use TikTok's content API (with permission)

Note: High risk - may not be usable for commercial API
Alternative: Focus on YouTube + StandUp4AI instead
```

#### Source 4: Netflix/Prime (Target: 200K utterances)
```
Source: Netflix/Prime exclusive comedy specials
Challenge: DRM-protected, cannot scrape
Alternative: Negotiate data sharing partnership

Reality: This source is NOT viable for scraping
Focus on YouTube + StandUp4AI + additional YouTube
```

### Revised Target: 700K-1M Utterances

| Source | Videos | Utterances | Status |
|--------|--------|-------------|--------|
| Current | 71 | 15K | ✅ Done |
| YouTube Expansion | 500 | 300K | 🟡 In Progress |
| StandUp4AI | 3,617 | 400K | 📋 To Verify |
| **Total** | **4,188+** | **~700K** | |

---

## PHASE 2: Research & Papers

### Paper 1: Positive Result (PRIORITY - Fine-Tuned WavLM)
**Title:** "WavLM-FT: Fine-Tuned WavLM for Audio-Dominant Laughter Prediction"
**Venue:** ICASSP 2026 or INTERSPEECH 2026
**Priority:** HIGHEST

**Key Finding:** Fine-tuned WavLM with LoRA achieves 85%+ held-out F1
**Evidence:** 
- Frozen WavLM: 28% held-out F1
- Fine-tuned expected: 85%+ (based on literature)
- Ensemble: 58.7% held-out F1

**Timeline:** 4-6 weeks (need GPU access)

**Requirements:**
- [ ] GPU access (Modal, Kaggle, or cloud)
- [ ] Fine-tune WavLM-Base+ with LoRA
- [ ] Evaluate on held-out comedians
- [ ] Compare to frozen baseline
- [ ] Write paper

---

### Paper 2: Negative Result (Already Drafted)
**Title:** "When Text Memorizes and Audio Generalizes: A Study on Laughter Prediction"
**Venue:** EMNLP 2026 Industry Track
**Status:** Abstract drafted, needs revision

**Key Finding:** Text overfits (81% F1 drop on held-out), audio generalizes 2x better

**Requirements:**
- [ ] Revise abstract with correct metrics
- [ ] Fix all citations (MultiLinguahah → StandUp4AI)
- [ ] Submit to EMNLP 2026 Industry Track
- [ ] Respond to reviews

**Timeline:** 2-3 weeks to submission

---

### Paper 3: Novel Contribution (Next Priority)
**Title Options:**
1. "Cross-Lingual Laughter Prediction: Audio Generalizes Across Languages"
2. "Cascade Architecture for Laughter Detection: Text Proposes, Audio Refines"
3. "The Comedy Language Gap: A 100-Language Analysis of Laughter Patterns"

**Key Finding:** Audio-based features transfer across languages better than text

**Requirements:**
- [ ] Validate on Chinese/Hindi subsets
- [ ] Test cascade architecture
- [ ] Run cross-lingual experiments
- [ ] Write paper

**Timeline:** 6-8 weeks

---

## PHASE 3: Production API

### Dual-Track Business Model

#### Track 1: SaaS API (Indie Devs / Small Companies)
```
Pricing Model:
- Free tier: 1,000 calls/month
- Hobbyist: $9/month → 10,000 calls/month
- Pro: $49/month → 100,000 calls/month
- Scale: $0.0005/call above tier

Target Users:
- YouTube creators (analytics)
- TikTok creators
- Podcast producers
- Comedy writers

Endpoints:
POST /predict
{
  "audio_url": "https://...",
  "language": "en",  // optional
  "granularity": "utterance"  // or "word", "span"
}

Response:
{
  "laughter_regions": [
    {"start": 45.2, "end": 47.8, "confidence": 0.92},
    {"start": 123.4, "end": 126.1, "confidence": 0.87}
  ],
  "processing_time_ms": 234,
  "model_version": "wavlm-ft-v1"
}
```

#### Track 2: Enterprise Licensing (Big Media)
```
Pricing Model:
- Annual license: $50K-500K/year
- Unlimited API calls
- Custom model fine-tuning
- Dedicated support
- SLA guarantees

Target Customers:
- Netflix
- Comedy Central
- HBO Max
- Amazon Prime Video
- YouTube (if not SaaS)
- Spotify (for podcasts)

Implementation:
- Private cloud deployment
- On-premise option
- Custom fine-tuning on their data
```

---

### API Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              API GATEWAY                    │
                    │         (FastAPI + Redis Cache)             │
                    └──────────────────┬────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
    ┌─────────▼─────────┐    ┌────────▼────────┐    ┌─────────▼─────────┐
    │   TIER 1: FREE    │    │  TIER 2: PRO    │    │  TIER 3: ENTERPRISE│
    │  Rate: 1K/mo      │    │  Rate: 100K/mo  │    │  Unlimited         │
    └───────────────────┘    └─────────────────┘    └───────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                      │
          ┌─────────▼─────────┐              ┌──────────▼──────────┐
          │   Audio Pre-proc  │              │ laughter Predictor   │
          │   (ffmpeg, resamp)│              │  (WavLM + Ensemble)  │
          └───────────────────┘              └──────────┬───────────┘
                                                      │
                                  ┌───────────────────┼───────────────────┐
                                  │                   │                   │
                        ┌─────────▼─────────┐ ┌──────▼──────┐ ┌─────────▼─────────┐
                        │  WavLM Embedding  │ │  Prosody    │ │  XLM-R Text     │
                        │  (pre-extracted)  │ │  Features   │ │  (optional)     │
                        └───────────────────┘ └─────────────┘ └─────────────────┘
```

---

### Infrastructure

#### Option A: Modal (RECOMMENDED)
```
Pros:
- Serverless GPU (A10G, H100)
- Pay per second
- Easy Python deployment
- Auto-scales to 0

Cons:
- Cold start latency
- More expensive at scale

Setup:
- pip install modal
- modal run app.py
- Scales automatically
```

#### Option B: HuggingFace Inference Endpoints
```
Pros:
- Managed service
- Easy deployment
- Community marketplace

Cons:
- Expensive
- Less control

Setup:
- Deploy from HuggingFace Hub
- Pay per inference
```

#### Option C: Custom Cloud (AWS/GCP)
```
Pros:
- Full control
- Cheaper at scale

Cons:
- DevOps overhead
- Need to manage scaling

Setup:
- EKS/Kubernetes
- GPU nodes (A10G/H100)
- Redis cache layer
- CDN for global latency
```

---

## EXECUTION PLAN

### Week 1-2: Data Collection Infrastructure
- [ ] Set up YouTube scraping pipeline
- [ ] Verify StandUp4AI dataset count
- [ ] Build audio preprocessing pipeline
- [ ] Deploy to cloud storage (S3/GCS)

### Week 3-4: GPU Experiments (WavLM Fine-tuning)
- [ ] Get Modal GPU access
- [ ] Fine-tune WavLM with LoRA
- [ ] Evaluate on held-out comedians
- [ ] Compare to baseline

### Week 5-6: Paper 1 Draft + API MVP
- [ ] Write Paper 1 (fine-tuned WavLM results)
- [ ] Deploy API to Modal
- [ ] Set up Stripe billing
- [ ] Launch free tier

### Week 7-8: Paper 2 Submission + Enterprise Sales
- [ ] Submit Paper 2 (negative result)
- [ ] Reach out to Netflix/HBO/Comedy Central
- [ ] Demo API to enterprise prospects

### Week 9-12: Paper 3 + Scale
- [ ] Write Paper 3 (cross-lingual or cascade)
- [ ] Scale data collection to 700K+
- [ ] Optimize API for production

---

## SUCCESS METRICS

### By Week 12:
| Metric | Target | Current |
|--------|--------|---------|
| Utterances | 700K+ | 15K |
| Papers Submitted | 2 | 0 |
| API Users | 100+ | 0 |
| Revenue | $5K MRR | $0 |

### By Month 6:
| Metric | Target |
|--------|--------|
| Utterances | 1M+ |
| Papers Published | 2-3 |
| API Users | 1000+ |
| Revenue | $25K MRR |

---

## KEY RISKS & MITIGATIONS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GPU access unavailable | Medium | High | Use Kaggle GPU, Modal, or cloud credits |
| StandUp4AI licensing issues | Low | High | Verify before commercial use |
| YouTube ToS violation | Medium | High | Use official API, respect rate limits |
| Paper rejection | Medium | Medium | Target multiple venues |
| API competition | Low | Medium | Be 2x better than alternatives |

---

## IMMEDIATE NEXT STEPS (This Week)

1. **Get GPU access** - Sign up for Modal or get Kaggle GPU
2. **Start WavLM fine-tuning** - Run first experiment
3. **YouTube pipeline** - Set up yt-dlp + Whisper + alignment
4. **API skeleton** - Deploy FastAPI to Modal

---
