#!/usr/bin/env python3
"""
Hindi/Hinglish Realistic Content Generator V2
Generates content with ~35% laughter rate (realistic, not 100%)
100% automated - no manual steps.
"""
import os
import requests
import json
import time
import random
import re
from pathlib import Path
from datetime import datetime

# Configuration
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/hindi_realistic_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Target: Generate diverse content, only ~35% will be marked as having laughter
# This is done by generating NON-LAUGHTER content and selectively adding markers

STYLE_TARGETS = {
    'vir_das': 250,      # Comedy style
    'zakir_khan': 250,    # Storytelling
    'biswa_kalyan_rath': 250,  # Witty
    'generic_hinglish': 300,   # Hinglish mix
    'pure_hindi': 300,    # Pure Hindi
    'indian_english': 200,     # Indian English content (not comedy)
}

PROMPTS = {
    # These generate content where only ~35% will get laughter markers
    'vir_das': '''Generate 20 Hindi/English mixed comedy lines (Vir Das style).
Include some lines that are:
- Setup only (no punchline, like "I went to the store and...")
- Punchline lines (ending in question or surprise)
Output ONLY JSON array:
[{"text":"line text without [LAUGHTER] marker","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'zakir_khan': '''Generate 20 Hindi storytelling lines (Zakir Khan style).
Include:
- Some regular conversation
- Some storytelling setups
- Some punchlines
Output ONLY JSON array:
[{"text":"Hindi line without [LAUGHTER]","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'biswa_kalyan_rath': '''Generate 20 witty Hindi/English lines (Biswa Kalyan Rath style).
Include mix of conversation, setups, and punchlines.
Output ONLY JSON array:
[{"text":"line without markers","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'generic_hinglish': '''Generate 20 Hinglish lines (Hindi + English mix).
Mix of:
- Simple conversations
- Question setups  
- Punchline endings
Output ONLY JSON array:
[{"text":"Hinglish line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'pure_hindi': '''Generate 20 pure Hindi lines (no English).
Include conversation and comedy elements.
Output ONLY JSON array:
[{"text":"Hindi line without markers","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'indian_english': '''Generate 20 Indian English conversation lines.
About daily life, observations, relatable content.
Output ONLY JSON array:
[{"text":"English line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:'''
}


def call_mistral(prompt: str) -> str:
    """Call Mistral API."""
    try:
        resp = requests.post(
            MISTRAL_URL,
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.8, "max_tokens": 2000},
            timeout=90
        )
        resp.raise_for_status()
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"  ❌ Mistral error: {e}")
        return ""


def parse_response(response: str) -> list:
    """Parse JSON from response."""
    if not response:
        return []
    
    # Clean markdown
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    
    arr_match = re.search(r'\[.*\]', response, re.DOTALL)
    if arr_match:
        try:
            data = json.loads(arr_match.group(0))
            if isinstance(data, list) and len(data) > 0:
                return data
        except:
            pass
    return []


def convert_to_training_format(items: list, style: str) -> list:
    """Convert to training format with REALISTIC ~35% laughter rate."""
    training = []
    
    for item in items:
        text = item.get("text", item.get("hindi", ""))
        item_type = item.get("type", "conversation")
        
        if not text or len(text) < 10:
            continue
        
        # Clean text
        text = text.replace('[LAUGHTER]', '').replace('[]', '').strip()
        words = text.split()
        n = len(words)
        
        if n < 4 or n > 35:
            continue
        
        # REALISTIC laughter assignment:
        # - punchline type → 70% chance of laughter
        # - setup type → 20% chance of laughter  
        # - conversation type → 15% chance of laughter
        if item_type == "punchline":
            has_laughter = random.random() < 0.70
            trigger_idx = max(2, n - random.randint(2, 5)) if has_laughter else -1
        elif item_type == "setup":
            has_laughter = random.random() < 0.20
            trigger_idx = max(2, n - random.randint(3, 6)) if has_laughter else -1
        else:  # conversation
            has_laughter = random.random() < 0.15
            trigger_idx = -1 if not has_laughter else random.randint(1, max(1, n-2))
        
        labels = [1 if i == trigger_idx else 0 for i in range(n)] if has_laughter and trigger_idx >= 0 else [0] * n
        
        # Language detection
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        is_hindi = hindi_chars >= 3 or style in ['vir_das', 'zakir_khan', 'biswa_kalyan_rath', 'pure_hindi']
        lang = "hi-latn" if is_hindi else "en"
        
        training.append({
            "example_id": f"realistic_{style}_{len(training)}",
            "language": lang,
            "comedian_id": f"realistic_{style}",
            "show_id": "hindi_realistic_v2",
            "words": words,
            "labels": labels,
            "label": 1 if has_laughter else 0,
            "is_sentence_level": False,
            "metadata": {
                "source": "mistral_realistic",
                "model": MODEL,
                "style": style,
                "item_type": item_type,
                "generated_at": datetime.now().isoformat()
            },
            **gen_features(words, trigger_idx if has_laughter else -1)
        })
    
    return training


def gen_features(words, trigger_idx):
    n = len(words)
    if trigger_idx < 0:
        return {
            'duchenne_joy_intensity': [0.15] * n,
            'duchenne_genuine_humor_probability': [0.15] * n,
            'duchenne_spontaneous_laughter_markers': [0.0] * n,
            'duchenne_setup_punchline_structure': ['neutral'] * n,
            'incongruity_expectation_violation_score': [0.25] * n,
            'incongruity_humor_complexity_score': [0.2] * n,
            'incongruity_resolution_time': [0.5] * n,
            'tom_speaker_intent_label': ['informative'] * n,
            'tom_speaker_intent_confidence': [0.6] * n,
            'tom_audience_perspective_score': [0.35] * n,
            'tom_social_context_humor_score': [0.25] * n,
            'tom_character_interaction_pattern': ['monologue'] * n,
            'tom_character_interaction_score': [0.0] * n
        }
    return {
        'duchenne_joy_intensity': [random.uniform(0.6, 0.9) if i == trigger_idx else random.uniform(0.1, 0.3) for i in range(n)],
        'duchenne_genuine_humor_probability': [random.uniform(0.6, 0.9) if i == trigger_idx else random.uniform(0.1, 0.3) for i in range(n)],
        'duchenne_spontaneous_laughter_markers': [0.0] * n,
        'duchenne_setup_punchline_structure': ['setup'] * trigger_idx + ['punchline'] + ['resolution'] * max(0, n - trigger_idx - 1),
        'incongruity_expectation_violation_score': [random.uniform(0.6, 0.9) if i == trigger_idx else random.uniform(0.1, 0.3) for i in range(n)],
        'incongruity_humor_complexity_score': [random.uniform(0.5, 0.8) if i == trigger_idx else random.uniform(0.1, 0.3) for i in range(n)],
        'incongruity_resolution_time': [random.uniform(0.1, 0.3) if i == trigger_idx else random.uniform(0.4, 0.6) for i in range(n)],
        'tom_speaker_intent_label': ['informative'] * n,
        'tom_speaker_intent_confidence': [random.uniform(0.6, 0.85) if i == trigger_idx else random.uniform(0.5, 0.7) for i in range(n)],
        'tom_audience_perspective_score': [random.uniform(0.6, 0.85) if i == trigger_idx else random.uniform(0.3, 0.5) for i in range(n)],
        'tom_social_context_humor_score': [random.uniform(0.5, 0.8) if i == trigger_idx else random.uniform(0.2, 0.4) for i in range(n)],
        'tom_character_interaction_pattern': ['monologue'] * n,
        'tom_character_interaction_score': [0.0] * n
    }


def save_jsonl(data, path):
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def main():
    print("=" * 70)
    print("HINDI REALISTIC CONTENT GENERATOR V2")
    print(f"Model: {MODEL}")
    print(f"Target: ~35% laughter rate")
    print("=" * 70)
    
    all_examples = []
    
    for style, target in STYLE_TARGETS.items():
        print(f"\n[Generating {style} - target: {target}]")
        prompt = PROMPTS.get(style, PROMPTS['generic_hinglish'])
        examples = []
        batch_num = 0
        
        while len(examples) < target:
            batch_num += 1
            response = call_mistral(prompt)
            
            if not response:
                time.sleep(3)
                continue
            
            items = parse_response(response)
            if items:
                batch = convert_to_training_format(items, style)
                examples.extend(batch)
                print(f"  Progress: {min(len(examples), target)}/{target} (batch #{batch_num})")
            else:
                print(f"  No parse from batch #{batch_num}")
            
            time.sleep(1.5)  # Rate limiting
        
        examples = examples[:target]
        all_examples.extend(examples)
        print(f"  ✓ {style}: {len(examples)} examples")
        
        # Periodic save
        random.shuffle(all_examples)
        n = len(all_examples)
        save_jsonl(all_examples[:int(0.8*n)], OUTPUT_DIR / "train.jsonl")
        save_jsonl(all_examples[int(0.8*n):int(0.9*n)], OUTPUT_DIR / "valid.jsonl")
        save_jsonl(all_examples[int(0.9*n):], OUTPUT_DIR / "test.jsonl")
    
    # Final split
    random.shuffle(all_examples)
    n = len(all_examples)
    train = all_examples[:int(0.8*n)]
    valid = all_examples[int(0.8*n):int(0.9*n)]
    test = all_examples[int(0.9*n):]
    
    save_jsonl(train, OUTPUT_DIR / "train.jsonl")
    save_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
    save_jsonl(test, OUTPUT_DIR / "test.jsonl")
    
    # Stats
    lang_counts = {}
    laugh_counts = {}
    for ex in train:
        lang = ex.get("language", "unknown")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        if ex.get("label") == 1:
            laugh_counts[lang] = laugh_counts.get(lang, 0) + 1
    
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print(f"Total: {n} examples")
    print(f"  Train: {len(train)}, Valid: {len(valid)}, Test: {len(test)}")
    print("\nLanguage & Laughter stats:")
    for lang in sorted(lang_counts.keys()):
        count = lang_counts[lang]
        laugh = laugh_counts.get(lang, 0)
        rate = 100 * laugh / count if count > 0 else 0
        print(f"  {lang}: {count} examples, {laugh} laughter ({rate:.1f}%)")
    
    print("=" * 70)


if __name__ == "__main__":
    main()