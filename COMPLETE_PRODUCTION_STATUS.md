# Complete Production Status

This repository is not using the historical integrated stack as the active production path.

## Active production candidate

The active candidate is the stand-up-specific XLM-R sequence-labeling pipeline documented in:

- `AGENTS.md`
- `CURRENT_STATUS.md`
- `docs/XLMR_STANDUP_ROADMAP.md`

## Validated output

Weak-label XLM-R baseline:

- validation F1: `0.7045`
- validation IoU-F1: `0.6327`
- test F1: `0.8142`
- test IoU-F1: `0.7322`

## Current blocker

The refined-label run is still being completed through the local teacher pipeline. That stage is now operational with incremental writes and resume support.

## Historical note

Older claims in this repo about the entire system being fully operational or production ready should be treated as historical and not as the current source of truth.
