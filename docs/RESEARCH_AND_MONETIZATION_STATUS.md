# Vision / Research / Monetization — verified status (Sep 7)

## RESEARCH PLAN (3 Papers -> API, June 20 PRD)
- **Paper 1 (arXiv): NEVER SUBMITTED.** Plan said "ready to submit" Jun 20; no arXiv ID exists anywhere; endorsement-request repo untouched since 2026-06-21; referenced draft `arxiv_paper_v2.md` does not exist (only `arxiv_preprint_v1.md`).
- **Paper 1 claims are NOT tier-mapped** (our own anchor rule): "ensemble 0.587 held-out, p<0.0001" = 555v-era numbers, label tier unverified. Submitting as-is would violate the standard we just set.
- **Papers 2/3 (INTERSPEECH/ACL 2027):** blocked on GPU fine-tuning experiments — never started.
- **The June insight was right though:** PRD_V4 listed "Label Leakage" as a publication path; today's 100% uid+label lexicon proof is its completion. The honest paper is now STRONGER than the June draft: Gillick-0.559 OOF ablation + 118v 0.3302 vs StandUp4AI 0.51 + label-circularity case study.
- **Research-track progress: ~35%.** (Analysis/materials strong; zero submissions; current numbers need one revalidation pass into a new draft.)

## MONETIZATION PLAN
- **No monetization plan document exists** — searched all project dirs, backups, GitHub.
- What exists instead:
  1. "3 papers -> production API" = aspirational header, no API/product/pricing section anywhere
  2. `10M_PIPELINE_ARCHITECTURE.md` (May 9) = infra sketch: 10M segments, en/zh/hi, **~$20/month Colab-tier cost** — an infrastructure design, not a business model
  3. `Chucklenet_predictor` repo = SDK skeleton whose README claims (humor strength 0-100%, reverse modeling, 12+ humor categories) exceed any validated result — built on the weakest data era (Kaggle word-level, cv-F1 0.238)
- **Monetization-track progress: ~10%.** Credibility assets (honest model card, reproducible pipeline, negative-result methodology) exist; product, pricing, distribution: none.
- Realistic sequencing: paper credibility -> HF/GitHub presence -> API demo (Space/Replicate) -> paid tier. All gated behind the same P0-P3 foundation.

## CONVERGENCE
All three goals (mission / research / monetization) bottleneck on the identical 3 steps:
**run v19 on Colab -> scale to 621v with Tier-2/3 anchor evals -> paper with honest numbers.**
Nothing else unlocks monetization before that chain completes.
