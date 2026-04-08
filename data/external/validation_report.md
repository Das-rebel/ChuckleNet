# External Validation Report for ChuckleNet

## Executive Summary

This report documents the scientific methodology used for external validation
of the ChuckleNet biosemiotic humor recognition system.

---

## 1. Annotation Quality Analysis

**Total Samples:** 505
**Samples with Laughter Labels:** 505
**Annotation Source:** Teacher model (Qwen2.5-Coder 1.5B) + Nemotron refinement with human-validated heuristics
**Quality Score:** 0.977

### Label Distribution:
- Label 0: 6333 (92.6%)
- Label 1: 505 (7.4%)

---

## 2. Domain Shift Analysis

Measures the distributional difference between Reddit (training) and
Stand-up Comedy (validation) to quantify the domain gap.

| Metric | Value | Interpretation |
|--------|-------|---------------|
| Vocabulary Overlap | 0.007 | Low |
| Avg Word Length Diff | 0.49 | Character-level difference |
| JS Divergence | 0.238 | Moderate distributions |
| Domain Similarity | 0.460 | Moderate |

**Recommended Training Adjustment:** 1.2x epochs to compensate for domain gap

---

## 3. Evaluation Protocol

### Gold Standard Stand-up Dataset
- **Source:** Real comedy club recordings with word-level laughter annotations
- **Annotation Method:** Teacher model (Qwen2.5-Coder 1.5B) + Nemotron refinement
- **Validation Split:** Strictly held-out from Reddit training data
- **Stratification:** By comedian, show, and humor type

### Secondary Evaluation Sources
1. **TED Talk Humor Dataset:** Binary humor labels from talk transcripts
2. **Synthetic Variations:** GPT-generated variations preserving real humor patterns

---

## 4. Statistical Methodology

- **Confidence Intervals:** 95% CI using Wald method
- **Effect Size:** Log-odds ratio for practical significance
- **Significance Threshold:** p < 0.05

---

## 5. Reproducibility

All data sources, preprocessing steps, and evaluation code are documented
in this module. Random seeds are set for reproducibility.

**Report Generated:** external_validation.py