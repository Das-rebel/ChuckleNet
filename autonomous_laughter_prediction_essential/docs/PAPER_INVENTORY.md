# Paper & Publication Plan Inventory
**Date:** 2026-05-16

## Papers Found in Project

| # | File | Size | Target Venue | Status | Key Issue |
|---|------|------|-------------|--------|-----------|
| 1 | `docs/PAPER_DRAFT_ACL_EMNLP.md` | 44KB | ACL/EMNLP 2026 | Complete draft | StandUp4AI missing, no error bars |
| 2 | `docs/PAPER_OUTLINE_ACL_EMNLP.md` | 12KB | ACL/EMNLP 2026 | Outline only | Projected results, not real |
| 3 | `docs/SOTA_PRD_RL_LAUGHTER_PREDICTION.md` | 16KB | ACL/EMNLP 2026 | Superseded | PRD v3, replaced by v4 |
| 4 | `docs/PRD_V4_10M_PIPELINE.md` | 16KB | N/A | Not started | Infrastructure PRD |
| 5 | `docs/PAPER_REVISION_PLAN.md` | 4KB | ACL SRW/Interspeech | Active plan | Post-peer-review fixes |

## Review Documents

| File | Source | Key Finding |
|------|--------|-------------|
| `docs/JENNI_PEER_REVIEW.md` | Jenni.ai | 10 comments, StandUp4AI critical |
| `docs/JENNI_REVIEW_ANALYSIS.md` | PI Agent | Not publishable without fused results |
| `docs/ORCHESTRA_REVIEW.md` | Orchestra Research | **Score: 2.75/6, Borderline Reject** |
| `docs/RESEARCH_PAPER_GAP_ANALYSIS.md` | Internal | Claims vs reality audit |
| `docs/RESEARCH_LIMITATIONS.md` | Internal | Honest limitations |
| `docs/UPDATED_RESEARCH_CLAIMS.md` | Internal | Revised claims |
| `docs/STANDUP4AI_REVISED_PLAN.md` | Internal | StandUp4AI benchmark plan (not executed) |
| `docs/GAP_ANALYSIS_2026_05_13.md` | Internal | 7 PRDs, 0 executed |

## What Has No LaTeX/PDF — Needs Conversion
- All paper content is **Markdown only**
- No `.bib` bibliography file
- No `.tex` LaTeX source
- No `paper/` directory (Orchestra recommended structure)
- Orchestra templates available at `~/.orchestra/skills/20-ml-paper-writing/ml-paper-writing/templates/`

## Two Distinct Papers Possible

### Paper A: Text-Only (Current Draft)
- **What:** XLM-R + biosemotic features for word-level laughter prediction
- **Results:** F1=0.819 (en), 0.752 (zh), 0.68 (hi, 48 examples)
- **Target:** ACL SRW (Student Research Workshop)
- **Blockers:** StandUp4AI comparison, error bars, LaTeX conversion
- **Effort to submission-ready:** 2-3 weeks

### Paper B: Multimodal (Future)
- **What:** WavLM audio + XLM-R text fusion
- **Results:** None yet (audio training incomplete)
- **Target:** EMNLP Findings or Interspeech
- **Blockers:** Audio training, fused model, audio-only baseline
- **Effort:** 6-8 weeks

## Recommended Priority
1. **Paper A → ACL SRW** (most realistic, fastest path)
2. **Paper B → Interspeech** (if WavLM training completes)
