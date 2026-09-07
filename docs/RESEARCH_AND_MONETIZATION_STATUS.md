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

---
## ⚠️ CORRECTION (Sep 7, later same day) — the above "no monetization plan exists" was WRONG

Deeper recheck (session transcripts + ~/ChuckleNet/ + context.db) found:

1. **PRD_V6_MULTI_PRODUCT_LAUGHTER_PLATFORM.md RECOVERED** (written Jun 3-4, lost in consolidation; full 12.8KB text extracted from session transcript, now in `docs/recovered/` + Drive backup). It DOES define 3 products with commercial-use sections: P1 Group Laughter Predictor (word-level discourse positioning; script debugging, content scoring, video editing), P2 Individual Laughter+Sarcasm (mental health, call centers, accessibility — needs diarization, VTT labels unusable), P3 Sarcasm-Aware Content Scorer.
2. **LAUGHTER_PREDICTION_RESEARCH_VISION.md RECOVERED** (9.9KB, same source/location).
3. **THE MONETIZATION PLAN EXISTS**: `DEFINITIVE_PLAN.md` (Aug 6, agent council) — "DEFINITIVE MONETISATION PLAN": this is a PAPER + OPEN SOURCE, not a startup. Option A: open-source + $200/hr consulting. Option B: API product (market tiny). **Option C (RECOMMENDED): career-first — paper as credential, GitHub as portfolio.**
4. **The planned F0 paper "When Simple Beats Deep" (F1=0.96 golden nugget per council) is DISQUALIFIED**: those were lexicon labels (100% uid+label match to aligned_utterances.jsonl, proven Sep 6-7). The publishable version is the inverse finding (weak-label pitfall) + honest fusion/benchmark numbers.
5. context.db (Aug 6) independently documented the era's label catastrophes: 697-video f0_500plus labels were voicing detection (49.7% pos), word-level cascade dead at IoU 0.50, WavLM unfreeze fails.

Revised track scores: research ~35-40% (materials stronger than thought; zero submissions still true); monetization = plan exists and says DON'T build a product — so progress under Option C = paper+portfolio readiness, gated on the same P0-P3 chain.
