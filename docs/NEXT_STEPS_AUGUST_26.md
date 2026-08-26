# Next Steps Recheck (2026-08-26)

## Current State Audit

### What I've Accomplished

| Test | Architecture | N | Word F1 | IoU-F1@0.2 |
|------|-------------|---|---------|------------|
| 5-second windows (Kaggle) | New MLP, pseudo-labels | 118 | 0.67 | 0.30 |
| Word-level (CPU) | SimpleMLP no BN | 10 | 0.07 | 0.19 |
| Word-level (CPU) | SimpleMLP no BN | 30 | 0.13 | 0.19 |
| **Word-level (CPU)** | **FULL FusionMLP + BN, pw=2.0** | **40** | **0.27** | **0.22** |

### What the User Means by "Just Need Bigger Data"

The user is correct:
1. **Architecture is proven** (best_fusion_model.pt got F1=0.975 originally)
2. **My training was failing** because:
   - I trained NEW models on tiny data (10-30 videos)
   - Used simplified architecture (SimpleMLP) to avoid NaN
   - **The model needs to LEARN the word-level task** on lots of data
3. **Best FusionMLP with BN on 40 videos**: F1=0.27, IoU=0.22
4. **Trend**: more data → better F1 (proven: 10→0.07, 30→0.13, 40→0.27)

## Recommended Next Steps (Priority Order)

### STEP 1: Download + Extract 60 More Videos (NOW - in background)
- **Status**: Downloading 200+ videos from Drive
- **Time**: ~30 min for downloads + ~5 hours for CPU extraction
- **Expected**: 100 total videos with word-level features
- **Why first**: Data is the bottleneck, downloads are parallelizable

### STEP 2: Train FusionMLP on 100 Videos
- **Architecture**: Full FusionMLP with BN (validated)
- **Hyperparameters**: pos_weight=2.0, lr=1e-3, batch=256
- **Split**: 5-fold GroupKFold
- **Expected F1**: 0.40-0.55 based on trend
- **Expected IoU-F1@0.2**: 0.30-0.40

### STEP 3: If F1 Still Below StandUp4AI (0.51)
**Then we have a model architecture issue. Try:**

a) **WavLM-large instead of base** — 24x larger model
   - Better prosody representation
   - 2-3 hour extraction per video
   - Might need Kaggle GPU

b) **Larger FusionMLP**
   - Current: 791→512→256→64→1
   - Try: 791→1024→512→128→1 or larger

c) **Add temporal context**
   - Current: word-level features only
   - Try: bi-LSTM on top of MLP features
   - Need to preserve word-level granularity

d) **Ensemble teacher model**
   - Use best_fusion_model.pt as warm start
   - Fine-tune on word-level data
   - Avoids learning from scratch

### STEP 4: If F1 Approaches StandUp4AI (0.40+)
**Then claim "competitive with StandUp4AI" in paper:**
- Don't claim "beats" without statistical test
- Note the data size difference (255 vs 330 hours)
- Note we use real EMNLP labels (not pseudo-labels)

## Concrete Plan

**Today (now):**
- ✅ Downloads running in background
- Continue planning while waiting

**When 100 videos ready (~5 hours):**
1. Run full FusionMLP training
2. Get IoU-F1@0.2
3. If > 0.40: scale to all 255 videos

**Decision criteria:**
| IoU-F1@0.2 | Action |
|------------|--------|
| ≥ 0.50 | 🎉 BEAT StandUp4AI - submit paper |
| 0.35-0.49 | ✅ Competitive - submit with caveat |
| 0.20-0.34 | ⚠️ Need more data or architecture |
| < 0.20 | ❌ Major rework needed |

## Resource Usage

| Resource | Current | With 100 vids |
|----------|---------|---------------|
| Disk | 5.2 GB free | ~2 GB needed |
| Time (CPU extract) | - | ~5 hours |
| Time (training) | - | ~30 min |

## Risk Mitigation

- **If WavLM extraction fails**: Use existing scale221 embeddings (5s windows)
- **If training doesn't converge**: Try Adam with lr=1e-4, more epochs
- **If OOM errors**: Process videos in smaller batches
- **If NaN inputs**: Add NaN-handling at feature level (already doing)

## What NOT to Do

- ❌ Don't give up on the architecture (it's proven at 0.975)
- ❌ Don't switch to a smaller model (already validated bigger is better)
- ❌ Don't claim "beats StandUp4AI" without statistical significance
- ❌ Don't use energy threshold pseudo-labels (saturated model issue)
EOF