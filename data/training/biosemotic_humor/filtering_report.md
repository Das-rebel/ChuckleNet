# Biosemotic Dataset Filtering Report

## Summary
- Retained rows: `103278`
- Source counts: `{'meld': 1669, 'reddit_jokes': 101609}`
- Split counts: `{'test': 10329, 'train': 82622, 'valid': 10327}`
- Removed counts: `{'hf_humor_proxy': 69745, 'meld': 9732, 'real_world_youtube_validation': 1440, 'synthetic_humor': 34}`

## Filtering Rules
- Keep all `reddit_jokes` rows.
- Keep only `meld` rows with `source_label_name = joy`, `quality_score > 95.0`, and multimodal timing context present in raw MELD files.
- Drop all remaining sources from the unified humor dataset.

## Humor Structure Balance
- Structure counts: `{'dialogic_banter': 1093, 'joyful_reaction': 403, 'generic_humor': 16, 'conversational_humor': 142, 'short_amusement': 15, 'narrative_reversal': 22225, 'setup_punchline_joke': 12369, 'quoted_dialogue_joke': 23805, 'question_answer_joke': 43210}`
- Speaker intent counts: `{'playful_banter': 707, 'reactive_amusement': 403, 'social_response': 528, 'humor_expression': 31, 'storytelling': 22225, 'comic_observation': 36174, 'joke_delivery': 43210}`
- Interaction pattern counts: `{'multi_party_banter': 978, 'dialogue_exchange': 660, 'single_turn': 31, 'monologue': 34594, 'reported_dialogue': 23805, 'call_and_response': 43210}`

## Feature Quality
- Mean biosemiotic viability: `0.6445`
- Mean genuine humor probability: `0.7416`
- Mean expectation violation: `0.6282`
- Mean social context humor score: `0.28`

## Validation Notes
- Allowed sources only: `True`
- MELD joy-only check: `True`
- MELD quality threshold check: `True`
- MELD multimodal context check: `True`
- This subset is positive-only and should be treated as a humor-rich feature-engineering corpus rather than a standalone binary classification dataset.

## Top Numeric Correlations
- `dialogue_turn_count` vs `multimodal_context_available`: `pearson=0.9072`
- `duchenne_genuine_humor_probability` vs `biosemiotic_viability_score`: `pearson=0.8755`
- `tom_speaker_intent_confidence` vs `tom_character_interaction_score`: `pearson=0.8564`
- `distinct_speakers` vs `multimodal_context_available`: `pearson=0.8423`
- `dialogue_turn_count` vs `distinct_speakers`: `pearson=0.8356`
- `incongruity_expectation_violation_score` vs `tom_speaker_intent_confidence`: `pearson=0.8063`
- `incongruity_expectation_violation_score` vs `tom_character_interaction_score`: `pearson=0.7752`
- `incongruity_expectation_violation_score` vs `biosemiotic_viability_score`: `pearson=0.7036`
- `duchenne_genuine_humor_probability` vs `incongruity_expectation_violation_score`: `pearson=0.699`
- `tom_audience_perspective_score` vs `tom_social_context_humor_score`: `pearson=0.6954`
