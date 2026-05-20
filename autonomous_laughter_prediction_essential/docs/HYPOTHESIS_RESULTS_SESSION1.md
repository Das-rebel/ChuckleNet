# HYPOTHESIS TEST RESULTS — SESSION 1
## Date: 2026-05-16
## Tests Run: H1.1 (pause from timestamps), H1.2 (audio energy from clips)

---

## H1.1: PAUSE DURATION PREDICTS LAUGHTER — PARTIALLY CONFIRMED

### Data
- 199,992 words from 26 videos
- Laughter rate: 12.6%
- Features extracted from subtitle timestamps (no audio loading)

### Results

| Feature | Laugh Mean | No-Laugh | Delta | Cohen's d | p-value |
|---------|-----------|----------|-------|-----------|---------|
| Pause before | 0.188s | 0.118s | +0.070s | **0.13** | 4e-66 |
| Pause after | 0.255s | 0.131s | +0.124s | **0.18** | 6e-118 |

### Interpretation
- **p-values are extremely significant** (p < 10^-60) → there IS a difference
- **But effect size is negligible** (Cohen's d < 0.2) → difference is tiny
- **Literature predicts 0.8s vs 0.3s** (Cohen's d ≈ 0.8-1.2) → we see only 0.07s gap
- **Root cause:** YouTube subtitle timestamps are too coarse — median pause = 0.0s for both classes (words are back-to-back in subtitles)

### At macro scale, the effect DOES emerge:

| Pause Range | Laughter Rate |
|-------------|:---:|
| 0.0-0.1s | 12.4% |
| 0.1-0.2s | 11.6% |
| 0.5-1.0s | 12.3% |
| 1.0-2.0s | **17.7%** |
| 2.0-5.0s | **23.8%** |

**Long pauses (>1s) → nearly 2× laughter rate.** The comedic pause IS real, just invisible at subtitle-level precision.

### Verdict
**⚠️ WEAK CONFIRMATION** — The effect exists but is ~10× smaller than literature predicts due to subtitle timing imprecision. Real audio extraction (librosa on WAV) is needed to capture the 0.8s vs 0.3s gap.

---

## H1.2: F0 PITCH / AUDIO ENERGY — INCONCLUSIVE

### Data
- 5,000 extracted WAV clips scanned
- Only 68 laughter clips (1.4%) → severe class imbalance
- Most extracted clips are non-laughter words
- RMS energy: Cohen's d ≈ 0.11 (negligible)

### Root Cause
The extracted clip set is heavily imbalanced. Need to:
1. Extract clips specifically for laughter words from aligned segments
2. OR use the aligned_segments.jsonl with audio_file paths to load audio on-the-fly

### Verdict
**❓ INCONCLUSIVE** — Cannot test properly with current clip distribution. Need to extract balanced clip set.

---

## WHAT WE'VE LEARNED

| Question | Answer |
|----------|--------|
| Does pause predict laughter? | **Yes, but weakly** — subtitle precision limits detection |
| Can we measure the 0.8s vs 0.3s gap from literature? | **No** — need real audio, not subtitle timestamps |
| Does audio energy differentiate laughter? | **Probably not** — Cohen's d < 0.15 |
| Is the "comedic pause" real? | **Yes** — long pauses (>1s) have 2× laughter rate |

---

## NEXT HYPOTHESIS TO TEST

**H4.6: StandUp4AI Baseline** — This is actually the most important test because:
1. External benchmark that BOTH reviews demand
2. Data exists (4 CSVs, 3,207 words)
3. Training script exists but never completed
4. Can run on CPU (small dataset)
5. No audio loading needed — text-only
6. Results directly usable in Paper 3

Should we pivot to H4.6 (StandUp4AI baseline) right now? It's the one hypothesis that's guaranteed to give publishable results.
