# ChuckleNet — Pre-Seed One-Pager — 2026-09-19

**The question we answer:** can machines get useful information from *how* people interact — information the transcript does not contain?

## Evidence (all human-verified labels, pre-registered, full control chain)

| Finding | Result | Controls passed |
|---|---|---|
| **Reaction anticipation** | Frozen speech representations predict audience laughter **up to 15 s ahead**, beating the full preceding transcript by **+0.11 F1** [+0.086, +0.139] | onset-bleed strata, comedian-disjoint folds, position shortcut, leakage discipline |
| Sequence structure matters | Destroying temporal order costs −0.077 F1; fine local order does not | paired 3-seed, order-shuffle/local/reverse |
| Honest nulls | Timing-aggregate features: null (×2). Generic emotion (MELD): null. | concurrent + prospective variants |
| Cross-lab check | Our protocol ports to second-lab public data (TIC-TALK); their kinematic correlate fails the same incremental standard ours passes | show-clustered bootstrap |

**Claim discipline:** performance/monologue speech validated; conversational-domain transfer pre-registered (MSP-Podcast, license in execution); not an emotion product.

## Product

A **real-time interaction-signal layer** for voice AI — reaction anticipation, endpoint pressure, hesitation-onset — as an API beside ASR/intent engines. Industry already pays for this signal family: endpoint-anticipation research integrated in production voice stacks (−505 ms latency).

**Outputs:** reaction-onset probability (0–15 s horizon) · endpoint pressure · interruption risk · hesitation onset.

## Business motion (per mandate §6–7)

- Free retrospective design-partner studies (20-conversation gate running; kit + 20 targeted outreach emails ready)
- Track A: voice-agent infra (Vapi, Retell, LiveKit, Deepgram…) · Track B: conversation operators (Yellow.ai, Ozonetel, Skit.ai…)
- Design-partner definition enforced: named owners, use case, metric, sandbox data, willingness to test

## Ask (pre-seed)

Raising to fund: conversational-domain validation (license in execution; compute trivial), 2–3 free partner pilots, one applied-domain benchmark. Research core is a single independent researcher with a 23-row reproducible results log; capital goes to evidence velocity, not headcount.

**Contact:** Subhajit Das — sdas22@gmail.com — github.com/Das-rebel
