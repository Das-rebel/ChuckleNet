# AGENT COUNCIL: COMPLETE HYPOTHESIS MATRIX + RESEARCH PLAN
## 4 Agents × 4 Domains = 26 Falsifiable Hypotheses
## Date: 2026-05-16

---

## DOMAIN 1: AUDIO — 7 Hypotheses (MiniMax Agent)

### H1.1: Pause Duration Predicts Laughter Better Than Random
**Hypothesis:** Pre-punchline pause duration is significantly longer for words that trigger laughter vs. words that don't (Δ ≥ 0.3s, matching Purandare 2006's 0.8s vs 0.3s finding).
**Experiment:** Extract pause duration before each word from 733K segments. t-test laughter vs non-laughter. 
**Threshold:** p < 0.001, Cohen's d > 0.5.
**Time:** 1 day
**Failure teaches:** Studio comedy editing removes natural pauses — subtitle timing ≠ real pause.

### H1.2: F0 Pitch Contour Changes Precede Laughter
**Hypothesis:** Within 500ms before a laughter-marked word, F0 slope is positive (rising pitch → punchline delivery) with ΔF0 ≥ 15Hz.
**Experiment:** librosa.pyin on 500ms windows before each word. Logistic regression: F0_slope → laughter probability.
**Threshold:** F0_slope coefficient significant (p < 0.01), adds ≥1% AUC over baseline.
**Time:** 1 day
**Failure teaches:** Comedy delivery is more about timing than pitch — or our 500ms window is wrong.

### H1.3: Acoustic Features Add ≥3% F1 to Text-Only XLM-R
**Hypothesis:** A simple acoustic feature vector (pause + F0 + RMS + speech rate = 8-dim) concatenated with XLM-R embeddings improves F1 by ≥3% over text-only.
**Experiment:** Extract 8 acoustic features per word. Train XLM-R+acoustic fusion. Compare to XLM-R alone.
**Threshold:** ΔF1 ≥ 0.03 (matching UR-FUNNY literature finding).
**Time:** 2 days
**Failure teaches:** Either (a) text already encodes prosodic structure, or (b) our feature extraction is broken.

### H1.4: Acoustic Features Help MORE for Cross-Lingual Transfer (Chinese)
**Hypothesis:** The F1 improvement from acoustic features is larger for Chinese (Δ ≥ 5%) than English (Δ ~3%), because XLM-R text representations are weaker for Chinese due to less pretraining data.
**Experiment:** Same fusion model, train EN, test EN+ZH. Measure ΔF1 per language.
**Threshold:** ΔF1(ZH) > ΔF1(EN) by ≥2%.
**Time:** 2 days
**Failure teaches:** Acoustic features are language-universal but don't compensate for text weakness — the model ignores them.

### H1.5: Pause Duration Alone Beats WavLM SSL Features
**Hypothesis:** A logistic regression using ONLY pause features (pre-word pause, post-word pause, speech rate) achieves F1 ≥ 0.55, beating our failed WavLM Phase A (F1=0.0).
**Experiment:** Extract pauses. Train logistic regression. Compare to WavLM checkpoint evaluation.
**Threshold:** F1 ≥ 0.55 (beats random baseline, proves audio signal exists).
**Time:** 1 day
**Failure teaches:** Pauses are too noisy in edited studio recordings — WavLM failure was fundamental not bug-based.

### H1.6: openSMILE eGeMAPS 88 Features Match or Beat Hand-Crafted Features
**Hypothesis:** openSMILE eGeMAPS (88 validated paralinguistic features) achieves F1 ≥ the 8 hand-crafted features (H1.3), validating the literature-driven feature set.
**Experiment:** Extract eGeMAPS for all 733K segments. Train classifier. Compare to H1.3 results.
**Threshold:** eGeMAPS F1 ≥ hand-crafted F1 (within 1%).
**Time:** 2 days
**Failure teaches:** The 88 eGeMAPS features are designed for emotion/affect, not comedy timing — domain mismatch.

### H1.7: Audio Features Are NOT Just Detecting Audience Laughter (Confound Check)
**Hypothesis:** The model's audio-based predictions correlate more strongly with comedian speech features (F0, pauses) than with background audio energy (RMS), proving the model uses delivery cues not audience reaction.
**Experiment:** Train two models: one on pre-word features, one on during-word features. If pre-word (delivery) model outperforms during-word (audience) model, confound is controlled.
**Threshold:** Pre-word model F1 > during-word model F1 by ≥5%.
**Time:** 2 days
**Failure teaches:** We're detecting audience laughter audio, not comedian delivery — fundamental confound.

---

## DOMAIN 2: SPAN REFORMULATION — 7 Hypotheses (MiniMax Agent)

### H2.1: The IoU-F1 Gap Is Real, Not Metric Artifact
**Hypothesis:** The 6.1% gap (IoU-F1=0.880 vs word-F1=0.819) is genuine model capability, not statistical artifact.
**Experiment:** Bootstrap CI on both metrics. Compute null distribution via shuffled labels. Compare gap on real vs random predictions.
**Threshold:** Random baseline gap < 1%; real gap > 5%.
**Time:** 1 day
**Failure teaches:** Gap is inherent to IoU thresholding, not model quality — spans aren't better.

### H2.2: Human Annotators Agree More on Spans Than Words
**Hypothesis:** Krippendorff's α for span-level annotation exceeds word-level α by ≥0.05.
**Experiment:** 3 annotators, 200 examples. Both word-level and span-level annotations. Compute inter-annotator agreement.
**Threshold:** Span α > word α + 0.05.
**Time:** 3 days
**Failure teaches:** Humans segment laughter at word level; span advantage is computational not cognitive.

### H2.3: The Gap Persists Cross-Linguistically (Chinese, Hindi)
**Hypothesis:** Both Chinese (3.8% gap) and Hindi (unknown) show IoU-F1 > word-F1 by ≥2%.
**Experiment:** Compute both metrics on ZH and HI test sets. Compare gap magnitude.
**Threshold:** All languages show gap ≥ 2%.
**Time:** 2 days
**Failure teaches:** Gap is English-specific (orthographic conventions like exclamation marks).

### H2.4: Span Predictions Transfer Better Cross-Domain
**Hypothesis:** Span-F1 degrades LESS than word-F1 when transferring from stand-up to UR-FUNNY/TED.
**Experiment:** Train on StandUp4AI, test on UR-FUNNY + TED. Compare transfer degradation.
**Threshold:** Span-F1 drop < word-F1 drop by ≥3%.
**Time:** 2 days
**Failure teaches:** Spans are domain-specific, capturing show structure not generalizable humor patterns.

### H2.5: The 73% Multi-Word Claim Is Verifiable
**Hypothesis:** ≥70% of laughter spans in weak labels cover 2+ consecutive words.
**Experiment:** Histogram of span lengths from aligned segments. Confirm ≥70% multi-word.
**Threshold:** Computed multi-word percentage within 5% of 73%.
**Time:** 1 day
**Failure teaches:** Weak labels exaggerate span extent — the 73% is an artifact of subtitle alignment.

### H2.6: StandUp4AI Word-F1 Underestimates Their Own Performance
**Hypothesis:** Recomputing StandUp4AI results with IoU-F1 increases their reported F1 by ≥5%.
**Experiment:** Obtain StandUp4AI annotations, simulate evaluation, compare metrics.
**Threshold:** IoU-F1 improvement ≥5% over their reported word-F1.
**Time:** 1 day
**Failure teaches:** Their annotations are single-word, making span evaluation impossible — different task.

### H2.7: Span Formulation Generalizes to Other Temporal Events
**Hypothesis:** Fillers ("uh", "um"), hesitations, and backchannels show IoU-F1 > word-F1 by ≥3%.
**Experiment:** Train on filler detection. Compare metrics. Test on conversational speech data.
**Threshold:** Filler IoU-F1 > word-F1 by ≥3%.
**Time:** 2 days
**Failure teaches:** Laughter is unique — span advantage doesn't generalize. Theory is narrow.

---

## DOMAIN 3: MULTIMODAL — 6 Hypotheses (MiniMax Agent)

### H3.1: Fusion Beats Text-Only by ≥3% (Literature-Consistent)
**Hypothesis:** Text + acoustic fusion (late concatenation) achieves F1 ≥ 0.849 (0.819 + 0.03).
**Experiment:** Concatenate XLM-R embeddings with 8 acoustic features → classifier. 5-fold CV.
**Threshold:** ΔF1 ≥ 0.03 over text-only.
**Time:** 2 days
**Failure teaches:** Text already captures everything acoustic offers at word level.

### H3.2: Acoustic Features Help MORE Where Text Is Weak
**Hypothesis:** Fusion improvement is larger for examples with low XLM-R confidence (bottom quartile) than high confidence (top quartile).
**Experiment:** Bucket predictions by XLM-R confidence. Measure ΔF1 per bucket.
**Threshold:** Bottom-quartile ΔF1 > top-quartile ΔF1 by ≥5%.
**Time:** 1 day
**Failure teaches:** Acoustic features correlate with text features — redundant not complementary.

### H3.3: Late Fusion (Concatenate) Beats Cross-Attention for Small Feature Sets
**Hypothesis:** For 8-40 acoustic features, simple concatenation outperforms cross-attention fusion in F1 by ≥1%.
**Experiment:** Compare late fusion (concatenate) vs cross-attention (4-layer transformer) on same data.
**Threshold:** Late fusion F1 > cross-attention F1 by ≥1%.
**Time:** 2 days
**Failure teaches:** Cross-attention needs high-dimensional SSL features to justify its complexity.

### H3.4: Fused Model Improves Cross-Lingual Transfer More Than English
**Hypothesis:** The fusion model's F1 improvement over text-only is larger for Chinese (+Δ5%) than English (+Δ3%).
**Experiment:** Train EN, zero-shot ZH. Measure fusion vs text-only gap per language.
**Threshold:** ΔF1(ZH) > ΔF1(EN) by ≥2%.
**Time:** 2 days
**Failure teaches:** Acoustic features are language-universal — or they're irrelevant to both languages.

### H3.5: Minimum Useful Acoustic Feature Set ≤ 5 Features
**Hypothesis:** An ablation removing features one-at-a-time shows ≥80% of the fusion benefit comes from ≤5 features (likely pauses + F0).
**Experiment:** Ablation study: remove each of 8 features, measure F1 drop.
**Threshold:** Top-2 features account for ≥60% of total acoustic benefit.
**Time:** 1 day
**Failure teaches:** All features contribute marginally — acoustic signal is diffuse not concentrated.

### H3.6: Audio-Text Fusion Improves Span-F1 More Than Word-F1
**Hypothesis:** The fusion benefit is larger for IoU-F1 (+5%) than word-F1 (+3%), because audio provides temporal boundary information (pause duration, speech rate) that particularly helps span boundary detection.
**Experiment:** Compute both metrics for text-only and fusion models. Compare Δ across metrics.
**Threshold:** ΔIoU-F1 > Δword-F1 by ≥2%.
**Time:** 1 day
**Failure teaches:** Audio helps word-level classification, not span-level — or vice versa.

---

## DOMAIN 4: DATA — 6 Hypotheses (MiniMax Agent)

### H4.1: 15% Label Offset Causes ≥5% F1 Degradation
**Hypothesis:** Correcting the ~15% label offset (aligning [laughter] markers more precisely to word boundaries) improves F1 by ≥5%.
**Experiment:** Manually correct 200 examples. Train identical model on corrected vs original labels. Compare F1.
**Threshold:** ΔF1 ≥ 0.05 from correction.
**Time:** 3 days
**Failure teaches:** XLM-R is robust to label noise — or the offset is systematic not random.

### H4.2: Weak Labels Correlate With Actual Audience Laughter (r ≥ 0.7)
**Hypothesis:** YouTube [laughter] markers correlate with actual audience laughter presence (r ≥ 0.7) when validated against human annotation.
**Experiment:** 200 examples: human annotator marks "did audience actually laugh here?" Compare to weak label.
**Threshold:** Cohen's κ ≥ 0.5 between weak label and human judgment.
**Time:** 3 days
**Failure teaches:** YouTube auto-subs are unreliable for laughter — weak supervision invalid.

### H4.3: Minimal Reliable Evaluation Set = 500 Examples
**Hypothesis:** Bootstrap subsampling shows that evaluation F1 stabilizes (std < 0.01) with ≥500 examples. Below this, F1 estimates are unreliable.
**Experiment:** Subsample test set from 100 to 4000 examples. Measure F1 variance.
**Threshold:** F1 standard deviation < 0.01 at n ≥ 500.
**Time:** 1 day
**Failure teaches:** Current 4,124 test set is adequate; or the task is so noisy it needs 5K+.

### H4.4: Synthetic Biosemotic Features Contain Label Leakage
**Hypothesis:** A model trained ONLY on biosemotic features (no text) achieves F1 ≥ 0.50, indicating label leakage from the LLM generation process.
**Experiment:** Train logistic regression on 32 biosemotic features alone, no XLM-R.
**Threshold:** F1 ≥ 0.50 → leakage confirmed.
**Time:** 1 day
**Failure teaches:** The features are genuinely predictive of laughter independent of text.

### H4.5: Data Splits Must Be Per-Show (Not Random) To Avoid Leakage
**Hypothesis:** Random split (80/10/10) inflates F1 by ≥3% vs per-show split where all segments from one video go to one split.
**Experiment:** Compare random split F1 to per-show split F1.
**Threshold:** Random split F1 > per-show split F1 by ≥3%.
**Time:** 1 day
**Failure teaches:** No data leakage — the task transfers across shows.

### H4.6: StandUp4AI 3,207 Words Can Train a Competitive Baseline
**Hypothesis:** XLM-R trained only on StandUp4AI's 3,207 manually labeled words achieves F1 ≥ 0.70 (competitive with their reported results).
**Experiment:** Run training/train_standup4ai_baseline.py with GPU enabled. Evaluate.
**Threshold:** F1 ≥ 0.70 on StandUp4AI test split.
**Time:** 1 day
**Failure teaches:** 3,207 words is too small — or our script is broken.

---

## PRIORITIZED EXECUTION PLAN

### Week 1: Core Validation (Must Know First)

| Day | Hypotheses | Why First |
|-----|-----------|-----------|
| **Day 1** | H2.1 (gap real?), H2.5 (73% verify), H4.3 (min eval set), H4.6 (StandUp4AI train) | Validates our core claims before anything else |
| **Day 2** | H1.1 (pause predicts?), H1.2 (F0 predicts?), H1.5 (pause alone beats WavLM) | Tests whether audio has ANY signal at all |
| **Day 3** | H2.2 (human span agree?), H4.1 (label offset effect), H4.2 (weak label validity), H4.4 (leakage check) | Human study + data quality — legitimizes everything |

### Week 2: What Works + How Much

| Day | Hypotheses |
|-----|-----------|
| **Day 4** | H1.3 (acoustic adds 3%?), H3.1 (fusion beats text), H3.5 (minimum features) |
| **Day 5** | H2.3 (cross-lingual gap), H1.4 (audio helps ZH more), H3.4 (fusion helps ZH more) |
| **Day 6** | H2.4 (cross-domain transfer), H2.6 (StandUp4AI recalc), H3.6 (fusion helps spans) |

### Week 3: Depth + Generalization

| Day | Hypotheses |
|-----|-----------|
| **Day 7** | H1.6 (eGeMAPS vs handcrafted), H1.7 (confound check) |
| **Day 8** | H2.7 (generalize to fillers), H3.2 (fusion helps where text weak) |
| **Day 9** | H3.3 (late vs cross-attention), H4.5 (split leakage) |
| **Day 10** | Integrate results → write paper |

---

## WHAT FAILURE ON EACH HYPOTHESIS MEANS

| If This Fails... | Then... |
|-----------------|---------|
| H1.1 + H1.2 both fail (no audio signal) | **Audio is useless for word-level laughter. Publish the negative result.** |
| H1.3 + H3.1 both fail (no fusion benefit) | **Text-only is the ceiling. Focus the paper on "text is sufficient".** |
| H2.2 fails (humans don't prefer spans) | **Span reformulation is metric hacking, not cognitive alignment. Drop it.** |
| H2.1 + H2.3 succeed | **Span reformulation IS the paper. Lead with it.** |
| H1.3 succeeds + H3.1 succeeds | **Fusion IS the paper. Show audio adds 3-5%.** |
| H4.2 fails (weak labels don't match real laughter) | **Fundamental problem. All results are suspect. Build human benchmark first.** |

---

## THE TWO PAPER PATHS (Decided by Week 1 Results)

### Path A: Audio ADDS value (H1.3/H3.1 succeed)
**Paper:** "Laughter Is Not a Word: Span-Based Multimodal Laughter Detection in Stand-up Comedy"
**Claim:** Span formulation + acoustic fusion achieves F1=X (text 0.819 → fusion 0.849+)
**Venue:** EMNLP Main or Findings

### Path B: Audio adds NOTHING (H1.3/H3.1 fail)
**Paper:** "What Makes Laughter Prediction Work? It's the Text and the Metric"
**Claim:** Text-only XLM-R already near-ceiling; audio and biosemotic features add noise; span reformulation is the real contribution
**Venue:** ACL SRW or EMNLP Workshop
**Angle:** Negative results + metric reformulation = "data and evaluation paper"

### Path C: Weak labels are broken (H4.2 fails)
**Paper:** "Weak Supervision for Laughter: When YouTube Subtitles Lie"
**Claim:** Document the gap between subtitle [laughter] markers and actual audience laughter; propose correction
**Venue:** EMNLP (evaluation track) or LREC
**Angle:** This is a DIFFERENT paper — data quality, not modeling

---

*Generated by Agent Council: 4 agents × 4 domains = 26 falsifiable hypotheses*
*Orchestra Research Frameworks: Ideation (10 lenses), Paper Writing, Review*
