#!/usr/bin/env python3
"""
Hindi/Hinglish Synthetic Laughter Data Generator
=================================================
Generates 4,000 Hindi/Hinglish comedy examples for laughter prediction training.

Phase H1-H3 from DATA_COLLECTION_STRATEGY_V10.md:
  H1.2: 500 synthetic (Phase 1)
  H1.4: 2,000 synthetic (Phases 2-3)
  H1.7: 500 synthetic (Phase 3)
  Total: 4,000 examples

Comedian styles:
  - Zakir Khan (Observational)
  - Biswa Kalyan Rath (Sardonic/Intellectual)
  - Kunal Kamra (Dark/Social Commentary)
  - Kaneez Surka (Physical/Situational)
  - Vir Das (General)
  - Generic Hinglish

Output: data/hindi_synthetic_4000.jsonl
"""

import json
import random
import time
import requests
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

# =============================================================================
# Configuration
# =============================================================================

PROJECT_DIR = Path("/Users/Subho/autonomous_laughter_prediction")
OUTPUT_FILE = PROJECT_DIR / "data" / "hindi_synthetic_4000.jsonl"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

TOTAL_TARGET = 4000
LAUGHTER_RATE = 0.40
BATCH_SIZE = 25  # examples per LLM call
TEMPERATURE = 0.7

# =============================================================================
# Comedian Style Prompts (from V10 Appendix A)
# =============================================================================

COMEDIAN_PROMPTS = {
    "zakir_khan": """Generate {n} Hindi/Hinglish stand-up comedy lines in the style of Zakir Khan.
Focus on relatable observations about Indian life - traffic, family gatherings, job interviews, train journeys, relatable everyday frustrations.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "मेरी मैरिड जब सोती है तो ऐसा खर्राटा लेती है जैसे Boeing 747 उतर रहा हो [LAUGHTER]"
Keep each line to 10-20 words. Mix of Hindi and Hinglish (70% Hinglish, 30% pure Hindi).
Output ONLY a JSON array of objects with this exact format:
[{{"text": "hindi/hinglish line with [LAUGHTER] marker", "comedian": "zakir_khan", "lang": "hi-latn"}}]
Include [LAUGHTER] in EVERY line. No other text.""",

    "biswa_kalyan_rath": """Generate {n} Hindi/Hinglish stand-up comedy lines in the style of Biswa Kalyan Rath.
Focus on logical absurdities, philosophical observations, nerdy humor, and sardonic takes on everyday situations.
Dark, intellectual humor with sharp wit.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "इस देश mein democracy चलती है जैसे WhatsApp group में कोई admin नहीं हो [LAUGHTER]"
Keep each line to 10-20 words. Mix of Hindi and Hinglish.
Output ONLY a JSON array of objects with this exact format:
[{{"text": "hindi/hinglish line with [LAUGHTER] marker", "comedian": "biswa_kalyan_rath", "lang": "hi-latn"}}]
Include [LAUGHTER] in EVERY line. No other text.""",

    "kunal_kamra": """Generate {n} Hindi/Hinglish stand-up comedy lines in the style of Kunal Kamra.
Focus on social commentary, politics, everyday frustrations, and observational humor about modern Indian life.
Sharp, direct, and relatable.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "सरकारी ऑफिस में जाते हैं तो लगता है कि time travel करके medieval Europe चले गए [LAUGHTER]"
Keep each line to 10-20 words. Mix of Hindi and Hinglish.
Output ONLY a JSON array of objects with this exact format:
[{{"text": "hindi/hinglish line with [LAUGHTER] marker", "comedian": "kunal_kamra", "lang": "hi-latn"}}]
Include [LAUGHTER] in EVERY line. No other text.""",

    "kaneez_surka": """Generate {n} Hindi/Hinglish stand-up comedy lines in the style of Kaneez Surka.
Focus on situational comedy, misunderstandings, physical humor, and lighter takes on relationships.
Playful and warm tone.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "मेरी aunt जब बात करती हैं तो एक particular subject पर आकर रुक जाती हैं [LAUGHTER]"
Keep each line to 10-20 words. Mix of Hindi and Hinglish.
Output ONLY a JSON array of objects with this exact format:
[{{"text": "hindi/hinglish line with [LAUGHTER] marker", "comedian": "kaneez_surka", "lang": "hi-latn"}}]
Include [LAUGHTER] in EVERY line. No other text.""",

    "vir_das": """Generate {n} Hindi/Hinglish stand-up comedy lines in the style of Vir Das.
Focus on bilingual observations, relatable urban Indian life, and smart wordplay.
Clever and polished comedy.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "मैं और मेरा phone हमेशा together रहते हैं, बस battery की life अलग है [LAUGHTER]"
Keep each line to 10-20 words. Mix of Hindi and Hinglish.
Output ONLY a JSON array of objects with this exact format:
[{{"text": "hindi/hinglish line with [LAUGHTER] marker", "comedian": "vir_das", "lang": "hi-latn"}}]
Include [LAUGHTER] in EVERY line. No other text.""",

    "pure_hindi": """Generate {n} pure Hindi (no English) stand-up comedy lines.
Use only Hindi Devanagari script words. Based on traditional Hindi humor and wordplay.
Each line should have a clear setup followed by a punchline word marked with [LAUGHTER].
Example: "वह तो हमें देखकर ही हंस पड़े [LAUGHTER]"
Keep each line to 10-20 words. Pure Hindi only.
Output ONLY a JSON array of objects with this exact format:
[{{"text": "pure hindi line with [LAUGHTER] marker", "comedian": "pure_hindi", "lang": "hi"}}]
Include [LAUGHTER] in EVERY line. No other text.""",
}

# Style distribution targets (sum = 4000)
STYLE_DISTRIBUTION = {
    "zakir_khan": 800,
    "biswa_kalyan_rath": 600,
    "kunal_kamra": 600,
    "kaneez_surka": 400,
    "vir_das": 800,
    "pure_hindi": 800,
}


# =============================================================================
# LLM Interface
# =============================================================================

def call_llm(prompt: str, model: str = "qwen2.5:1.5b") -> str:
    """Call local LLM via Ollama."""
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE,
                    "top_p": 0.9,
                    "num_predict": 1500,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"    LLM call failed: {e}")
        return ""


# =============================================================================
# Parsing
# =============================================================================

def extract_json_array(text: str) -> List[Dict]:
    """Extract JSON array from LLM response."""
    text = text.strip()

    # Remove markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        in_block = False
        code_lines = []
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                code_lines.append(line)
        text = "\n".join(code_lines)

    # Find JSON array boundaries using balanced bracket counting
    i = 0
    n = len(text)
    results = []

    while i < n:
        # Find opening bracket
        while i < n and text[i] not in "{\\":
            i += 1
        if i >= n:
            break

        # Count brackets to find closing
        depth = 0
        j = i
        while j < n:
            c = text[j]
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0:
                    break
            j += 1

        if depth == 0:
            try:
                obj = json.loads(text[i:j+1])
                if isinstance(obj, list):
                    results.extend(obj)
                elif isinstance(obj, dict):
                    results.append(obj)
            except json.JSONDecodeError:
                pass

        i = j + 1

    return results


# =============================================================================
# Validation
# =============================================================================

def validate_example(ex: Dict) -> bool:
    """Validate a single example."""
    if not isinstance(ex, dict):
        return False

    text = ex.get("text", "")
    if not text or "[LAUGHTER]" not in text:
        return False

    # Remove marker and check word count
    clean = text.replace("[LAUGHTER]", "").strip()
    words = clean.split()
    if len(words) < 5 or len(words) > 25:
        return False

    lang = ex.get("lang", "")
    if lang not in ("hi", "hi-latn"):
        return False

    comedian = ex.get("comedian", "")
    valid_comedians = list(COMEDIAN_PROMPTS.keys())
    if comedian not in valid_comedians:
        return False

    return True


def compute_trigger_index(text: str) -> int:
    """Find the word index of the trigger (word before first [LAUGHTER])."""
    idx = text.find("[LAUGHTER]")
    if idx == -1:
        return -1
    before = text[:idx].strip().split()
    return len(before) - 1 if before else 0


# =============================================================================
# Format Conversion
# =============================================================================

def convert_to_training_format(ex: Dict, example_id: int) -> Dict:
    """Convert to training format matching existing dataset schema."""
    text = ex["text"]
    trigger_idx = compute_trigger_index(text)

    # Remove [LAUGHTER] marker
    clean_text = text.replace("[LAUGHTER]", "").strip()
    words = clean_text.split()

    # Create per-word labels (1 at trigger, 0 elsewhere)
    labels = [1 if i == trigger_idx else 0 for i in range(len(words))]

    return {
        "example_id": f"hindi_synth_{example_id:06d}",
        "language": ex.get("lang", "hi-latn"),
        "comedian_id": ex.get("comedian", "unknown"),
        "show_id": "hindi_synthetic",
        "words": words,
        "labels": labels,
        "label": 1,  # All have laughter by design
        "is_sentence_level": False,
        "source": "synthetic",
        "generation_model": "qwen2.5:1.5b",
        "generation_temperature": TEMPERATURE,
        "metadata": {
            "original_text": text,
            "generation_date": time.strftime("%Y-%m-%d"),
        }
    }


# =============================================================================
# Generation
# =============================================================================

def generate_batch(style: str, n: int) -> List[Dict]:
    """Generate a batch of examples for a given style."""
    prompt_template = COMEDIAN_PROMPTS[style]
    prompt = prompt_template.format(n=n)

    response = call_llm(prompt)
    if not response:
        return []

    parsed = extract_json_array(response)
    valid = [ex for ex in parsed if validate_example(ex)]
    return valid


def generate_style(style: str, target: int) -> List[Dict]:
    """Generate all examples for a style."""
    examples = []
    max_attempts = 10
    delay = 1.0

    print(f"\n  Generating {target} examples for style: {style}")

    while len(examples) < target:
        batch_size = min(BATCH_SIZE, target - len(examples))
        batch = generate_batch(style, batch_size)

        if batch:
            examples.extend(batch)
            print(f"    Progress: {len(examples)}/{target}")
        else:
            max_attempts -= 1
            if max_attempts == 0:
                print(f"    Max attempts reached. Got {len(examples)}/{target}")
                break

        time.sleep(delay)

    print(f"  Done: {len(examples)}/{target} for {style}")
    return examples[:target]


def generate_all() -> List[Dict]:
    """Generate all Hindi synthetic examples."""
    print("=" * 70)
    print("HINDI/HINGLISH SYNTHETIC DATA GENERATION")
    print("=" * 70)
    print(f"  Target: {TOTAL_TARGET} examples")
    print(f"  Laughter rate: {LAUGHTER_RATE*100}% (all positive by design)")
    print(f"  Temperature: {TEMPERATURE}")
    print(f"  Output: {OUTPUT_FILE}")
    print("=" * 70)

    all_examples = []
    example_id = 0

    for style, target in STYLE_DISTRIBUTION.items():
        batch = generate_style(style, target)
        for ex in batch:
            all_examples.append(convert_to_training_format(ex, example_id))
            example_id += 1

        # Small delay between styles to avoid rate limiting
        if style != list(STYLE_DISTRIBUTION.keys())[-1]:
            time.sleep(1)

    return all_examples


# =============================================================================
# Validation & Stats
# =============================================================================

def print_stats(examples: List[Dict]):
    """Print dataset statistics."""
    n = len(examples)
    print(f"\n{'='*70}")
    print("DATASET STATISTICS")
    print("=" * 70)
    print(f"  Total examples: {n}")

    # Language distribution
    langs = Counter(ex["language"] for ex in examples)
    print(f"\n  Language distribution:")
    for lang, count in sorted(langs.items(), key=lambda x: -x[1]):
        print(f"    {lang}: {count} ({100*count/n:.1f}%)")

    # Comedian distribution
    comedians = Counter(ex["comedian_id"] for ex in examples)
    print(f"\n  Comedian distribution:")
    for comedian, count in sorted(comedians.items(), key=lambda x: -x[1]):
        print(f"    {comedian}: {count}")

    # Word count stats
    word_counts = [len(ex["words"]) for ex in examples]
    print(f"\n  Word count: mean={sum(word_counts)/n:.1f}, "
          f"min={min(word_counts)}, max={max(word_counts)}")

    # Laughter rate
    laughter_count = sum(1 for ex in examples if ex["label"] == 1)
    print(f"\n  Laughter examples: {laughter_count}/{n} ({100*laughter_count/n:.1f}%)")

    # Validate all examples have exactly one trigger
    trigger_counts = [sum(ex["labels"]) for ex in examples]
    bad_triggers = sum(1 for c in trigger_counts if c != 1)
    if bad_triggers > 0:
        print(f"\n  WARNING: {bad_triggers} examples have != 1 triggers!")
    else:
        print(f"\n  All examples have exactly 1 trigger word.")

    # Check for near-duplicates
    texts = [ex["metadata"]["original_text"] for ex in examples]
    unique_texts = len(set(texts))
    dupes = n - unique_texts
    if dupes > 0:
        print(f"  WARNING: {dupes} duplicate texts found!")

    print("=" * 70)


# =============================================================================
# Main
# =============================================================================

def main():
    """Run the generation pipeline."""
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    test_mode = '--test' in sys.argv
    
    # Check if output already exists
    if OUTPUT_FILE.exists() and not force:
        print(f"{OUTPUT_FILE} already exists. Use --force to overwrite.")
        return

    # Generate
    examples = generate_all()

    if not examples:
        print("\nNo examples generated. Check Ollama connectivity.")
        return

    # Save
    print(f"\nSaving {len(examples)} examples to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Saved to {OUTPUT_FILE}")

    # Stats
    print_stats(examples)

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"Total examples: {len(examples)}")


if __name__ == "__main__":
    main()

# Add incremental save functionality
def save_incrementally(examples: List[Dict], output_file: Path):
    """Save examples to file incrementally."""
    with open(output_file, "a", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
