# Teacher Prompt Residual Smoke

This note records a targeted smoke test of the updated teacher prompt on the
`13` unresolved moved-target cases from `docs/REMAINING_TEACHER_REPAIRS.md`.

## Prompt change

- refinement prompt version: `lexical_target_v2`
- new instruction: prefer a content-bearing lexical word, avoid stopwords /
  punctuation where possible, and quote the exact chosen word in `note`

## Smoke result

- input subset: `13` residual cases
- backend/model: `ollama` + `qwen2.5-coder:1.5b`
- output: `13 / 13` kept
- new target word distribution: `{"beach": 13}`
- old failure mode: quoted stopword `My`
- new note pattern: `'beach'`

## Interpretation

The prompt-only change fixed the exact residual `My`-quote cluster in a bounded
subset run. This is promising, but it is not yet a full clean-split teacher
regeneration. The next step, if teacher work continues, is rerunning the clean
teacher refinement end to end with `lexical_target_v2` and then rebuilding the
safe hybrid.
