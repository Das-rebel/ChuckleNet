# Decisions Map — Autonomous Laughter Prediction

> Comprehensive map of all decisions, assumptions, constraints, and experimental results.
> Generated: 2026-05-24 from 28 source documents across `docs/`.
> Mapped: **27 core decisions**, **18 assumptions**, **11 constraints**, **9 negative results**, **5 positive results**, **10 Orchestra gaps**.

---

## A. CORE DECISIONS (Research Direction)

### Decision D1: Text-Only XLM-R as Anchor Model
- **Decision**: XLM-R-Base word-level sequence labeling is the ONLY consistently strong signal. All other approaches (audio, biosemotic, multimodal) add noise or fail.
- **Alternatives considered**: Wav2Vec2/WavLM audio-only, biosemotic feature fusion, multimodal cross-attention, RL fine-tuning, teacher refinement
- **Rationale**: After 40+ experiments across audio prosody, biosemiotic features, WavLM fusion, and multimodal approaches, the ONLY consistently strong signal is text-only XLM-R (F1=0.819).
- **Evidence**: 
  - Biosemiotc features: +0.003 F1 (noise, with label leakage confirmed F1=0.829 from features alone)
  - F0/Energy/Pause acoustic: F1=0.20-0.27 (weak)
  - WavLM audio-only: F1=0.0 (failed)
  - Gated multimodal fusion: Gate→1.0, audio learns nothing (collapsed)
  - Teacher refinement: F1=0.078 (catastrophic)
  - XLM-R text-only: F1=0.819 (strong)
- **Orchestra assessment**: ALIGNED — ADR-001 explicitly documents this as the anchor.

### Decision D2: Span Reformulation as Primary Contribution
- **Decision**: The primary contribution is reformulating laughter prediction as a span detection task (like NER) rather than word-level sequence labeling.
- **Alternatives considered**: Word-level F1 as primary metric, sentence-level classification, clip-level binary
- **Rationale**: IoU-F1=0.880 vs word-F1=0.819 — a 6.1% gap that validates span-level prediction. 100% of laughter labels span 2+ words (100% multi-word confirmed, avg span=19.4 words). Literature (Gillick 2019) validates span-based audio detection (F1=0.89).
- **Evidence**: IoU-F1=0.880 >> word-F1=0.819 across all test sets. Multi-word spans are the norm. Purandare 2006 confirms laughter is supra-segmental (0.8s pauses).
- **Orchestra assessment**: ALIGNED — ADR-002 documents span reformulation as primary contribution.

### Decision D3: Utterance-Level, Not Word-Level, for Audio Fusion
- **Decision**: Audio analysis operates at utterance level (3-15s clips), NOT word level.
- **Alternatives considered**: Word-level audio features (F0, MFCC, pause per word), clip-level binary, frame-level
- **Rationale**: Laughter is a speaker behavior spanning 1-10+ seconds. Per-word acoustic features hit F1=0.29 ceiling because laughter is supra-segmental. Word-level analysis (0.3s windows) averages out signal. Literature (MultiLinguahah 2026) confirms audio humor detection F1=62-68% at utterance level.
- **Evidence**: Word-level audio: F1=0.20-0.27. Utterance-level audio: MultiLinguahah F1=0.68 (en) / F1=0.80 (hu). H6.1 F0 DROP test was at word-level (explains negligible Cohen's d=0.063).
- **Orchestra assessment**: ALIGNED — ADR-004 and ADR-011 document this pivot.

### Decision D4: Gated Fusion Over Cross-Attention
- **Decision**: Use gated fusion (`fused = g*t + (1-g)*a`) over cross-attention for multimodal fusion.
- **Alternatives considered**: Cross-attention (768×768 params), late fusion (ensemble), early fusion (concatenation)
- **Rationale**: Only 15K utterances available. Cross-attention has 768×768 = 589K parameters — overfitting risk. Gate has only 2×256×256 = 128K params.
- **Evidence**: ADR-005 documents gated fusion decision. ADR-007 documents gate collapse issue (gate_mean > 0.95 = always trusts text).
- **Orchestra assessment**: ALIGNED — ADR-005.

### Decision D5: Pre-Extract WavLM Embeddings to Disk
- **Decision**: Pre-extract all WavLM embeddings once, save to .pt file, before fusion training.
- **Alternatives considered**: On-the-fly WavLM inference during training, streaming embeddings
- **Rationale**: WavLM inference is expensive (forward pass per 10ms window). Running on-the-fly during training wastes GPU cycles. ~4.6GB for 15K utterances fits in storage.
- **Evidence**: ADR-006 documents ~2hr one-time Colab compute for 15K utterances. Gist provided: https://gist.github.com/Das-rebel/10b79eddcf2dce5ec4ff298ec3a46b0d
- **Orchestra assessment**: ALIGNED — ADR-006.

### Decision D6: Resume Capability for All Training Scripts
- **Decision**: All training scripts must support `--resume <checkpoint.pt>` flag.
- **Alternatives considered**: No resume (rerun from scratch), manual checkpoint management
- **Rationale**: Training runs take 4+ hours. Interruptions lose all progress. Incrementally append results to results.json.
- **Evidence**: ADR-008 documents checkpoint every epoch minimum requirement. AGENTS.md provides resume command for refine_weak_labels.
- **Orchestra assessment**: ALIGNED — ADR-008.

### Decision D7: Orchestra Research Two-Loop Methodology
- **Decision**: Adopt Orchestra Research methodology for all future experiments — research-state.yaml central tracking, protocol.md before experiments, inner/outer loop separation.
- **Alternatives considered**: Ad-hoc experimentation without protocol documentation, informal hypothesis tracking
- **Rationale**: Orchestra Research's AI-research-SKILLs (98 skills) provides a two-loop architecture (inner optimization + outer synthesis) that was NOT followed in early experiments, leading to undocumented decisions.
- **Evidence**: ADR-009 documents what was missed: no protocol.md before experiments, no research-state.yaml across sessions, no inner/outer loop separation. GAP_ANALYSIS_2026_05_13.md confirms "46 of 51 training scripts are dead code."
- **Orchestra assessment**: ALIGNED — ADR-009. Gap: research-state.yaml created 2026-05-24, still missing protocol.md per-hypothesis directories.

### Decision D8: Paper Strategy — ACL SRW First, Then Resource Paper
- **Decision**: Submit sequence: (1) ACL SRW 2-3 weeks, (2) LREC-COLING resource paper 2-3 weeks, (3) EMNLP weak supervision study 3-4 weeks.
- **Alternatives considered**: EMNLP Main, Interspeech, single-paper-all-findings
- **Rationale**: Orchestra review gave 2.75/6 (borderline reject). ACL SRW has lower bar for honest student work. StandUp4AI is critical missing comparison. Resource papers have high acceptance probability. 733K segments is genuinely unique.
- **Evidence**: ORCHESTRA_ALL_4_PAPERS_REVIEW.md scores Paper 3 at 2.75/6. ENSEMBLE_FINAL_STRATEGY.md ranks ACL SRW #1 priority. ADR-010 documents submission sequence.
- **Orchestra assessment**: ALIGNED — ADR-010.

### Decision D9: Do NOT Trust LLM-Generated Labels for Supervision
- **Decision**: LLM-generated labels for supervision are untrustworthy without human verification.
- **Alternatives considered**: Use LLM-refined labels as ground truth, synthetic biosemiotc feature generation, automated label refinement
- **Rationale**: Teacher refinement (Qwen2.5-coder:1.5b) on 520 refined labels → F1=0.078 (catastrophic failure). Biosemiotc features achieved F1=0.829 from features alone (label leakage). LLMs hallucinate labels when given task framing.
- **Evidence**: H4.4 confirmed F1=0.829 from biosemiotc features alone (no text). Teacher refinement F1=0.078. ADR-012 documents this decision.
- **Orchestra assessment**: ALIGNED — ADR-012.

### Decision D10: Per-Video Split for Evaluation
- **Decision**: All final evaluations use per-video splits. Random split reported as upper bound.
- **Alternatives considered**: Random cross-video split, per-comedian split, temporal split
- **Rationale**: Random split inflates F1 by ~1.9% vs per-show split due to comedian-style leakage. Below 3% threshold but real.
- **Evidence**: H4.5 results — Random split F1=0.218, per-show split F1=0.199. Gap = 1.9%. ADR-013 documents this.
- **Orchestra assessment**: ALIGNED — ADR-013.

### Decision D11: Cross-Lingual Transfer Degradation Is the Real Challenge
- **Decision**: Prioritize cross-lingual transfer research over audio for the next phase.
- **Alternatives considered**: Audio-first research, audio+text fusion, more English data
- **Rationale**: English F1=0.819, Chinese F1=0.752 (-7%), Hindi F1=0.68 (-14% with only 48 examples). This ~14% drop EN→HI is the fundamental unsolved challenge. Audio (F1=0.20) is far below text (F1=0.82) even for English.
- **Evidence**: Paper draft shows EN F1=0.819, ZH F1=0.752, HI F1=0.68. ADR-014 documents this priority shift.
- **Orchestra assessment**: ALIGNED — ADR-014.

### Decision D12: Negative Results Are Publishable
- **Decision**: Compile negative results into a publishable ArXiv preprint + EMNLP workshop paper.
- **Alternatives considered**: Suppress negative results, spin failures as future work, single paper covering all
- **Rationale**: Three genuine negative results: (1) Teacher refinement fails F1=0.078, (2) Biosemiotc features add +0.003 (noise with leakage), (3) Audio prosody adds +0.05 at word-level (negligible). Negative results are citeable and establish scientific honesty.
- **Evidence**: ENSEMBLE_FINAL_STRATEGY.md and ADR-015 document this decision. "Weak Signals" paper pitched as quick ArXiv submission.
- **Orchestra assessment**: ALIGNED — ADR-015.

### Decision D13: WavLM-Base+ Over Wav2Vec2-Base
- **Decision**: Switch audio encoder from Wav2Vec2-Base to WavLM-Base+ (microsoft/wavlm-base-plus).
- **Alternatives considered**: Wav2Vec2-Base, HuBERT-Base, XLSR-53, Whisper encoder, Data2Vec-Audio
- **Rationale**: Same size (95M params, 768-dim), +4.7% on SUPERB emotion benchmarks, denoising pretraining handles noisy comedy audio, drop-in replacement. Wav2Vec2 was baseline (363MB cached); WavLM downloads 360MB.
- **Evidence**: MODEL_SELECTION.md documents +4.7% on IEMOCAP emotion (65.6→70.3), +13.3% on VoxCeleb speaker ID. Denoising pretraining directly relevant to overlapping audience laughter audio.
- **Orchestra assessment**: ALIGNED — documented in EXECUTION_PLAN_10M.md.

### Decision D14: Utterance-Level Realignment (PRD v5.0 Pivot)
- **Decision**: Pivot from word-level (±5s window) to utterance-level (VTT utterance overlap) for label assignment.
- **Alternatives considered**: Keep word-level labeling, use fixed window sizes, sentence-level grouping
- **Rationale**: 91.1% of positive labels are in spans >10 words (median=16). TF-IDF F1=0.08 at word level confirms word-level classification is inappropriate. Function words are equally distributed (χ²=2.2, p=0.14) — the problem is window granularity, not function words. Audio features are negligible at word level (Cohen's d=0.15) but literature predicts strong signal at utterance level.
- **Evidence**: PRD_V5_AUDIO_FIRST.md documents complete paradigm shift from word-level to utterance-level. GAP_ANALYSIS_2026_05_13.md confirms "word-level labels are fundamentally broken."
- **Orchestra assessment**: ALIGNED — PRD v5.0 explicitly replaces PRD v4.0.

### Decision D15: 10M Segment Pipeline Superseded
- **Decision**: PRD v4.0 (10M audio segments pipeline) is superseded by PRD v5.0 (utterance-level audio-first).
- **Alternatives considered**: Execute PRD v4.0 as planned, hybrid approach
- **Rationale**: 10M pipeline required Windows GPU (not available), Colab T4 (too slow), and assumed word-level labeling was valid. After validation (Statcheck + Deepchecks + Jenni Peer Review), word-level labels are fundamentally broken.
- **Evidence**: PRD_V4_10M_PIPELINE.md is dated 2026-05-09. PRD_V5_AUDIO_FIRST.md (2026-05-18) explicitly states "replaces PRD v4.0." GAP_ANALYSIS_2026_05_13.md: "All 10 tasks in tasks_10m_pipeline.json are status: pending."
- **Orchestra assessment**: ALIGNED — v4.0 never executed, superseded by v5.0 paradigm shift.

### Decision D16: No Synthetic Data Generation
- **Decision**: Do NOT generate more synthetic Hindi/Hinglish data.
- **Alternatives considered**: Generate 3,000+ synthetic Hindi examples via LLM, use synthetic for training, augment with synthetic
- **Rationale**: 85% of merged_final is already synthetic. Synthetic data has label leakage risk (confirmed in H4.4). LLM-generated labels are untrustworthy (Decision D9). Hindi data should be collected from real sources.
- **Evidence**: GAP_ANALYSIS_2026_05_13.md: "85% of merged_final already synthetic." MULTILINGUAL_DATA_COLLECTION_PLAN.md target was 4,000 examples but only 48 collected. HINDI_SCALING_STRATEGY.md and HINDI_SCALING_AUTOMATED.md were never fully executed.
- **Orchestra assessment**: ALIGNED — GAP_ANALYSIS_2026_05_13.md explicitly lists "do NOT generate more synthetic data" in anti-actions.

### Decision D17: No Energy Threshold Audio Detection
- **Decision**: Energy threshold detection fails on studio recordings — do not use as primary audio detection method.
- **Alternatives considered**: Energy threshold for laugh track detection, amplitude-based segmentation, VAD-based pause detection
- **Rationale**: Energy threshold detection fails on professional comedy audio where audience laughter is mixed cleanly with dialogue and does not produce energy spikes. Studio recordings have clean audio with no laugh track energy signature.
- **Evidence**: EXECUTION_PLAN_10M.md explicitly lists "Energy threshold audio detection — fails on studio recordings" in "what to avoid." GAP_ANALYSIS_2026_05_13.md: "Energy threshold detection fails on studio recordings with clean audio."
- **Orchestra assessment**: ALIGNED — confirmed failed in practice.

### Decision D18: StandUp4AI Comparison Is Non-Negotiable
- **Decision**: Any paper submission MUST include comparison against StandUp4AI (Barrière et al., 2025).
- **Alternatives considered**: Compare only against MHD (sitcom), compare only against UR-FUNNY (TED talks), no external comparison
- **Rationale**: Orchestra ML-paper-writing review flagged StandUp4AI as the #1 critical missing reference. StandUp4AI is the most directly competing work. Not comparing against it undermines paper credibility.
- **Evidence**: ORCHESTRA_RESEARCH_REVIEW.md: "StandUp4AI (2025) is the most critical missing reference." ORCHESTRA_ALL_4_PAPERS_REVIEW.md: "Missing: StandUp4AI, FunnyNet-W, M2H2."
- **Orchestra assessment**: ALIGNED — H4.6 confirmed TF-IDF F1=0.73 on StandUp4AI 4-CSV subset.

### Decision D19: IoU-F1 as Co-Primary Metric
- **Decision**: Report BOTH word-level F1 AND IoU-F1 (span-level) as co-primary metrics.
- **Alternatives considered**: Report only word-level F1, report only IoU-F1, report IoU-F1 as primary
- **Rationale**: IoU-F1=0.880 vs word-F1=0.819 represents a 6.1% gap that is not captured by word-level metrics alone. The span gap is a genuine finding, not an artifact. Both metrics are needed to tell the full story.
- **Evidence**: Paper draft reports "F1=0.819, IoU-F1=0.880" as key results. ENSEMBLE_FINAL_STRATEGY.md: "IoU-F1=0.880 vs word-F1=0.819 — 6.1% gap validates span detection reformulation."
- **Orchestra assessment**: ALIGNED — ADR-002.

### Decision D20: pos_weight=5.0 Is Optimal
- **Decision**: Use positive class weight of 5.0 for class imbalance.
- **Alternatives considered**: pos_weight=3.0, 4.0, 6.0, no class weighting, focal loss
- **Rationale**: Ablation shows pos_weight=5.0 is optimal: val F1=0.785, test F1=0.819. Lower values (3.0, 4.0) underperform. Value of 6.0 begins to over-weight positive class, degrading precision.
- **Evidence**: Paper draft Table 4: pos_weight=3.0 (val=0.772), pos_weight=4.0 (val=0.778), pos_weight=5.0 (val=0.785), pos_weight=6.0 (val=0.780).
- **Orchestra assessment**: ALIGNED — documented in paper ablation.

### Decision D21: XLM-R Unfreeze Last 4 Layers
- **Decision**: Freeze first 8 layers, fine-tune last 4 layers of XLM-R.
- **Alternatives considered**: Freeze all (frozen backbone), unfreeze all, unfreeze last 2 layers, unfreeze last 6 layers
- **Rationale**: Balance between pretrained language knowledge preservation and task-specific adaptation. Last 4 layers are most task-specific. Full unfine-tuning risks catastrophic forgetting of multilingual representations.
- **Evidence**: Paper draft Section 4.3: "fine-tune last 4 transformer layers while freezing the first 8." Memory confirmed architecture with 12 total layers.
- **Orchestra assessment**: ALIGNED — no contrary evidence found.

### Decision D22: Auxiliary Biosemiotc Heads with Weight=0.3
- **Decision**: Use auxiliary biosemiotc heads with weight 0.3 for multi-task learning.
- **Alternatives considered**: No auxiliary heads (aux=0.0), aux=0.1, aux=0.5, aux=1.0
- **Rationale**: aux=0.3 provides best validation F1=0.785. Multi-task supervision provides marginal but consistent benefit. Note: biosemiotc features themselves contain label leakage (H4.4), but the auxiliary loss structure is sound.
- **Evidence**: Paper draft Table 5: aux=0.0 (val=0.782), aux=0.1 (val=0.784), aux=0.3 (val=0.785), aux=0.5 (val=0.783).
- **Orchestra assessment**: ALIGNED — ablation results documented. Note: features invalidated by H4.4, but aux weight optimization was done on original data.

### Decision D23: Label Smoothing=0.1
- **Decision**: Use label smoothing of 0.1 in training.
- **Alternatives considered**: No label smoothing, label smoothing=0.05, label smoothing=0.2
- **Rationale**: Label smoothing prevents overconfident predictions. Value of 0.1 is standard in NLP practice.
- **Evidence**: Paper draft Section 4.2: "We use label smoothing with ε=0.1."
- **Orchestra assessment**: ALIGNED — standard NLP practice, no counter-evidence.

### Decision D24: Single NVIDIA Tesla T4 GPU Training
- **Decision**: Train on single NVIDIA Tesla T4 GPU (16GB memory).
- **Alternatives considered**: Multi-GPU training, CPU-only training, A100, RTX 4090
- **Rationale**: Colab T4 is the available compute. Single T4 fits the model (batch_size=12, max_seq_len=256). Training time ~29 min/epoch.
- **Evidence**: Paper draft Section 4.3: "Training on a single NVIDIA Tesla T4 GPU (16GB memory)." GAP_ANALYSIS_2026_05_13.md confirms no local GPU available.
- **Orchestra assessment**: ALIGNED — confirmed compute constraint.

### Decision D25: No RL Fine-Tuning in Current Paper
- **Decision**: Remove or clearly label RL section as proposed, not validated.
- **Alternatives considered**: Include full RL methodology, run RL experiments, claim RL results
- **Rationale**: RL framework described in Section 4.4 of paper draft is entirely proposed, not validated. Orchestra review gave 2.75/6. Including speculative methodology weakens the paper.
- **Evidence**: ORCHESTRA_RESEARCH_REVIEW.md: "RL section is entirely proposed, not validated — half the methodology section describes work not done." Paper draft acknowledges "RL framework described in this section is proposed and has not yet been experimentally validated."
- **Orchestra assessment**: ALIGNED — must remove or clearly label RL as proposed.

### Decision D26: Only 3 Languages With Real Data
- **Decision**: Claim multilingual results only for English, Chinese, and Hindi/Hinglish (not 100+ languages).
- **Alternatives considered**: Claim 100+ language coverage, claim 6-7 languages (StandUp4AI set), limit to English only
- **Rationale**: Only 3 languages have real training data: English (74%), Chinese (26%), Hindi (0.5%). All other language data either doesn't exist or is synthetic. Paper draft honest claims box documents this.
- **Evidence**: Paper draft: "We evaluate on three languages (English, Chinese, Hindi/Hinglish), not 100+." RESEARCH_LIMITATIONS.md: "3 languages vs 100+ claimed."
- **Orchestra assessment**: ALIGNED — honest claims box in paper draft explicitly limits to 3 languages.

### Decision D27: 2 Languages With Meaningful Test Sets
- **Decision**: Only English and Chinese have proper test sets. Hindi test set is too small (48 examples) for reliable metrics.
- **Alternatives considered**: Include Hindi test F1 as primary result, report Hindi as validated baseline
- **Rationale**: Hindi has only 48 manually annotated examples. F1=0.68 on Hindi is preliminary and statistically meaningless. English and Chinese have proper splits (3,000+ and 1,000+ test examples respectively).
- **Evidence**: Paper draft: "Hindi F1=0.68 based on 48-example manually annotated set, with cross-lingual transfer from English model. This is a preliminary baseline; the small dataset size limits the reliability of this estimate."
- **Orchestra assessment**: ALIGNED — paper draft explicitly warns about Hindi estimate reliability.

---

## B. ARCHITECTURE DECISIONS

### Architecture A1: XLM-R-Base Text Backbone
- **Decision**: Use `FacebookAI/xlm-roberta-base` as text encoder (278M params, 768-dim hidden).
- **Alternatives considered**: mBERT, XLM-R-Large, DeBERTa, IndicBERT
- **Rationale**: Proven at F1=0.819 on our data. Strong cross-lingual transfer. HuggingFace standard. XLM-R-Large (560M) too large for marginal gain.
- **Evidence**: Paper draft uses "XLM-RoBERTa-base." AGENTS.md: "Promoted current winner: weak-label XLM-R with positive_class_weight=5.0."
- **Status**: ✅ Cached (1GB), proven.

### Architecture A2: WavLM-Base+ Audio Encoder (Switched from Wav2Vec2)
- **Decision**: Use `microsoft/wavlm-base-plus` as audio encoder (95M params, 768-dim hidden).
- **Alternatives considered**: Wav2Vec2-Base (original), HuBERT-Base, XLSR-53
- **Rationale**: Same size as Wav2Vec2-Base, +4.7% on emotion benchmarks, denoising pretraining. Drop-in replacement.
- **Evidence**: MODEL_SELECTION.md documents switch. EXECUTION_PLAN_10M.md: "WavLM-Base+ for audio encoder — superior to Wav2Vec2 on paralinguistic tasks, denoising pretraining helps with noisy comedy audio."
- **Status**: ✅ Downloaded (360MB).

### Architecture A3: Gated Multimodal Fusion Architecture
- **Decision**: Architecture: Text branch (XLM-R 768→256) + Audio branch (WavLM 768→256) with gated fusion → CrossAttention (4 layers) → classifier (512→256→2).
- **Alternatives considered**: Cross-attention only, concatenation only, ensemble
- **Rationale**: Total params ~470M fits in 16GB VRAM with fp16 + gradient checkpointing. Gate prevents audio from learning nothing.
- **Evidence**: MODEL_SELECTION.md: "CrossAttention([text_emb, audio_emb]) — 4 layers." EXECUTION_PLAN_10M.md fusion architecture described.
- **Status**: ⚠️ Phase 1 text-only running, audio branch pending.

### Architecture A4: eGeMAPS 88 + Prosodic + Spectral + WavLM Feature Set
- **Decision**: Utterance-level audio features = eGeMAPS 88 features (openSMILE) + prosodic 5 features (F0, pause, speech rate) + voice quality 3 features (HNR, jitter, shimmer) + spectral 42 features + energy 4 features + WavLM 768 embeddings = 910 features total.
- **Alternatives considered**: MFCC-only (120-dim), Wav2Vec2 embeddings only, spectrogram only
- **Rationale**: PRD v5.0 expanded feature set from MFCC-only to comprehensive acoustic suite based on Jenni peer review. HNR enables Duchenne vs social laughter classification (novel contribution angle).
- **Evidence**: PRD_V5_AUDIO_FIRST.md Table in Section 4.1. ACOUSTIC_PIPELINE_STATUS: "eGeMAPS 88 features via openSMILE (installed), 543 min audio across 5 comedians."
- **Status**: ⚠️ Feature extraction pipeline created and tested (extract_prosody_v1.py), not yet run on all files.

### Architecture A5: 3-Language Target (en, zh, hi-latn)
- **Decision**: Target 3 languages: English (1,500 videos), Chinese (1,000 videos), Hindi/Hinglish (1,200 videos) = 1,640 videos.
- **Alternatives considered**: Add Bengali, French, Spanish (from StandUp4AI), 100+ languages
- **Rationale**: These 3 languages cover the primary comedy markets. Chinese has lower words-per-video yield (~6K vs 8K for EN) so needs more videos. Additional languages add complexity without proportional benefit.
- **Evidence**: PRD_V4_10M_PIPELINE.md Table: "English (417 videos target 3.3M words), Chinese (556 videos), Hindi (667 videos)." Later refined to 1,640 videos total.
- **Status**: ⚠️ Never executed (PRD v4.0 superseded).

### Architecture A6: GDrive + rclone Storage Architecture
- **Decision**: Audio files + alignment metadata stored on GDrive (~135GB total), accessed via rclone from local/Colab.
- **Alternatives considered**: Local SSD only, AWS S3, HuggingFace datasets
- **Rationale**: 5TB GDrive available, existing OAuth from Chrome extension, shared between local and Colab. ~135GB / 4,630GB free.
- **Evidence**: PRD_V4_10M_PIPELINE.md storage architecture. EXECUTION_PLAN_10M.md: "rclone config gdrive: (use existing OAuth from Chrome extension)."
- **Status**: ✅ 172 files, 2.12 GB on GDrive. No model files uploaded.

### Architecture A7: faster-whisper tiny for Transcription
- **Decision**: Use `faster-whisper tiny` for Whisper transcription (130x realtime on RTX 4090).
- **Alternatives considered**: faster-whisper base (slower but more accurate), Whisper large-v2, Whisper medium
- **Rationale**: tiny is 39M params vs base 74M or large 155M. Speed >> accuracy for word timestamps. On RTX 4090: ~130x realtime. Base is only 2x slower but 5% better — "still worth it on 4090" per PRD.
- **Evidence**: PRD_V4_10M_PIPELINE.md: "faster-whisper tiny for speed, Wav2Vec2-base for audio encoder." EXECUTION_PLAN_10M.md: "base + RTX 4090: 100x realtime → 12.3 hrs for 3,700 videos."
- **Status**: ✅ Script created (whisper_batch_gdrive.py).

### Architecture A8: VTT [laughter] Marker Alignment
- **Decision**: Use VTT [laughter]/[applause] markers as ground truth, aligned to Whisper timestamps with ±5s window.
- **Alternatives considered**: Manual annotation, crowd-sourced labels, audio-only detection, pause-based detection
- **Rationale**: VTT markers are freely available, cover all YouTube videos with subtitles, provide weak supervision without manual labeling. ±5s window captures audience reaction lag.
- **Evidence**: EXECUTION_PLAN_10M.md: "Laughter markers: [laughter], [laughing], [applause], (audience laughing), [笑声], [鼓掌]." PRD_V4_10M_PIPELINE.md: "Word labeled as laugh if: (a) falls within laughter event interval, (b) within 5s before a laughter event, (c) 2 words before trigger."
- **Status**: ✅ Validated on 733K segments. ISSUE: 91.1% of labels are in spans >10 words (median=16) — fundamental label granularity problem.

### Architecture A9: ChuckleNet Project Name
- **Decision**: Project named "ChuckleNet" (not TMLPD-related).
- **Alternatives considered**: StandUp Laughter, LaughterNet, AudioComedy
- **Rationale**: Historical choice, GitHub repo at github.com/Das-rebel/ChuckleNet. Memory confirms: "chucklenet = autonomous laughter prediction project."
- **Evidence**: GitHub repo `github.com/Das-rebel/ChuckleNet`. Separate from `adaptive-memory-multi-model-router` (TMLPD project).
- **Status**: ✅ Active.

### Architecture A10: 4-Script Canonical Pipeline
- **Decision**: Canonical pipeline is exactly 4 scripts (not 51 training scripts): convert_standup_raw_to_word_level.py → refine_weak_labels_nemotron.py → xlmr_standup_word_level.py → run_xlmr_standup_pipeline.py.
- **Alternatives considered**: Use any of the 51 training scripts, full pipeline with audio
- **Rationale**: GAP_ANALYSIS_2026_05_13.md confirms "46 of 51 training scripts are dead code." Only 2-3 scripts actively used. Canonical path documented in AGENTS.md.
- **Evidence**: AGENTS.md: "canonical path: convert → refine → xlmr → run." GAP_ANALYSIS: "train.py (552 lines) confirmed NOT working."
- **Status**: ⚠️ Refine script broken (produces 0% laughter), others working.

### Architecture A11: Word-Level Sequence Labeling (Not Sentence-Level)
- **Decision**: Task is word-level sequence labeling (BIO-style), not sentence-level classification.
- **Alternatives considered**: Sentence-level binary (laugh/no-laugh per sentence), clip-level binary, span-level detection
- **Rationale**: Word-level enables precise laughter trigger identification. Sentence-level loses timing information. IoU-F1 validates span-level formulation as better metric.
- **Evidence**: Paper draft title: "Word-Level Laughter Prediction in Multilingual Stand-up Comedy: A Sequence Labeling Approach." ENSEMBLE_FINAL_STRATEGY.md: "Word vs Span: Rethinking Laughter Prediction Metrics."
- **Status**: ✅ Working (F1=0.819 word-level).

### Architecture A12: BioSemiotic Features (Now Invalidated)
- **Decision**: Originally: integrate 32-dim biosemiotc features (Duchenne 4 + Incongruity 3 + ToM 4 + Cue 7 + Structural 3 + Linguistic 4 + Metadata 6) with XLM-R.
- **Alternatives considered**: Text-only (no biosemiotc), different feature groups, learned features
- **Rationale**: Originally claimed: biosemiotc features operationalize humor theory (Duchenne, incongruity-resolution, ToM) and improve F1. ToM features showed largest individual contribution (+0.002 val F1).
- **Evidence**: Paper draft Section 4.1 documents 32-dim biosemiotc features. Table 3: Full model (all 32 dims, aux=0.3) → val F1=0.785 vs baseline 0.782 (+0.003).
- **Status**: 🔴 INVALIDATED — H4.4 confirmed F1=0.829 from biosemiotc features ALONE (no text). Label leakage. All ablation results using these features are invalid.

### Architecture A13: Positive Class Weight=5.0
- **Decision**: Use CrossEntropyLoss with pos_weight=5.0 for class imbalance (~37% laughter rate).
- **Alternatives considered**: pos_weight=3.0, 4.0, 6.0, focal loss, class-balanced loss
- **Rationale**: 37% laughter rate means ~1.7:1 imbalance (not extreme). pos_weight=5.0 is optimal per ablation (val F1=0.785).
- **Evidence**: Paper draft Section 4.2: "α=5.0 is the positive class weight (validated through ablation)." AGENTS.md: "Pos_weight capped at 5.0 for class imbalance."
- **Status**: ✅ Validated.

### Architecture A14: Linear Warmup Schedule (500 Warmup Steps)
- **Decision**: Learning rate follows linear warmup with 500 warmup steps, then linear decay.
- **Alternatives considered**: Cosine schedule, constant LR, step decay
- **Rationale**: Standard HuggingFace default. 500 warmup steps is conservative for our dataset size.
- **Evidence**: Paper draft Section 4.3: "500 warmup steps, reaching a peak of 2×10⁻⁵, then decaying linearly."
- **Status**: ✅ Standard practice.

### Architecture A15: AdamW Optimizer with Weight Decay=0.02
- **Decision**: Use AdamW optimizer with weight decay 0.02.
- **Alternatives considered**: SGD with momentum, Adam, RAdam
- **Rationale**: Standard for transformer fine-tuning. Weight decay provides regularization.
- **Evidence**: Paper draft Section 4.3: "AdamW optimizer with weight decay 0.02."
- **Status**: ✅ Standard practice.

---

## C. ASSUMPTIONS

### Assumption A1: VTT [laughter] Markers Reflect Real Audience Laughter
- **Assumption**: The [laughter] markers in YouTube auto-generated subtitles accurately indicate when audience members laughed.
- **Evidence for**: YouTube uses speech recognition + audio analysis to detect laughter. Markers are consistent across multiple videos from same comedian. StandUp4AI uses same labeling approach.
- **Evidence against**: YouTube's speech recognition may misalign by ±5s. Studio recordings may have mixed audio that confuses detection. Jenni peer review suggests ~15% label offset.
- **Test status**: Tested — word-level TF-IDF F1=0.08 confirms labels are noisy, but XLM-R F1=0.819 shows text still captures signal.
- **Risk if wrong**: HIGH — if VTT markers are random, our entire training signal is noise. Paper claims rest on this assumption.

### Assumption A2: Word-Level Labels Mean "This Word Triggered Laughter"
- **Assumption**: A word labeled `label=1` means "this specific word caused the audience to laugh."
- **Evidence for**: Standard weak supervision formulation. Used successfully in StandUp4AI and UR-FUNNY.
- **Evidence against**: 91.1% of positive labels are in spans >10 words (median=16). ±5s window means label actually means "within earshot of laughter." Function words equally distributed in both classes (χ²=2.2, p=0.14).
- **Test status**: Tested — function word analysis shows equal distribution, proving labels don't mean "trigger word."
- **Risk if wrong**: HIGH — if labels mean "near laughter" not "causes laughter," our evaluation metrics are inflated and task formulation is wrong.

### Assumption A3: XLM-R Learns Laughter Patterns, Not Subtitle Alignment Noise
- **Assumption**: XLM-R F1=0.819 reflects genuine humor detection capability, not just learning to predict which function words appear near subtitle markers.
- **Evidence for**: XLM-R achieves high F1 on held-out test data. IoU-F1=0.880 shows model captures span structure. Model generalizes across comedians.
- **Evidence against**: 54% of positive labels are function words. TF-IDF F1=0.08 at word level. When function words are removed, F1 drops significantly. Paper draft acknowledges "function words equally distributed."
- **Test status**: Untested — no ablation removing function words from training.
- **Risk if wrong**: MEDIUM — if model only learns function-word proximity, our F1 metric is measuring subtitle alignment artifacts.

### Assumption A4: Pause Duration Indicates Punchline Timing
- **Assumption**: Longer pauses before a word indicate punchline delivery, triggering audience laughter (Purandare 2006: 0.8s vs 0.3s gap).
- **Evidence for**: Purandare 2006 shows 0.8s vs 0.3s pause gap (Cohen's d≈0.8-1.2). Our H1.1 shows long pauses (>1s) have 2× laughter rate (23.8% vs 12.4%).
- **Evidence against**: Our subtitle-level data shows Cohen's d=0.13 — ~5× smaller than literature. YouTube subtitle timestamps are too coarse (median pause=0.0s for both classes).
- **Test status**: Tested (H1.1) — effect exists but 5× smaller than literature due to coarse timestamps.
- **Risk if wrong**: MEDIUM — pause is a real signal but invisible at our precision level. Need librosa on actual WAV files.

### Assumption A5: F0 DROP at Punchline (Pickering 2009)
- **Assumption**: Laughter-context words have lower F0 (pitch) than non-laugh words at punchlines.
- **Evidence for**: Pickering et al. 2009, Attardo & Meziani 2009 report F0 DROP (not rise) at punchlines. Bertero 2016: F0 range wider at punchlines.
- **Evidence against**: H6.1 results show 5 Hz difference (Cohen's d=0.063, negligible). Studio editing averages out prosody. Only 68 laughter clips in initial sample.
- **Test status**: Tested (H6.1, Session 4) — effect is real (p<10⁻⁶) but negligible (d=0.063). Distributions overlap 98%.
- **Risk if wrong**: MEDIUM — F0 DROP is real but impractical for classification due to overlap.

### Assumption A6: Audio Features Will Work at Utterance Level
- **Assumption**: Audio features (eGeMAPS, WavLM) will achieve meaningful F1 at utterance level, even though they fail at word level.
- **Evidence for**: MultiLinguahah (2026) achieves F1=0.68 on US English at utterance level. Literature predicts d≥0.5 at utterance level (Bachorowski 2001). PRD v5.0 explicitly pivots to utterance-level.
- **Evidence against**: Studio recordings average out prosody. WavLM extraction has never succeeded (Colab GPU needed). Audio-only has never been trained successfully.
- **Test status**: Untested at utterance level — word-level only tested.
- **Risk if wrong**: HIGH — if audio also fails at utterance level, the entire PRD v5.0 paradigm shift is invalid.

### Assumption A7: Cross-Lingual Transfer Degrades Because of Semantic Gaps
- **Assumption**: EN→ZH (-7%) and EN→HI (-14%) performance drops are due to semantic/cultural humor differences, not tokenization or data quality.
- **Evidence for**: Chinese-specific humor (tonal puns, wordplay) not captured by English-pretrained XLM-R. Hindi/Hinglish code-mixing not well-represented.
- **Evidence against**: Chinese data is smaller (26% vs 74%). Hindi has only 48 examples. Small data could explain degradation, not semantic gaps.
- **Test status**: Untested — cannot separate data size effect from semantic gap.
- **Risk if wrong**: MEDIUM — if it's just data size, collecting more Hindi data solves the problem.

### Assumption A8: Synthetic Hindi Data Would Be Useful for Training
- **Assumption**: LLM-generated Hindi/Hinglish comedy examples would add useful training signal.
- **Evidence for**: DATA_COLLECTION_STRATEGY_V10.md planned 4,000 synthetic Hindi examples. HINDI_SCALING_STRATEGY.md outlined generation via LLM with comedian-style prompts.
- **Evidence against**: H4.4 proved LLM-generated features contain label leakage. Teacher refinement (LLM labels) failed catastrophically (F1=0.078). GAP_ANALYSIS: "85% of merged_final already synthetic."
- **Test status**: Not tested for Hindi specifically. H4.4 showed generic LLM generation risk.
- **Risk if wrong**: MEDIUM — adding more synthetic Hindi data could introduce label leakage or cultural artifacts.

### Assumption A9: IoU-F1=0.880 Is a Genuine Improvement, Not an Artifact
- **Assumption**: The 6.1% gap between IoU-F1 (0.880) and word-F1 (0.819) reflects genuine span-level prediction quality, not metric manipulation.
- **Evidence for**: IoU-F1 is a stricter metric requiring boundary agreement. Span structure is validated by literature (Gillick 2019). Gap is consistent across languages.
- **Evidence against**: If labels are spans by construction (±5s window), IoU-F1 might just be measuring how well the model reproduces the window boundaries, not actual humor detection.
- **Test status**: Untested — no human baseline for IoU-F1.
- **Risk if wrong**: LOW — the gap is real and meaningful even if partially artifact.

### Assumption A10: 73K Aligned Segments Is Sufficient Data
- **Assumption**: 733K word-level segments from 26-49 videos is enough to train a generalizable laughter prediction model.
- **Evidence for**: XLM-R achieves F1=0.819 on this data. Per-video split avoids leakage. 733K segments is larger than most humor detection datasets.
- **Evidence against**: 26-49 videos is a tiny sample of comedy diversity. 13.2% positive rate means only ~97K positive examples. Performance may not generalize to new comedians.
- **Test status**: Validated — model generalizes to held-out test set, but test set may not represent real comedy diversity.
- **Risk if wrong**: MEDIUM — model may overfit to watched comedians' styles.

### Assumption A11: Same Video Across Train/Val/Test Is Leakage
- **Assumption**: Having the same video in both train and val/test splits causes data leakage that inflates metrics.
- **Evidence for**: H4.5 shows 1.9% gap between random split (0.218) and per-show split (0.199). Comedian style patterns learned in training transfer to test.
- **Evidence against**: Comedy is highly formulaic — same setups, same structures. Leakage may reflect genuine skill transfer, not data contamination.
- **Test status**: Tested (H4.5) — gap exists but below 3% significance threshold.
- **Risk if wrong**: LOW — per-show split is the conservative, correct approach.

### Assumption A12: Biosemiotc Features Encode Humor Theory Signal
- **Assumption**: Biosemiotc features (Duchenne markers, incongruity scores, ToM inference) capture genuine humor mechanisms from text.
- **Evidence for**: ToM features showed +0.002 val F1 improvement. Literature validates Duchenne laughter markers, incongruity-resolution theory.
- **Evidence against**: H4.4 proves these features achieve F1=0.829 from features ALONE (no text). This is impossible without label leakage — the LLM that generated features encoded the answer.
- **Test status**: Tested and INVALIDATED (H4.4). LLM-generated features cheat.
- **Risk if wrong**: HIGH — all biosemiotc ablation results are invalid.

### Assumption A13: Teacher Refinement Would Improve Labels
- **Assumption**: Using Qwen2.5-coder:1.5b to refine weak labels would produce cleaner training supervision.
- **Evidence for**: LLM has world knowledge about humor. Could identify actual punchlines vs setup words. Nemotron/openchat style refinement works for other tasks.
- **Evidence against**: Teacher refinement produced F1=0.078 (catastrophic). Parsing bug caused 0% laughter detected. LLM labels don't match human judgment.
- **Test status**: Tested and FAILED — disabled after F1=0.078.
- **Risk if wrong**: N/A — approach abandoned.

### Assumption A14: StandUp4AI Comparison Will Validate Our Approach
- **Assumption**: Running our model on StandUp4AI's 4 labeled CSVs will produce comparable results, validating our approach.
- **Evidence for**: StandUp4AI uses same VTT [laughter] labeling approach. H4.6 shows TF-IDF F1=0.73 on the 4 CSVs (vs 0.25 random baseline). Signal is present.
- **Evidence against**: StandUp4AI labels may have different quality/precision. Different video selection could produce different results. We haven't run XLM-R on StandUp4AI yet.
- **Test status**: Partially tested — TF-IDF works, XLM-R not yet run.
- **Risk if wrong**: MEDIUM — if XLM-R underperforms on StandUp4AI, our approach may not generalize.

### Assumption A15: Word Duration Predicts Laughter
- **Assumption**: Shorter words (quick delivery) or longer words (emphasized delivery) predict laughter.
- **Evidence for**: H6.1 shows word_duration coefficient +0.21 in Logistic Regression (meaning longer words slightly more associated with laughter).
- **Evidence against**: Coefficient is small. Comedy delivery patterns are complex. Word duration confounded with pause patterns.
- **Test status**: Tested as part of H6.1 — small signal but not independently validated.
- **Risk if wrong**: LOW — even if wrong, doesn't fundamentally undermine the approach.

### Assumption A16: Comedic Pause Is Real but Requires librosa
- **Assumption**: The "comedic pause" (long silence before punchlines) exists and is detectable with proper audio analysis.
- **Evidence for**: H1.1 shows pauses >1s have 23.8% laughter rate (2× baseline). Purandare 2006: 0.8s vs 0.3s gap. Literature extensively validates.
- **Evidence against**: YouTube subtitle timestamps are too coarse. Need librosa on WAV files to measure actual pause duration. Initial extraction had only 68 laugh clips.
- **Test status**: Tested at subtitle level — effect found but too small. Need real audio extraction.
- **Risk if wrong**: MEDIUM — if real audio analysis also fails, comedic pause finding is not usable.

### Assumption A17: Laughter Rate ~37% Is Representative
- **Assumption**: ~37% laughter rate in our dataset is representative of stand-up comedy.
- **Evidence for**: Multiple data sources (StandUp4AI, our aligned data) show similar rates. Comedy specials are designed to generate laughter.
- **Evidence against**: Positive rate varies widely: our data 13.2%, merged_final 37%, StandUp4AI CSV 17.6%. Different labeling thresholds produce very different rates. YouTube markers may over-trigger.
- **Test status**: Not systematically tested.
- **Risk if wrong**: LOW — different rates just change optimal pos_weight.

### Assumption A18: We Can Collect More Hindi Data Without Synthetic Generation
- **Assumption**: Real Hindi/Hinglish comedy data can be collected through YouTube transcripts, podcast extraction, or manual annotation without resorting to LLM-generated synthetic data.
- **Evidence for**: 48 real Hindi examples exist. YouTube has Hindi comedy content. Podcasts available. DATA_COLLECTION_STRATEGY_V10.md planned real collection.
- **Evidence against**: YouTube videos unavailable (per HINDI_SCALING_STRATEGY.md). Hindi expansion never completed. All PRDs planned but none executed.
- **Test status**: Not tested — collection attempted but not completed.
- **Risk if wrong**: MEDIUM — if real collection fails, we'd need synthetic data which has its own problems.

---

## D. CONSTRAINTS

### Hardware Constraints
| Resource | Constraint | Impact |
|----------|-------------|--------|
| GPU | No local GPU available | Cannot run WavLM extraction locally |
| GPU | Colab T4 (16GB) is primary | Slow iteration, 90-min timeout |
| RAM | 32GB+ needed for DataLoader | Current Mac may be limiting |
| Storage | 500GB+ NVMe for clip cache | Limited cache sizes |
| Windows GPU | RTX 4090 not available per GAP_ANALYSIS | 10M pipeline never started |
| Network | Colab disconnects | Checkpoint requirements |

### Data Constraints
| Constraint | Detail | Impact |
|------------|--------|--------|
| Language coverage | Only 3 languages (en, zh, hi-latn) have real data | Multilingual claim is misleading |
| Hindi data | 48 examples only (0.5% of dataset) | Hindi F1=0.68 is statistically meaningless |
| Chinese test set | 0 examples in test set per GAP_ANALYSIS | Cannot evaluate Chinese properly |
| Audio segments | 12,395 aligned from 4 videos | Audio model training blocked |
| Positive rate | 13.2% (word-level) to 37% (merged_final) | Variable, impacts class weighting |
| Label quality | ~15% offset in VTT timestamps | Systematic noise in labels |

### Compute/Storage Constraints
| Constraint | Detail | Impact |
|------------|--------|--------|
| GDrive storage | ~135GB for 10M pipeline | Storage allocated but pipeline not started |
| Colab timeout | 90 min per session | Need checkpointing for long runs |
| Training time | ~29 min/epoch on T4 | Full training ~5 hours |
| Audio extraction | 2-4 hours CPU for all files | Bottleneck for acoustic features |

### Timeline Constraints
| Constraint | Detail | Impact |
|------------|--------|--------|
| ACL/EMNLP 2026 | Deadline pressure | Forces focus on current results |
| 12-week RL plan | Never started | Resource misallocation |
| 4-week Hindi plan | Never completed | Hindi gap remains |
| Colab GPU | Needed for WavLM | Blocks audio pipeline |

### Other Constraints
| Constraint | Detail | Impact |
|------------|--------|--------|
| No working audio model | WavLM extraction never succeeded | Fusion training cannot start |
| Gate collapse | Phase 1 gate→1.0 | Audio branch never learns |
| Teacher refinement broken | refine_weak_labels_nemotron.py outputs 0% laughter | Autonomous loop blocked |
| GitHub not updated | Only 73/796 files committed | Risk of losing work |
| Winning model not backed up | Local Mac only, not on GDrive | Catastrophic loss risk |

---

## E. NEGATIVE RESULTS (What Failed)

| Experiment | Result | Lesson |
|-----------|--------|--------|
| **Teacher refinement** (Qwen2.5-coder:1.5b) | F1=0.078 (vs baseline 0.819) | LLMs hallucinate labels when given task framing. Never use LLM output as direct supervision without validation. |
| **Biosemiotc features** (10 dims, no text) | F1=0.829 from features alone | LLM-generated features encode labels. All biosemiotc ablation results are invalid. |
| **WavLM audio-only** | F1=0.0 | Audio SSL fails at word-level with current setup. All-same-class bug or feature extraction issue. |
| **Gated fusion Phase 1** | gate_mean=1.0, audio learns nothing | Audio branch is too weak. Text dominates before audio even starts learning. |
| **F0 DROP at word level** | Cohen's d=0.063 (negligible) | Prosody is real but invisible at word level due to studio editing. N=60K makes trivially small effects significant. |
| **Pause alone** | F1=0.20 vs 0.55 target | Temporal context alone is insufficient for word-level classification. |
| **Pause trajectory** (H12.2) | F1=0.20 | Temporal context sequences don't improve over scalar pause. |
| **Biosemiotc ablation** | +0.003 val F1 (within noise) | XLM-R already captures what biosemiotc features measure. Hand-crafted features add nothing to pretrained transformers. |
| **Function word noise theory** | χ²=2.2, p=0.14 (not significant) | Function words equally distributed (61.2% vs 61.6%). Original "54% function word noise" claim was FALSE. Problem is span length, not function words. |

---

## F. POSITIVE RESULTS (What Worked)

| Experiment | Result | Lesson |
|-----------|--------|--------|
| **XLM-R word-level** | F1=0.819, IoU-F1=0.880 | Text-only is the ceiling. IoU-F1 gap validates span reformulation. |
| **StandUp4AI external benchmark** | TF-IDF F1=0.73 on 4 CSVs | External comparison is possible. StandUp4AI has clear signal. |
| **Span reformulation** | IoU-F1=0.880 vs word-F1=0.819 | Span-level prediction is genuinely different from word-level. Primary contribution reframed. |
| **Per-show split** | Minor leakage (1.9%) | Leakage is real but below significance threshold. Use per-show splits for final reporting. |
| **Temporal position** | Peak 20-30% through show (p=4e-143) | Show-level structural pattern is real. Cannot be used at word-level. |
| **H4.4 label leakage discovery** | F1=0.829 from features alone | This is a publishable negative result — validates that LLM-generated features cheat. |
| **WavLM-Base+ switch** | +4.7% on emotion benchmarks | Drop-in replacement for Wav2Vec2. Denoising pretraining relevant to our noisy audio. |
| **Comedic pause at scale** | Pauses >1s → 2× laughter rate | Effect exists at macro level. Need librosa on actual WAV files to exploit. |

---

## G. ORCHESTRA RESEARCH GAP ANALYSIS

| Orchestra Requirement | Our Status | Gap |
|---------------------|------------|-----|
| **Research state tracking** | research-state.yaml created (2026-05-24) | ✅ Created but late — 4 sessions already completed without it |
| **protocol.md before experiments** | Missing for all H1-H14 experiments | 🔴 Missing entirely — no temporal proof |
| **research-log.md** | Missing | 🔴 No decision timeline documented |
| **findings.md** | Created prior | ✅ Existed, but now superseded by research-state.yaml |
| **Inner/outer loop separation** | Not followed | 🔴 All experiments were ad-hoc |
| **Per-hypothesis directories** | Missing | 🔴 No experiments/{slug}/ structure |
| **Two-loop methodology** | Not followed | 🔴 Only hypothesis tests, no synthesis loop |
| **Domain skill routing** | Partial | ⚠️ Only used for paper writing review |
| **Experiment trajectory tracking** | Partial | ⚠️ metric_value/baseline/delta now tracked in yaml |
| **Literature routing to skills** | Not systematic | 🔴 Papers cited but not routed to academic-plotting, etc. |

### Orchestra Paper-Ready Assessment

| Paper | Score | Status | Blockers |
|-------|-------|--------|----------|
| Paper 1 (ChucklleNet biosemiotc) | 2.0/6 | ❌ NOT ready | Contradictory F1 numbers, no methodology, likely AI-generated |
| Paper 2 (COLING cross-cultural) | 2.0/6 | ❌ NOT ready | No results table, ~90 lines, likely AI-generated |
| Paper 3 (Word-Level Laughter) | 2.75/6 | ⚠️ 2-3 weeks to ready | Missing StandUp4AI baseline, no error bars, speculative RL |
| Paper 4 (Multimodal Outline) | N/A | ❌ All projected | Audio failed (F1=0.0), no actual results, no API |

### Orchestra Recommended Submission Path

| Priority | Paper | Venue | Timeline | Status |
|----------|-------|-------|----------|--------|
| #1 | StandUp NER (Paper 3, fixed) | ACL SRW | 2-3 weeks | Needs: StandUp4AI baseline, error bars, remove RL |
| #2 | LaughBank-733K Resource | LREC-COLING | 2-3 weeks | 733K segments is genuinely unique |
| #3 | Negative Results ArXiv | ArXiv | 1 week | Quick, establishes honesty |

---

## H. KEY FINDINGS FROM HYPOTHESIS SESSIONS

### Session 1 (H1.1, H1.2)
- Pause before laugh: 0.188s vs 0.118s (d=0.13) — effect 5× smaller than literature
- Long pauses (>1s): 23.8% laughter rate vs 12.4% baseline — comedic pause IS real
- F0/energy extraction: only 68 laugh clips — need balanced extraction

### Session 2 (H2.5, H4.4, H4.5)
- 100% multi-word spans — but it's an artifact of ±5s window labeling
- **H4.4 CRITICAL**: F1=0.829 from biosemiotc features alone — label leakage confirmed
- H4.5: 1.9% split leakage — minor, below threshold

### Session 3 (H12.2, H5)
- Pause trajectory F1=0.20 — temporal context alone insufficient
- Temporal position peak at 20-30% through show (p=4e-143) — show structure real

### Session 4 (H6.1)
- F0 DROP confirmed (p<10⁻⁶) but negligible (d=0.063) — 5 Hz difference, 98% overlap
- F0+energy F1=0.27 — simple acoustic features reach ceiling at word level
- RMS max is ONLY useful acoustic feature (coef=0.82)

---

## I. SUMMARY STATISTICS

| Category | Count |
|----------|-------|
| Core decisions mapped | 27 |
| Architecture decisions mapped | 15 |
| Assumptions mapped | 18 |
| Constraints documented | 11 categories |
| Negative results | 9 |
| Positive results | 8 |
| Orchestra gaps | 10 |
| Hypothesis sessions completed | 4 |
| Total hypotheses | 26 (9 completed, 17 pending) |

---

## J. DECISION QUALITY ASSESSMENT

### Well-Validated Decisions (High Confidence)
- D1 (XLM-R anchor), D2 (span reformulation), D9 (no LLM labels), D10 (per-video split), D13 (WavLM switch), D20 (pos_weight=5.0), D26 (3 languages only)

### Partially Validated (Medium Confidence)
- D3 (utterance-level), D6 (resume capability), D11 (cross-lingual priority), D14 (v5.0 pivot), D18 (StandUp4AI comparison)

### Unvalidated/Problematic (Low Confidence)
- D4 (gated fusion — gate collapsed), D5 (WavLM extraction never succeeded), D12 (negative results publishable — not yet done), D15 (10M pipeline superseded but not replaced)

---

*Generated: 2026-05-24*
*Source files: 28 documents across `docs/`*
*Confidence: Decisions A1-A27 verified against source documents. Assumptions A1-A18 traced to hypothesis results or paper drafts.*