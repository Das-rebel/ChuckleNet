#!/usr/bin/env python3
"""
Hindi/Hinglish synthetic data generation using Sarvam AI API.
Optimized for Indic languages (Hindi, Hinglish, Bengali, etc.)
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

# Use sarvam-m (legacy 24B) - no reasoning traces unlike sarvam-30b/105b
MODEL = "sarvam-m"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Prompt templates for different comedian styles
PROMPTS = {
    'vir_das': """Generate 5 Hindi comedy lines in Vir Das style. Include [LAUGHTER] marker AFTER the punchline word.

Each line format: {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"}

Example: {"hindi": "मैं कल तुमसे मिला [LAUGHTER] और बहुत खुश हुआ", "trigger": 4, "lang": "hi-latn"}

Generate 5 lines:""",

    'zakir_khan': """Generate 5 Hindi comedy lines in Zakir Khan storytelling style. Include [LAUGHTER] marker AFTER the punchline word.

Each line format: {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"}

Example: {"hindi": "मैं कल बाजार गया [LAUGHTER] और सबने मुझे देखा", "trigger": 4, "lang": "hi-latn"}

Generate 5 lines:""",

    'biswa_kalyan_rath': """Generate 5 witty Hindi comedy lines in Biswa Kalyan Rath style. Include [LAUGHTER] marker AFTER the punchline word.

Each line format: {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"}

Example: {"hindi": "यह सब बुरा है [LAUGHTER] लेकिन सच है", "trigger": 2, "lang": "hi-latn"}

Generate 5 lines:""",

    'generic_hinglish': """Generate 5 Hinglish comedy lines (Hindi + English mix). Include [LAUGHTER] marker AFTER the punchline word.

Each line format: {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi-latn"}

Example: {"hindi": "I went to the market [LAUGHTER] and everyone stared", "trigger": 5, "lang": "hi-latn"}

Generate 5 lines:""",

    'pure_hindi': """Generate 5 pure Hindi comedy lines (no English). Include [LAUGHTER] marker AFTER the punchline word.

Each line format: {"hindi": "setup punchline_word [LAUGHTER] continuation", "trigger": position, "lang": "hi"}

Example: {"hindi": "आज मैं घर गया [LAUGHTER] और सबने प्यार किया", "trigger": 4, "lang": "hi"}

Generate 5 lines:"""
}

STYLE_TARGETS = {
    'vir_das': 400,
    'zakir_khan': 400,
    'biswa_kalyan_rath': 300,
    'generic_hinglish': 500,
    'pure_hindi': 400
}


def call_sarvam(prompt: str, model: str = None) -> str:
    """Call Sarvam API for text generation.
    
    Uses sarvam-m (legacy 24B) model which doesn't output reasoning traces.
    Content is wrapped in <V>...</V> tags - these are stripped.
    """
    if model is None:
        model = MODEL
    
    try:
        response = requests.post(
            SARVAM_API_URL,
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.8
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract content - sarvam-m outputs in <V> tags
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Strip <V> tags if present
        if content:
            import re
            content = re.sub(r'<V>\s*', '', content)
            content = re.sub(r'\s*</V>', '', content)
        
        return content.strip()
    except Exception as e:
        print(f"  ❌ Sarvam API error: {e}")
        return ""


def parse_response(response: str) -> List[Dict]:
    """Parse JSON lines from response. Handles various formats."""
    examples = []
    
    if not response:
        return examples
    
    # Remove markdown code blocks
    lines = response.split('\n')
    cleaned_lines = []
    in_block = False
    for line in lines:
        if line.strip().startswith('```'):
            in_block = not in_block
            continue
        if not in_block:
            cleaned_lines.append(line)
    response = '\n'.join(cleaned_lines)
    
    # Try to find JSON array or individual JSON objects
    import re
    
    # First, try to find a JSON array format: [...]
    array_match = re.search(r'\[\s*\{[^{}]*\}\s*\]', response, re.DOTALL)
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
    
    # Second, try to find individual JSON objects (possibly wrapped in backticks)
    # Match {\"hindi\": ...} patterns
    json_objects = re.findall(r'\{[^{}]*\}', response)
    
    for json_str in json_objects:
        # Skip if it looks like part of a larger structure
        if json_str.count('{') > 2:  # Likely nested, skip
            continue
        try:
            data = json.loads(json_str)
            if validate_example(data):
                examples.append(normalize_example(data))
        except json.JSONDecodeError:
            continue
    
    return examples


def validate_example(data: Dict) -> bool:
    """Validate example has required fields."""
    hindi = data.get('hindi', data.get('text', data.get('content', '')))
    if not hindi or len(hindi) < 5:
        return False
    if '[LAUGHTER]' not in hindi:
        return False
    return True


def normalize_example(data: Dict) -> Dict:
    """Normalize example format."""
    hindi = data.get('hindi', data.get('text', data.get('content', '')))
    
    # Determine language
    lang = data.get('lang', data.get('language', 'hi-latn'))
    if lang not in ['hi', 'hi-latn', 'hin-latn']:
        lang = 'hi-latn'
    
    # Find trigger position from [LAUGHTER] marker
    laughter_pos = []
    temp_text = hindi
    while True:
        pos = temp_text.find('[LAUGHTER]')
        if pos == -1:
            break
        before = temp_text[:pos].replace('[LAUGHTER]', '').split()
        if before:
            laughter_pos.append(len(before) - 1)
        temp_text = temp_text[pos + len('[LAUGHTER]'):]
    
    trigger_idx = laughter_pos[0] if laughter_pos else data.get('trigger', data.get('trigger_word_index', 0))
    
    return {
        'hindi': hindi,
        'trigger': trigger_idx,
        'lang': lang,
        'style': data.get('style', data.get('comedian_style', 'unknown'))
    }


def generate_examples(style: str, target: int) -> List[Dict]:
    """Generate examples for a style."""
    prompt = PROMPTS.get(style, PROMPTS['generic_hinglish'])
    examples = []
    batch_size = 5
    max_attempts = (target // batch_size) * 3
    
    print(f"  Generating {target} {style} examples...")
    
    for attempt in range(max_attempts):
        if len(examples) >= target:
            break
        
        response = call_sarvam(prompt)
        if not response:
            time.sleep(1)
            continue
        
        batch = parse_response(response)
        if batch:
            examples.extend(batch)
            print(f"    Progress: {min(len(examples), target)}/{target}")
        
        time.sleep(0.5)
    
    print(f"  ✓ Generated {len(examples)} {style} examples")
    return examples[:target]


def convert_to_training_format(examples: List[Dict], style: str) -> List[Dict]:
    """Convert to training format."""
    training = []
    
    for ex in examples:
        words = ex['hindi'].replace('[LAUGHTER]', '').strip().split()
        trigger_idx = ex.get('trigger', 0)
        
        labels = [1 if i == trigger_idx else 0 for i in range(len(words))]
        
        training_example = {
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
                'style': style,
                'generation_date': time.strftime('%Y-%m-%d')
            }
        }
        
        # Add biosemotic features
        training_example.update(generate_biosemotic_features(words, trigger_idx))
        training.append(training_example)
    
    return training


def generate_biosemotic_features(words: List[str], trigger_idx: int) -> Dict:
    """Generate biosemotic features."""
    n = len(words)
    return {
        'duchenne_joy_intensity': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.0, 0.3) for i in range(n)],
        'duchenne_genuine_humor_probability': [random.uniform(0.7, 1.0) if i == trigger_idx else random.uniform(0.0, 0.3) for i in range(n)],
        'duchenne_spontaneous_laughter_markers': [0.0] * n,
        'duchenne_setup_punchline_structure': ['setup'] * trigger_idx + ['punchline'] + ['resolution'] * (n - trigger_idx - 1),
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
    print("HINDI GENERATION USING SARVAM AI (OPTIMIZED FOR INDIC)")
    print("=" * 70)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Target: {sum(STYLE_TARGETS.values())} examples")
    print("=" * 70)
    
    all_examples = []
    progress_file = OUTPUT_DIR / "progress.json"
    
    for style, target in STYLE_TARGETS.items():
        print(f"\n[Generating {style} ({target} examples)]")
        
        start = time.time()
        examples = generate_examples(style, target)
        elapsed = time.time() - start
        
        # Convert to training format
        training = convert_to_training_format(examples, style)
        all_examples.extend(training)
        
        # Save checkpoint after each style
        print(f"  Saving checkpoint...")
        random.shuffle(all_examples)
        n = len(all_examples)
        train = all_examples[:int(0.8*n)]
        valid = all_examples[int(0.8*n):int(0.9*n)]
        test = all_examples[int(0.9*n):]
        
        save_jsonl(train, OUTPUT_DIR / "train.jsonl")
        save_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
        save_jsonl(test, OUTPUT_DIR / "test.jsonl")
        
        # Update progress
        progress = {
            "style": style,
            "generated": len(all_examples),
            "target": sum(STYLE_TARGETS.values()),
            "pct": round(100 * len(all_examples) / sum(STYLE_TARGETS.values()), 1),
            "time_min": round(elapsed / 60, 1)
        }
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        print(f"  ✓ {style} complete: {len(training)} examples in {elapsed:.1f}s")
    
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE!")
    print(f"Total: {len(all_examples)} examples")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
