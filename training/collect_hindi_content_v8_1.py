#!/usr/bin/env python3
"""
Hindi/Hinglish Content Collector - V8.1
Runs all collectors and merges with existing data
Target: ~35% laughter rate for Hindi content
100% automated - no manual steps.
"""
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential")
OUTPUT_DIR = PROJECT_DIR / "data" / "v8_1_hindi_final"

def run_script(script_name, description):
    """Run a Python script and report status."""
    print(f"\n{'='*70}")
    print(f"RUNNING: {description}")
    print(f"Script: {script_name}")
    print("=" * 70)
    
    result = subprocess.run(
        ["python3", "-u", str(PROJECT_DIR / "training" / script_name)],
        cwd=str(PROJECT_DIR),
        capture_output=False
    )
    
    if result.returncode == 0:
        print(f"✓ {description} completed successfully")
    else:
        print(f"❌ {description} failed with code {result.returncode}")
    
    return result.returncode == 0

def load_jsonl(path):
    """Load from JSONL."""
    return [json.loads(line) for line in path.read_text().strip().split('\n') if line]

def save_jsonl(data, path):
    """Save to JSONL."""
    with open(path, 'w') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def analyze_dataset(path, name):
    """Analyze a dataset."""
    data = load_jsonl(path)
    n = len(data)
    
    # By language
    lang_counts = {}
    lang_laughter = {}
    for ex in data:
        lang = ex.get('language', 'unknown')
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        lang_laughter[lang] = lang_laughter.get(lang, 0) + ex.get('label', 0)
    
    print(f"\n{name} ({n} examples):")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        rate = 100 * lang_laughter.get(lang, 0) / count if count > 0 else 0
        print(f"  {lang}: {count} ({100*count/n:.1f}%), laughter: {rate:.1f}%")
    
    return data

def main():
    print("=" * 70)
    print("HINDI/HINGLISH CONTENT COLLECTION - V8.1")
    print("=" * 70)
    
    # Step 1: Scrape Reddit
    print("\n[Step 1] Scraping Reddit Hindi/Hinglish jokes...")
    reddit_success = run_script(
        "scrape_reddit_hindi_jokes.py",
        "Reddit Hindi/Hinglish Jokes Scraper"
    )
    
    if not reddit_success:
        print("⚠ Reddit scraping failed, continuing with other sources...")
    
    # Step 2: Scrape News Humor
    print("\n[Step 2] Scraping Hindi news humor...")
    news_success = run_script(
        "scrape_hindi_news_humor.py",
        "Hindi News Humor Scraper"
    )
    
    if not news_success:
        print("⚠ News scraping failed, continuing...")
    
    # Step 3: Analyze collected data
    print("\n" + "=" * 70)
    print("ANALYZING COLLECTED DATA")
    print("=" * 70)
    
    # Check Reddit data
    reddit_dir = PROJECT_DIR / "data" / "reddit_hindi_jokes"
    if reddit_dir.exists():
        for split in ['train.jsonl', 'valid.jsonl', 'test.jsonl']:
            if (reddit_dir / split).exists():
                analyze_dataset(reddit_dir / split, f"Reddit {split}")
    else:
        print("Reddit data not found")
    
    # Check News data
    news_dir = PROJECT_DIR / "data" / "hindi_news_humor"
    if news_dir.exists():
        for split in ['train.jsonl', 'valid.jsonl', 'test.jsonl']:
            if (news_dir / split).exists():
                analyze_dataset(news_dir / split, f"News {split}")
    else:
        print("News data not found")
    
    # Step 4: Load existing data
    print("\n" + "=" * 70)
    print("LOADING EXISTING DATA")
    print("=" * 70)
    
    combined_dir = PROJECT_DIR / "data" / "combined_multilingual"
    
    existing_train = load_jsonl(combined_dir / "train.jsonl") if (combined_dir / "train.jsonl").exists() else []
    existing_valid = load_jsonl(combined_dir / "valid.jsonl") if (combined_dir / "valid.jsonl").exists() else []
    existing_test = load_jsonl(combined_dir / "test.jsonl") if (combined_dir / "test.jsonl").exists() else []
    
    print(f"\nExisting data:")
    print(f"  Train: {len(existing_train)}")
    print(f"  Valid: {len(existing_valid)}")
    print(f"  Test: {len(existing_test)}")
    
    # Step 5: Create final merged dataset
    print("\n" + "=" * 70)
    print("CREATING FINAL DATASET")
    print("=" * 70)
    
    # Combine all
    final_train = existing_train.copy()
    final_valid = existing_valid.copy()
    final_test = existing_test.copy()
    
    # Add Reddit data
    if reddit_dir.exists():
        for split, final_list in [('train.jsonl', final_train), ('valid.jsonl', final_valid), ('test.jsonl', final_test)]:
            if (reddit_dir / split).exists():
                data = load_jsonl(reddit_dir / split)
                final_list.extend(data)
                print(f"Added {len(data)} Reddit examples to {split}")
    
    # Add News data
    if news_dir.exists():
        for split, final_list in [('train.jsonl', final_train), ('valid.jsonl', final_valid), ('test.jsonl', final_test)]:
            if (news_dir / split).exists():
                data = load_jsonl(news_dir / split)
                final_list.extend(data)
                print(f"Added {len(data)} News examples to {split}")
    
    # Save final dataset
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_jsonl(final_train, OUTPUT_DIR / "train.jsonl")
    save_jsonl(final_valid, OUTPUT_DIR / "valid.jsonl")
    save_jsonl(final_test, OUTPUT_DIR / "test.jsonl")
    
    print(f"\n{'='*70}")
    print("V8.1 FINAL DATASET CREATED")
    print(f"{'='*70}")
    print(f"Total: {len(final_train) + len(final_valid) + len(final_test)} examples")
    print(f"  Train: {len(final_train)}")
    print(f"  Valid: {len(final_valid)}")
    print(f"  Test: {len(final_test)}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Final analysis
    print("\n" + "=" * 70)
    print("FINAL DATASET ANALYSIS")
    print("=" * 70)
    
    # Language distribution
    lang_counts = {}
    lang_laughter = {}
    for ex in final_train:
        lang = ex.get('language', 'unknown')
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        lang_laughter[lang] = lang_laughter.get(lang, 0) + ex.get('label', 0)
    
    print("\nLanguage distribution (train):")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        rate = 100 * lang_laughter.get(lang, 0) / count if count > 0 else 0
        print(f"  {lang}: {count} ({100*count/len(final_train):.1f}%), laughter: {rate:.1f}%")
    
    # Total laughter rate
    total_laughter = sum(ex.get('label', 0) for ex in final_train)
    total_rate = 100 * total_laughter / len(final_train) if final_train else 0
    print(f"\nTotal laughter rate: {total_rate:.1f}%")
    
    # Save metadata
    metadata = {
        "created": datetime.now().isoformat(),
        "total_examples": len(final_train) + len(final_valid) + len(final_test),
        "train_count": len(final_train),
        "valid_count": len(final_valid),
        "test_count": len(final_test),
        "language_distribution": lang_counts,
        "laughter_by_language": {k: 100 * lang_laughter.get(k, 0) / v if v > 0 else 0 for k, v in lang_counts.items()},
        "total_laughter_rate": total_rate
    }
    
    with open(OUTPUT_DIR / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Dataset ready at: {OUTPUT_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()