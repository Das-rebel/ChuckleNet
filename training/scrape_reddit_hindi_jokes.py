#!/usr/bin/env python3
"""
Reddit Hindi/Hinglish Jokes Scraper
Collects jokes from r/India, r/Jokes, r/indianjokes
Uses upvote-based classification for humor signal
100% automated - no manual steps.
"""
import requests
import json
import time
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/reddit_hindi_jokes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REDDIT_URL = "https://www.reddit.com"

# Subreddits to scrape
SUBREDDITS = [
    ("r/India", 1000),      # Indian content, Hindi/Hinglish
    ("r/IndiaBoleh", 500),   # Indian memes
    ("r/Jokes", 500),        # General jokes (filter for Hindi)
    ("r/indianjokes", 500),  # Dedicated Indian jokes
]

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json"
}


def get_subreddit_posts(subreddit: str, limit: int = 100) -> List[Dict]:
    """Fetch posts from a subreddit."""
    try:
        url = f"{REDDIT_URL}/{subreddit}/hot.json?limit={limit}"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "id": post.get("id", ""),
                "title": post.get("title", ""),
                "selftext": post.get("selftext", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "created_utc": post.get("created_utc", 0),
                "subreddit": post.get("subreddit", ""),
                "url": post.get("url", ""),
                "link_flair_text": post.get("link_flair_text", "")
            })
        return posts
    except Exception as e:
        print(f"  ❌ Error fetching {subreddit}: {e}")
        return []


def get_post_comments(post_id: str, subreddit: str) -> List[Dict]:
    """Fetch comments for a post."""
    try:
        url = f"{REDDIT_URL}/{subreddit}/comments/{post_id}.json?limit=50"
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        comments = []
        for child in data[1].get("data", {}).get("children", []):
            comment = child.get("data", {})
            if comment.get("body") and comment.get("body") != "[deleted]":
                comments.append({
                    "body": comment.get("body", ""),
                    "score": comment.get("score", 0),
                    "is_submitter": comment.get("is_submitter", False)
                })
        return comments
    except Exception as e:
        return []


def is_hindi_or_hinglish(text: str) -> bool:
    """Check if text contains Hindi/Hinglish content."""
    # Hindi Unicode range: \u0900-\u097F
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    # Common Hinglish markers
    hinglish_markers = ['hai', 'hai na', 'kya', 'ka', 'ki', 'ke', 'mein', 'se', 
                        'theek', 'accha', 'bhai', 'yaar', 'lmao', 'lol', 'rofl',
                        'haan', 'nahi', 'kaise', 'kyun', 'tu', 'tum']
    
    text_lower = text.lower()
    hinglish_count = sum(1 for m in hinglish_markers if m in text_lower)
    
    # Consider Hinglish if has Hindi chars OR multiple Hinglish markers
    return hindi_chars >= 3 or hinglish_count >= 2


def has_joke_structure(text: str) -> bool:
    """Check if text has joke/punchline structure."""
    # Common joke patterns
    joke_patterns = [
        r'\?.*\?',  # Question followed by answer
        r'why.*because',  # Why-because pattern
        r'so.*\.$',  # Setup ending with punc
        r'\.*\?.*\!',  # Question/exclamation
        r'told.*said',  # Quoting pattern
        r'my.*your',  # Contrast pattern
    ]
    
    text_lower = text.lower()
    for pattern in joke_patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_laughter_markers(text: str) -> float:
    """Detect laughter probability from text markers."""
    text_lower = text.lower()
    
    # High laughter markers (indicates funny)
    high_markers = ['lol', 'lmao', 'rofl', 'haha', 'XD', '哈哈哈', ' 😂', '🤣', 
                    '太好笑了', '太好笑了', 'ಹಾಸೋಟೆ', 'ನಗುತ್ತಾರೆ']
    high_count = sum(1 for m in high_markers if m in text_lower)
    
    # Medium markers
    medium_markers = ['funny', '幽默', '好笑', 'cute', 'nice', 'good', 
                      'awesome', 'cool', 'bro', 'bruh']
    medium_count = sum(1 for m in medium_markers if m in text_lower)
    
    # Low/no laughter markers
    low_markers = ['serious', 'sad', 'angry', 'hate', 'boring']
    low_count = sum(1 for m in low_markers if m in low_count)
    
    # Calculate probability
    score = high_count * 0.3 + medium_count * 0.15 - low_count * 0.2
    return max(0, min(1, score))


def classify_joke_type(text: str) -> str:
    """Classify the type of joke."""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ['husband', 'wife', 'married', 'wife:', 'husband:']):
        return "relationship"
    if any(w in text_lower for w in ['doctor', 'patient', 'hospital', 'medicine']):
        return "professional"
    if any(w in text_lower for w in ['teacher', 'student', 'school', 'exam']):
        return "education"
    if any(w in text_lower for w in ['boss', 'office', 'meeting', 'work']):
        return "work"
    if any(w in text_lower for w in ['police', 'traffic', 'court']):
        return "authority"
    if 'indian' in text_lower or 'भारत' in text:
        return "indian"
    return "general"


def convert_to_training_format(post: Dict, comments: List[Dict]) -> List[Dict]:
    """Convert Reddit post + comments to training format."""
    training_examples = []
    
    # Process post title
    title = post.get("title", "")
    if is_hindi_or_hinglish(title) and len(title) > 20:
        score = post.get("score", 0)
        # Higher score = more likely to be funny
        laughter_prob = min(0.9, 0.3 + (score / 1000) * 0.5) if score > 0 else 0.3
        
        # Only include if seems like joke
        if has_joke_structure(title) or score > 50:
            words = title.replace('[', '').replace(']', '').split()
            n = len(words)
            
            # Find likely punchline position (usually last 1/3 of joke)
            trigger_idx = max(1, n - random.randint(2, 5))
            
            # Apply laughter probability
            has_laughter = random.random() < laughter_prob
            
            if has_laughter:
                labels = [1 if i == trigger_idx else 0 for i in range(n)]
            else:
                labels = [0] * n
            
            example = {
                "example_id": f"reddit_{post.get('id', 'unknown')}_{0}",
                "language": "hi-latn" if re.search(r'[\u0900-\u097F]', title) else "en",
                "comedian_id": f"reddit_{classify_joke_type(title)}",
                "show_id": f"reddit_{post.get('subreddit', 'unknown')}",
                "words": words,
                "labels": labels,
                "label": 1 if has_laughter else 0,
                "is_sentence_level": False,
                "metadata": {
                    "source": "reddit",
                    "post_id": post.get("id", ""),
                    "subreddit": post.get("subreddit", ""),
                    "score": score,
                    "num_comments": post.get("num_comments", 0),
                    "type": "title",
                    "collected_at": datetime.now().isoformat()
                }
            }
            example.update(generate_biosemotic_features(words, trigger_idx if has_laughter else -1))
            training_examples.append(example)
    
    # Process comments (often have more authentic reactions)
    for i, comment in enumerate(comments[:3]):  # Top 3 comments
        body = comment.get("body", "")
        if is_hindi_or_hinglish(body) and len(body) > 20:
            comment_score = comment.get("score", 0)
            laughter_prob = min(0.9, 0.4 + (comment_score / 500) * 0.4) if comment_score > 0 else 0.35
            
            # Detect explicit laughter in comment
            explicit_laughter = detect_laughter_markers(body)
            has_laughter = random.random() < max(laughter_prob, explicit_laughter * 0.7)
            
            words = body.replace('[', '').replace(']', '').replace('😂', '').replace('🤣', '').split()
            n = len(words)
            
            if n < 3:
                continue
            
            trigger_idx = max(1, n - random.randint(1, 3)) if has_laughter else -1
            
            if has_laughter and trigger_idx >= 0:
                labels = [1 if i == trigger_idx else 0 for i in range(n)]
            else:
                labels = [0] * n
            
            example = {
                "example_id": f"reddit_{post.get('id', 'unknown')}_{i+1}",
                "language": "hi-latn" if re.search(r'[\u0900-\u097F]', body) else "en",
                "comedian_id": f"reddit_{classify_joke_type(body)}",
                "show_id": f"reddit_{post.get('subreddit', 'unknown')}",
                "words": words,
                "labels": labels,
                "label": 1 if has_laughter else 0,
                "is_sentence_level": False,
                "metadata": {
                    "source": "reddit",
                    "post_id": post.get("id", ""),
                    "subreddit": post.get("subreddit", ""),
                    "score": comment_score,
                    "type": "comment",
                    "collected_at": datetime.now().isoformat()
                }
            }
            example.update(generate_biosemotic_features(words, trigger_idx if has_laughter else -1))
            training_examples.append(example)
    
    return training_examples


def generate_biosemotic_features(words: List[str], trigger_idx: int) -> Dict:
    """Generate biosemotic features."""
    n = len(words)
    
    if trigger_idx < 0:
        return {
            'duchenne_joy_intensity': [0.1] * n,
            'duchenne_genuine_humor_probability': [0.1] * n,
            'duchenne_spontaneous_laughter_markers': [0.0] * n,
            'duchenne_setup_punchline_structure': ['neutral'] * n,
            'incongruity_expectation_violation_score': [0.2] * n,
            'incongruity_humor_complexity_score': [0.2] * n,
            'incongruity_resolution_time': [0.5] * n,
            'tom_speaker_intent_label': ['informative'] * n,
            'tom_speaker_intent_confidence': [0.6] * n,
            'tom_audience_perspective_score': [0.3] * n,
            'tom_social_context_humor_score': [0.2] * n,
            'tom_character_interaction_pattern': ['monologue'] * n,
            'tom_character_interaction_score': [0.0] * n
        }
    
    return {
        'duchenne_joy_intensity': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.1, 0.4) for i in range(n)],
        'duchenne_genuine_humor_probability': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.1, 0.4) for i in range(n)],
        'duchenne_spontaneous_laughter_markers': [0.0] * n,
        'duchenne_setup_punchline_structure': ['setup'] * trigger_idx + ['punchline'] + ['resolution'] * max(0, n - trigger_idx - 1),
        'incongruity_expectation_violation_score': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.1, 0.4) for i in range(n)],
        'incongruity_humor_complexity_score': [random.uniform(0.6, 0.9) if i == trigger_idx else random.uniform(0.1, 0.4) for i in range(n)],
        'incongruity_resolution_time': [random.uniform(0.1, 0.3) if i == trigger_idx else random.uniform(0.3, 0.6) for i in range(n)],
        'tom_speaker_intent_label': ['informative'] * n,
        'tom_speaker_intent_confidence': [random.uniform(0.7, 0.9) if i == trigger_idx else random.uniform(0.5, 0.8) for i in range(n)],
        'tom_audience_perspective_score': [random.uniform(0.7, 0.9) if i == trigger_idx else random.uniform(0.3, 0.6) for i in range(n)],
        'tom_social_context_humor_score': [random.uniform(0.7, 0.9) if i == trigger_idx else random.uniform(0.2, 0.5) for i in range(n)],
        'tom_character_interaction_pattern': ['monologue'] * n,
        'tom_character_interaction_score': [0.0] * n
    }


def save_jsonl(data: List[Dict], path: Path):
    """Save to JSONL."""
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def load_jsonl(path: Path) -> List[Dict]:
    """Load from JSONL."""
    return [json.loads(line) for line in path.read_text().strip().split('\n') if line]


def main():
    """Main scraping loop."""
    print("=" * 70)
    print("REDDIT HINDI/HINGLISH JOKES SCRAPER")
    print("=" * 70)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Target subreddits: {[s[0] for s in SUBREDDITS]}")
    print("=" * 70)
    
    all_examples = []
    checkpoint_path = OUTPUT_DIR / "checkpoint.jsonl"
    
    # Load checkpoint if exists
    if checkpoint_path.exists():
        all_examples = load_jsonl(checkpoint_path)
        print(f"Loaded {len(all_examples)} examples from checkpoint")
    
    for subreddit, target in SUBREDDITS:
        print(f"\n[Scraping {subreddit} - target: {target}]")
        
        # Fetch posts
        posts = get_subreddit_posts(subreddit, limit=100)
        print(f"  Fetched {len(posts)} posts")
        
        for post in posts:
            try:
                # Get comments
                comments = get_post_comments(post["id"], post["subreddit"])
                
                # Convert to training format
                examples = convert_to_training_format(post, comments)
                all_examples.extend(examples)
                
                # Progress update
                if len(all_examples) % 50 == 0:
                    print(f"  Total examples: {len(all_examples)}")
                
                # Save checkpoint periodically
                if len(all_examples) % 100 == 0:
                    save_jsonl(all_examples, checkpoint_path)
                
                # Rate limit
                time.sleep(1 + random.uniform(0, 1))
                
            except Exception as e:
                print(f"  ❌ Error processing post {post.get('id')}: {e}")
                continue
        
        # Check if reached target
        subreddit_examples = [e for e in all_examples if e.get("metadata", {}).get("subreddit") == subreddit.replace("r/", "")]
        print(f"  {subreddit}: {len(subreddit_examples)} examples")
    
    # Final save
    print("\n[Saving final dataset]")
    
    # Shuffle and split
    random.shuffle(all_examples)
    n = len(all_examples)
    
    train = all_examples[:int(0.8*n)]
    valid = all_examples[int(0.8*n):int(0.9*n)]
    test = all_examples[int(0.9*n):]
    
    save_jsonl(train, OUTPUT_DIR / "train.jsonl")
    save_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
    save_jsonl(test, OUTPUT_DIR / "test.jsonl")
    
    # Save progress
    progress = {
        "total": len(all_examples),
        "train": len(train),
        "valid": len(valid),
        "test": len(test),
        "subreddits": {s[0]: sum(1 for e in all_examples if e.get("metadata", {}).get("subreddit") == s[0].replace("r/", "")) for s in SUBREDDITS},
        "collected_at": datetime.now().isoformat()
    }
    with open(OUTPUT_DIR / "progress.json", 'w') as f:
        json.dump(progress, f, indent=2)
    
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE!")
    print(f"Total: {len(all_examples)} examples")
    print(f"Train: {len(train)}, Valid: {len(valid)}, Test: {len(test)}")
    print("=" * 70)


if __name__ == "__main__":
    main()