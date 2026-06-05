# Multilingual Data Collection Plan - UPDATED
**Generated:** 2026-05-02
**Last Updated:** 2026-05-02

---

## Current Language Distribution

| Language | Code | Records | % of Total | Laughter Labels | Status |
|----------|------|---------|------------|-----------------|--------|
| English | `en` | 7,402 | 74.0% | ✅ 37% | ✅ Ready |
| Chinese | `zh` | 2,598 | 26.0% | ✅ 37% | ✅ Ready |
| **Hindi/Hinglish** | `hi`, `hi-latn` | 0 | 0% | - | 🔄 Collecting |

**Total current:** 10,000 records (2 languages)

---

## Target Multilingual Distribution

| Language | Target Records | Target % | Priority | Status |
|----------|---------------|----------|----------|--------|
| English | 5,000 | 45% | Baseline | ✅ Have |
| Hindi/Hinglish | 2,000 | 18% | 🔴 HIGH | 🔄 In Progress |
| Chinese | 1,000 | 9% | Baseline | ✅ Have |
| **Spanish** | ~~1,000~~ | ~~10%~~ | ~~MED~~ | ❌ **NOT NEEDED** |
| **French** | ~~500~~ | ~~5%~~ | ~~MED~~ | ❌ **NOT NEEDED** |
| Bengali | 500 | 5% | LOW | ⏸️ Optional |

**Target total:** ~11,000-12,000 records (3-4 languages)

---

## 🔴 HIGH PRIORITY: Hindi/Hinglish Collection

### Target Comedians

| Comedian | Platform | Language | Specials | Expected Yield |
|----------|----------|----------|----------|----------------|
| **Vir Das** | Netflix/YouTube | Hindi/Hinglish | 3+ | 2000+ words |
| **Zakir Khan** | YouTube | Hinglish | 5+ | 3000+ words |
| **Biswa Kalyan Rath** | Amazon Prime/YouTube | Hindi | 3+ | 1500+ words |
| **Kaneez Surka** | YouTube | Hinglish | 3+ | 1200+ words |
| **Atul Khatri** | YouTube | Hindi | 2+ | 800+ words |

**Target:** 1,000-2,000 examples in Hindi/Hinglish

### Collection Strategy

**Method 1: YouTubeTranscriptApi** (Preferred if unblocked)
```python
from youtube_transcript_api import YouTubeTranscriptApi
ytt = YouTubeTranscriptApi()
transcript = ytt.fetch('VIDEO_ID')
```

**Method 2: yt-dlp + Whisper** (Fallback if IP blocked)
```bash
yt-dlp -x --audio-format mp3 URL
whisper audio.mp3 --language hi --output_format json
```

### Video ID Search Terms
```
"Vir Das stand up Netflix"
"Zakir Khan haq se single"
"Biswa Kalyan Rath Biswa Mast Aadmi"
"Kaneez Surka comedy"
"Atul Khatri stand up"
```

---

## LOW PRIORITY: Bengali Collection (Optional)

| Comedian | Platform | Expected Yield |
|----------|----------|----------------|
| Mir Afsar Ali | YouTube | 1000+ words |
| Sourav Ghosh | YouTube | 800+ words |

**Target:** 500 examples in Bengali (optional)

---

## Data Processing Pipeline

### Step 1: Collection
```bash
python3 training/collect_indian_comedy.py
```

### Step 2: Processing
```bash
python3 training/process_youtube_transcripts.py --comedian "Vir Das"
```

### Step 3: Label Refinement
```bash
python3 /Users/Subho/training/refine_weak_labels_nemotron.py \
  --input-file data/processed/vir_das/train.jsonl \
  --output-file data/processed/vir_das/refined.jsonl \
  --backend ollama
```

### Step 4: Merge into training set
```bash
# Merge Hindi/Hinglish data into expanded_10k or create new dataset
```

---

## Expected Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Hindi/Hinglish collection | 1-2 hours | 1,000+ examples |
| Bengali collection (optional) | 30-60 min | 500+ examples |
| Processing & labeling | 1-2 hours | All data formatted |
| **Total** | **2-4 hours** | **1,500-2,500 multilingual examples** |

---

## Success Metrics

- ✅ Hindi/Hinglish: 1,000+ examples with word-level labels
- ✅ Bengali: 500+ examples (optional)
- ✅ Final dataset: 11,000-12,000 examples across 3-4 languages
- ✅ Language distribution: ~45% EN, ~18% HI, ~10% ZH, ~5% BN

---

## Next Steps

1. 🔄 Hindi/Hinglish collection (agent running now)
2. ⏸️ Process collected data
3. ⏸️ Merge into training set
4. ✅ Run V8.1 ablation on expanded multilingual dataset

---

*Status: Hindi/Hinglish collection in progress, Spanish/French NOT needed*
