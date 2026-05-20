# Jenni Peer Review Simulation — Complete Results
**Date:** 2026-05-16
**Document:** Multimodal Laughter Detection in Multilingual Stand-up Comedy Using WavLM and XLM-R Word-Level Fusion
**URL:** https://app.jenni.ai/editor/rT6Ghl2JCbDBmjsVIbNV
**Account:** New account (logged in by user)

---

## Peer Review: 10 Expert Comments

### Comment 1 — Missing Visual Modality Discussion
The paper argues for multimodal fusion but does not justify the exclusion of the visual modality. Recent works like "FunnyNet-W" (Liu et al., 2024) and "AVR" (Sharma et al., 2024) demonstrate the importance of visual features in funny moment and humour detection. While focusing on audio-text is valid, a brief discussion in the "Discussion" or "Limitations" section explaining this choice would enhance completeness.

### Comment 2 — Teacher-Refinement F1=0.08 Needs Explanation
The claim that teacher-refinement using LLM labels severely degraded performance (F1 = 0.08) is a significant finding. However, the audit highlights recent literature (Romanowski et al., 2025; Inoue et al., 2025) demonstrating LLMs achieving much higher F1 scores (e.g., 43.14% to 51%) in similar humour detection tasks. This discrepancy suggests that the low performance may be due to the specific implementation rather than LLM incapacity. Authors should provide details on the LLM model version, prompt templates, and methodology used for this experiment to ensure reproducibility and explain the observed difference from current field standards.

### Comment 3 — Data Leakage / Confound Risk
The document synopsis mentioned the paper lacks a dedicated "Limitations" section. Given that the data involves audio from stand-up performances, it is important to discuss the potential for "data leakage" where the model might simply detect audience laughter rather than the comic's prosodic cues. This should be acknowledged as a limitation and, ideally, addressed with further analysis.

### Comment 4 — Missing Audio-Only Baseline
To fully evaluate the contribution of each modality, it is standard practice in multimodal machine learning to include an audio-only baseline, in addition to the text-only baseline already provided. This would help ascertain if text is genuinely contributing or if the model is primarily detecting laughter from audio cues alone.

### Comment 5 — Missing StandUp4AI Benchmark
The audit indicates a critical gap regarding a major recent work, "StandUp4AI: A New Multilingual Dataset for Humor Detection in Stand-up Comedy Videos" (Barrière et al., 2025). This work directly addresses word-level laughter detection in multilingual stand-up and could serve as a crucial benchmark for comparison or contextualisation of your dataset.

### Comment 6 — Missing M2H2 Hindi Dataset Comparison
The section states the dataset includes three languages. The audit identified "M2H2: A Multimodal Multiparty Hindi Dataset For Humor Recognition in Conversations" (Chauhan et al., 2021) as relevant prior art for multimodal Hindi humour. It would be beneficial to discuss how your dataset compares to or builds upon this existing Hindi-specific multimodal dataset.

### Comment 7 — Novelty Claim Too Strong
The claim that "No prior work has combined WavLM audio features with XLM-R text representations for multilingual laughter detection" is a strong assertion of novelty. While the specific combination might be novel, the broader task of multimodal multilingual laughter detection and the individual components (WavLM, XLM-R) are not. It would strengthen the paper to elaborate on why this particular combination is significant and how it differs from similar multimodal fusion approaches in the literature, especially considering works like Barrière et al. (2025) which focus on multilingual stand-up comedy.

### Comment 8 — Missing Hindi-Specific Literature
Given that Hindi is one of the target languages, the literature review should include prior work on Hindi-specific humor detection. "M2H2: A Multimodal Multiparty Hindi Dataset For Humor Recognition in Conversations" (Chauhan et al., 2021) provides early baselines for Hindi multimodal fusion and is directly relevant.

### Comment 9 — Outdated Barrière Citation
This section cites Barrière et al. (2024) for sequence labeling. However, a highly relevant recent work by Barrière et al. (2025), "StandUp4AI: A New Multilingual Dataset for Humor Detection in Stand-up Comedy Videos," is a critical missing baseline from this literature review. It directly addresses word-level sequence labeling for humor in multilingual stand-up and should be discussed to properly position the current work.

### Comment 10 — "Largest Dataset" Claim May Be Outdated
The claim of having "one of the largest multilingual laughter detection datasets to date" may be outdated. A more recent work, "StandUp4AI: A New Multilingual Dataset for Humor Detection in Stand-up Comedy Videos" (Barrière et al., 2025), introduces a dataset of 330 hours across seven languages, which is substantially larger than the 49 performances mentioned here. This should be acknowledged and potentially compared against to properly contextualise the dataset size and contribution.

---

## Key References Found by Peer Reviewer

| Reference | Relevance |
|-----------|-----------|
| Barrière et al. (2025) StandUp4AI | **CRITICAL** — Direct competitor, multilingual stand-up, word-level |
| Chauhan et al. (2021) M2H2 | Hindi multimodal humor dataset |
| Liu et al. (2024) FunnyNet-W | Visual modality for humor detection |
| Sharma et al. (2024) AVR | Audio-visual humor recognition |
| Romanowski et al. (2025) | LLM-based humor detection benchmarks |
| Inoue et al. (2025) | LLM humor detection F1 scores |

---

## Summary: What Needs to Change Before Publication

### Critical (Must Fix)
1. **Add StandUp4AI (Barrière 2025) comparison** — This is the most direct competitor. Our paper MUST discuss it.
2. **Add audio-only baseline** — Standard practice for multimodal papers
3. **Explain teacher-refinement failure** — Provide model version, prompt, methodology details
4. **Add Limitations section** — Discuss data leakage risk, no visual modality

### Important (Should Fix)
5. **Weaken novelty claim** — "No prior work" is too strong given StandUp4AI
6. **Add M2H2 Hindi dataset** comparison
7. **Justify excluding visual modality**
8. **Contextualize dataset size** against StandUp4AI's 330 hours

### Minor
9. **Update Barrière 2024 → 2025** citation
10. **Add Hindi-specific literature**

---

*Saved by PI Agent via Brave CDP, 2026-05-16*
