# Human Labeling Services — Lowest-Cost Survey & Recommendation — 2026-09-18

**Purpose:** identify the lowest-cost defensible human-labeling path for (a) gold-anchor validation of our EMNLP-derived laughter windows, and (b) optional scale labeling of new videos.
**Research channel:** agent-reach → Exa web search + Jina reader (Sep 2026 pricing sources: secondtalent country-rate survey updated 2026-09-14, Prolific pricing docs, AITraining.jobs platform comparison, Label Your Data vendor reviews, worldmetrics audio-annotation vendor rankings).

---

## 0. What we actually need

| Need | Detail | Priority |
|---|---|---|
| Gold anchors | 3 independent annotators × 10–15 existing videos; laugh onset/offset spans; measure agreement (Krippendorff α, IoU) vs EMNLP-derived windows | **Now** — validates the label tier our entire P1/P2 evidence chain rests on (anchor rule) |
| Scale labels | 100–300 new videos, event spans, for external/horizon validation and P4 transfer | Later, only if P3/P4 demands it |
| Tooling | Audio span labeling with playback; export JSON; free/self-hosted | Label Studio (open source) fits exactly |

Per-video cost driver: ~10–15 min audio → 15–20 min task with replay; ×2–3 annotators; ×QC adjudication ⇒ **~1.0–1.3 human-hours per fully-QC'd video**.

---

## 1. Market state — September 2026 (material changes)

- **Amazon Mechanical Turk shuts down September 30, 2026** (12 days from this memo). Excluded from all plans.
- **Remotasks** cut off workers in Kenya, Nigeria, Pakistan (Mar 2024) — vendor risk category.
- **Prolific** now lists a 42.8% pay-as-you-go platform fee for corporate customers (lower for research plans); recommended participant pay $8–12/hr.
- **Toloka** pivoted to enterprise data partner; no self-serve microtask pricing.
- Reported global labeling pay spans **$1.32–2/hr** (Kenyan bulk work, TIME/Sama reporting) to **$25–50/hr** (US AI-training generalists). Ethical floor for us: **≥$6/hr** — sub-$3 sourcing is a reputational and quality liability we will not touch.

## 2. Cost comparison for our task (all-in, per fully-QC'd video)

| Option | Effective rate | Est. cost/video (2–3 annotators) | Quality risk | Notes |
|---|---|---|---|---|
| **Prolific** (crowd, research plan) | $11–17/hr all-in | **$11–22** | Low–med | Best screening (audio setup checks, attention filters), academic-grade pool |
| **Clickworker** | $6–15/hr effective | $6–19 | Medium | Per-task pricing; needs own QC layer |
| **India BPO vendor** (iMerit, Shaip, Cogito, Habile, Predusk) | $3–7/hr at volume | $3–9 at 100+ hrs; higher at pilot volumes | Low w/ managed QC | Quote-based; onboarding overhead; best only at volume |
| **Freelance** (Upwork/Fiverr) | $5–15/hr | $5–20 | High variance | We supply tooling + QC; fine for pilots |
| **Enterprise** (Scale, Appen, TELUS, Sama, Defined.ai) | $25–100+/hr | $40–150+ | Lowest | Overkill at our stage |
| **Model-assisted + crowd verify** (Label Studio + our Level A detector pre-labels) | — | **$3–6** via Prolific; **$1.5–3** via Clickworker | Medium (bias toward model) | Cuts human time 3–5×; must keep a held-out no-prelabel QC slice |

## 3. Recommendation

### Phase 1 — gold anchors now (~$120–200 total)
1. **Tool:** self-host Label Studio; task = laugh onset/offset spans on 5 s-windowed audio; export JSON; store as canonical artifact.
2. **Workforce:** Prolific (research plan), 3 annotators/video, $9–10/hr pay, audio-device screening + attention checks; dual annotation with agreement (α, IoU@0.2 vs EMNLP windows) reported.
3. **Volume:** 12 videos ≈ 15 human-hours ≈ **$135–200 all-in**.
4. **Output:** citable label-validation artifact ("EMNLP-derived windows match independent human annotation at IoU-F1 X.XX, α = 0.XX") — required before any Tier-1 claim scaling.

### Phase 2 — scale only if needed
Clickworker or an Indian vendor with **model-assisted pre-labels** from our Level A detector (humans verify/correct; hold out a 20% no-prelabel slice for unbiased QC). Target **<$5/video all-in**; engage only when P3/P4 produces a concrete dataset need.

### Not recommended
MTurk (shutting), enterprise vendors (cost), sub-$3/hr sourcing (ethics/reputation).

---

## 4. Immediate next actions

1. Install Label Studio locally; write the laughter-span task spec (align to B/I/L semantics + onset/offset).
2. Draft the Prolific study (12 videos × 3 annotators); verify current researcher plan fee at signup (source cited 42.8% is the corporate PAYG figure).
3. Budget request: **$200** from pre-seed funds for Phase 1.
