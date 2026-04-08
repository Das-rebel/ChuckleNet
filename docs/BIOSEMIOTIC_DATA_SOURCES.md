# Biosemiotic Data Source Inventory

Date: 2026-04-05

This inventory focuses on datasets that are materially useful for biosemiotic humor modeling:

- explicit or weak laughter supervision
- setup/punchline or context/punchline structure
- multimodal cues tied to audience response, facial expression, prosody, or dialogue context
- annotations that help model incongruity, surprise, speaker intent, or social interaction

## Recommended Acquisition Order

### Tier 1: Directly aligned with the current stand-up objective

1. **StandUp4AI**
   - Type: multilingual stand-up comedy, multimodal, word-level sequence labeling
   - Why it matters: closest match to the current repo objective; audience laughter is the supervision signal and the task is framed at word level rather than clip-level classification
   - Biosemiotic value:
     - audience-laughter timing
     - setup/punchline continuity
     - cross-lingual humor transfer
     - multimodal context from live performance
   - Source:
     - ACL Anthology: https://aclanthology.org/2025.findings-emnlp.919/
   - Evidence:
     - the paper describes more than 330 hours of stand-up comedy in seven languages
     - the full dataset is automatically annotated for audience laughter, with a validation subset manually annotated
   - Recommendation: highest-priority external benchmark and weak-supervision source
   - Integration note: convert into the internal word-level JSONL format first, then score with the existing external benchmark bridge

2. **UR-FUNNY**
   - Type: multimodal humor detection with explicit context and punchline structure
   - Why it matters: gives a clean context/punchline representation with aligned text, audio, and visual features
   - Biosemiotic value:
     - explicit punchline fields
     - context sentences
     - word-aligned acoustic and facial features
     - humor vs non-humor contrastive supervision
   - Sources:
     - ACL Anthology: https://aclanthology.org/D19-1211/
     - Official repository: https://github.com/ROC-HCI/UR-FUNNY
   - Evidence:
     - the repo exposes `punchline_sentence`, `context_sentences`, `covarep_features_sdk`, and `openface_features_sdk`
   - Recommendation: highest-priority source for training explicit incongruity and punchline-localization features
   - Integration note: adapt it into a context-plus-punchline auxiliary task rather than forcing it directly into the current single-token weak-label scheme

3. **Open Mic**
   - Type: stand-up comedy humor-rating dataset
   - Why it matters: same performance domain as the repo, with audience-laughter-derived humor strength rather than binary labels
   - Biosemiotic value:
     - stand-up transcripts
     - clip-level humor quotient
     - laughter-duration-based rating signal
     - diverse comedians and live-performance dynamics
   - Sources:
     - ACL Anthology: https://aclanthology.org/2021.emnlp-main.789/
     - Official repository reference: https://github.com/cfiltnlp/AI-OpenMic
   - Evidence:
     - the paper reports about 40 hours of stand-up clips with humor quotient scores derived from audience laughter
   - Recommendation: strong secondary stand-up source for ranking, calibration, and weak regression targets
   - Integration note: useful for auxiliary funniness scoring or reranking, not a direct replacement for word-level laughter labels

### Tier 2: Strong conversational or sitcom humor resources

4. **MUStARD / MUStARD++**
   - Type: multimodal sarcasm and pragmatic incongruity in TV-show dialogue
   - Why it matters: sarcasm is not identical to humor, but it is rich in speaker-intent reversal, audience inference, and contextual incongruity
   - Biosemiotic value:
     - dialogue context
     - audiovisual delivery cues
     - speaker-intent modeling
     - pragmatic mismatch and theory-of-mind supervision
   - Sources:
     - MUStARD paper: https://aclanthology.org/P19-1455/
     - MUStARD repository reference from the paper: https://github.com/soujanyaporia/MUStARD
     - MUStARD++ paper: https://aclanthology.org/2022.lrec-1.756/
     - MUStARD++ repository reference from the paper: https://github.com/apoorva-nunna/MUStARD_Plus_Plus
   - Evidence:
     - MUStARD is compiled from popular TV shows and each utterance includes historical dialogue context
     - MUStARD++ adds emotion, valence, arousal, and sarcasm-type annotations
   - Recommendation: high-priority auxiliary dataset for ToM and intent features, not primary laughter supervision
   - Integration note: best used for intent heads and context-mismatch pretraining

5. **MUCH**
   - Type: multimodal conversational humor corpus from a Chinese sitcom
   - Why it matters: directly targets conversational humor rather than sarcasm, with text, acoustic, and visual cues
   - Biosemiotic value:
     - multi-speaker interaction
     - exaggerated expression and intonation
     - humor labels in conversational context
   - Source:
     - ACL Anthology: https://aclanthology.org/2024.lrec-main.1021/
   - Evidence:
     - the paper reports 34,804 utterances, of which 7,079 are humorous
   - Recommendation: high-priority conversational-humor source if multilingual or cross-cultural transfer is in scope
   - Integration note: useful for dialogue-pattern features and multimodal conversation encoders

6. **Big Bang Theory canned-laughter corpus**
   - Type: sitcom punchline detection via laugh-track-aligned dialogue
   - Why it matters: directly links dialogue turns to laugh-track-derived punchline labels
   - Biosemiotic value:
     - laugh-track timing
     - dialogue-to-punchline mapping
     - audio plus text signal
   - Sources:
     - NAACL 2016: https://aclanthology.org/N16-1016/
     - LREC 2016: https://aclanthology.org/L16-1079/
   - Evidence:
     - the authors built a corpus from The Big Bang Theory where punchlines are annotated using canned laughter embedded in the audio track
   - Recommendation: medium-priority because it is historically important and structurally relevant, but acquisition may require reproducing the corpus rather than downloading a clean packaged release
   - Integration note: useful if you want explicit laugh-track timing without waiting for more stand-up data

### Tier 3: Humor-theory and mechanism-focused text resources

7. **Humicroedit**
   - Type: humorous headline micro-edits with funniness ratings
   - Why it matters: very clean for modeling incongruity, surprise, superiority, and setup/punchline effects in text
   - Biosemiotic value:
     - tiny edits with large semantic shifts
     - explicit funniness scores
     - theory-grounded humor analysis
   - Sources:
     - NAACL 2019 dataset paper: https://aclanthology.org/N19-1012/
     - SemEval 2020 task: https://aclanthology.org/2020.semeval-1.98/
   - Evidence:
     - the dataset contains 15,095 edited headlines with five judges per headline
     - the paper explicitly states the data support incongruity, superiority, and setup/punchline theories
   - Recommendation: highest-priority text-only dataset for explicit incongruity feature learning
   - Integration note: ideal for pretraining semantic-shift and expectation-violation scorers

8. **FunLines**
   - Type: humorous headline generation and rating game
   - Why it matters: extends the Humicroedit style with more topical and game-generated humor
   - Biosemiotic value:
     - humor rating supervision
     - many near-minimal edits
     - topic-conditioned humorous reframing
   - Sources:
     - ACL demo paper: https://aclanthology.org/2020.acl-demos.28/
     - SemEval task summary with counts: https://aclanthology.org/2020.semeval-1.98/
   - Evidence:
     - the SemEval task paper reports an additional 8,248 annotated FunLines training headlines
   - Recommendation: useful extension to Humicroedit for scale and topical variety
   - Integration note: merge with Humicroedit for a dedicated text-only incongruity auxiliary objective

9. **rJokesData**
   - Type: large-scale rated joke corpus
   - Why it matters: broad coverage and scale for joke-style pretraining
   - Biosemiotic value:
     - explicit audience rating proxy
     - massive joke variety
     - useful for language-only humor priors
   - Sources:
     - Official repository: https://github.com/orionw/rJokesData
     - Linked LREC paper from the repository: https://aclanthology.org/2020.lrec-1.753/
   - Evidence:
     - the repository describes more than 550k rated English jokes and includes split TSV files plus the full unsplit corpus
   - Recommendation: medium-priority because it overlaps conceptually with the current Reddit-joke pool, but it is valuable for scale and rating-aware pretraining
   - Integration note: better as a pretraining source than as a standalone evaluation benchmark

### Tier 4: Small but biosemiotically rich calibration resource

10. **Cheese!**
    - Type: face-to-face conversational corpus with smile and humor annotations
    - Why it matters: small, but directly tied to smiling behavior and the success or failure of humorous sequences
    - Biosemiotic value:
      - manual annotations of smiling and humor
      - face-to-face interaction
      - conversational success/failure framing
    - Source:
      - ACL Anthology: https://aclanthology.org/2020.lrec-1.59/
    - Evidence:
      - the paper describes 11 French conversations of about 15 minutes each and manual annotations of smiling and humor
    - Recommendation: niche but excellent for validating Duchenne-style proxies and social-context assumptions
    - Integration note: use as a diagnostic or qualitative calibration set, not a main training source

## Best Next Moves

1. Acquire `StandUp4AI` and evaluate it through the existing word-level external benchmark bridge.
2. Acquire `UR-FUNNY` and build an auxiliary context-to-punchline feature pretraining path.
3. Acquire `Open Mic` for stand-up funniness regression and ranking.
4. Add `Humicroedit + FunLines` as a text-only semantic-incongruity pretraining task.
5. Add one conversational auxiliary source, preferably `MUStARD++` or `MUCH`, for theory-of-mind and interaction features.

## Practical Caveat

No source above, by itself, provides a credible path to a guaranteed `90%+` F1 on the repo's current task. The current filtered biosemotic subset is positive-only, and most of the strongest external sources differ in annotation granularity:

- word-level laughter sequence labeling: `StandUp4AI`
- clip-level funniness rating: `Open Mic`
- context/punchline humor classification: `UR-FUNNY`
- conversational sarcasm or humor classification: `MUStARD++`, `MUCH`
- text-only humor intensity or ranking: `Humicroedit`, `FunLines`, `rJokesData`

The realistic path is multi-task transfer plus better evaluation, not simply appending more rows.
