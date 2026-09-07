# Label Hierarchy — the corrected spine of the project story (Sep 7)

Four label schemes have existed. Every historical number maps to exactly one tier.

| Tier | Scheme | Source | Used by | Verdict |
|---|---|---|---|---|
| 0 (retired) | Humor-LEXICON `label_any` | text contains humor vocabulary (aligned_utterances.jsonl — 100% uid+label match to July-16 npz) | 0.96 era: July-16 87v fusion 0.9759/test 0.9729, F0-LR "0.98", Top200 0.9759, Ensemble 0.941 | Labeler-derived (prosody predicts labels 0.994 on unseen videos). Models learned "humor-word acoustics". NOT laughter detection. |
| 1 (weak, current workhorse) | VTT caption laughter markers | bracket tags `[laughter] [laugh] [lol] [mdr]` typed by human captioners, real timestamps | **v19 canonical pipeline (training AND self-eval)**, 621-video scale-up, kaggle_frame 626v | Honest weak supervision. Numbers must be reported as "caption-marker detection", never "laughter detection" |
| 2 (benchmark truth) | StandUp4AI / EMNLP 2025 annotations | published benchmark ground truth (330hr, 7 langs) | 118v IoU eval: **IoU-F1@0.2 = 0.3302** (merge 0.8) vs their 0.51 baseline | The real competitive comparison. Gap to close: +0.18 |
| 3 (gold) | Gillick-162v real laughter labels | audio-verified laughter segments | **Fusion segment F1 = 0.559** (WavLM 0.548 / prosody 0.537), OOF GroupKFold, revalidated Sep 7 | Strongest validated claim. Only 162 TED videos |

## Naming corrections (verified Sep 7)
- The "Gillick 87" in colab_package notebooks is a MISNOMER: July-16 87v has **0 videos** in the Gillick-162v set (0/87 in the gillick_audio pool; only 22/87 in the 634-comedy list). Mixed-source corpus.
- Gillick-162v ∩ local gillick_audio pool = 61/162 (features were precomputed in fusion_features.npz, so eval unaffected).
- "EMNLP labels" (118v eval) = StandUp4AI benchmark annotations.
- Best-ever 118v number is **0.3302** IoU-F1@0.2 (docs/BEST_118V_RESULTS.md); "0.310" elsewhere was the pre-threshold-sweep value.

## The rule that prevents history repeating
Any model trained on Tier-1 weak labels must NEVER be evaluated only on the same weak scheme it trained on. Scale-up (v19 → 621v) must always carry a Tier-2/3 anchor eval (StandUp4AI-truth holdout and/or Gillick-162v) before any number is reported.
