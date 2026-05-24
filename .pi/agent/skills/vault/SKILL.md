---
name: vault
description: >
  Search the OmniClaw personal knowledge vault (bookmarks, tweets, Instagram posts).
  Use when user says "search vault", "/vault <query>", "find in my bookmarks",
  "search my knowledge graph", "look up ideas", "find concepts", "search for <topic>"
  in the vault/personal knowledge graph.
---

Search vault knowledge base for ideas, concepts, and relevant content.

## How to Execute

### Step 1: Extract Keywords from Natural Language Query

**Input:** "find me ideas to improve or post about it easily"
**Stopwords removed:** a, an, the, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, can, to, of, in, for, on, with, at, by, from, as, or, and, but, find, me, my, i, want, need, look, up, search, get, give, some, ideas

**Keywords:** `improve post ideas`
**Bigrams:** `post about` (if both words are keywords)

### Step 2: Build Search URL (CRITICAL - use single q= parameter)

```
GET https://serve-vault-search-338789220059.asia-south1.run.app/search?q=<KEYWORDS>&limit=5
```

**WRONG:** `?q=llm&q=routing&q=npm` (this causes 404)
**RIGHT:** `?q=llm%20routing%20npm` (single q= with URL-encoded spaces)

For "LLM routing npm growth":
- Keywords: `llm routing npm growth`
- URL: `https://serve-vault-search-338789220059.asia-south1.run.app/search?q=llm%20routing%20npm%20growth&limit=5`

### Step 3: Parse Results

Parse the JSON response. Format results with:
- Source icon: 🐦 Twitter, 📷 Instagram
- Title (name field)
- Caption snippet (truncated to 100 chars)
- **Topic** (what post is about - from TEXT, highlighted)
- **Visual description** (what image shows - from BLIP, de-emphasized)
- URL link if present

## Response Format

Present as a clean bulleted list or numbered list with source icons.
Highlight the **topic** field (extracted from post text) over visual metadata.
If no results, try broader keywords.

## Keyword Extraction Examples

| Natural Language | Keywords | Notes |
|-----------------|----------|-------|
| "find me ideas to improve or post about it easily" | `improve post ideas` | Remove stopwords |
| "how to get more npm downloads" | `npm downloads growth` | "get" removed |
| "developer tool marketing ideas" | `developer tool marketing` | |
| "open source launch strategy" | `open source launch` | |
| "LLM routing best practices" | `llm routing` | |
| "AI agent framework comparison" | `ai agent framework` | |
| "bookmarked github repos" | `github repos` | Remove "bookmarked" |

## Search Priority (v3)

The vault now prioritizes text content over visual metadata:
1. **content** (1.0) - Post text, captions - HIGHEST
2. **topic** (0.8) - Topic extracted from text
3. **name** (0.6) - Username/title
4. **visual_description** (0.2) - What image shows - LOWEST
5. **vlTags** (0.1) - Visual tags from BLIP - IGNORE

## Context

Vault contains 16,000+ bookmarks (12,000 Twitter + 4,000 Instagram).
SQLite-based full-text search with keyword matching.

## Troubleshooting

If no results:
1. Try fewer keywords (2-3 most important)
2. Try single keyword search
3. Check if keyword contains stopwords that weren't filtered

## Trigger

Any of:
- "/vault"
- "search vault"
- "search my knowledge graph"
- "find in bookmarks"
- "look up in vault"