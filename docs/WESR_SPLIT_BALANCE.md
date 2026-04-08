# WESR Split Balance

This report compares the current overlap-safe split assignment against the best assignment that also favors discrete/continuous coverage in validation and test.

## Current assignment

- coverage penalty: `1`
- count penalty: `79.0`
- split stats: `{"test": {"example_count": 23, "laughter_type_counts": {"continuous": 20, "discrete": 3}}, "train": {"example_count": 505, "laughter_type_counts": {"continuous": 264, "discrete": 241}}, "valid": {"example_count": 102, "laughter_type_counts": {"continuous": 102}}}`

## Recommended assignment

- coverage penalty: `0`
- count penalty: `82.0`
- split stats: `{"test": {"example_count": 105, "laughter_type_counts": {"continuous": 84, "discrete": 21}}, "train": {"example_count": 502, "laughter_type_counts": {"continuous": 282, "discrete": 220}}, "valid": {"example_count": 23, "laughter_type_counts": {"continuous": 20, "discrete": 3}}}`
- component map: `{"comedy_club_transcript_1": "test", "comedy_transcript_100_observational": "train", "comedy_transcript_12_relatable": "train", "comedy_transcript_13_tech": "train", "comedy_transcript_14_personal": "train", "comedy_transcript_29_personal": "valid", "observational_comedy_2": "valid"}`

## Interpretation

A better WESR-balanced overlap-safe split exists and should be considered before using discrete/continuous metrics as a promotion gate.
