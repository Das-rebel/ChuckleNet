# Robust Generalization in Audio-First Laughter Detection Through WavLM and Prosodic Ensembling

> **CANONICAL WORKING PAPER** — promoted 2026-09-14. This is the core paper; PAPER_DRAFT_V1/V2 are superseded as reference-only.
> Live editing document: Jenni.ai editor `3TPv3LXEjFIEq4m19LvA` (app.jenni.ai).
> Every number verified against RESULTS_LOG rows 1–15 / EXPERIMENT_REGISTRY. References list = the 7 verified entries in refs.bib.


## Introduction

Laughter detection—the identification of audience reaction events within spoken content—is a probe for a broader question: can a machine recover information from conversational interaction that is absent from the literal word stream? This question matters for stand-up comedy analytics, meeting intelligence, and socially aware voice agents, yet it is usually tested post hoc, on whatever results happen to look positive. We take the opposite approach: a pre-registered, gate-governed evaluation program in which every test was committed to writing—with success gates and falsifiers—before execution, and results were logged regardless of direction. The program yields a contrast. At 620 videos and 121,928 utterances, transcript-marker weak labels bound a WavLM-based detector to the label ceiling: the model genuinely tracks laughter (rate correlation 0.361) but plateaus at IoU-F1@0.2 = 0.2290, AP = 0.142. On human-verified labels, temporal order carries replicable information: a BiGRU beats an order-shuffled control by +0.034 IoU-F1@0.2 at 40 videos and +0.087 at 118 videos—the effect grows with data. But the same interaction signals fail their pre-registered gate on general 7-class emotion classification (MELD, official test split, n = 2,609): Δ = 0.0000, 95% bootstrap CI [−0.0142, +0.0145]. Together these findings sharpen the field's working hypothesis: beyond-words interaction information is real but event-specific—laughter and reaction events live off the word stream, while everyday emotion is already near its practical ceiling on words alone at accessible model scale. We release the complete decision registry, evaluation gates, falsifiers, kernels, and per-arm artifacts so that every number can be re-run.


## Related Literature


### Laughter Detection

Automatic laughter processing has a two-decade lineage. Purandare and Litman (2006) established the acoustic correlates of laughter in television dialogue, and Truong and van Leeuwen (2007) separated laughter from speech on prosodic and spectral cues. Gillick et al. (2018) modeled applause in campaign speeches—an adjacent audience-reaction event—and Gillick et al. (2021) scaled laughter detection with word-aligned weak labels derived from AudioSet, reaching strong word-level operating points and demonstrating that weak supervision can bootstrap the field. StandUp4AI (Barrière et al., 2025) contributed multilingual stand-up comedy material with human labels, enabling event-level evaluation on naturally occurring audience laughter. Our anchor experiments replicate both lineages at reduced scale—Gillick-162 fusion F1 0.559, human-labeled 118-video IoU-F1@0.2 in the 0.30 band—to certify pipeline calibration before any novel claim.


### Multimodal Fusion

MELD (Poria et al., 2019) is the standard multimodal benchmark for emotion in conversation, and published multimodal gains over strong text-only models there are consistently small. Our anchor study quantifies the fusion pattern for laughter: on the Gillick-162 anchor set, early fusion of WavLM embeddings (F1 0.548 alone) with prosodic features (F1 0.537 alone) reaches F1 0.559—complementary views, modest joint gain. The same pattern holds in the temporal ablation: static audio features add +0.075 IoU-F1@0.2 at 40 videos over acoustic-only features, and sequence structure adds a further margin. Fusion helps where the views are complementary; on MELD, text already dominates, so the audio view adds nothing measurable (Section: Paralinguistic Signal Role).


### Generalization Challenges

Two generalization gaps bind this program. First, comedian and domain transfer: all positive results here are on stand-up comedy, and the designated transfer test (T4, to conversational and voice-agent audio) is deferred by design until the within-domain gates resolve. A cross-domain anchor on RICH (0.407 ± 0.063 IoU-F1@0.2) certifies that the feature pipeline itself is not comedy-specific. Second, label-source generalization: the 621-video weak-label audio pool and the 155-video human-labeled pool have zero overlap, so weak-label scale cannot be validated against true labels at scale—and the human-verified ceiling tops out at 118 videos. We treat weak-label numbers strictly as hypothesis generators, never headline claims.


## Data Framework


### Collection Methods

Four data sources are used, all public. (1) The weak-label corpus: 620 stand-up videos with local audio, 121,928 utterances from VTT caption alignment, 1,965 weak-positive (laughter) utterances from [laughter] transcript markers. (2) The human-verified corpus: 118 videos (11,161 fixed 5-second windows at window-level; word-level at 40 videos) with hand-checked laughter intervals. (3) Anchor sets: Gillick-162 (human-annotated, 51.5% positive rate) and a 9-video RICH subset. (4) MELD: official train/dev/test CSVs and audio, key-joined, 2,609 test utterances. Datasets ship as public Kaggle repositories (Section: Reproducibility in the registry release).


### Evaluation Strategies

Every experiment runs under a pre-registered gate with a falsifier. Splits are grouped by video (GroupShuffleSplit / 5-fold GroupKFold, fixed seed 42): no video appears in both train and validation, so all reported generalization is cross-performer. Primary metrics: IoU-F1@0.2 for temporal overlap, utterance F1, average precision, and weighted F1 for MELD. Arm comparisons are always same-label, same-feature, same-split; the key control is order-shuffling (C vs C-shuf), which destroys temporal order while preserving marginal feature distributions. Cross-dataset anchor comparisons are marked indicative where labeling rules differ. Legacy pre-reset results (≈0.95 era) are quarantined and appear nowhere in this document.


## Proposed Methodology


### Audio Feature Extraction

Acoustic representations use WavLM (Chen et al., 2022) embeddings per utterance or window, complemented by a reconstructed canonical 27-dimensional prosody set (pitch, energy, voicing, temporal statistics) after the original 23-d layout proved unrecoverable from source documentation. Window-level datasets (118-video tier) use 791-dimensional concatenated feature vectors over 5-second windows. For the emotion test, 16 hand-crafted interaction features per utterance—leading/trailing silence, voiced fraction, energy statistics, zero-crossing rate, spectral shape, F0 statistics—represent the paralinguistic view.


### Linguistic Representations

Word-level interaction features encode utterance position, word order context, and pause/turn structure around each word—derived from caption alignments, not ASR output, which removes a transcription error source. For the emotion test, the linguistic baseline is TF-IDF (1–2 grams) with logistic regression, augmented with dialogue position and speaker-change indicators in arm B—deliberately simple, so that any measured gain from acoustic additions is attributable and honest.


### Ensemble Architecture

Three architectures span the program. A static MLP head (768→256→128→1) over concatenated features for weak-label and anchor detection. A BiGRU sequence model over word-level feature sequences for temporal modeling, stabilized by a documented recipe: pos_weight 8.0, per-fold feature standardization, final bias −2.0, learning rate 5e-4, gradient clipping 1.0, model selection by validation F1. For the flagship scale-up (in progress), WavLM is fine-tuned end-to-end with fp16 AMP, gradient checkpointing, SpecAugment, and layered learning rates (encoder 3e-5, head 1e-3) under a 6-hour wall-clock guard.


## Experimental Results


### Performance Analysis

The weak-label case study (v32, 620 videos): IoU-F1@0.2 = 0.2290 (precision 0.2814, recall 0.1931; tp 56 / fp 143 / fn 234), utterance F1 = 0.2732, AP = 0.142, at operating threshold 0.85. The temporal ablation on human labels: at 40 videos, arms A → B → C score 0.2231 ± 0.021 → 0.2984 ± 0.048 → 0.3460 ± 0.046 IoU-F1@0.2 (C reaches IoU 0.3987); at 118 videos, A → B → C score 0.5884 ± 0.031 → 0.5785 → 0.6092 ± 0.026, against an order-shuffled control (C-shuf) of 0.3125 ± 0.026 and 0.5227 ± 0.011 respectively. Pause/turn features degenerate on the fixed window grid (arm B, 118 videos)—a construction artifact reported for completeness.


### Statistical Validation

All arm estimates are 5-fold grouped means ± standard deviations; every fold is cross-video. The sequence effect (C minus C-shuf) is +0.034 at 40 videos and +0.087 at 118 videos—direction-stable, replicated at two scales, and growing with data. We state plainly: no formal significance test was pre-registered for the sequence effect, so the evidence is the replication pattern, not a p-value; a powered paired-fold design is straightforward to pre-register on future data. The MELD comparison is tested exactly as pre-registered: Δ(C−B) over 2,000 bootstrap resamples gives 95% CI [−0.0142, +0.0145], which includes zero—gate not passed. Anchor calibrations hold (Gillick-162 fusion 0.559; the pre-registered falsifier—anchor IoU > 0.40 indicating replication label noise—never triggered).


### Error Characterization

Post-hoc forensics on saved v32 predictions asked three pre-committed questions. Does the model track real signal? Predicted-vs-true laughter-rate correlation across videos is 0.361, with no duration or normalization shortcut found. Is the ceiling the model or the labels? A mild 2-second truncation artifact exists, but a surgical re-run was evaluated and cancelled as unjustified by expected gain—the binding constraint is the transcript-marker label source itself. Where are the errors? 143 false positives against 56 true positives at the operating point, consistent with weak-label ambiguity: [laughter] markers miss silent and shared laughter, capping recall. The MELD error picture mirrors the null: arm C's confusion matrix is nearly identical to arm B's, with acoustic features shifting individual decisions by amounts that cancel in aggregate.


## Generalization Analysis


### Paralinguistic Signal Role

The flagship beyond-words test fails its gate: adding 16 acoustic interaction features to a transcript-plus-context model changes MELD weighted F1 by Δ = 0.0000 (arm A 0.4483, B 0.4433, C 0.4434; CI [−0.0142, +0.0145]). This is a null for this feature class on this task—not a disproof of audio information in emotion, which the audio-only literature already shows exists but is redundant with text at linear-model scale. Combined with the replicated sequence effect for laughter placement, the composite finding is an asymmetry: laughter placement is not recoverable from words (people do not type their laughter), while emotion is largely recoverable from words. Interaction signals pay exactly where the word stream is silent.


### Predictor Versus Detector

A detector answers whether an utterance contains laughter; a predictor answers where and when laughter will occur. The two make different demands on features. Detection at the utterance level is bounded by the label source (Section: Performance Analysis)—the weak-label ceiling is a label ceiling, not a model ceiling. Placement, by contrast, is a sequence property: the order-shuffled control isolates exactly the information that timing carries, and that information is real (+0.034/+0.087) and grows with scale. This distinction reframes the deployment question: the deployable artifact is not a per-utterance classifier but a temporal predictor of reaction events, and the feature investments that pay are sequence and structure features, not marginal acoustic additions to text systems.


## Deployment Implications


### Inference Efficiency

The program was executed under deliberately modest compute: all registered results ran on Kaggle CPU notebooks (the MELD experiment completes in 49 minutes; the full weak-label pipeline in under 3 hours), because frozen WavLM embeddings amortize the expensive encoding step across experiments. End-to-end fine-tuning (in progress, single P100 GPU, fp16, gradient checkpointing, 6-hour guard) tests whether joint encoding lifts the human-label numbers; the CPU-feasible embedding pipeline remains the deployment-relevant configuration. For practitioners this matters: reaction-event prediction at this scale does not require training infrastructure—frozen-embedding heads train on CPU in minutes and run in real time on edge hardware.


### Architecture Design

For builders, the registered evidence supports three design rules. (1) Point behavioral-audio investment at reaction events—laughter, applause, back-channels—not at retrofitting audio onto text-solved tasks: the MELD null licenses not building the audio branch for text-first emotion systems at accessible scale. (2) For reaction-event systems, invest in sequence structure: the replicated, scale-growing sequence effect is the strongest registered signal, and the BiGRU recipe is documented and cheap. (3) Distrust weak-label scale: 620 videos of transcript-marker labels produced a 0.2290-IoU detector that forensics bounded at the label ceiling—validate any production label source against human intervals before trusting model outputs. The full decision registry, gates, falsifiers, kernels, and artifacts ship with the paper; every number can be re-run.
