#!/usr/bin/env python3
"""
Merge Hindi data with expanded_10k dataset.
"""
import json
import os
from collections import Counter
from pathlib import Path


def merge_datasets(
    base_dir: str,
    hindi_dir: str,
    output_dir: str
) -> dict:
    """Merge base dataset with Hindi data."""

    os.makedirs(output_dir, exist_ok=True)

    stats = {
        'total_examples': 0,
        'total_words': 0,
        'languages': Counter(),
        'splits': {}
    }

    for split in ['train', 'valid', 'test']:
        # Load base dataset
        base_path = os.path.join(base_dir, f'{split}.jsonl')
        base_examples = []

        if os.path.exists(base_path):
            with open(base_path) as f:
                base_examples = [json.loads(line) for line in f]

        # Load Hindi data
        hindi_path = os.path.join(hindi_dir, f'{split}.jsonl')
        hindi_examples = []

        if os.path.exists(hindi_path):
            with open(hindi_path) as f:
                hindi_examples = [json.loads(line) for line in f]

        # Merge
        merged_examples = base_examples + hindi_examples

        # Save merged
        output_path = os.path.join(output_dir, f'{split}.jsonl')
        with open(output_path, 'w') as f:
            for ex in merged_examples:
                f.write(json.dumps(ex) + '\n')

        # Calculate stats
        n_merged = len(merged_examples)
        n_base = len(base_examples)
        n_hindi = len(hindi_examples)

        # Count languages
        languages = Counter()
        total_words = 0
        for ex in merged_examples:
            lang = ex.get('language', 'unknown')
            languages[lang] += 1
            total_words += len(ex.get('words', []))

        stats['splits'][split] = {
            'total': n_merged,
            'base': n_base,
            'hindi': n_hindi,
            'words': total_words,
            'languages': dict(languages)
        }

        stats['total_examples'] += n_merged
        stats['total_words'] += total_words
        stats['languages'].update(languages)

        print(f"\n{split.upper()}:")
        print(f"  Base examples: {n_base}")
        print(f"  Hindi examples: {n_hindi}")
        print(f"  Merged: {n_merged}")
        print(f"  Words: {total_words}")
        print(f"  Languages: {dict(languages)}")

    return stats


def main():
    """Main function."""
    base_dir = '/Users/Subho/autonomous_laughter_prediction_essential/data/expanded_10k'
    hindi_dir = '/Users/Subho/autonomous_laughter_prediction_essential/data/indian_comedy_processed'
    output_dir = '/Users/Subho/autonomous_laughter_prediction_essential/data/expanded_10k_with_hindi'

    print("=" * 70)
    print("MERGING HINDI DATA WITH expanded_10k")
    print("=" * 70)
    print(f"\nBase dataset: {base_dir}")
    print(f"Hindi dataset: {hindi_dir}")
    print(f"Output: {output_dir}")

    stats = merge_datasets(base_dir, hindi_dir, output_dir)

    print("\n" + "=" * 70)
    print("FINAL STATISTICS")
    print("=" * 70)
    print(f"\nTotal examples: {stats['total_examples']}")
    print(f"Total words: {stats['total_words']}")
    print(f"\nLanguage distribution:")
    for lang, count in stats['languages'].most_common():
        pct = 100 * count / stats['total_examples']
        print(f"  {lang}: {count} ({pct:.1f}%)")
    print("=" * 70)


if __name__ == '__main__':
    main()
