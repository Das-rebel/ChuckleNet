# Refined Label Audit

This report compares the weak-label training set against the teacher-refined set and audit log.

## Summary

- Weak examples: `520`
- Audited examples: `520`
- Refined examples kept: `475` (91.35%)
- Examples dropped: `45` (8.65%)
- Kept examples with moved target index: `68` (14.32% of kept examples)
- Average absolute target shift: `12.191` tokens
- Weak average target position ratio: `1.0`
- Refined average target position ratio: `0.9271`
- Weak punctuation targets: `70.77%`
- Refined punctuation targets: `66.74%`
- Moved targets landing on punctuation: `20`
- Moved targets landing on stopwords: `43`

## Top Teacher Reason Tags

- Keep: `laughter (249), punchline (215), reversal (119), surprise (94), laughing (7)`
- Drop: `request_error (29), weak_positive (16)`

## Top Positive Tokens

- Weak: `" (165), ! (137), ? (66), useless (19), month (17), decision (17), calling (17), personally (17)`
- Refined: `" (123), ! (114), ? (63), useless (18), month (17), ' (17), my (16), personally (16)`

## Suspicious Moved Targets

- `comedy_transcript_36_observational_seg_002` weak `"`@36 -> refined `'`@20 (punctuation, confidence=1.0, tags=punchline,reversal)
  note: The line contains the punchline 'I'm good!' which is a clear trigger word for laughter.
- `comedy_transcript_18_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.
- `comedy_transcript_23_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.
- `comedy_transcript_28_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.
- `comedy_transcript_30_observational_seg_001` weak `"`@17 -> refined `"`@10 (punctuation, confidence=0.98, tags=traffic,nice)
  note: The audience laughs after saying 'Nice traffic'
- `comedy_transcript_38_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.
- `comedy_transcript_3_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.
- `comedy_transcript_43_tech_seg_003` weak `"`@27 -> refined `'`@10 (punctuation, confidence=0.98, tags=punchline,reversal)
  note: The line contains the punchline word 'I'm using a Mac!' which is followed by laughter.

## Interpretation

- If punctuation or stopword targets rise sharply, the teacher is likely relocating positives onto syntactically weak trigger positions.
- If many kept examples move the target index, the refined set is not just filtering examples; it is changing the supervision geometry the model learns from.
- If the refined average position shifts earlier in the sentence, that is consistent with recall loss when weak labels were originally anchored near laughter-adjacent endings.
