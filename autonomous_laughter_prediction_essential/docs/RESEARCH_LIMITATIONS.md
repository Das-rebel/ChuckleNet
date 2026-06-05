# Research Limitations Summary

**For paper abstract/limitations section**

---

## Key Limitations of Current Work

### 1. Dataset Scale
**Claim vs Reality:**
- Claimed: 100+ languages, 3M words, 130K+ laughter labels
- Actual: 3 languages (English, Chinese, Hindi), ~165K words, ~3,700 laughter labels

**Impact:** Our claims significantly exceeded actual achievements. The dataset is ~5% of claimed scale.

### 2. Multilingual Coverage
**Claim vs Reality:**
- Claimed: 100+ languages with "global comedy representation"
- Actual: Primarily English (74%) and Chinese (26%), with minimal Hindi (0.5%)

**Impact:** The "multilingual" claim is misleading - the dataset is heavily English-centric.

### 3. Laughter Labels
**Claim vs Reality:**
- Claimed: 130,000+ word-level laughter annotations
- Actual: ~3,700 examples with laughter labels (40% of 10,048 = ~4K total)

**Impact:** Label count is ~3% of claimed amount.

### 4. Data Collection Method
- YouTube transcripts contain speech but NOT audience laughter markers
- Synthetic data used to supplement real data (may not reflect authentic comedy)
- Manual annotation was not performed due to time constraints
- Hindi/Hinglish data generated synthetically rather than collected from real sources

### 5. Performance Validation
- Model achieved F1 > 0.81 on English/Chinese test set
- Hindi performance NOT evaluated (0% laughter labels in Hindi data)
- Cross-lingual transfer claims not experimentally validated

---

## What We Actually Achieved

### Positive Contributions
1. **Functional multilingual pipeline** - Demonstrated framework can process en/zh data
2. **Biosemotic feature integration** - Novel feature engineering approach  
3. **Scalable architecture** - XLM-R based framework extensible to new languages
4. **Realistic baseline** - F1 0.81 on supported languages is meaningful

### Honest Claims Going Forward
- "We present a framework for multilingual laughter prediction, validated on English and Chinese"
- "Our approach achieves F1 > 0.81 on two-language benchmark"
- "We demonstrate feasibility and release code/data for replication"
- "Hindi/Hinglish expansion planned as future work"

### Limitations to State
1. Dataset limited to 3 languages (vs 100+ claimed)
2. Scale ~5% of originally claimed 3M words
3. Hindi performance not evaluated (0% laughter in Hindi subset)
4. Synthetic data may not reflect authentic comedy patterns
5. Cross-lingual transfer to Hindi not empirically validated

---

## Suggested Paper Framing

### Option A: Modest Claims
**Title:** "Word-Level Laughter Prediction in Stand-up Comedy: A Bilingual Study"
- Focus on en/zh results only
- Acknowledge Hindi expansion as future work
- Frame 3-language dataset as "initial multilingual validation"

### Option B: Honest Limitations
**Title:** "Toward Multilingual Laughter Prediction: A Feasibility Study"
- Acknowledge dataset limitations explicitly
- Frame as "proof of concept" rather than comprehensive solution
- List specific gaps: only 3 languages, scale limited, Hindi not evaluated

### Option C: Hybrid Approach
**Title:** "Multilingual Laughter Prediction: Validated on English/Chinese, Hindi Planned"
- Report actual results on en/zh
- Do NOT claim 100+ language capability
- Present Hindi generation as work-in-progress
- Be transparent about synthetic vs real data

---

## Key Numbers for Paper

| Metric | Original Claim | Actual | % Achieved |
|--------|---------------|--------|------------|
| Languages | 100+ | 3 | 3% |
| Words | 3,000,000 | 165,634 | 5.5% |
| Laughter labels | 130,000 | ~3,700 | 2.8% |
| F1 Score (en/zh) | >0.4240 | 0.8194 | 193% |

**Note:** F1 exceeded target, but on limited language set.

---

## Recommendations for Submission

1. **Revise claims** to match actual dataset (3 languages, not 100+)
2. **Be explicit** about synthetic vs real data sources
3. **Do NOT claim** Hindi performance without evaluation
4. **Frame as** "feasibility study" or "initial results" rather than comprehensive solution
5. **Highlight** actual contributions: biosemotic features, XLM-R pipeline, real F1 performance

---

*This document reflects honest assessment of project status as of 2026-05-04*