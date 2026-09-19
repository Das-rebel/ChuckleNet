# P3 Outreach Send Plan — v2 pipeline — 2026-09-19

**Rule:** NOTHING sends until (a) its dossier exists, (b) the email is rewritten with dossier-specific hooks, (c) a verified or clearly-labeled pattern address exists, and (d) the user approves the final wave list.

---

## Phase status

| Phase | Owner | Status |
|---|---|---|
| 0. Prospect list (20) | done | ✅ `P3_DISCOVERY_KIT_2026-09-18.md` |
| 1. Deep-research dossiers (20) | 5 parallel research agents | 🔄 running |
| 2. Quality review of dossiers | main agent | pending phase 1 |
| 3. Email v2 rewrites (per-company hooks, no templates) | main agent | pending phase 2 |
| 4. Tracker update (contacts, tiers, addresses) | main agent | pending phase 3 |
| 5. User approval of Wave-1 list | user | pending |
| 6. Send + log (SMTP via sdas22 for email; LinkedIn/Discord/GitHub manual for those channels) | user + main agent | pending |

## Email v2 requirements (every email must have)

1. A **specific, recent, verifiable hook** from the dossier (launch, blog take, repo commit, job ad) in the first two lines
2. One-sentence evidence claim (15 s anticipation, +0.11 F1, controls) — never overclaimed to "emotion AI"
3. The free-retrospective offer with the 6-point design-partner ask folded in
4. A named human recipient; pattern-guess addresses allowed only if labeled and no generic alias exists
5. ≤150 words, one question at the end
6. Follow-up #1 prepared at send time (+4 business days, new information or angle, not a bump)

## Waves (draft — finalized after dossiers)

- **Wave 1 (day 1):** all Tier-1 companies (strong fit + named contact found) — Track A open-source/dev-heavy first (Pipecat Discord + GitHub + email in parallel where channels exist)
- **Wave 2 (day 3–4):** Tier-2 with pattern addresses
- **Wave 3 (week 2):** remainder + follow-ups to silent Wave-1
- **Timing:** Tue–Thu; Track A targets US Pacific morning; Track B India targets 10:30–11:30 IST
- **Cadence cap:** max 6 first-touches/day to protect deliverability (sdas22 domain reputation)
- **Logging:** every send appended to `P3_DISCOVERY_TRACKER.csv` same day; responses land in sdas22 INBOX (checked each cycle)

## Verification standards (carried from user rules E1–E4)

- No generic aliases (info@/hello@/support@/contact@/hr@) — ever
- No careers@ blasts
- Every address labeled VERIFIED or PATTERN-GUESS in the tracker
- Unsubscribes/DO-NOT-CONTACT notes honored permanently
