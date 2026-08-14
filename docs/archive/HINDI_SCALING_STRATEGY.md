# Hindi/Hinglish Scaling Strategy

**Date:** 2026-05-02
**Status:** 🚀 ACTIVE PLAN
**Target:** 4,000 Hindi/Hinglish examples with 35-40% laughter rate

---

## 🎯 Scaling Objectives

### Current State

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Examples | 48 | 4,000 | -3,952 |
| Words | 2,327 | 100,000+ | -97,673 |
| Laughter rate | 0% | 35-40% | -35-40% |
| Dataset % | 0.5% | 40% | -39.5% |
| Comedians | 1 (Vir Das) | 10+ | -9 |

### Success Criteria

- ✅ **4,000+ Hindi/Hinglish examples**
- ✅ **35-40% laughter rate** (balanced labels)
- ✅ **10+ comedians** (diverse styles)
- ✅ **Word-level labels** (accurate annotations)
- ✅ **Biosemotic features** (consistent with en/zh)

---

## 📊 Data Sources

### Source 1: YouTube with Professional Transcripts 🔴 HIGH PRIORITY

**Strategy:** Find comedy videos with:
- Netflix/Amazon Prime subtitles (include `[laughter]` markers)
- Professional captioning (not auto-generated)
- Manual fan transcriptions with audience reactions

**Target Comedians:**

| Comedian | Platform | Expected Yield | Status |
|----------|----------|----------------|--------|
| **Vir Das** | Netflix/YouTube | 800 words | ✅ 2,327 words done |
| **Zakir Khan** | Amazon Prime/YouTube | 1,500 words | 🔴 High priority |
| **Biswa Kalyan Rath** | Amazon Prime | 1,200 words | 🔴 High priority |
| **Kaneez Surka** | YouTube | 800 words | 🟡 Medium priority |
| **Atul Khatri** | YouTube | 600 words | 🟡 Medium priority |
| **Rohan Joshi** | YouTube | 500 words | 🟡 Medium priority |
| **Kunal Kamra** | YouTube | 500 words | 🟡 Medium priority |
| **Aditi Mittal** | YouTube | 400 words | 🟡 Medium priority |
| **Kenny Sebastian** | YouTube | 400 words | 🟡 Low priority |
| **Sumukhi Suresh** | YouTube | 300 words | 🟡 Low priority |

**Total target:** 6,000+ words → ~240 examples (25 words avg)

**Challenge:** YouTube videos currently unavailable
**Solution:**
1. Search for alternative video sources
2. Find fan-transcribed content
3. Use Netflix/Prime subtitle extraction
4. Manual annotation of available audio

---

### Source 2: Manual Annotation of Existing Audio 🔴 HIGH PRIORITY

**Strategy:** Manually annotate the 2 Vir Das videos we have

**Process:**
1. Listen to 2,327 words of Vir Das audio
2. Mark laughter timestamps manually
3. Convert to word-level labels
4. Expected: 30-40% laughter rate (typical comedy)

**Tools:**
- Audio annotation software (ELAN, Praat, or custom)
- Excel/Google Sheets for manual labeling
- Python script to convert to JSONL format

**Time Estimate:**
- 2,327 words / 150 words/min = ~15.5 min audio
- Annotation time: 3-5x real-time = 45-80 min
- **Total: 1-2 hours**

**Output:**
- 48 examples with accurate laughter labels
- Laughter rate: ~35-40%
- **Immediate benefit: Hindi evaluation possible**

**Priority:** 🔴 DO THIS FIRST (1-2 hours, high impact)

---

### Source 3: Synthetic Hindi/Hinglish Generation 🟡 MEDIUM PRIORITY

**Strategy:** Use LLM to generate Hindi/Hinglish comedy with laughter markers

**Prompt Template:**
```
You are generating stand-up comedy data for laughter prediction.
Generate 10 examples of Hindi/Hinglish comedy punchlines.
Each example should:
1. Be 10-20 words long
2. Contain clear humor (setup + punchline)
3. Mark the trigger word with [LAUGHTER]
4. Include translation in English
5. Mark language as "hi-latn" for Hinglish, "hi" for Hindi

Format: {"hindi": "...", "english": "...", "trigger_word_index": N, "language": "hi-latn"}
```

**Generation Plan:**

| Phase | Examples | Laughter Rate | Comedian Style | Timeline |
|-------|----------|---------------|----------------|----------|
| Phase 1 | 500 | 40% | Generic Hindi | 1 hour |
| Phase 2 | 500 | 40% | Zakir Khan style | 1 hour |
| Phase 3 | 500 | 40% | Vir Das style | 1 hour |
| Phase 4 | 500 | 40% | Biswa style | 1 hour |
| Phase 5 | 1,000 | 40% | Mixed styles | 2 hours |
| **TOTAL** | **3,000** | **40%** | **Diverse** | **6 hours** |

**Quality Control:**
- Review 10% of generated examples
- Verify laughter trigger accuracy
- Check language authenticity (Hindi vs Hinglish)
- Ensure biosemotic features make sense

**Output:**
- 3,000 synthetic examples
- 40% laughter rate (1,200 laughter examples)
- 2,000+ non-laughter examples

**Challenge:** Synthetic may not match real comedy
**Mitigation:**
- Mix with real data (70% real, 30% synthetic)
- Use human-in-the-loop for quality
- Validate on held-out test set

---

### Source 4: Hinglish Comedy Podcasts 🔴 HIGH PRIORITY

**Strategy:** Extract comedy from Hinglish podcasts with transcripts

**Target Sources:**
- **The Ranveer Show** (comedy episodes)
- **Aisi Taisi Democracy** (satire show)
- **The Viral Fever** (TVF podcasts)
- **Comedy Central Hindi** (podcasts)
- **BBC Hindi** (comedy segments)

**Process:**
1. Download podcast audio
2. Use Whisper for transcription
3. Identify comedy segments manually
4. Mark laughter triggers
5. Convert to training format

**Expected Yield:** 1,000-2,000 words
**Priority:** 🔴 High (real comedy, diverse content)

---

### Source 5: Existing Hindi Comedy Datasets 🟢 LOW PRIORITY

**Strategy:** Search for public Hindi comedy datasets

**Potential Sources:**
- **IndicNLP** (Hindi NLP corpora)
- **AI4Bharat** (Indian language datasets)
- **Hinglish datasets** (social media, code-mixed text)
- **Academic datasets** (search arXiv, papers with code)

**Challenge:** Likely no word-level laughter datasets
**Solution:**
- Use for non-laughter text
- Manually add laughter labels
- Augment with comedy content

---

## 📋 Tagging Strategy

### Problem
Current Hindi data has 0% laughter because:
1. YouTube transcripts don't include laughter markers
2. Whisper transcribes speech only
3. No audience reaction data

### Solution: Multi-Stage Tagging Pipeline

#### Stage 1: Manual Annotation (Priority: 🔴 HIGH)
**Target:** 2 Vir Das videos (48 examples, 2,327 words)

**Process:**
1. **Audio Review** - Listen to each segment
2. **Laughter Detection** - Mark when audience laughs
3. **Word Mapping** - Map laughter to trigger word
4. **Label Assignment** - Set `label=1` for trigger word

**Tool:** Simple web interface or spreadsheet

**Format:**
```csv
example_id,word,timestamp,has_laughter,trigger_word_index
indian_ufHrTI_E4Kk_0,"The",0.0,0,-1
indian_ufHrTI_E4Kk_0,"one",0.1,0,-1
indian_ufHrTI_E4Kk_0,"thing",0.2,0,-1
indian_ufHrTI_E4Kk_0,"joke",0.5,1,3  # Laughter here!
```

**Timeline:** 1-2 hours
**Output:** 48 examples with accurate labels

---

#### Stage 2: Weak Label Generation (Priority: 🟡 MEDIUM)
**Target:** 500+ examples from podcasts/new sources

**Process:**
1. **Audio Analysis** - Use audio features to detect laughter
   - Volume spikes
   - Laughter detection models (VoxCeleb, etc.)
   - Audio classification

2. **Heuristic Labeling** - Use comedy patterns
   - Punctuation markers (!, ...)
   - Setup-punchline structure
   - Language-specific humor patterns

3. **Teacher Model** - Use Nemotron/Qwen to identify triggers
   - Already tested on Hindi (all 0s, but pipeline works)
   - Provide examples with laughter for learning

**Tools:**
- `librosa` (audio analysis)
- `pyannote.audio` (speaker diarization)
- `webrtcvad` (voice activity detection)
- Custom laughter detection models

**Timeline:** 4-6 hours
**Output:** 500+ weakly labeled examples

---

#### Stage 3: Synthetic Generation (Priority: 🟡 MEDIUM)
**Target:** 3,000 examples

**Process:**
1. **LLM Generation** - Generate comedy with laughter markers
2. **Format Conversion** - Convert to training format
3. **Biosemotic Features** - Generate features (or use teacher)
4. **Quality Control** - Human review of 10%

**Prompt Engineering:**
```python
prompt = f"""
Generate {n} Hindi/Hinglish comedy examples.

Each example should have:
1. 10-20 words of comedy text
2. 1 trigger word marked with [LAUGHTER]
3. English translation
4. Language tag (hi or hi-latn)

Format JSON:
{{
  "text": "... [LAUGHTER] ...",
  "trigger_word_index": N,
  "language": "hi-latn",
  "translation": "..."
}}
"""
```

**Timeline:** 6 hours
**Output:** 3,000 synthetic examples

---

#### Stage 4: Semi-Supervised Refinement (Priority: 🟢 LOW)
**Target:** All examples

**Process:**
1. **Train initial model** on manually labeled data
2. **Predict** on unlabeled data
3. **High-confidence predictions** → auto-label
4. **Low-confidence** → human review
5. **Iterate** until convergence

**Tools:**
- Active learning frameworks
- Weak supervision (Snorkel)
- Human-in-the-loop (LabelStudio)

**Timeline:** Ongoing
**Output:** Continuously improving labels

---

## 🚀 Implementation Plan

### Phase 1: Quick Wins (Week 1)

| Task | Time | Output | Priority |
|------|------|--------|----------|
| Manual annotation of 2 Vir Das videos | 2 hours | 48 examples | 🔴 CRITICAL |
| Generate 500 synthetic Hindi examples | 1 hour | 500 examples | 🔴 HIGH |
| Search for alternative YouTube videos | 2 hours | Video list | 🔴 HIGH |
| **Total** | **5 hours** | **~548 examples** | **🔴** |

**Result:** Hindi becomes 5.5% of dataset (up from 0.5%)

---

### Phase 2: Scale Up (Week 2-3)

| Task | Time | Output | Priority |
|------|------|--------|----------|
| Generate 2,500 synthetic examples | 5 hours | 2,500 examples | 🔴 HIGH |
| Extract 1,000 words from podcasts | 4 hours | ~40 examples | 🟡 MEDIUM |
| Weak label 500 podcast examples | 3 hours | 500 examples | 🟡 MEDIUM |
| Collect YouTube data if available | 4 hours | 100+ examples | 🟡 MEDIUM |
| **Total** | **16 hours** | **~3,140 examples** | **🔴** |

**Result:** Hindi becomes 24% of dataset (approaching target)

---

### Phase 3: Target Achievement (Week 4)

| Task | Time | Output | Priority |
|------|------|--------|----------|
| Final synthetic generation (500) | 1 hour | 500 examples | 🟡 MEDIUM |
| Semi-supervised refinement | 4 hours | Improved labels | 🟢 LOW |
| Quality control & validation | 2 hours | Verified dataset | 🟡 MEDIUM |
| **Total** | **7 hours** | **~500 examples** | **🟡** |

**Result:** **4,000+ Hindi examples, 40% of dataset** ✅

---

## 📊 Expected Final Dataset

### Target Distribution (10,000 examples)

| Language | Examples | % | Laughter | Status |
|----------|----------|---|----------|--------|
| English | 5,000 | 50% | 1,850 (37%) | ✅ Ready |
| Chinese | 1,000 | 10% | 370 (37%) | ✅ Ready |
| **Hindi/Hinglish** | **4,000** | **40%** | **1,600 (40%)** | 🎯 **Target** |
| **TOTAL** | **10,000** | **100%** | **3,820 (38%)** | ✅ **Balanced** |

### Hindi/Hinglish Breakdown

| Source | Examples | Laughter | Type | Status |
|--------|----------|----------|------|--------|
| Manual annotation (Vir Das) | 48 | 19 (40%) | Real | ✅ Week 1 |
| Synthetic (generic) | 500 | 200 (40%) | Synthetic | ✅ Week 1 |
| Synthetic (Zakir Khan style) | 500 | 200 (40%) | Synthetic | ✅ Week 2 |
| Synthetic (Vir Das style) | 500 | 200 (40%) | Synthetic | ✅ Week 2 |
| Synthetic (Biswa style) | 500 | 200 (40%) | Synthetic | ✅ Week 2 |
| Podcast extraction | 1,000 | 350 (35%) | Real | ✅ Week 2 |
| Weak label generation | 500 | 175 (35%) | Weak | ✅ Week 2 |
| Synthetic (mixed) | 1,000 | 400 (40%) | Synthetic | ✅ Week 3 |
| Semi-supervised | 452 | 156 (35%) | Refined | ✅ Week 4 |
| **TOTAL** | **5,000** | **2,000** | **Mixed** | **✅ Target Met** |

---

## 🎯 Success Metrics

### Quantitative Metrics

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Hindi examples | 4,000 | 48 | -3,952 |
| Hindi % of dataset | 40% | 0.5% | -39.5% |
| Hindi laughter rate | 35-40% | 0% | -35-40% |
| Hindi comedians | 10+ | 1 | -9 |

### Qualitative Metrics

- ✅ **Diverse comedy styles** (observational, satirical, storytelling)
- ✅ **Authentic Hinglish** (code-mixed, not pure Hindi)
- ✅ **Cultural relevance** (Indian-specific humor)
- ✅ **Accurate laughter labels** (verified by human)
- ✅ **Consistent format** (matches en/zh structure)

---

## 📋 Risk Mitigation

### Risk 1: YouTube Videos Unavailable
**Mitigation:**
- Focus on podcasts with transcripts
- Manual annotation of existing audio
- Synthetic generation as backup

### Risk 2: Synthetic Data Quality
**Mitigation:**
- Human review of 10-20%
- Mix with real data (70/30)
- Use teacher model for refinement

### Risk 3: Manual Annotation Time
**Mitigation:**
- Start with 48 examples (quick win)
- Use weak supervision for scaling
- Semi-supervised learning for rest

### Risk 4: Hinglish vs Hindi Confusion
**Mitigation:**
- Clearly label language (hi vs hi-latn)
- Train separate models if needed
- Code-mixed text as separate category

---

## 🚀 Next Immediate Actions

### Today (2 hours)

1. **Manual annotation of Vir Das videos** ⏰ 2 hours
   - Listen to 2,327 words (~15.5 min audio)
   - Mark laughter triggers
   - Convert to training format
   - **Result:** 48 examples with 35-40% laughter

2. **Generate 500 synthetic examples** ⏰ 1 hour
   - Use LLM with comedy prompt
   - Generate Hindi and Hinglish
   - Verify quality
   - **Result:** 500 examples with 40% laughter

### This Week (8 hours)

1. **Generate 2,000 more synthetic examples** ⏰ 4 hours
2. **Search for podcast sources** ⏰ 2 hours
3. **Extract podcast comedy** ⏰ 2 hours

### Next 3 Weeks (20+ hours)

1. **Complete 4,000 example target**
2. **Quality control & validation**
3. **Merge with main dataset**
4. **Train and evaluate**

---

## 📊 Resource Requirements

### Tools & Libraries

| Tool | Purpose | Status |
|------|---------|--------|
| `openai-whisper` | Audio transcription | ✅ Installed |
| `librosa` | Audio analysis | 🔴 Need install |
| `pyannote.audio` | Speaker diarization | 🔴 Need install |
| `ollama` | Local LLM | ✅ Installed |
| `label-studio` | Manual annotation | 🔴 Optional |
| Excel/Sheets | Manual annotation | ✅ Available |

### Time Investment

| Phase | Hours | Output |
|-------|-------|--------|
| Quick wins | 5 | 548 examples |
| Scale up | 16 | 3,140 examples |
| Target achievement | 7 | 500 examples |
| **TOTAL** | **28 hours** | **4,000+ examples** |

---

## 🎉 Summary

**Goal:** Scale Hindi/Hinglish from 48 examples (0.5%) to 4,000 examples (40%)

**Strategy:**
1. 🔴 **Manual annotation** (quick win, 48 examples)
2. 🔴 **Synthetic generation** (main source, 3,000 examples)
3. 🟡 **Podcast extraction** (real data, 1,000 examples)
4. 🟢 **Semi-supervised** (refinement, ongoing)

**Timeline:** 4 weeks, 28 hours total

**Success Criteria:**
- ✅ 4,000+ Hindi/Hinglish examples
- ✅ 35-40% laughter rate
- ✅ 40% of dataset
- ✅ Diverse comedy styles

**Status:** 🚀 READY TO START

---

*Generated: 2026-05-02*
