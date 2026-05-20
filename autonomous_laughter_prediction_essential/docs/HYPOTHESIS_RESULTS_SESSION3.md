# Session 3 Results: Expanded Research Tree

**Date:** 2026-05-16  
**Status:** Research complete, implementation pending

---

## Key Findings

### 1. Interaction Model Architecture (thinkingmachines.ai)
- **200ms chunks** - aligns with word timing (~150-250ms per word)
- **Native time-awareness** - captures pause direction (before punchline)
- **No VAD harness** - model learns boundaries natively
- **Concurrent streams** - handle overlapping laughter + speech
- **Early fusion** - all modalities processed jointly

### 2. MultiLinguahah (arxiv:2605.06309)
- **Pipeline:** Audio → Voice Removal → Energy Seg → BYOL-A → Isolation Forest
- **Key insight:** Laughter is UNIVERSAL across languages
- **BYOL-A** self-supervised encoder works cross-lingually
- **F1=0.68** on US English stand-up, **F1=0.80** on Hungarian

### 3. Temporal Position (CONFIRMED)
- Peak at **20-30%** through show (15% laugh rate)
- Min at **90-100%** (10.1%)
- Chi-square **p=4e-143**

### 4. Linguistics Papers
| Paper | Finding |
|-------|---------|
| Pickering 2009 | F0 DROP (not rise!) at punchline |
| Purandare 2006 | Pause 0.8s before punchline (p<0.001) |
| Bachorowski 2001 | Laughter 250-500Hz oscillating |
| Bertero 2016 | F0 range wider at punchlines |
| Gillick 2019 | CNN on spectrograms F1=0.89 |

---

## Hypotheses Formed

### H12: Interaction Model Architecture
- H12.1: 200ms chunks > word-level
- H12.2: Pause trajectory > scalar pause ← **TESTED: F1=0.20 (no improvement)**
- H12.3: No VAD > Whisper VAD
- H12.4: CTC loss for native boundaries

### H13: MultiLinguahah-Inspired
- H13.1: BYOL-A encoder > MFCCs
- H13.2: Isolation Forest for unsupervised detection
- H13.3: Unsupervised label augmentation
- H13.4: Multilingual transfer (en→zh→hi)

### H14: Hybrid Text+Audio
- H14.1: XLM-R + prosody (F1 > 0.87 target)
- H14.2: Early fusion > late fusion
- H14.3: Cross-modal attention

---

## Test Results

### H12.2: Pause Trajectory
- **Result:** F1=0.20 (no improvement over simple pause)
- **Conclusion:** Temporal context alone insufficient, need F0/energy features

### H5: Temporal Position
- **Result:** CONFIRMED (p=4e-143)
- **Finding:** Peak at 20-30% through show

---

## Implementation Priority

1. **F0 + Energy extraction** (H6.1) - Next week
2. **XLM-R + Prosody fusion** (H14.1) - This month
3. **BYOL-A/WavLM encoder** (H13.1) - Short-term
4. **Multilingual transfer** (H13.4) - Future

---

## References

1. Interaction Model - https://thinkingmachines.ai/blog/interaction-models/
2. MultiLinguahah - https://arxiv.org/abs/2605.06309
3. Pickering et al. (2009) - Prosodic markers of humor
4. Purandare & Litman (2006) - Pause before punchline
5. Gillick et al. (2019) - CNN on spectrograms F1=0.89
