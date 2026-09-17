# T4 READINESS & DATA SURVEY — transfer test (stand-up → conversation → voice-agent)
**Date:** 2026-09-13 · **Status:** READY-TO-DECIDE (data source choice = user decision; all mandatory pillars T1–T3 closed)

## 1. What T4 must show (pre-registered draft gate)

The T2 result (sequence order carries laughter signal, +0.034/+0.087 over order-shuffled controls on true labels) was established on **stand-up monologue**. T4 asks whether the finding **transfers to conversational speech** — the domain where the voice-agent use case actually lives.

Pre-registered gate (mirrors T2 protocol, to be committed to EXPERIMENT_REGISTRY before any run):
- **Primary:** on a conversation corpus with true laughter labels, 5-fold GroupKFold by speaker/meeting, C (BiGRU) beats C-shuf (order-permuted control) — same stability recipe, same arms.
- **Secondary (cross-domain):** stand-up-trained detector evaluated zero-shot on conversation data beats the naive/energy baseline on IoU-F1@0.2.
- **Falsifier:** if C-shuf ≥ C on conversation data, the temporal finding is domain-specific (monologue-only) — that would be a publishable negative too.
- Registry rule carried over: weak-label (VTT-marker) conversation results are hypothesis generators, never headline claims.

## 2. Candidate data sources (surveyed 2026-09-13)

| Source | Domain | Laughter labels | License | Effort/risk |
|---|---|---|---|---|
| **MSP-Podcast** (lab-msp.com) | conversational podcasts, 409h+, 264,705 turns (v2.0) | emotion+dim. annotations standard; **laughter-event labels: TO CONFIRM at license time** (later versions reportedly include them) | free for academic research, **signed agreement required** (email to MSP Lab) | LOW risk, best-matched domain; wait for agreement turnaround |
| **AMI Meeting Corpus** (Edinburgh / OpenSLR 16) | multi-party meetings | **explicit laughter labels: TO CONFIRM** (annotations zips contain dialogue-act + vocalization layers) | **CC BY-NC-SA — free direct download, no signature** | LOWEST friction; laughter label layer unverified |
| **IEMOCAP** (USC SAIL) | dyadic actor conversations | emotion labels only (no first-class laughter) — would need **our own annotation pass** | free academic, signed USC agreement | HIGH: annotation cost to create laughter ground truth |
| **Switchboard** (LDC) | telephone conversations | vocalization/laughter transcriptions exist (Gillick-2021 lineage) | **LDC paid license** | COST blocker |
| **Podcast VTT weak-label line** (our own machinery) | conversational podcasts | transcript `[laughter]` markers | none (YouTube ToS considerations same as 620v line) | fast hypothesis-generator; **never headline** per registry rule |

## 3. Recommended path (ranked)

1. **AMI first** (free, immediate): download annotations zip, verify whether laughter events are labeled with usable density; if yes → T4 primary on meetings.
2. **MSP-Podcast in parallel** (best labels/domain): user sends license request to MSP Lab (Busso lab, UT-Dallas); run T4 primary there if laughter labels confirmed in the released version.
3. **Weak-label podcast line** as cheap pre-study while licenses are pending — same VTT pipeline as v32, conversation domain, hypothesis-generator only.
4. IEMOCAP / Switchboard only if 1–2 fail (annotation cost / license cost).

## 4. What we already have (no new compute needed to start)

- T2 pipeline + BiGRU stability recipe (locked) — reusable as-is on any conversation corpus
- Feature builder (WavLM768+prosody23, 791-d) — the T2 C-arm feature space
- 118v stand-up model artifacts — for the cross-domain zero-shot secondary test
- MELD acoustic artifacts (meld_acoustic_official.npz, meld_frames.pkl) — reusable infrastructure reference, **not** a T4 eval set (no laughter labels)
- All Kaggle CPU kernels — T4 stays CPU-only like the rest

## 5. Decision needed from user

- [ ] Approve T4 gate wording (above) → then it goes into EXPERIMENT_REGISTRY as E06 pre-run entry
- [ ] Pick data path: AMI-first (free) / MSP-Podcast-first (license email) / both in parallel
- [ ] If MSP-Podcast: send the license request (only the user can sign)

**Until the user picks, T4 is blocked on decision, not on data or compute.**
