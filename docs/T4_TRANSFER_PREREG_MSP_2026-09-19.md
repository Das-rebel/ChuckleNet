# T4 Transfer Protocol — Pre-Registration — 2026-09-19

**Mandate:** V4 §8 (P4 transfer) — unlocked: P1/P2 yielded meaningful, hardened evidence.
**Trigger condition:** MSP-Podcast DUA executed (form filled 2026-09-19, awaiting user signature + Busso office acceptance). Zero-spend constraint respected: academic license is free.
**Smallest lawful dataset:** MSP-Podcast emotion-labeled release (conversational podcast speech; 2,220+ speakers).

---

## Question (mandate wording)

> Does the learned interaction representation retain incremental value after domain shift? (stand-up → conversational speech)

## Operationalization

Replace "learned representation" with our **established protocol** — the Level A prospective design — and ask whether the beyond-transcript acoustic increment survives the domain shift:

**Task (T4-primary):** predict laugh/vocalization onset in the next window from preceding context only, on MSP-Podcast segments arranged in show-time order.

**Critical data question (open with Busso's office):** MSP-Podcast's standard release labels emotions per segment; laughter/vocalization event timestamps may exist in unreleased versions (asked Sep 13; unanswered). Transfer target options, in order of preference:
1. **If vocalization/laughter flags exist:** onset prediction per our Level A task (direct replication).
2. **If not (emotion-only):** predict next-segment *emotional events* where the reaction family applies (happiness/arousal spikes) — a weaker, clearly-labeled fallback; claim narrows to "affective-reaction anticipation."

## Arms (identical to Level A, audio features recomputed on MSP audio)

1. `position_only` — shortcut control
2. `words_before` — cumulative transcript TF-IDF (ASR transcripts available in corpus)
3. `acoustic_before` — frozen WavLM context `[mean t−2..t, t, position]` (same frozen backbone, no fine-tuning — tests representation transfer, not fitting capacity)
4. `acoustic_plus_words`

## Protocol invariants (non-negotiable)

- GroupKFold by **show** (speaker-overlap exists across MSP partitions — group by podcast show ID, and additionally report speaker-disjoint sensitivity)
- Seeds 42/43/44; identical MLP; early stopping on val F1@0.5
- TF-IDF train-fold only; features strictly ≤ t; predictions mapped to original order
- Video-clustered (show-clustered) bootstrap, 10k resamples
- Gates: CI95 lower > 0 AND mean ΔF1 > 0.02 (treatment − baseline)
- Onset-bleed stratification repeated at MSP resolution
- All results reported regardless of direction (MELD null precedent)

## Pre-registered outcomes

| Result | Meaning | Action |
|---|---|---|
| Gates pass at MSP resolution | Beyond-words prospective signal **transfers to conversational speech** | Mandate P4 progression opens: voice-agent/customer-service domain next; commercial claim upgrades to "domain-transferred" |
| Gates fail | Signal is **performance-domain-specific** (audience structure) | Thesis narrows honestly to audience-reaction products (livestreams, content, voice agents serving creators); P4 continues with a different second domain only if a specific partner use case demands it |

## Cost

Zero cash. Compute: CPU-sufficient for frozen-feature extraction + MLP protocol (MSP audio ~120 h; WavLM CPU extraction feasible over several days, or free Kaggle GPU hours). No new paid services.
