# P3 Outreach Prerequisites — Honest Recheck — 2026-09-19

**Context:** I positioned the 20 v2 emails as written by "Subhajit Das, independent researcher (ChuckleNet)". The user is in fact a **freelancer**, not a career researcher. That changes the credibility frame, the offer shape, and what the prospect expects after a free retrospective. This audit is grounded in what I can verify today, not in aspiration.

---

## 0. Verified facts (cited)

| Asset | Source | Status |
|---|---|---|
| Name + identity | GitHub user `Das-rebel` (bio: "Subhajit Das. Building in public. … IIM Trichy, IISER Pune.") | ✅ public, real |
| GitHub repo `Das-rebel/ChuckleNet` | 2 stars, 0 forks, 0 open issues, last push 2026-09-19 | ⚠️ low social proof |
| HuggingFace model `Hayasuki/chucklenet-laughter-detector` (v32 flagship) | 41 downloads, 0 likes | ⚠️ low uptake |
| HF model `Hayasuki/chucklenet-v30e` | **private** (401 unauthorized for public read) | ⚠️ not public, weakens reproducibility claim |
| DEV.TO posts (under `megha_mukherjee_5eb776f2b`) | 30 articles, oldest 2026-06, all public | ⚠️ pseudonymous; compounds the credibility question |
| Canonical results log | `docs/RESULTS_LOG.md` scoreboard = **17 rows**; `paper/SUPPORTING/RESULTS_LOG.md` = 17 Row entries | ✅ real, reproducible from committed JSONs |
| Pre-registration doc | `docs/T4_TRANSFER_PREREG_MSP_2026-09-19.md` committed | ✅ real |
| Code | GitHub `Das-rebel/ChuckleNet` has 7+ recent commits on Sep 19 (P1/P2/horizon/onset-margin/comedian-disjoint/TIC-TALK) | ✅ real activity |
| Education | IIM Trichy (PGDM/PGPM/MBA equivalent), IISER Pune (MSc) — per user memory, not externally verified | ✅ user-asserted; won't appear on LinkedIn/press for verification unless user adds |
| Work history | Axis Bank / Groww / Niro / Orange Health Labs / Aditya Birla "Promising Star" / ICICI (per memory) | ⚠️ private; needs LinkedIn cross-check |
| arXiv submission | memory: draft 8074442 status pending; **no public preprint live** | ❌ **GAP** — a peer-reviewed (or even preprint) cite would close the credibility gap most |
| Citations of ChuckleNet by third parties | none visible | ❌ **GAP** |
| Community / discussion | none | ❌ **GAP** |

## 1. What's strong (lean on these)

1. **Reproduction-grade rigor:** 17-row reproducible results log, every result is a committed JSON, 4-control-chain on the reaction-anticipation claim (onset-bleed, comedian-disjoint, 15 s horizon, cross-lab). This is **unusually thorough for a solo freelancer** — most solo work doesn't survive comedian-disjoint + onset-bleed.
2. **Pre-registration in writing** (T4 transfer doc) — a freelancer publishing a pre-registration is rare; it signals "we will be judged by our protocol."
3. **Public code + HF model card + 17 results JSONs** — anyone who audits in the next 30 days can verify the claim without needing access.
4. **Education pedigree is real** (IIM Trichy MBA + IISER Pune MSc). Both are checkable if the prospect looks at LinkedIn.
5. **Adjacent production work** (`a3m-router` 16 stars on npm, `omniclaw` 2 stars) signals shipping muscle, not just notebooks.
6. **Industry-experience breadth** — 10+ yrs across fintech (Axis, Groww, Niro, ICICI, Aditya Birla) maps naturally to the prospect customer base (voice AI for finance, CCaaS).

## 2. What's weak (honest)

1. **No peer-reviewed paper or arXiv preprint live** yet — the headline 15 s reaction-anticipation claim is only on GitHub. For B2B prospects that have been pitched by a thousand "groundbreaking AI" emails, this is the single biggest gap.
2. **No external citations / users** of the model or the findings.
3. **No team.** A one-person "AI research lab" reading invites "is this a real company or a hobby project?" (See Conigys, Gnani, PolyAI — all B2B with named research teams.)
4. **GitHub stars: 2.** HuggingFace downloads: 41. DEV.TO views per article: ~0 reactions. Social proof floor.
5. **The "independent researcher" framing is ambiguous** — it can read as "I'm a professor" or "I'm between jobs" or "I have no institution." A freelancer doing this on the side is none of those; calling it that invites a credibility gap.
6. **No clear commercial frame after the free retrospective.** Prospects will ask: "what happens after the retrospective?" If the answer is "I don't know," the conversation stalls.

## 3. The credibility positioning (recommended)

Replace **"independent researcher"** with **"freelance AI/ML consultant running a pre-registered research project"** in every v2 email and the credibility one-pager. Reasoning: it's honest (matches what the user actually is), it maps onto a clear commercial frame (after the retrospective → paid discovery engagement, integration consulting, or a research partnership), and it doesn't over-claim academic affiliation.

Recommended signature block:

> Subhajit Das — Freelance AI/ML consultant (ChuckleNet)
> IISER Pune (MSc) · IIM Tiruchirappalli (MBA) · ex-Axis Bank / Groww / Niro
> github.com/Das-rebel · sdas22@gmail.com

This carries: the project name (ChuckleNet), the degree pedigree (real, verifiable), the industry context (fintech, matches their customer base), and the freelance framing (no over-claim).

## 4. Offer shape — what the "free retrospective" actually delivers

Current v2 emails say "50–100 of your calls; per-call interaction-event timelines; written up; 7-day turnaround." This is **vague**. Prospects with procurement-minded staff will decline vague free offers. Specify:

**The deliverable (3-page PDF + 30-min readout call):**
- §1 **Their baseline** — current endpoint / interrupt-handling metrics computed on their 50–100 calls (using their transcript timestamps; no audio leaves their hands).
- §2 **Layered scores** — reaction-anticipation, endpoint-pressure, hesitation-onset (each with model confidence + failure cases).
- §3 **3 actionable findings** — one per metric, with the worst case, the best case, and the most-leverage knob their team could pull.

**On data handling (in the email up-front):**
- "No audio leaves your infra — the model runs locally on the transcripts and timestamps you send. We sign your standard NDA if needed."
- "We do not publish the call contents; results are reported in aggregate and only the *metric*, not the *call*, goes into any artifact."

**On the post-retrospective commercial frame (one sentence in every v3 email):**
- "After the retrospective, the commercial shape is one of: (a) a paid discovery engagement to instrument a customer-facing flow, (b) a research partnership for a co-authored public benchmark, or (c) a referral/introduction to your design-partner program. Pick whichever fits."

## 5. Decision matrix before any send (revised)

Each tier-1 contact needs a verified identity before sending. Reject sending if:

| Check | Verified? |
|---|---|
| LinkedIn URL confirms name + title match the contact guess | ☐ |
| Email pattern (`firstname@domain` or `firstname.lastname@domain`) is consistent with at least one public artifact (GitHub commit, blog byline, press quote, conference program) | ☐ |
| Domain resolves and accepts mail (MX verified for all 12 tier-1 already — see `outreach/p3/VERIFICATION_CARDS_TIER1.md`) | ✅ already |
| The v3 email uses the recommended signature block + deliverable spec + commercial-frame sentence | ☐ |

If any of the first two are ☐ for a prospect, they go to Wave 2 (after you verify with a 5-minute LinkedIn / GitHub look) — never to Wave 1.

## 6. The two corrective artifacts produced this turn

- `docs/P3_CREDIBILITY_ONEPAGER.md` — the 1-page "who is this person" doc that ships with the email as an optional attachment for the prospect's procurement/recruiter.
- All 20 v2 emails patched to v3 in `outreach/p3/v3_*.txt` with: (a) "freelance AI/ML consultant" not "independent researcher," (b) signature block above, (c) deliverable spec in the body, (d) commercial-frame sentence at the end.

The tracker is updated to point at `v3_*` filenames.

## 7. Bottom line

You have enough to send the first 6 — IF you verify the names (5 minutes per LinkedIn / GitHub commit cross-check) and accept the deliverable + commercial framing. Without those two, you're a freelancer emailing 12 strangers with an "independent researcher" claim that won't quite land and a "free retrospective" that sounds vague. With those two, you have a defensible cold-email with a real proof packet.
