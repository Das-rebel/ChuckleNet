# GPU Options for ML Training — Best Value (2024-2025)

**Researched from:** r/MachineLearning discussions, pricing analyses  
**Date:** 2026-05-14  
**For:** Training WavLM audio model (~12-36 hrs GPU time needed)

---

## TL;DR RECOMMENDATION

| Use Case | Best Option | Cost | Why |
|----------|------------|------|-----|
| **Free, small scale** | Kaggle (free T4) | $0 | 9hrs/week, no setup |
| **Best value paid** | Vast.ai A100 40GB | ~$0.40-0.70/hr | Market model = cheaper |
| **Easiest setup** | Colab Pro ($10/mo) | $10/mo + usage | T4/P100, ready to go |
| **RTX 4090 local** | Buy used (~$500-800) | ~$0.15/hr amortized | Best perf/$, own forever |
| **If you have RTX 4090** | Use it! | $0 | Already superior to T4 |

---

## FREE OPTIONS (No Cost)

### 1. Kaggle Notebooks — T4 16GB (FREE)
| Feature | Detail |
|---------|--------|
| GPU | Tesla T4 16GB |
| Hours | 9 hours/week GPU time |
| Storage | 20GB output, 20GB dataset |
| Strength | No setup, good for prototyping |
| Weakness | 9hr/week limit, sessions can die |
| Best for | Testing scripts, small training runs |

**How:** kaggle.com → New Notebook → Runtime → GPU T4

### 2. Google Colab (FREE Tier)
| Feature | Detail |
|---------|--------|
| GPU | T4 16GB (sometimes P100) |
| Hours | Unclear, often limited |
| Strength | Familiar, easy |
| Weakness | "Increasingly unreliable" per Reddit |
| Best for | Quick experiments only |

**Reddit verdict:** "Colab free tier is barely worth it anymore" (multiple 2024 posts)

### 3. Gradient Community Notebooks (Paperspace)
| Feature | Detail |
|---------|--------|
| GPU | Free GPU (models vary) |
| Hours | Unlimited |
| Strength | Free, persistent notebooks |
| Weakness | Not well known |
| URL | paperspace.com/gradient/free-gpu |

---

## PAID OPTIONS (~$0.10-2.50/hr)

### 4. Colab Pro — $10/month
| Feature | Detail |
|---------|--------|
| GPU | T4 or P100 16GB |
| Cost | $10/mo + per-minute after included |
| Included | ~12-15 hrs/month GPU |
| Strength | Easiest setup, familiar UI |
| Weakness | Expensive for heavy use, runtime limits |
| Best for | Casual use, prototyping |

**Note:** Pro no longer gives V100 — only T4/P100 (per Reddit complaints)

### 5. Vast.ai — Best Bang for Buck
| GPU | Memory | On-Demand | Spot/Interruptible |
|-----|--------|-----------|-------------------|
| A100 40GB | 40GB | ~$0.73-1.00/hr | ~$0.40-0.60/hr |
| A100 80GB | 80GB | ~$1.00-1.61/hr | ~$0.60-1.00/hr |
| H100 | 80GB | ~$2.00+/hr | ~$1.20+/hr |
| RTX 4090 | 24GB | ~$0.20-0.35/hr | ~$0.15-0.25/hr |

| Feature | Detail |
|---------|--------|
| Model | Marketplace (bid/ask) |
| Strength | Cheapest for A100/H100 |
| Weakness | UI less polished, spot = can be interrupted |
| Best for | Serious training, cost-sensitive |
| Setup | SSH or Jupyter, bring own image |

**Tip:** Use "interruptible" instances for 30-50% savings. WavLM training with checkpointing = safe.

### 6. RunPod
| GPU | Memory | On-Demand | Spot |
|-----|--------|-----------|------|
| A100 80GB | 80GB | $1.69-1.99/hr | $0.69-0.99/hr |
| H100 80GB | 80GB | $2.49/hr | ~$1.50/hr |

| Feature | Detail |
|---------|--------|
| Strength | Easy UI, persistent disks |
| Weakness | More expensive than Vast.ai |
| Best for | Stable production workloads |

### 7. Lambda Labs
| GPU | Memory | Price |
|-----|--------|-------|
| A100 80GB | 80GB | $1.29/hr |
| V100 32GB | 32GB | ~$0.90/hr |

| Feature | Detail |
|---------|--------|
| Strength | Pre-configured PyTorch/TensorFlow |
| Weakness | More expensive than Vast.ai |
| Best for | Quick start, less config |

### 8. sfcompute (mentioned on Reddit as "goated prices")
| GPU | Memory | Price (est) |
|-----|--------|-------------|
| H100 | 80GB | ~$1.50-2.00/hr |
| A100 | 80GB | ~$0.80-1.00/hr |

| Feature | Detail |
|---------|--------|
| Strength | Cheapest H100 option noted |
| Weakness | Less known, newer |
| URL | sfcompute.com |

---

## FOR YOUR USE CASE (WavLM Training)

### WavLM Training Requirements
- **Model:** WavLM-Base+ (94M params)
- **GPU RAM:** 2-4GB for small batches, 8GB+ for large
- **Time:** Phase A (30min), Phase B (2hrs), Phase C (4-12hrs on 733K+ segments)

### Recommended Path

| Phase | Data | GPU Need | Best Option |
|-------|------|----------|-------------|
| Test/Proto | 10K samples | T4 ok | **Kaggle free** |
| Phase A | 50K samples | T4 fine | **Colab Pro ($10)** |
| Phase B | 200K samples | T4/A100 | **Vast.ai RTX 4090** (~$0.20/hr) |
| Phase C | 733K+ segments | A100 40GB+ | **Vast.ai A100 spot** (~$0.50/hr) |
| Full 10M | 10M segments | A100 80GB | **Vast.ai A100 80GB spot** (~$0.75/hr) |

### Cost Estimates

| Task | GPU | Hours | Vast.ai Cost | Colab Pro Cost |
|------|-----|-------|--------------|-----------------|
| Phase A (50K) | T4 | 1 | ~$0.10 | $1-2 |
| Phase B (200K) | RTX 4090 | 4 | ~$0.80 | N/A |
| Phase C (733K) | A100 40GB | 12 | ~$6-8 | N/A |
| Full (10M) | A100 80GB | 36 | ~$25-30 | N/A |

**Total for full training:** ~$35-40 on Vast.ai vs ~$200+ on Lambda/RunPod

---

## COMPARISON MATRIX

| Provider | Cheapest GPU | $/hr | Free Tier | Best For |
|----------|-------------|------|-----------|----------|
| **Kaggle** | T4 16GB | $0 | ✅ 9hr/wk | Prototyping |
| **Colab** | T4 16GB | $0 | ✅ Limited | Quick tests |
| **Gradient** | Varies | $0 | ✅ Unlimited | Free persistent |
| **Vast.ai** | RTX 4090 | $0.15 | ❌ | Cost-conscious pros |
| **Colab Pro** | T4/P100 | $0.07 | $10/mo | Easy prototyping |
| **Lambda** | A100 80GB | $1.29 | ❌ | Quick start |
| **RunPod** | A100 80GB | $0.69 | ❌ | Stable prod |
| **sfcompute** | H100 | ~$1.50 | ❌ | Cheapest H100 |

---

## REDDIT COMMUNITY VERDICT

From r/MachineLearning discussions (2024-2025):

1. **"Vast.ai for cost optimization, Lambda for ease of use"** — common sentiment
2. **"Colab Pro isn't worth it anymore"** — multiple complaints about GPU access quality
3. **"RunPod H100 = $2.49/hr"** — more expensive but reliable
4. **"Spot instances 30-70% cheaper"** — use checkpointing to handle interruptions
5. **"For 10M segments, get an A100 80GB on Vast.ai spot"** — best value for large training
6. **"sfcompute has goated prices for H100"** — newer, good rates

---

## ACTION ITEMS

### If you want FREE:
1. Go to kaggle.com → Notebooks → New → GPU T4
2. Run: `python training/train_wavlm_audio_v2.py --phase A --max-samples 10000 --epochs 3`

### If you want BEST VALUE:
1. Sign up at vast.ai
2. Rent RTX 4090 (~$0.20/hr) or A100 40GB (~$0.50/hr) spot
3. SSH in, `pip install transformers librosa faster-whisper`
4. Run: `python training/train_wavlm_audio_v2.py --phase C --max-samples 500000 --epochs 5`

### If you have RTX 4090 locally:
1. **Use it.** RTX 4090 24GB > A100 40GB for your workload.
2. ~4 hours to train on 733K segments, ~$0.15-0.20 electricity

---

## PRICING SOURCES

- Vast.ai marketplace (live pricing)
- Lambda Labs (lambdalabs.com/service/gpu-cloud)
- RunPod (runpod.io)
- Reddit r/MachineLearning "Cloud GPU Price Analysis - December 2024"
- Community mentions: sfcompute.com, Tensordock, Neysa, Shadeform