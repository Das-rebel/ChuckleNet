# StandUp4AI Benchmark Gap Analysis & Roadmap

**Date:** 2026-04-01
**Target:** >42.4% F1 on StandUp4AI
**Current Status:** 0.0% F1 on English-only slice, 1.04% F1 on 4-example public slice

---

## Executive Summary

The 42.4% F1 target from the StandUp4AI paper is **not achievable** with current infrastructure because:

1. The full dataset is not publicly available (requires email request to authors)
2. Only 4 labeled examples exist in the public repository
3. A fundamental label schema mismatch exists between internal and StandUp4AI formats

---

## 1. Public Dataset Analysis

### Available Data
| Resource | Location | Contents |
|----------|----------|----------|
| Public Examples | `/tmp/standup4ai_dataset_main/dataset-main/Examples_label/` | 4 CSV files (cs, en, es, fr) |
| Full Dataset | Available on demand | Contact vbarriere@dcc.uchile.cl |

### Public Example Label Statistics
| File | Language | L (Laughter) | O (Other) | Total | L% |
|------|----------|--------------|-----------|-------|-----|
| -1FrUOEswOk.csv | French | 97 | 955 | 1052 | 9.2% |
| 0g7nezWZyfY.csv | Czech | 118 | 936 | 1054 | 11.2% |
| 1xvwYZwm8Ig.csv | English | 277 | 534 | 811 | 34.2% |
| 6JQzl2LlXbQ.csv | Spanish | 72 | 214 | 286 | 25.2% |

**Key Observation:** The English example has the HIGHEST laughter density (34.2%), yet the model achieves 0.0% F1 on English-only evaluation.

---

## 2. Label Format Mismatch Analysis

### Internal Dataset Schema
```json
{
  "text": "I told my wife [laughter]",
  "labels": [0, 0, 0, 0, 1],  // 1 positive token per example
  "laughter_type": "discrete"
}
```

### StandUp4AI Schema
```csv
text,timestamp,label
Bonsoir...,"[9.241, 9.481]",L
Ils,"[9.501, 15.563]",L
m'ont,"[15.583, 15.743]",O
...
```

**Mismatch Metrics:**
- Internal: **exactly 1** positive token per positive example
- StandUp4AI: **~141** average positive tokens per positive span
- StandUp4AI: **3.84** tokens per positive span on average

### Impact
The model was trained on sentence-level weak supervision where a single token marks the entire laughter segment. StandUp4AI uses word-level sequence labeling where multiple consecutive tokens can be labeled "L" (laughter).

---

## 3. Current Model Performance

### Benchmark Results on Public Examples
| Configuration | F1 | IoU-F1 | Notes |
|---------------|-----|--------|-------|
| Default (argmax) | 0.0104 | 0.0204 | 4 languages |
| English-only | 0.0000 | 0.0000 | 1 example, 118 tokens |
| With chunking (128) | 0.0104 | 0.0204 | 28 chunks evaluated |
| Best decode policy | 0.2308 | 0.1980 | topk_span with cue bonus |

### English Failure Analysis
Token-level inspection shows the model predicts content words (`other`, `yesterday`) instead of filler/discourse markers near labeled laughter spans.

---

## 4. Paths Forward

### Option A: Obtain Full StandUp4AI Annotations (Recommended)

**Action:** Email vbarriere@dcc.uchile.cl requesting dataset access

**Expected Outcome:** 70 manually annotated videos (10 per language) with precise laughter annotations

**Timeline:** 1-2 weeks for response

**Requirements:**
- State research purpose (laughter detection in stand-up comedy)
- Commit to non-commercial use
- Agree to cite the paper

**Advantage:** This is the ONLY way to get meaningful benchmark validation

### Option B: Adapt via Span-Aware Training

**What Works:**
- Span-aware auxiliary supervision improved public slice from F1 0.0104 to 0.0268
- Cue-biased span supervision achieved strongest English transfer (F1 0.1322)

**What Doesn't Work:**
- Still trades away internal validation gate
- Does not solve English transfer fully

**Recommendation:** Continue span-aware experiments ONLY if Option A is delayed

### Option C: Fine-tune on Small StandUp4AI Subset

**Not Viable:** Only 4 examples available publicly - insufficient for fine-tuning

---

## 5. Recommended Action Items

### Immediate (Week 1)
1. **Contact StandUp4AI authors** to request full dataset access
   - Email: vbarriere@dcc.uchile.cl
   - Template message provided below

2. **Continue autoresearch** on internal dataset only
   - Current blocker: validation IoU-F1 has not moved above 0.3333
   - Focus on breaking this plateau

### Short-term (Week 2-4)
1. If dataset received:
   - Evaluate on full StandUp4AI test set
   - Identify specific failure modes
   - Design targeted interventions

2. If delayed:
   - Continue span-aware experiments with bounded resource
   - Document transfer learning failure modes

### Medium-term (Month 2+)
1. Design curriculum that bridges sentence-level weak labels to word-level StandUp4AI format
2. Explore multi-task learning with both internal and StandUp4AI supervision
3. Consider collecting small English stand-up dataset if commercial licensing allows

---

## 6. Email Template for Dataset Request

```
Subject: StandUp4AI Dataset Access Request for Laughter Detection Research

Dear Dr. Barriere,

I am a researcher working on automatic laughter detection in stand-up comedy
transcripts. I recently came across your EMNLP 2025 paper "StandUp4AI: A New
Multilingual Dataset for Humor Detection in Stand-up Comedy Videos" and am
interested in using your dataset to benchmark my model's performance.

Would it be possible to obtain access to the StandUp4AI dataset? I commit to:
- Using the dataset solely for academic research purposes
- Providing proper citation in any resulting publications
- Respecting any usage restrictions you specify

My specific research focus is word-level laughter prediction in English
stand-up comedy transcripts. The dataset's word-level annotations would be
invaluable for evaluating cross-domain transfer capabilities.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your Institution]
```

---

## 7. Realistic Assessment

### What 42.4% F1 Means
- The 42.4% F1 is from a multilingual model trained on the **full** StandUp4AI dataset
- It requires word-level sequence labeling, not sentence-level classification
- The internal model is not trained for this task format

### Achievable Goals
| Goal | Feasibility | Notes |
|------|-------------|-------|
| Beat 0% F1 on English | High | Already have evidence with cue-aware topk_span |
| Reach 10% F1 on public 4-example | Medium | Requires continued span-aware experiments |
| Match 42.4% F1 | Impossible | Cannot achieve without full dataset |

### Recommended Success Metric
**Revise target to: Demonstrate measurable English transfer (>5% F1 on English slice)**

This is achievable with continued span-aware experiments and would validate the transfer learning approach.

---

## 8. Conclusion

The 42.4% F1 target is not achievable because:

1. **No access to full dataset** - StandUp4AI requires dataset request
2. **Label schema mismatch** - Sentence-level vs word-level sequence labeling
3. **English transfer failure** - 0.0% F1 despite 34% laughter density in English example

**Next Step:** Request dataset access immediately. Continue internal research in parallel.
