# 10M AUDIO SEGMENT PIPELINE — EXECUTION PLAN
**Goal:** SOTA audio + text laughter detection model
**Target:** 10,000,000 aligned audio-word segments across en/zh/hi-latn
**Date:** 2026-05-13
**Based on:** Full audit of all PRDs, code, data, GitHub, GDrive

---

## EXECUTIVE SUMMARY

**We are 7.3% there — not 0%.** 733K usable segments already exist with audio files, labels, and timestamps. The plan leverages this foundation rather than starting from scratch.

| What | Current | Target | Gap |
|------|---------|--------|-----|
| Aligned segments | 733K (usable) | 10M | 9.27M |
| Audio files | 301 MP3s | ~3,700 | ~3,400 |
| Languages | en (dominant) | en, zh, hi-latn | zh + hi |
| Text training data | 19K merged_final | 19K (sufficient) | 0 |
| Audio encoder | Wav2Vec2-Base | **WavLM-Base+** (switched) | ✅ Done |
| Working model | XLM-R text F1=0.82 | Text F1=0.82 + Audio F1>0.65 | Audio model |

**Key insight:** Train on what we have NOW while scaling data collection in parallel.

---

## RESEARCH FINDINGS APPLIED

### What works (keep):
- ✅ **Direct VTT [laughter] alignment** — 5s window around markers, proven on 733K segments
- ✅ **XLM-R word-level sequence labeling** — F1=0.819 on en+zh
- ✅ **pos_weight=5.0** for class imbalance
- ✅ **faster-whisper tiny** for transcription (130x realtime)
- ✅ **WavLM-Base+ for audio encoder** — superior to Wav2Vec2 on paralinguistic tasks, denoising pretraining helps with noisy comedy audio
- ✅ **GDrive + rclone** for storage and Colab access
- ✅ **VTT subtitles as ground truth** — no manual labeling needed
- ✅ **MFCC + delta + delta-delta** for audio features (40-dim each = 120-dim)

### What to avoid (lessons):
- ❌ **Teacher refinement** — broken, outputs 0% laughter, skip entirely
- ❌ **Energy threshold audio detection** — fails on studio recordings
- ❌ **Biosemotic features** — synthetic, contain label leakage
- ❌ **Synthetic data** — 85% of merged_final is synthetic, don't generate more
- ❌ **Writing more PRDs** — 7 exist, execute don't plan

---

## PHASE 0: FOUNDATION (Week 1 — START NOW)

**Goal:** Establish working pipeline on existing data before scaling

**✅ MODEL SWITCHED:** Wav2Vec2-Base → **WavLM-Base+** (microsoft/wavlm-base-plus)
- Downloaded (22s), verified working (62ms/seg CPU, 16 seg/s)
- Same size (95M params), same API, +4.7% on emotion benchmarks
- Denoising pretraining handles noisy comedy audio

### 0.1: Extract Audio Waveform Segments (IN PROGRESS)
**What:** Use `aligned_segments.jsonl` to extract actual `.wav` clips
**Script:** `training/extract_audio_segments.py` ✅ CREATED, TESTED (126 seg/s, 4 workers)
**Input:** 733K segments with `audio_file`, `start`, `end`  
**Output:** `data/audio_comedy/extracted_clips/{video_id}/{word_idx}.wav`  
**Time:** ~2 hours compute (reading 22GB MP3s, writing WAVs)  
**Command:** `python training/extract_audio_segments.py --workers 8`

```python
# Pseudocode
for segment in aligned:
    y, sr = librosa.load(segment.audio_file, offset=start, duration=end-start)
    sf.write(f"extracted_clips/{video_id}/{word_idx}.wav", y, sr)
```

### 0.2: Validate & Clean Aligned Data
**What:** Check 733K segments for issues  
**Actions:**
- Filter out segments where audio_file is GDrive path (not local)
- Remove empty `audio_file` entries (8,527 segments)
- Flag batches with suspiciously low positive rates (<5% = likely non-comedy)
- Verify `end > start` for all timestamps
**Success:** Clean 700K+ segments ready for training

### 0.3: Split Into Train/Val/Test
**What:** Create proper splits, stratified by label  
**Ratio:** 80/10/10  
**Constraint:** Same video must not span splits (avoid data leakage)  
**Success:** Clean splits saved to `data/audio_comedy/splits/`

### 0.4: Train WavLM Phase A (quick baseline)
**What:** Frozen WavLM-Base+ → MLP classifier on 733K segments
**Script:** `training/train_wavlm_audio.py` ✅ CREATED
**Time:** ~30 min CPU (frozen encoder) for 733K segments
**Command:** `python training/train_wavlm_audio.py --phase A --epochs 5 --batch-size 32`
**Target:** F1 ≥ 0.55

### 0.5: Upload Everything to GDrive
**What:** rclone push extracted clips + cleaned data  
**Destination:** `gdrive:laughter_prediction/extracted_clips/`  
**Size est:** ~5-10GB for 700K WAV clips at 16kHz mono

---

## PHASE 1: FIRST MODELS (Week 1-2)

**Goal:** Train baseline audio model on existing 700K segments, text model on 19K

### 1.1: Text XLM-R Baseline (uses existing merged_final)
**Script:** `training/train_xlmr_combined.py`  
**Data:** 19K train / 3K valid / 1.8K test (7 languages)  
**Config:** XLM-R-base, pos_weight=5.0, unfreeze 4 layers, batch=32, lr=5e-5, 5 epochs  
**Target:** F1 ≥ 0.82 (matching promoted baseline)  
**Time:** 2-3 hours CPU  
**Output:** `experiments/xlmr_text_baseline_v2/`

### 1.2: Audio Wav2Vec2 Baseline
**Script:** `training/train_wav2vec2_audio.py`  
**Data:** 700K extracted WAV segments from Phase 0  
**Config:** Wav2Vec2-base, fp16, batch=256, lr=1e-4, 10 epochs, torch.compile  
**Target:** Audio-only F1 ≥ 0.60  
**Time:** 8-12 hours on T4/RTX 4090  
**Output:** `experiments/wav2vec2_audio_baseline/`

### 1.3: MFCC Feature Pre-computation
**Script:** Create `training/compute_mfcc_features.py`  
**What:** 40 MFCC + delta + delta-delta = 120-dim per word segment  
**Why:** Faster training, smaller files than raw WAV  
**Time:** ~30 min on 700K segments  
**Output:** `data/audio_comedy/mfcc_features/` (numpy .npz, ~2-3GB)

---

## PHASE 2: SCALE TO 10M SEGMENTS (Weeks 2-6)

**Goal:** Reach 10M segments by collecting ~3,400 more videos across 3 languages

### 2.1: Language Strategy

| Language | Target Videos | Target Segments | Current | Priority | Status |
|----------|---------------|-----------------|---------|----------|--------|
| English | 1,500 | 4,000,000 | ~700K (batch1-15) | P1 — add 1,200 more | 🔄 In progress |
| Chinese | 1,000 | 3,000,000 | 0 | P1 — start from zero | ⏳ Pending |
| Hindi/Hinglish | 1,200 | 3,000,000 | 0 | P2 — harder, lower yield | ⏳ Pending |

**Note:** Chinese has lower words-per-video yield (~6K vs 8K for EN) so needs more videos.

### 2.2: Pipeline Scripts Created

| Script | Purpose | Status |
|--------|---------|--------|
| `training/find_comedy_videos.py` | Search YouTube, filter by laugh density | ✅ Created |
| `training/download_audio_batch.py` | Parallel yt-dlp to GDrive/local | ✅ Created |
| `training/whisper_batch_gdrive.py` | Batch Whisper transcription (tiny/base/large) | ✅ Created |
| `training/align_10m_segments.py` | VTT + Whisper alignment at scale | ✅ Created |

### 2.3: Execution Commands

**Step 1: Find videos (per language)**
```bash
# English - find 1,200 more videos
python training/find_comedy_videos.py --lang en --target 1200

# Chinese - find 1,000 videos
python training/find_comedy_videos.py --lang zh --target 1000

# Hindi - find 1,200 videos
python training/find_comedy_videos.py --lang hi-latn --target 1200
```

**Step 2: Download audio + VTT**
```bash
# Download with 4 parallel workers
python training/download_audio_batch.py \
  --lang en \
  --video-list data/video_candidates/en.json \
  --workers 4 \
  --gdrive  # or omit for local
```

**Step 3: Whisper transcription**
```bash
# On RTX 4090 (fastest)
python training/whisper_batch_gdrive.py \
  --lang en \
  --model base \
  --device cuda \
  --compute-type float16

# On Colab T4 (fallback)
python training/whisper_batch_gdrive.py \
  --lang en \
  --model tiny \
  --device cuda \
  --compute-type int8_float16
```

**Step 4: Alignment**
```bash
python training/align_10m_segments.py \
  --lang en \
  --audio-dir gdrive:laughter_prediction/audio/en \
  --transcript-dir gdrive:laughter_prediction/transcripts/en \
  --vtt-dir gdrive:laughter_prediction/vtt/en \
  --output gdrive:laughter_prediction/aligned/en.jsonl
```

### 2.2: Video Discovery Pipeline

**Script:** `training/find_comedy_videos.py` (create)

**Per language search strategy:**

```
ENGLISH:
  "stand up comedy special full"  
  "comedy special netflix"
  "comedian full show"
  → Filter: auto-subs available, >20 [laughter] markers
  
CHINESE:
  "单口相声" (stand-up comedy)
  "脱口秀" (talk show / stand-up) 
  "相声大会" (crosstalk comedy show)
  "中国喜剧" (Chinese comedy)
  → Filter: auto-subs available, [laughter] / [笑] markers

HINDI/HINGLISH:
  "hindi stand up comedy zakir khan"
  "hinglish comedy special"
  "indian comedy show"
  "hindi hasya kavi sammelan"
  → Filter: auto-subs or manual subs available
```

**Technical approach:**
```bash
# Step 1: Search YouTube
yt-dlp "ytsearch100:stand up comedy special" --flat-playlist --dump-json > results.json

# Step 2: Filter by subtitle availability
yt-dlp --list-subs <url> | grep -q "en"  # Has English subs?

# Step 3: Check laugh density
yt-dlp --skip-download --write-auto-sub --sub-lang en <url>
grep -c "\[laughter\]" *.vtt  # Count laugh markers
```

**Rate limiting:** 20 searches/min, ~5 hours for 4,000 searches

### 2.3: Download Pipeline

**Script:** `training/download_audio_batch.py` (create)

```bash
# Parallel download with 4 workers
yt-dlp -x --audio-format mp3 --audio-quality 5 \
  -o "gdrive:laughter_prediction/audio/{lang}/%(id)s.%(ext)s" \
  --download-archive downloaded.txt \
  <url>

# Also download VTT subtitles
yt-dlp --skip-download --write-auto-sub --sub-lang en \
  -o "gdrive:laughter_prediction/vtt/{lang}/%(id)s" \
  <url>
```

**Time per video:** ~2 min download, ~4 workers → 1,600 videos/day
**Total:** ~2 days for 3,400 videos (with 4 parallel workers)

### 2.4: Batch15 — Process What's Already Downloaded

**What:** 214 MP3s in batch15/ — transcribe and align them NOW
**Status:** Audio files exist, no transcripts or alignment yet
**Action:**
1. Run faster-whisper on all 214 batch15 files → GDrive transcripts
2. Align with VTT markers → GDrive aligned segments
3. Merge with existing 733K segments
**Est. yield:** ~500K additional segments (214 × ~2,400 avg)
**Time:** 3-4 hours GPU (Whisper) + 1 hour CPU (alignment)

---

## PHASE 3: WHISPER TRANSCRIPTION (Weeks 3-4)

**Goal:** Word-level timestamps for all 3,700+ videos

### 3.1: Batch Whisper Pipeline

**Script:** `training/whisper_batch_gdrive.py` (already exists, verify & use)

**Config:**
```python
model = faster_whisper.WhisperModel("tiny", device="cuda", compute_type="int8_float16")
# On RTX 4090: ~130x realtime → 1 hr audio = 28 sec processing
# On Colab T4: ~100x realtime → 1 hr audio = 36 sec processing
```

**Strategy:**
- Run on Windows RTX 4090 when available → free, faster
- Fallback to Colab T4 if GPU busy → $10/mo Colab Pro
- Batch by language to minimize context switching
- Save transcripts incrementally so interrupted runs are resumable

**Time estimates:**
| GPU | Speed | 3,700 videos × 45 min avg | Sessions |
|-----|-------|---------------------------|----------|
| RTX 4090 | 130x | ~21 GPU hours | 14 × 90 min |
| Colab T4 | 100x | ~28 GPU hours | 19 × 90 min |

### 3.2: Transcript Validation

**Check per transcript:**
- Word timestamps present and sequential
- Language auto-detected matches expected
- Min words per video (>100 = has actual speech content)
- Min duration (>2 min)

**Rejection criteria:** <100 words OR <2 min → flag for manual review

---

## PHASE 4: ALIGNMENT AT SCALE (Week 4)

**Goal:** Parse VTT markers, align with Whisper timestamps → 10M labeled segments

### 4.1: Alignment Script

**Script:** Create `training/align_10m_segments.py` (based on existing `align_whisper_to_vtt.py`)

**Algorithm (proven on 733K segments):**
```
1. Parse VTT: extract all [laughter]/[applause]/[laughing] timestamp ranges
2. For each Whisper word:
   a. If word timestamp overlaps with laughter marker range → label=1
   b. If word is within 5s BEFORE a laughter marker → label=1 (punchline)
   c. Else → label=0
3. Output JSONL per language: {video_id, word, start, end, label, audio_file}
```

**Laughter markers to detect:**
```
en: [laughter], [laughing], [applause], [Applause], (audience laughing)
zh: [笑声], [笑], [掌声], [鼓掌]
hi: [हंसी], [ताली], [हंसते], [प्रशंसा]
```

### 4.2: Alignment Quality Checks

**Per-language validation:**
- Positive rate should be 8-15% (comedy norm)
- Rate <5% = likely non-comedy content → flag
- Rate >25% = possible over-triggering → review markers
- Check 50 random segments manually for label accuracy

---

## PHASE 5: FEATURE EXTRACTION + TRAINING (Week 4-5)

### 5.1: MFCC Pre-computation at Scale

**What:** 120-dim MFCC features per word for all 10M segments  
**Storage:** 10M × 120 × 4 bytes = ~4.8GB numpy (fits GDrive easily)  
**Time:** ~1 hour on RTX 4090 for 10M segments using torchaudio batch processing  
**Why pre-compute:** 10x faster training vs. on-demand audio loading

### 5.2: Per-Language Audio Models

**Train separately for each language:**

```bash
# English
python training/train_wav2vec2_audio.py \
  --features-dir gdrive:laughter_prediction/features/en/ \
  --aligned-file gdrive:laughter_prediction/aligned/en.jsonl \
  --lang en --batch-size 256 --epochs 10

# Chinese  
python training/train_wav2vec2_audio.py \
  --features-dir gdrive:laughter_prediction/features/zh/ \
  --aligned-file gdrive:laughter_prediction/aligned/zh.jsonl \
  --lang zh --batch-size 256 --epochs 10

# Hindi
python training/train_wav2vec2_audio.py \
  --features-dir gdrive:laughter_prediction/features/hi-latn/ \
  --aligned-file gdrive:laughter_prediction/aligned/hi-latn.jsonl \
  --lang hi-latn --batch-size 256 --epochs 10
```

**Training config:**
- Model: facebook/wav2vec2-base (95M params)
- Head: 2-layer MLP (768 → 256 → 2)
- Loss: CrossEntropyLoss with pos_weight=5.0
- Optimizer: AdamW, lr=1e-4, fp16, torch.compile
- DataLoader: num_workers=4, pin_memory=True

### 5.3: Multimodal Fusion

**Architecture:**
```
Text Branch:   XLM-R (768-dim) → projection (256-dim)
Audio Branch:  Wav2Vec2 (768-dim) → projection (256-dim)
Fusion:        [text_emb || audio_emb] → CrossAttention(6 layers)
Classifier:    512 → 256 → 2
```

**Train on:** Paired (text, audio, label) examples where both exist
**Target:** Multimodal F1 ≥ 0.75

---

## PHASE 6: EVALUATION + PAPER (Week 5-6)

### 6.1: Comprehensive Evaluation

**Metrics per language and per model:**
| Model | en F1 | zh F1 | hi F1 | Overall |
|-------|-------|-------|-------|---------|
| XLM-R text | | | | |
| Wav2Vec2 audio | | | | |
| Multimodal fusion | | | | |

**Ablations:**
- Text-only vs audio-only vs multimodal
- Per-language performance
- Effect of segment count on audio model (100K, 500K, 1M, 3M, 10M)

### 6.2: Paper Writing

**Venue:** ACL/EMNLP 2026 (or INTERSPEECH for audio focus)  
**Core claims (honest):**
- 10M word-level audio segments with laugh labels across 3 languages
- Wav2Vec2 + XLM-R multimodal fusion for laughter prediction
- Weak supervision from subtitle markers — no manual labeling
- Open-source pipeline from YouTube → trained model

---

## TIMELINE

```
WEEK 1  ████████  Phase 0: Extract 733K WAVs, validate data
        ████████  Phase 1: Train XLM-R text + Wav2Vec2 audio baselines

WEEK 2  ████████  Phase 2: Video discovery (find 3,400 videos)
        ████████  Phase 2: Start downloading batch by batch

WEEK 3  ████████  Phase 2: Continue downloads
        ████████  Phase 3: Whisper transcription (batch by language)

WEEK 4  ████████  Phase 3: Finish Whisper
        ████████  Phase 4: Alignment at scale → 10M segments
        ████████  Phase 5: MFCC pre-computation

WEEK 5  ████████  Phase 5: Train per-language audio models
        ████████  Phase 5: Multimodal fusion training

WEEK 6  ████████  Phase 6: Evaluation, ablations, paper writing
```

---

## COMPUTE REQUIREMENTS

| Task | GPU | Time | Cost |
|------|-----|------|------|
| Extract 733K WAV clips | CPU | 2 hrs | $0 |
| XLM-R text training | CPU | 3 hrs | $0 |
| Wav2Vec2 audio (733K) | RTX 4090 | 12 hrs | $0 |
| Whisper 3,700 videos | RTX 4090 | 21 hrs | $0 |
| Wav2Vec2 × 3 lang (10M) | RTX 4090 | 36 hrs | $0 |
| Multimodal fusion | RTX 4090 | 6 hrs | $0 |
| **TOTAL** | | **~80 hrs** | **$0** (owned GPU) |

**Colab fallback:** +40% time, ~$40-60 total (Colab Pro $10/mo × 2 months)

---

## SUCCESS CRITERIA

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Total segments | 10,000,000 | Line count in aligned JSONL |
| Languages | 3 (en, zh, hi-latn) | Unique language values |
| Positive rate | 8-15% | Label=1 count / total |
| Audio model F1 | ≥ 0.65 | Per-language weighted avg |
| Text model F1 | ≥ 0.82 | On merged_final test set |
| Multimodal F1 | ≥ 0.78 | On paired test set |
| Paper submitted | Yes | ArXiv / ACL submission |

---

## IMMEDIATE NEXT ACTIONS (TODAY)

1. **Create `training/extract_audio_segments.py`** — extract WAVs from 733K aligned segments
2. **Process batch15** — 214 MP3s already downloaded, just need transcripts
3. **Train XLM-R text baseline** — quick win, 3 hours on Mac
4. **Upload winning checkpoint** to GDrive before it's lost

---

## FILE MANIFEST (✅ = created, 🔄 = in progress, ⏳ = pending)

| Script | Purpose | Status |
|--------|---------|--------|
| `training/extract_audio_segments.py` | Extract WAV from aligned segments (librosa) | ✅ |
| `training/extract_audio_segments_fast.py` | Extract WAV using ffmpeg (100x faster) | ✅ |
| `training/train_wavlm_audio.py` | WavLM 3-phase training (frozen/partial/full) | ✅ |
| `training/train_wavlm_audio_v2.py` | WavLM on-the-fly loading (no pre-extraction) | ✅ |
| `training/find_comedy_videos.py` | YouTube search + filter by laugh density | ✅ |
| `training/download_audio_batch.py` | Parallel yt-dlp to GDrive/local | ✅ |
| `training/whisper_batch_gdrive.py` | Batch Whisper transcription | ✅ |
| `training/align_10m_segments.py` | VTT + Whisper alignment at scale | ✅ |
| `training/compute_mfcc_features.py` | Batch MFCC extraction | ⏳ |
| `training/train_fusion_model.py` | Multimodal cross-attention | ⏳ |

---

## SCALING TO 10M: QUICK START

```bash
# 1. Find videos (run for each language)
python training/find_comedy_videos.py --lang en --target 1200
python training/find_comedy_videos.py --lang zh --target 1000
python training/find_comedy_videos.py --lang hi-latn --target 1200

# 2. Download audio + VTT
python training/download_audio_batch.py --lang en --video-list data/video_candidates/en.json --workers 4

# 3. Whisper transcription (RTX 4090)
python training/whisper_batch_gdrive.py --lang en --model base --device cuda

# 4. Align to create labeled segments
python training/align_10m_segments.py --lang en \
  --audio-dir gdrive:laughter_prediction/audio/en \
  --transcript-dir gdrive:laughter_prediction/transcripts/en \
  --vtt-dir gdrive:laughter_prediction/vtt/en \
  --output gdrive:laughter_prediction/aligned/en.jsonl

# 5. Train WavLM on new data
python training/train_wavlm_audio_v2.py --phase C --epochs 10
```

---

**END OF EXECUTION PLAN**
