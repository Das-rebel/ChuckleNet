#!/usr/bin/env python3
"""
Expand Hindi/Hinglish content to reach 2000 examples.
Generates additional diverse content with realistic ~35% laughter rate.
"""
import requests
import json
import time
import random
import re
from pathlib import Path
from datetime import datetime
import os

MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-small-latest"

OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/hindi_expand")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Generate more of each style to reach 2000 total
STYLE_TARGETS = {
    'vir_das_extra': 200,
    'zakir_khan_extra': 200,
    'biswa_kalyan_rath_extra': 200,
    'pure_hindi_extra': 200,
    'hinglish_extra': 200,
    'desi_conversation': 175,
}

PROMPTS = {
    'vir_das_extra': '''Generate 20 Hindi/English mixed comedy lines (Vir Das style).
Include mix of: conversation, setups, and punchlines.
Output ONLY JSON array:
[{"text":"Hindi-English line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'zakir_khan_extra': '''Generate 20 Hindi storytelling lines (Zakir Khan style).
Include storytelling elements and some humor.
Output ONLY JSON array:
[{"text":"Hindi line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'biswa_kalyan_rath_extra': '''Generate 20 witty Hindi/English lines (Biswa Kalyan Rath style).
Dry humor and observational comedy.
Output ONLY JSON array:
[{"text":"Hinglish line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'pure_hindi_extra': '''Generate 20 pure Hindi lines (no English words).
Everyday conversations and observations.
Output ONLY JSON array:
[{"text":"Pure Hindi line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'hinglish_extra': '''Generate 20 Hinglish lines ( Hindi + English mix).
About daily Indian life, relatable content.
Output ONLY JSON array:
[{"text":"Hinglish line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',

    'desi_conversation': '''Generate 20 Indian conversation lines.
Simple daily conversations, no explicit comedy.
Output ONLY JSON array:
[{"text":"Conversation line","type":"setup|punchline|conversation"},{"text":"...","type":"..."}]
Generate NOW - 20 items:''',
}


def call_mistral(prompt: str) -> str:
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
    if not response:
        return []
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
    training = []
    for item in items:
        text = item.get("text", "")
        item_type = item.get("type", "conversation")
        
        if not text or len(text) < 10:
            continue
        
        text = text.replace('[LAUGHTER]', '').replace('[]', '').strip()
        words = text.split()
        n = len(words)
        
        if n < 4 or n > 35:
            continue
        
        # Realistic laughter assignment
        if item_type == "punchline":
            has_laughter = random.random() < 0.65
            trigger_idx = max(2, n - random.randint(2, 5)) if has_laughter else -1
        elif item_type == "setup":
            has_laughter = random.random() < 0.20
            trigger_idx = max(2, n - random.randint(3, 6)) if has_laughter else -1
        else:
            has_laughter = random.random() < 0.15
            trigger_idx = -1 if not has_laughter else random.randint(1, max(1, n-2))
        
        labels = [1 if i == trigger_idx else 0 for i in range(n)] if has_laughter and trigger_idx >= 0 else [0] * n
        
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        is_hindi = hindi_chars >= 3 or 'extra' in style or 'desi' in style
        lang = "hi-latn" if is_hindi else "en"
        
        training.append({
            "example_id": f"expand_{style}_{len(training)}",
            "language": lang,
            "comedian_id": f"expand_{style}",
            "show_id": "hindi_expand",
            "words": words,
            "labels": labels,
            "label": 1 if has_laughter else 0,
            "is_sentence_level": False,
            "metadata": {
                "source": "mistral_expand",
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
    print("EXPANDING HINDI/HINGLISH TO 2000")
    print(f"Target: 1175 new examples")
    print("=" * 70)
    
    all_examples = []
    
    for style, target in STYLE_TARGETS.items():
        print(f"\n[Generating {style} - target: {target}]")
        prompt = PROMPTS.get(style, PROMPTS['hinglish_extra'])
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
                print(f"  No parse batch #{batch_num}")
            
            time.sleep(1.5)
        
        examples = examples[:target]
        all_examples.extend(examples)
        print(f"  ✓ {style}: {len(examples)} examples")
    
    # Save
    random.shuffle(all_examples)
    n = len(all_examples)
    save_jsonl(all_examples, OUTPUT_DIR / "expanded.jsonl")
    
    # Stats
    hindi_count = sum(1 for ex in all_examples if ex.get('language') == 'hi-latn')
    en_count = sum(1 for ex in all_examples if ex.get('language') == 'en')
    laugh_count = sum(1 for ex in all_examples if ex.get('label') == 1)
    
    print()
    print("=" * 70)
    print("EXPANSION COMPLETE!")
    print(f"New examples: {n}")
    print(f"  Hindi/Hinglish (hi-latn): {hindi_count}")
    print(f"  English (en): {en_count}")
    print(f"  Laughter: {laugh_count} ({100*laugh_count/n:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()