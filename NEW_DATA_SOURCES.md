# New Comedy Transcript Data Sources

## Executive Summary

Successfully scraped **139 new comedy transcripts** with **8,149 [laughter] segments** from Scraps from the Loft, bringing the total potential training examples from ~102 to **8,149+** (based on individual laughter segment extraction).

## Data Sources Investigated

### 1. Scraps from the Loft (SUCCESSFUL)
**Status**: Successfully scraped 139 transcripts with laughter tags

**URL**: https://scrapsfromtheloft.com/comedy/

**Data Retrieved**:
- 139 comedy transcripts with [laughter] annotations
- 8,149 total [laughter] segments
- 1,212,627 total words
- 108 unique comedians/shows

**Laughter Tag Types Found**:
- `[chuckles]`: 94 transcripts
- `[laughs]`: 82 transcripts
- `[laughter]`: 65 transcripts
- `[laughing]`: 54 transcripts
- `[audience laughs]`: 40 transcripts
- `[snickers]`: 6 transcripts
- `[audience laughter]`: 4 transcripts

**Sample Transcripts**:
- Dave Chappelle: SNL Monologue (78 laughter segments)
- Hasan Minhaj: Off with His Head (177 laughter segments)
- Pete Davidson: Turbo Fonzarelli (89 laughter segments)
- Jack Whitehall: Settle Down (75 laughter segments)

**Scraping Method**:
- Extracted all `<p>` tag content from article pages
- Used regex to identify [laughter] annotations
- Threaded scraping with 4 workers for efficiency
- Total URLs found: 256 comedy transcripts (139 with laughter tags)

**Limitations**:
- Not all transcripts contain [laughter] tags
- Some transcripts are from non-US markets (UK comedians)
- No TV sitcom transcripts available on this source

---

### 2. OpenSubtitles API (BLOCKED)
**Status**: 403 Forbidden - Cloudflare protection

**URL**: https://www.opensubtitles.com/

**Issue**: Requires API key, site protected by Cloudflare

**Requirements for Access**:
- Free API key from opensubtitles.com
- API allows searching for subtitles with SDH (hearing-impaired) tags
- Would provide TV comedy subtitles with [laughter] annotations

---

### 3. Addic7ed (ACCESSIBLE but limited)
**Status**: Site accessible but JavaScript-rendered content

**URL**: https://www.addic7ed.com/

**Findings**:
- Contains TV comedy subtitles with SDH tags
- Requires JavaScript rendering to access content
- Would need Selenium/Playwright for scraping

**Potential**:
- TV sitcoms: Friends, The Big Bang Theory, The Office
- Would provide additional [laughter] tagged data

---

### 4. SubSlikescript (BLOCKED)
**Status**: 403 Forbidden

**URL**: https://subslikescript.com/

**Issue**: Cloudflare protection

---

### 5. StandUp4AI Dataset (NOT FOUND)
**Status**: GitHub repository not found

**Expected Repository**: https://github.com/StandUp4AI/standup4ai

**Note**: This EMNLP 2025 dataset would have provided 3,617 stand-up comedy videos with word-level laughter annotations

---

### 6. HuggingFace Datasets
**Status**: Found but limited

**Search Results**:
- `Helsinki-NLP/open_subtitles`: Large subtitle corpus but no laughter annotations
- `RayYuki/CodecBench_laughterscape_ver1.0`: Laughter detection dataset
- `mohammed-bahumaish/laughterscape-normalized`: Laughter detection dataset

---

### 7. Scraps from Loft Stand-Up Section (NO LAUGHTER TAGS)
**URL**: https://scrapsfromtheloft.com/stand-up-comedy-scripts/

**Status**: Contains transcripts but without [laughter] annotations

---

## Data Format

### Original Format (comprehensive_training_dataset.json)
```json
{
  "title": "Weather Small Talk #35",
  "type": "observational",
  "transcript_number": 35,
  "laughter_segments": [
    {"text": "[laughter]", "type": "discrete"},
    {"text": "[audience laughs]", "type": "continuous"}
  ],
  "total_laughter_count": 8,
  "discrete_laughter": 5,
  "continuous_laughter": 3,
  "wesr_bench_compliant": true
}
```

### New Scraped Format
```json
{
  "url": "https://scrapsfromtheloft.com/comedy/dave-chappelle-unstoppable-transcript/",
  "title": "Dave Chappelle: Unstoppable (2024) | Transcript",
  "laughter_count": 78,
  "laughter_types": ["[laughter]", "[audience laughs]"],
  "content": "Full transcript text with [laughter] tags...",
  "word_count": 8543
}
```

---

## Additional Sources to Explore

1. **TV Sitcom Subtitles via Addic7ed**
   - Would provide Friends, The Office, Big Bang Theory transcripts
   - Requires JavaScript rendering (Selenium/Playwright)

2. **YouTube Comedy Specials**
   - Would need yt-dlp for downloading
   - Then speech-to-text and laughter detection
   - Large video files (500MB-2GB per special)

3. **Podcast Transcripts**
   - Comedy Bang Bang, WTF with Marc Maron
   - Usually don't have [laughter] tags

4. **Netflix Comedy Specials**
   - Closed captions contain [laughter] tags
   - Would need screen recording or API access

---

## Summary Statistics

| Metric | Original | New | Combined |
|--------|----------|-----|----------|
| Full transcripts | 102 | 139 | 241 |
| Total [laughter] segments | ~500 | 8,149 | 8,649 |
| Total words | ~50,000 | 1,212,627 | 1,262,627 |
| Potential training examples | 102 | 8,149 | 8,249+ |

---

## Files Generated

- `/data/raw/scraped_comedy_transcripts.json` - Raw scraped transcripts (139)
- `/data/raw/comprehensive_training_dataset_merged.json` - Combined dataset (241 examples)
- `/data/raw/all_scraps_from_loft_urls.json` - All scraped URLs (256)

---

## Recommendations for Additional Data

1. **Immediate**: Use Selenium to scrape Addic7ed for TV sitcom subtitles
2. **Medium-term**: Access StandUp4AI dataset if repository becomes available
3. **Long-term**: Set up YouTube scraping pipeline for comedy specials
4. **Data Augmentation**: Generate synthetic [laughter] patterns from existing data

---

## Technical Notes

- Scrapping performed with Python `requests` + `BeautifulSoup4`
- 4 concurrent workers for parallel scraping
- Rate limiting: 0.3-0.5s delay between requests
- Total scraping time: ~15 minutes for 256 URLs
- Success rate: 54% (139/256 URLs had [laughter] tags)