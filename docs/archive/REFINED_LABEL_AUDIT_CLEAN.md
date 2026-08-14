# Refined Label Audit

This report compares the weak-label training set against the teacher-refined set and audit log.

## Summary

- Weak examples: `505`
- Audited examples: `505`
- Refined examples kept: `505` (100.0%)
- Examples dropped: `0` (0.0%)
- Kept examples with moved target index: `134` (26.53% of kept examples)
- Average absolute target shift: `3.739` tokens
- Weak average target position ratio: `1.0`
- Refined average target position ratio: `0.9451`
- Weak punctuation targets: `80.0%`
- Refined punctuation targets: `62.57%`
- Moved targets landing on punctuation: `26`
- Moved targets landing on stopwords: `21`

## Top Teacher Reason Tags

- Keep: `punchline (331), surprise (227), content-bearing lexical word (144), punchline phrase (30), laugh (21)`
- Drop: `n/a`

## Top Positive Tokens

- Weak: `" (162), ! (161), ? (81), yesterday (21), useless (20), beach (20), beer (20), rain (17)`
- Refined: `! (160), ? (87), " (69), yesterday (21), i (21), useless (20), beach (20), drinking (20)`

## Suspicious Moved Targets

- `comedy_club_transcript_1_seg_001` weak `"`@19 -> refined `?`@18 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'Do you want room for milk? '
- `comedy_transcript_11_observational_seg_001` weak `"`@19 -> refined `?`@18 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'Do you want room for milk? '
- `comedy_transcript_12_relatable_seg_003` weak `"`@15 -> refined `"`@12 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'They love outdoor activities'
- `comedy_transcript_16_observational_seg_001` weak `"`@19 -> refined `?`@18 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'Do you want room for milk? '
- `comedy_transcript_17_relatable_seg_003` weak `"`@15 -> refined `"`@12 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'They love outdoor activities'
- `comedy_transcript_22_relatable_seg_003` weak `"`@15 -> refined `"`@12 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'They love outdoor activities'
- `comedy_transcript_27_relatable_seg_003` weak `"`@15 -> refined `"`@12 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'They love outdoor activities'
- `comedy_transcript_2_relatable_seg_003` weak `"`@15 -> refined `"`@12 (punctuation, confidence=0.95, tags=punchline,surprise)
  note: 'They love outdoor activities'

## Interpretation

- If punctuation or stopword targets rise sharply, the teacher is likely relocating positives onto syntactically weak trigger positions.
- If many kept examples move the target index, the refined set is not just filtering examples; it is changing the supervision geometry the model learns from.
- If the refined average position shifts earlier in the sentence, that is consistent with recall loss when weak labels were originally anchored near laughter-adjacent endings.
