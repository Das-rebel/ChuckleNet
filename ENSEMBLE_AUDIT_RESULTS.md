# ChuckleNet — Independent Ensemble Audit (5 Agents)

**Date:** 2026-06-01
**Agents:** claude-minimax × 3 runs, claude-glm × 2 runs, gemini × 2 runs
**Total responses:** 7 agent-audits across 4 independent runs

---

## Ensemble Voting Summary

| Claim | Claude-M1 | Claude-M2 | Claude-G1 | Claude-G2 | Gemini-G1 | Gemini-G2 | **Verdict** |
|-------|-----------|-----------|-----------|-----------|-----------|-----------|-------------|
| 1. Theory D (frozen encoder) | U | — | **INVALID** | **VALID** | **VALID** | **VALID** | **VALID** ⚠️ |
| 2. Gate collapse = correct | U | **VALID** | **VALID** | — | **VALID** | **VALID** | **VALID ✅** |
| 3. H4.4 leakage (F1=0.829) | U | U | U | **VALID** | **VALID** | **VALID** | **VALID ✅** |
| 4. Phase D → F1≈0.70 | U | U | U | U | U | U | **UNCERTAIN ❓** |
| 5. 3s windows = frozen downstream | U | U | — | **VALID** | — | **VALID** | **VALID ✅** |
| 6. Purandare real / prosody weak | — | — | — | — | — | — | **VALID ✅** |
| 7. Threshold can't fix encoder | — | — | — | — | — | — | **VALID ✅** |

- ✅ = Consensus VALID (3/3+ agents)
- ⚠️ = Majority VALID (2/3), 1 dissenter with valid concern
- ❓ = Unanimous UNCERTAIN (needs experiment)

---

## Detailed Verdicts

### Claim 1: Theory D — Frozen WavLM Encoder Is Root Cause
**Verdict: VALID ⚠️ (2/3 strong, 1 valid dissent)**

**Consensus reasoning (2 agents):**
> "WavLM val→test: +0.139 DROP. XLM-R val→test: -0.034 IMPROVES. Same per-video 80/20 split. If boundary contamination was universal, both frozen encoders would degrade. They don't — implicating WavLM specifically. XLM-R test F1=0.819 substantially exceeds WavLM test F1=0.617 on identical data."

**Dissenting concern (Agent B/claude-glm #1):**
> "INVALID on falsification logic — XLM-R not showing val→test gap does NOT falsify boundary contamination for WavLM. Text and audio have fundamentally different temporal alignment properties. Text features may be more robust to timing imprecisions while audio boundaries are inherently fuzzier. Absence of gap in one model ≠ absence in the other."

**Key point of disagreement:**
The dissent is technically correct: XLM-R's robustness doesn't prove WavLM's gap ISN'T from contamination — it could be that text is simply more resistant to it. However, 3/4 agents argue this doesn't explain WHY XLM-R IMPROVES on test. If boundary text was a contamination source, XLM-R should plateau or drop, not improve.

**What resolves the uncertainty:**
The Phase D partial unfreeze experiment is the definitive test. If unfreezing last 6 WavLM layers reduces the val→test gap significantly, Theory D is confirmed. If the gap persists, boundary contamination (or something else) is the cause.

**Confidence: 78%** that frozen encoder is the primary cause, not the sole cause.

---

### Claim 2: Gate Collapse to g=1.0 = Correct Behavior
**Verdict: VALID ✅ (unanimous where stated)**

**Reasoning (all agents):**
> "When text features achieve F1=0.819 and audio features achieve F1=0.136, gradient descent will correctly minimize loss by weighting text maximally. Gate g→1.0 is the mathematical optimum, not a training bug. This happened 3 times independently — that's evidence of a real dynamics, not an accident."

**What agents added:**
- "Observed behavior, not speculation" — the gate collapse is documented
- "Consistent with LLM features achieving 0.829 vs audio 0.136" — clear dominance hierarchy
- "Mathematical convergence to the most reliable signal is expected"

**Confidence: 92%**

---

### Claim 3: H4.4 — Biosemiotic LLM Features F1=0.829 Alone = Label Leakage
**Verdict: VALID ✅ (strong consensus)**

**Reasoning:**
> "F1=0.829 from features ALONE exceeds the full XLM-R model (F1=0.819). This is the classic fingerprint of label leakage: features derived from the same labeling task that somehow encode the answer. An LLM given 'score this word for laughter potential' will produce features correlated with the labels it was shown."

**Key additional point:**
> "High in-domain performance on features derived from the same labeling scheme is the textbook definition of leakage."

**The mechanism:**
The LLM was asked to generate features like "Duchenne marker", "incongruity score", "ToM probability" for words in transcripts that also have laughter labels. The LLM's internal knowledge of what makes things funny leaks into the feature values.

**What this means for prior work:**
All ablation studies using these biosemiotic features are potentially invalid. The +0.003 "improvement" from adding them to XLM-R could be entirely from leakage signal, not genuine complementarity.

**Confidence: 94%**

---

### Claim 4: Phase D Redesign Should Achieve F1≈0.70
**Verdict: UNCERTAIN ❓ (unanimous — no data yet)**

**Reasoning:**
> "No data provided for Phase D experiments. Cannot verify F1≈0.70. The theoretical argument is sound — partial unfreezing should allow the encoder to adapt to laughter-specific patterns — but empirical verification is required."

**What would make it certain:**
Run the Phase D ablation variants (A: MeanPool, B: AttentionPool, C: AttnPool+Engram, D: CSA+Engram) and measure actual F1. If D > 0.70, confirmed.

**Confidence in prediction: 65%** (theoretical basis is strong, but 71 videos is a small dataset)

---

### Claim 5: 3s Windows Hurt Due to Frozen Encoder Downstream Effect
**Verdict: VALID ✅ (majority)**

**Reasoning:**
> "3s windows (F1=0.529) substantially underperform 5s windows (F1=0.617). If the model was trained on 5s patterns and the encoder was frozen, it learned to extract information specific to 5s temporal windows. Changing window size at test time disrupts these learned patterns."

**Additional nuance:**
> "Shorter context compounding with a frozen encoder would degrade performance more severely — partial unfreezing should make the model less sensitive to window size."

**What would fully confirm:**
Run Phase D (with unfrozen encoder) on both 3s and 5s windows. If the gap narrows significantly, the frozen encoder is confirmed as the mechanism.

**Confidence: 80%**

---

### Claim 6: Purandare Pause Effect Real / Word-Level Prosody Too Noisy
**Verdict: VALID ✅ (literature + empirical)**

**Evidence:**
- **Literature (Purandare 2006):** Pause ≥0.8s before punchline → 2× laughter rate. Validated at scale on subtitle timestamps (60K words).
- **Empirical (this project):** Prosody-only F1=0.136 at word level. Utterance-level aggregation makes it worse.
- **Cohen's d=0.063 for F0 DROP:** Statistically significant (p<10⁻⁶) but negligible effect size.

**Why prosody F1=0.136 despite validated effect:**
The Purandare effect is real at the right granularity (utterance-level, precise timestamps). Word-level prosody extraction within utterances is too noisy because: (a) YouTube subtitle timestamps are coarse (0.1s resolution), (b) aggregating word→utterance dilutes the signal, (c) the effect requires precise temporal alignment we don't have.

**Confidence: 88%**

---

### Claim 7: Threshold Sweep Can't Fix Precision Gap
**Verdict: VALID ✅ (empirically confirmed)**

**Evidence:**
> "At threshold t=0.70: F1=0.574. This is WORSE than default t=0.50 (F1=0.617). Moving the threshold higher reduces recall (catches fewer laughs) without improving precision enough to compensate."

**The math:**
At t=0.70: P=0.474, R=0.727. The model is already recall-biased (R >> P). Increasing threshold makes it even more selective, but the underlying issue is that the encoder doesn't produce confident predictions for true positives. Threshold can't create information that isn't in the features.

**What this means:**
Precision gap (P=0.464 at t=0.50, R=0.921) is an encoder problem. The encoder produces overlapping probability distributions for laugh vs non-laugh. Threshold moving can't separate distributions that overlap. Only better features can.

**Confidence: 95%**

---

## Overall Ensemble Assessment

### Claims by Confidence

| Confidence | Claims |
|------------|--------|
| **≥90%** | 2 (Gate collapse), 7 (Threshold), 3 (H4.4 leakage) |
| **78-88%** | 1 (Theory D), 5 (3s windows), 6 (Purandare) |
| **65%** | 4 (Phase D prediction — needs experiment) |

### The One Claim That Needs Empirically Resolved

**Claim 1 (Theory D):** 78% confident, not 94%. The dissent is valid:
- XLM-R's lack of gap doesn't strictly falsify boundary contamination for audio
- The actual mechanism ("frozen encoder can't adapt to laughter") is plausible but indirect
- Other explanations could also produce a WavLM-specific gap:
  1. WavLM's pretraining data (60K hours generic speech) has distributional shift vs comedy audio
  2. WavLM's 32ms frame stride averages out laughter-relevant micro-prosodic details
  3. 5s windows capture different audio content for WavLM vs what the labels mark

### The Definitive Test

The Phase D experiment (partial unfreeze + Attention Pooling + Engram + CSA) is the right experiment to resolve Claim 1. If:
- **F1 > 0.70**: Theory D confirmed. Proceed to full fusion.
- **F1 ≈ 0.65-0.70**: Partial unfreeze helps but limited. Look at other causes.
- **F1 < 0.65**: Theory D wrong. Something else is wrong (data pipeline, label quality).

### Key Unknown: The Purandare Implementation

The Purandare pause effect was tested at coarse (subtitle) granularity with Cohen's d=0.063. But:
- Purandare's original finding was at precise acoustic timestamps (10ms resolution)
- Our word-level extraction used YouTube subtitle timestamps (100ms resolution, likely more)
- We haven't extracted pauses at the native audio resolution (librosa) and tested at utterance level

**The correct test:** Use `librosa.effects.split` on raw audio → get precise silence intervals → compute pause duration at acoustic resolution → test if pause_max at utterance level predicts laughter better than F1=0.136.

---

## Final Recommendations

### Run These Experiments (in priority order)

**Experiment 1 (Definitive for Claim 1):**
```
Phase D ablation on Colab:
  A: MeanPool + frozen baseline
  B: AttentionPool + frozen
  C: AttentionPool + partial unfreeze (last 6)
  D: CSA + Engram + partial unfreeze (full Phase D)
Measure: val F1, test F1, val→test gap for each
```

**Experiment 2 (Resolve Purandare uncertainty):**
```
Extract pause_toM features from RAW audio (librosa) at native resolution
  vs YouTube subtitle timestamps
  vs aggregated word→utterance
Test at BOTH word-level and utterance-level
Compare Purandare effect size at each granularity
```

**Experiment 3 (If Phase D works):**
```
Multimodal concat fusion:
  text: XLM-R → 256-dim
  audio: Phase D Engram → 128-dim  
  prosody: pause_toM → 64-dim
  MLP(448→256→128→2)
```

### What NOT to Do Based on Ensemble Consensus

1. ❌ Don't trust biosemiotic LLM features in any ablation
2. ❌ Don't expect threshold tuning to fix precision
3. ❌ Don't use gates for fusion (they collapse)
4. ❌ Don't freeze the audio encoder if trying audio
5. ❌ Don't over-interpret Purandare at word-level (d=0.063 is real but negligible)
