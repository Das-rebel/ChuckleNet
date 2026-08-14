#!/usr/bin/env python3
"""
Hindi/Hinglish synthetic data generation using Sarvam AI API.
Optimized for speed - generates 20 examples per API call.
Uses sarvam-m (legacy 24B) model - no reasoning traces.
"""
import requests
import json
import time
import random
from pathlib import Path
from typing import List, Dict

# Configuration
SARVAM_API_KEY = "sk_0ct1mbzm_wsoETmHdputtlGmsowQgnd7K"
SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/synthetic_hindi_sarvam")
MODEL = "sarvam-m"  # Legacy 24B - no reasoning traces

# Prompt templates - request 20 at a time for speed
PROMPTS = {
    'vir_das': '''Generate EXACTLY 20 Hindi comedy lines in Vir Das style.
Each line MUST have [LAUGHTER] marker AFTER the punchline word.
Output format - ONLY valid JSON array, NO other text:
[
  {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"},
  ... (20 items total)
]
Example: {"hindi": "मैं कल तुमसे मिला [LAUGHTER] और बहुत खुश हुआ", "trigger": 4, "lang": "hi-latn"}
Generate NOW - 20 lines:''',

    'zakir_khan': '''Generate EXACTLY 20 Hindi comedy lines in Zakir Khan storytelling style.
Each line MUST have [LAUGHTER] marker AFTER the punchline word.
Output format - ONLY valid JSON array, NO other text:
[
  {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"},
  ... (20 items total)
}
Generate NOW - 20 lines:''',

    'biswa_kalyan_rath': '''Generate EXACTLY 20 witty Hindi comedy lines in Biswa Kalyan Rath style.
Each line MUST have [LAUGHTER] marker AFTER the punchline word.
Output format - ONLY valid JSON array, NO other text:
[
  {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"},
  ... (20 items total)
]
Generate NOW - 20 lines:''',

    'generic_hinglish': '''Generate EXACTLY 20 Hinglish comedy lines (Hindi + English mix).
Each line MUST have [LAUGHTER] marker AFTER the punchline word.
Output format - ONLY valid JSON array, NO other text:
[
  {"hindi": "I went to market [LAUGHTER] and everyone stared", "trigger": 5, "lang": "hi-latn"},
  ... (20 items total)
]
Generate NOW - 20 lines:''',

    'pure_hindi': '''Generate EXACTLY 20 pure Hindi comedy lines (no English words).
Each line MUST have [LAUGHTER] marker AFTER the punchline word.
Output format - ONLY valid JSON array, NO other text:
[
  {"hindi": "आज मैं घर गया [LAUGHTER] और सबने प्यार किया", "trigger": 4, "lang": "hi"},
  ... (20 items total)
]
Generate NOW - 20 lines:'''
}

STYLE_TARGETS = {
    'vir_das': 400,
    'zakir_khan': 400,
    'biswa_kalyan_rath': 400,
    'generic_hinglish': 400,
    'pure_hindi': 400
}


def call_sarvam(prompt: str) -> str:
    """Call Sarvam API - sarvam-m model, no reasoning."""
    try:
        response = requests.post(
            SARVAM_API_URL,
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.8
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Strip <V> tags
        if content:
            import re
            content = re.sub(r'<V>\s*', '', content)
            content = re.sub(r'\s*</V>', '', content)
        
        return content.strip()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return ""


def parse_response(response: str) -> List[Dict]:
    """Parse JSON array from response."""
    if not response:
        return []
    
    # Try direct JSON array parse first
    import re
    examples = []
    
    # Remove thinking tags if any
    response = re.sub(r'<V>.*?</V>\s*', '', response, flags=re.DOTALL)
    
    # Find JSON array
    array_match = re.search(r'\[\s*\{[^]]+\}\s*\]', response, re.DOTALL)
    if array_match:
        try:
            parsed = json.loads(array_match.group(0))
            if isinstance(parsed, list):
                for item in parsed:
                    if validate_example(item):
                        examples.append(normalize_example(item))
                if examples:
                    return examples
        except json.JSONDecodeError:
            pass
    
    # Try finding individual JSON objects
    json_objects = re.findall(r'\{[^{}]+\}', response)
    for json_str in json_objects:
        try:
            data = json.loads(json_str)
            if validate_example(data):
                examples.append(normalize_example(data))
        except json.JSONDecodeError:
            continue
    
    return examples


def validate_example(data: Dict) -> bool:
    """Validate required fields."""
    hindi = data.get('hindi', '')
    return len(hindi) > 10 and '[LAUGHTER]' in hindi


def normalize_example(data: Dict) -> Dict:
    """Normalize example format."""
    hindi = data.get('hindi', '')
    lang = data.get('lang', 'hi-latn')
    if lang not in ['hi', 'hi-latn']:
        lang = 'hi-latn'
    
    # Find trigger position from [LAUGHTER]
    temp_text = hindi
    laughter_pos = -1
    word_count = 0
    while True:
        pos = temp_text.find('[LAUGHTER]')
        if pos == -1:
            break
        before = temp_text[:pos].replace('[LAUGHTER]', '').strip().split()
        laughter_pos = len(before) - 1
        temp_text = temp_text[pos + len('[LAUGHTER]'):]
        if laughter_pos >= 0:
            break
    
    if laughter_pos < 0:
        laughter_pos = data.get('trigger', 3)
    
    return {
        'hindi': hindi,
        'trigger': laughter_pos,
        'lang': lang,
        'style': data.get('style', 'unknown')
    }


def convert_to_training_format(examples: List[Dict], style: str) -> List[Dict]:
    """Convert to training format with biosemotic features."""
    training = []
    for ex in examples:
        words = ex['hindi'].replace('[LAUGHTER]', '').strip().split()
        trigger_idx = ex.get('trigger', 0)
        n = len(words)
        
        labels = [1 if i == trigger_idx else 0 for i in range(n)]
        
        example = {
            'example_id': f"sarvam_{style}_{len(training)}",
            'language': ex.get('lang', 'hi-latn'),
            'comedian_id': style,
            'show_id': 'synthetic_sarvam',
            'words': words,
            'labels': labels,
            'label': 1,
            'is_sentence_level': False,
            'metadata': {
                'source': 'sarvam_api',
                'model': MODEL,
                'style': style,
                'generation_date': time.strftime('%Y-%m-%d')
            }
        }
        
        # Add biosemotic features
        example.update(generate_biosemotic_features(words, trigger_idx))
        training.append(example)
    
    return training


def generate_biosemotic_features(words: List[str], trigger_idx: int) -> Dict:
    """Generate biosemotic features."""
    n = len(words)
    return {
        'duchenne_joy_intensity': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.0, 0.3) for i in range(n)],
        'duchenne_genuine_humor_probability': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.0, 0.3) for i in range(n)],
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


def main():
    """Main generation loop."""
    print("=" * 70)
    print("HINDI GENERATION USING SARVAM AI (FAST - 20 per call)")
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Target: {sum(STYLE_TARGETS.values())} examples")
    print("=" * 70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_examples = []
    
    for style, target in STYLE_TARGETS.items():
        print(f"\n[Generating {style} ({target} examples)]")
        prompt_template = PROMPTS.get(style, PROMPTS['generic_hinglish'])
        examples = []
        batch_size = 20
        batch_count = 0
        
        while len(examples) < target:
            batch_count += 1
            
            response = call_sarvam(prompt_template)
            if not response:
                time.sleep(2)
                continue
            
            batch = parse_response(response)
            if batch:
                examples.extend(batch)
                print(f"  Progress: {min(len(examples), target)}/{target} (batch #{batch_count})")
            
            time.sleep(0.5)  # Rate limiting
        
        # Trim to target
        examples = examples[:target]
        
        # Convert to training format
        training = convert_to_training_format(examples, style)
        all_examples.extend(training)
        
        # Save checkpoint
        print(f"  Saving {len(training)} examples...")
        random.shuffle(all_examples)
        n = len(all_examples)
        train = all_examples[:int(0.8*n)]
        valid = all_examples[int(0.8*n):int(0.9*n)]
        test = all_examples[int(0.9*n):]
        
        save_jsonl(train, OUTPUT_DIR / "train.jsonl")
        save_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
        save_jsonl(test, OUTPUT_DIR / "test.jsonl")
        
        # Progress file
        progress = {
            "style": style,
            "total_generated": len(all_examples),
            "target": sum(STYLE_TARGETS.values()),
            "pct": round(100 * len(all_examples) / sum(STYLE_TARGETS.values()), 1)
        }
        with open(OUTPUT_DIR / "progress.json", 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(f"  ✓ {style} complete: {len(training)} examples")
    
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print(f"Total: {len(all_examples)} examples")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()