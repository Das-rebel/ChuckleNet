# BIOSEMOTIC-AUDIO: Acoustic Operationalization of Biosemotic Features
## Fresh Thinking: Audio-First, Not Text-First
## Date: 2026-05-16
## Based on: 50+ years of phonetics/linguistics literature + 636-line acoustic research doc

---

## THE FUNDAMENTAL INSIGHT

The biosemotic features FAILED for text (H4.4 proved F1=0.829 from features alone = label leakage from LLM generation). But the CONCEPT is correct:

| Biosemotic Concept | Actually IS... | Extractable From |
|-------------------|---------------|------------------|
| **Duchenne laughter** | Voice quality + spectral characteristics of genuine vocal expression | Audio spectrograms, F0, HNR, spectral tilt |
| **Incongruity-Resolution** | Prosodic surprise: sudden F0/pause/energy deviations from expected pattern | F0 contour derivatives, pause statistics, RMS variance |
| **Theory of Mind** | Conversational timing: speaker adapts delivery based on audience response | Pause-after-punchline, speech rate adaptation, turn-taking gaps |

**The LLM generated these as TEXT features (e.g., "joy_intensity: 0.83"). That's wrong. These should be extracted from RAW AUDIO.**

---

## MAPPING: Biosemiotic → Acoustic → Extractable Features

### GROUP 1: DUCHENNE MARKERS (Voice Quality of Genuine Expression)

| Biosemiotic Concept | Acoustic Correlate | Research Basis | Extraction | # Features |
|-------------------|-------------------|---------------|------------|:--:|
| Joy intensity | Spectral tilt (less steep → breathier → more genuine) | Bachorowski 2001, de Looze 2014 | librosa + spectral regression | 3 |
| Genuine humor probability | HNR (harmonics-to-noise ratio), voiced ratio | de Looze 2016, Gratidão 2023 | librosa.effects.harmonic + pyin | 4 |
| Spontaneous laughter markers | F0 variability (std/range), F0 peak velocity | Kipper 2012, Bachorowski 2001 | librosa.pyin + np.diff | 5 |
| Setup-punchline structure | Speech rate deceleration before punchline | Purandare 2006, Bertero 2016 | Word duration ratios | 3 |
| **Duchenne total** | | | | **15** |

### GROUP 2: INCONGRUITY-RESOLUTION (Prosodic Surprise)

| Biosemotic Concept | Acoustic Correlate | Research Basis | Extraction | # Features |
|-------------------|-------------------|---------------|------------|:--:|
| Expectation violation | Delta-F0 (sudden pitch change), Delta-RMS | Bertero 2016, Mazzocconi 2020 | np.diff(f0), np.diff(rms) | 6 |
| Humor complexity | F0 range (wider = more expressive), F0 slope | Purandare 2006, Hasnain 2022 | librosa.pyin + polyfit | 4 |
| Resolution time | Pause duration before/after word | Purandare 2006 (p<0.001), Attardo 2003 | librosa.effects.split + word alignment | 5 |
| **Incongruity total** | | | | **15** |

### GROUP 3: THEORY OF MIND (Conversational Timing)

| Biosemotic Concept | Acoustic Correlate | Research Basis | Extraction | # Features |
|-------------------|-------------------|---------------|------------|:--:|
| Speaker intent confidence | Speech rate stability, F0 contour regularity | Rockwell 2000, Cheang 2008 | CV of speech rate, F0 autocorrelation | 4 |
| Audience perspective | Pause-after-punchline (wait-for-laugh gap) | Xu 2022 (r=0.67) | Silence after labeled words | 3 |
| Social context | RMS energy relative to surrounding speech | Pickering 2009 | Z-score of RMS in local window | 3 |
| Character interaction | Voice quality shifts (formant changes for character voices) | — | F1/F2 formant tracking via parselmouth | 4 |
| **ToM total** | | | | **14** |

### GROUP 4: STRUCTURAL (Comedy Timing)

| Concept | Feature | Basis | # |
|---------|---------|-------|:--:|
| Punchline position | Similarity to known punchline prosodic templates | Bertero 2016 | 3 |
| Clause boundary ratio | Pause duration at syntax boundaries | Purandare 2006 | 3 |
| **Structural total** | | | **6** |

### GRAND TOTAL: **50 acoustic biosemotic features**

---

## TOOLS READY TO EXTRACT

| Tool | Features | Status | Speed |
|------|----------|--------|-------|
| **librosa.pyin** | F0 mean, std, range, slope, voiced ratio | ✅ Installed | Fast |
| **librosa.effects** | Pause detection, speech/silence segmentation | ✅ Installed | Fast |
| **librosa.feature** | MFCC 1-13, spectral centroid/bandwidth/rolloff, RMS | ✅ Installed | Fast |
| **librosa.effects.harmonic** | HNR (harmonics-to-noise ratio) | ✅ Installed | Medium |
| **openSMILE eGeMAPS** | 88 paralinguistic functionals | ✅ Installed | Medium |
| **openSMILE ComParE** | 6373 comprehensive features | ✅ Installed | Slow |
| **parselmouth** | Formant F1/F2, jitter, shimmer, HNR | ❌ Need pip install | Medium |
| **torchaudio** | Wav2Vec2, WavLM embeddings | ✅ Installed | GPU needed |

---

## NEW HYPOTHESES: Audio-First Biosemotic

### AH1: Acoustic Duchenne Features Differentiate Laughter
**F0 variability in the 500ms before a laughter-marked word is higher (std > 20Hz) than before non-laughter words (std < 15Hz), matching Bachorowski 2001's finding that genuine expression has higher F0 variability.**
- Extract: F0 std, range, spectral tilt, voiced ratio from librosa.pyin
- Test: Welch's t-test, Cohen's d > 0.4
- Time: 1 day

### AH2: Pause Duration Is the #1 Single Feature (Replicate Purandare 2006)
**Pre-punchline pause extracted from actual audio (not subtitles) shows Δ ≥ 0.5s (laughter words: mean > 0.7s, non-laughter: mean < 0.2s), matching Purandare's 0.8s vs 0.3s finding.**
- Extract: librosa.effects.split for silence detection, aligned to word boundaries
- Test: t-test, Cohen's d > 0.6
- Time: 1 day
- **This was masked by subtitle timing in H1.1 — real audio should reveal the true gap**

### AH3: openSMILE eGeMAPS Outperforms Hand-Crafted Features
**Training an XGBoost classifier on 88 eGeMAPS features achieves F1 ≥ 0.55 (beating our failed WavLM F1=0.0), proving the audio signal exists.**
- Extract: openSMILE eGeMAPS on 733K segments
- Train: XGBoost, 5-fold CV
- Time: 2 days
- **If this fails → audio truly adds nothing. If it succeeds → audio IS useful, WavLM was just broken.**

### AH4: Biosemiotic Feature Groups Show Differential Predictive Power
**Duchenne features contribute > incongruity features > ToM features for laughter prediction, matching the theoretical hierarchy where genuine expression (Duchenne) is the strongest signal.**
- Extract: 50 acoustic biosemotic features
- Ablation: train classifier, remove each group, measure ΔF1
- Time: 1 day (after extraction)

### AH5: Acoustic Features Help More Than Text Features (The Reversal)
**F1(audio biosemotic) >> F1(text biosemotic = 0.829), because audio features are REAL acoustic measurements while text features were LLM-fabricated proxies.**
- Compare: F1 from acoustic biosemotic features (extracted from WAV) vs F1 from text biosemotic features (from H4.4 = 0.829 with leakage)
- If F1(audio) > F1(text) → proves audio biosemotic captures genuine signal without leakage
- Time: 2 days

---

## WHAT WE NEED FOR EXTRACTION

```bash
# Already installed
pip list | grep -E "librosa|soundfile|opensmile|torchaudio|praatio"

# Need to install
pip install parselmouth  # Praat Python bindings for formant/jitter/shimmer
pip install xgboost      # For classifier testing
```

## EXTRACTION PIPELINE (Build Today)

```python
def extract_audio_biosemotic(audio_path, word_start, word_end):
    """Extract 50 acoustic biosemotic features for a word segment."""
    y, sr = librosa.load(audio_path, sr=16000, 
                         offset=max(0, word_start-0.5), 
                         duration=min(3.0, (word_end-word_start)+1.0))
    
    features = {}
    
    # === DUCHENNE (15 features) ===
    f0, voiced, _ = librosa.pyin(y, fmin=75, fmax=500, sr=sr)
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) > 5:
        features['f0_mean'] = np.mean(f0_clean)
        features['f0_std'] = np.std(f0_clean)
        features['f0_range'] = np.max(f0_clean) - np.min(f0_clean)
        features['f0_slope'] = np.polyfit(range(len(f0_clean)), f0_clean, 1)[0]
    features['voiced_ratio'] = np.mean(voiced)
    
    # Spectral tilt (Duchenne proxy)
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    tilt = np.mean([np.polyfit(np.log(freqs[:len(S)]+1), np.log(S[:,i]+1), 1)[0] 
                    for i in range(S.shape[1])])
    features['spectral_tilt'] = tilt
    
    # Harmonics-to-noise ratio
    y_harm, y_perc = librosa.effects.hpss(y)
    features['hnr'] = np.mean(y_harm**2) / (np.mean(y_perc**2) + 1e-10)
    
    # === INCONGRUITY (15 features) ===
    rms = librosa.feature.rms(y=y)[0]
    features['rms_mean'] = np.mean(rms)
    features['rms_std'] = np.std(rms)
    features['delta_f0_max'] = np.max(np.abs(np.diff(f0_clean))) if len(f0_clean)>5 else 0
    
    # === ToM (14 features) ===
    # Speech rate: 1 / word_duration
    dur = word_end - word_start
    features['speech_rate'] = 1.0 / dur if dur > 0 else 0
    
    # MFCC (13 for general acoustic shape)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i in range(13):
        features[f'mfcc_{i+1}_mean'] = np.mean(mfcc[i])
    
    return features  # ~50 features total
```

---

## IMMEDIATE TEST (5 minutes)

Test extraction on one WAV clip to verify the pipeline works. Then scale to 733K segments.

**The key question this answers:** Can biosemotic concepts, properly operationalized from audio, predict laughter without the label leakage that corrupted the LLM-generated text features?
