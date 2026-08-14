#!/usr/bin/env python3
"""Generate Hindi synthetic data with INCREMENTAL save."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# Configuration
PROJECT_DIR = Path("/Users/Subho/autonomous_laughter_prediction")
OUTPUT_FILE = PROJECT_DIR / "data" / "hindi_synthetic_4000.jsonl"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

COMEDIAN_PROMPTS = {
    "zakir_khan": """Generate {n} examples of Hindi standup comedy text transcriptions with laughter annotations.
Each example should be a realistic transcription of Indian standup comedy.
Include patterns like: speaker pauses, audience laughter markers, comedic timing.
Format as JSON array with fields: text, label (1 for laughter, 0 for no laughter), comedian_style.
Make them realistic and diverse.""",
    
    "biswa_kalyan_rath": """Generate {n} examples of Indian English/Hindi bilingual standup comedy transcriptions.
Include crowd work, observational comedy patterns.
Format as JSON array with fields: text, label, comedian_style.""",
    
    "kunal_kamra": """Generate {n} examples of conversational Indian comedy style transcriptions.
Format as JSON array with fields: text, label, comedian_style.""",
}

BATCH_SIZE = 50
FORCE = True

def call_llm(prompt: str) -> Optional[str]:
    """Call local Ollama LLM."""
    try:
        result = subprocess.run([
            "curl", "-s", "http://localhost:11434/api/generate",
            "-d", json.dumps({
                "model": "qwen2.5:1.5b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 2048}
            })
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return response.get("response", "")
    except Exception as e:
        print(f"LLM error: {e}")
    return None

def extract_json_array(text: str) -> List:
    """Extract JSON array from LLM response."""
    import re
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return []

def save_incrementally(examples: List[Dict]):
    """Save examples incrementally to file."""
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

def main():
    print(f"Output: {OUTPUT_FILE}")
    
    # Count existing examples
    existing = 0
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            existing = sum(1 for _ in f)
        print(f"Existing examples: {existing}")
        if existing > 0 and not FORCE:
            print(f"{OUTPUT_FILE} already exists. Use --force to overwrite.")
            return
    
    total_target = 4000
    target_per_style = total_target // 4  # 1000 per style
    
    for style, prompt_template in COMEDIAN_PROMPTS.items():
        style_file = OUTPUT_FILE.parent / f"{style}_count.txt"
        
        # Get count for this style
        style_count = 0
        if style_file.exists():
            style_count = int(style_file.read_text().strip())
        
        print(f"\nGenerating for style: {style} (current: {style_count}/{target_per_style})")
        
        while style_count < target_per_style:
            batch_size = min(BATCH_SIZE, target_per_style - style_count)
            prompt = prompt_template.format(n=batch_size)
            
            response = call_llm(prompt)
            if not response:
                print(f"  Failed to get response, retrying...")
                continue
            
            parsed = extract_json_array(response)
            if not parsed:
                print(f"  No valid JSON, retrying...")
                continue
            
            # Save incrementally
            save_incrementally(parsed)
            style_count += len(parsed)
            
            print(f"  Progress: {style_count}/{target_per_style}")
            
            # Update style count
            style_file.write_text(str(style_count))
    
    print(f"\nDone! Total saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
