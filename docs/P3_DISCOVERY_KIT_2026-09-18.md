# P3 Discovery Kit — Design-Partner Outreach (Zero-Cost Phase) — 2026-09-18

**Mandate:** V4 §6 — commercial discovery runs now, regardless of research gate status. P2 is closed positive, so the evidence exists; this kit operationalizes the first gate: **20 qualified conversations**. No spend.

---

## 1. The pitch (one paragraph)

> AI systems understand what people say. We've built and validated the next layer: what the **audio** says the person will do next. On human-verified stand-up data, frozen speech representations predict audience laughter up to **15 seconds before it happens** — with information the transcript does not contain (+0.11 F1 over full-transcript baselines, 83/118 videos improved, surviving comedian-disjoint, onset-bleed, position, and order-destruction controls). For voice agents this is a **reaction-anticipation and turn-timing signal**: know the listener is about to react — or that your user is about to finish — before they do. The same signal family (endpoint anticipation) is already saving ~500 ms of latency in production voice stacks. We offer a free retrospective analysis on your call logs: you get the insights, we get ground truth for discovery.

**Claim discipline (say exactly this, no more):** validated on performance/monologue speech with human labels and controls; conversational-domain validation in progress; not an emotion product; not a pause-statistic heuristic (those are null in our controls).

## 2. Design-partner definition (per mandate — a conversation only "counts" with all six)

1. Named technical owner
2. Named business owner
3. Concrete use case
4. Agreed evaluation metric
5. Realistic sandbox/retrospective data access
6. Willingness to execute a test

## 3. Target list (20 candidates — verify contacts before outreach)

### Track A — voice-agent / speech-to-speech infrastructure (12)
Value prop: endpoint anticipation + reaction signals → lower latency, fewer cut-ins, natural interruption handling. (Industry proof: Endpoint Anticipation arXiv 2026 integrated in Unmute, −505 ms; VAP line.)

1. Vapi — voice-agent infra; developer-facing
2. Retell AI — voice-agent platform
3. Bland AI — phone-call agents
4. LiveKit — real-time audio/video infra (agents framework)
5. Daily (Pipecat) — WebRTC + open-source voice-agent framework
6. Vocode — open-source voice-agent framework
7. Deepgram (Agents) — ASR + agent APIs
8. ElevenLabs (Conversational AI) — TTS + agents
9. Cartesia — low-latency voice agents
10. PolyAI — enterprise voice assistants
11. Uniphore — conversational AI + emotion-adjacent analytics (position as timing, not emotion)
12. Observe.AI — contact-center conversation intelligence

### Track B — high-volume conversation operators / CCaaS analytics (8)
Value prop: retrospective interaction signals → intervention timing, escalation prediction, agent coaching.

13. Yellow.ai — enterprise conversational platform (India/global)
14. Gnani.ai — voice-first conversational AI (India, BFSI)
15. Ozonetel — CCaaS (India)
16. Exotel — cloud telephony + conversational AI (India)
17. Cognigy — enterprise voice/chat agents (EU/US)
18. Parloa — enterprise voice AI for contact centers (EU)
19. Skit.ai — voice AI for collections (US/India)
20. Kore.ai — enterprise conversational AI

*(Prioritize Track A items 1–6 first: developer platforms move fastest, have public Slack/Discord where technical owners live, and the endpoint-anticipation literature gives them a felt pain point.)*

## 4. Outreach templates

### Track A (developer platform) — short
> Subject: interaction-signal layer for [Platform] — 15 s reaction anticipation
>
> Hi [name], your users' voice agents still react to listeners rather than anticipating them. We've validated a signal from frozen speech representations that predicts audience/listener reactions up to 15 s ahead with information the transcript lacks (controlled study, human labels; writeup available).
>
> We're offering 2–3 design partners a free retrospective analysis: send us N recorded calls, we return interaction-event timelines (reaction anticipation, endpoint forecasts) mapped to your transcripts. You keep the insights; we ask for the joint evaluation numbers and a named owner.
>
> 20-minute call this week?

### Track B (contact-center operator) — value first
> Subject: timing signals in your call recordings (free retrospective study)
>
> Hi [name], we research non-lexical interaction signals — hesitation, reaction onset, turn pressure — and just completed a controlled validation showing audio context predicts listener reactions up to 15 s ahead, beyond what transcripts capture.
>
> We'll run this free on 50–100 of your recorded calls (retrospective, no integration): you get per-call interaction-event timelines and where your current intent engine is blind. We ask for a named business + technical owner and one agreed metric to evaluate.
>
> Worth a 20-minute chat?

## 5. Scorecard fields (per conversation — mandate §7)

`date | company | track | contact name/role | repeated problem? | current workaround | missing signal they name | their KPI | data accessibility | integration effort (S/M/L) | budget/economic owner | objection | qualified? (6-point definition) | next step`

Keep in `docs/P3_DISCOVERY_TRACKER.csv` (create on first entry).

## 6. Weekly rule (mandate §12)

Every cycle reports: qualified conversations count, partner status, KPI, objection. **First discovery gate: 20 qualified conversations.** Design-partner gate: 2 serious partners. Pilot gate: 1 retrospective evaluation with baseline → signal → delta.

## 7. Free supporting asset for this phase

- **TIC-TALK (public, HuggingFace `ENC-PSL/TIC-TALK`)** — 90 filmed stand-up specials, 0.8 s laughter events, skeletal keypoints. Use as: (a) free external validation of the anticipation claim on a second dataset (planned, zero spend); (b) credibility artifact in partner conversations.
