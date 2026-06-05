# Hindi/Hinglish Content Collection Plan (V8.1 Revised)

## Problem Statement
- Previous synthetic Hindi generation produced **100% laughter rate** (unrealistic)
- English/Zh data has ~35-40% laughter rate
- Hindi YouTube transcripts have **0% laughter** (no laughter markers in subtitles)

## Goal
Collect Hindi/Hinglish content with **realistic ~35% laughter rate**

---

## Strategy 1: Reddit Hindi/Hinglish Jokes (AUTOMATED)

### Why Reddit?
- r/IndiaBoleh, r/Jokes, r/indianjokes have user-annotated joke structures
- Comments often contain "lol", "ROFL", laughter markers
- 100% automated scraping

### Implementation
```python
# Scrape Hindi/Hinglish joke threads
# Identify punchlines from [removed] joke structures
# Mark laughter based on comment engagement (upvotes = funny)
# Target: 2,000 Hindi/Hinglish jokes with ~35% laughter rate
```

### Scripts Needed
- `scrape_reddit_hindi_jokes.py` - Scrape r/India, r/Jokes for Hindi content

---

## Strategy 2: Hindi News Article Humor (AUTOMATED)

### Why News?
- Headlines with wordplay/humor
- satirical articles from The Hindu, Indian Express
- Headline puns naturally have lower laughter density

### Implementation
```python
# Scrape Hindi news headlines
# Identify satirical headlines
# Mark as humor-positive with low laughter density (~20-30%)
```

---

## Strategy 3: Synthetic Generation with Realistic Rates (AUTOMATED)

### Problem with Previous Approach
Generated comedy lines → 100% have [LAUGHTER] → unrealistic

### New Approach: Two-Stage Generation
1. Generate regular Hindi conversational text (0% laughter)
2. Select ~35% and add [LAUGHTER] markers based on biosemotic rules

### Or: Generate Non-Comedy + Selective Labeling
```python
# Stage 1: Generate 2000 Hindi conversation lines (no comedy)
# Stage 2: Classify which are "setup" vs "punchline"
# Stage 3: Label only ~35% as having laughter trigger
```

---

## Strategy 4: StandupComedyDatabase Hindi (AUTOMATED)

### Why?
- Has structured comedian metadata
- Joke setups and punchlines already separated

### Implementation
```python
# Check StandupComedyDatabase for Hindi comedians
# List: Rajneesh Kumar, Sunil Grover, Amit Tandon, etc.
# Scrape their joke structures
```

---

## Strategy 5: Mix Existing Data (NO GENERATION)

### Current Assets
- `data/synthetic_hindi_mistral/`: 1,600 examples (100% laughter) - TOO HIGH
- `data/combined_multilingual/`: 38 Hindi examples (0% laughter) - TOO LOW

### Solution: Keep Only Real Data
- Drop synthetic Hindi (100% laughter is unrealistic)
- Keep the 38 real YouTube examples
- Collect new Reddit/News Hindi data with proper rates

---

## Revised Collection Targets

| Source | Target | Laughter Rate | Method |
|--------|--------|---------------|--------|
| Reddit Hindi/Hinglish | 2,000 | ~35% | Automated scrape + upvote-based classification |
| Hindi News Humor | 500 | ~25% | Automated scrape |
| YouTube transcripts (refine) | 500 | ~35% | Re-process with better laughter detection |
| Existing combined data | 38 | 0% | Keep, will be part of test set |
| **TOTAL** | **3,000** | **~32%** | |

---

## Implementation Plan

### Step 1: Scrape Reddit (Priority)
```bash
# Create scrape script
# Use Reddit JSON API (no auth needed for public data)
# Target: r/IndiaBoleh, r/Jokes, r/indianjokes
```

### Step 2: Process & Label
- Classify joke structures
- Map upvote ratios to laughter probability
- Generate word-level labels

### Step 3: Validate Laughter Rate
- Target: 30-40% laughter rate
- If too high: filter more aggressively
- If too low: supplement with news humor

### Step 4: Merge with Existing
- Add to `data/v8_1_final/` replacing synthetic Hindi

---

## Why This Works Better

1. **Real laughter markers** - Reddit has genuine user reactions
2. **Diverse content** - Not just comedy, includes conversations
3. **Automated classification** - Upvotes = humor signal
4. **Realistic rates** - Natural distribution from real data

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Hindi/Hinglish examples | 3,000+ | 1,638 (unrealistic rate) |
| Laughter rate | 30-40% | hi: 100%, hi-latn: 100% |
| Language distribution | hi 15-20% | hi: 0.4%, hi-latn: 16.6% |
| Word-level labels | 100% | 100% |

---

## Timeline

- **Day 1**: Reddit scraping script + first 500 examples
- **Day 2**: News humor scraping + validation
- **Day 3**: Merge, validate, final dataset

---

## Alternative: Use Existing en/zh Data as Reference

Since we know English (36.3%) and Zh (37.9%) have realistic rates, we can:
1. Analyze their word-level patterns
2. Use those patterns to guide Hindi generation
3. Force Hindi generation to match ~35% laughter rate

**Current Plan**: Reddit-based collection with upvote classification