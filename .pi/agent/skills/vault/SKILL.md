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

Remove stopwords and keep meaningful words (length > 2).

**Stopwords to remove:**
a, an, the, is, are, was, were, be, been, being, have, has, had, do, does, did, will, would, could, should, may, might, can, to, of, in, for, on, with, at, by, from, as, or, and, but, find, me, my, i, want, need, look, up, search, get, give, some, ideas, about, what, how, who, when, where, why, which, that, this, these, those, it, its, they, them, their, we, us, our, you, your, please, help, thanks, thank, recently, bookmark, bookmarked, bookmarks, just, like, really

**Examples:**

| Input | Keywords |
|-------|----------|
| "find ideas to improve posting" | `improve posting` |
| "how to get npm downloads" | `npm downloads` |
| "developer tool marketing" | `developer tool marketing` |
| "github linked repos" | `github repos` |
| "recently bookmarked twitter threads" | `twitter threads` |

### Step 2: Build Search URL

```
GET https://serve-vault-search-338789220059.asia-south1.run.app/search?q=<KEYWORDS>&limit=5
```

**CRITICAL:** Use single `q=` parameter with URL-encoded spaces (NOT multiple `&q=` params).

- ❌ WRONG: `?q=llm&q=routing&q=npm`
- ✅ RIGHT: `?q=llm%20routing%20npm`

### Step 3: Parse and Format Results

The API returns JSON with this structure:
```json
{
  "query": "github repos",
  "count": 5,
  "results": [
    {
      "id": "tw_8200",
      "type": "twitter_tweet",
      "name": "@username",
      "content": "post text...",
      "url": "https://x.com/...",
      "topic": "AI/ML, Developer",
      "score": 2.82,
      "visual_description": "a man with a beard",
      "metadata": {
        "vlTags": ["tech", "landscape"],
        "vlMood": "Vibrant",
        "narrative": "description",
        "visual_description": "a man with a beard"
      }
    }
  ]
}
```

**Format each result like this:**

- **Icon by type:**
  - `twitter_tweet` → 🐦 Twitter
  - `instagram_post` → 📷 Instagram  
  - `entity` → skip (entities have no useful content)
  - default → 🌐 Link

- **Title:** (CRITICAL - read this carefully)
  - If `name` field has ANY value (including '@username') → use it as-is
  - If `name` field is EMPTY ('') for instagram_post → MUST use first 50 chars of `content` as title
  - If `name` field is EMPTY ('') for entity → SKIP this result entirely
  
  **COMMON BUG TO AVOID:** When `name=''` for instagram_post, do NOT show 'Untitled'. You MUST use `content[:50]` as the title instead.

- **Caption:** Show first 120 chars of `content`. If content is empty, skip this result.

- **Topic:** Show `topic` field if present (e.g., "AI/ML, Developer"). Skip if empty.

- **Visual description:** Show `visual_description` field if present. Add: 📸 "description"

- **URL:** Show `url` field after the content

**Important:** Skip any result where both `name` AND `content` are empty/null. These are entities that add no value.

### Response Format

Present results as a numbered list. If no results, try broader keywords.

## Examples

**Query:** "github repos"
```
1. 🐦 @gusik4ever — the fastest growing GitHub repos in finance this week...
   🏷 AI/ML, Developer
   https://x.com/gusik4ever/status/...
```

**Query:** "AI tools"
```
1. 📷 — This Free AI Just Killed Paid Web Scraping Tools...
   🏷 Developer, AI Tools, AI/ML
   📸 a man with a beard and a black shirt
```

## Context

Vault contains 16,000+ bookmarks (12,000 Twitter + 4,000 Instagram).
SQLite-based keyword search with +1000 char content + BLIP visual descriptions.

## Trigger

Any of:
- "/vault"
- "search vault"
- "search my knowledge graph"
- "find in bookmarks"
- "look up in vault"
- "vault results for"
- "🔍 vault"
- "check vault"
- "recheck vault"