#!/usr/bin/env python3
"""
Analyze language distribution across all training datasets.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

def read_jsonl(filepath: str) -> List[dict]:
    """Read a JSONL file and return list of records."""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def analyze_dataset(filepath: str, dataset_name: str) -> Dict:
    """Analyze a single dataset for language distribution."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {dataset_name}")
    print(f"Path: {filepath}")
    print(f"{'='*60}")

    records = read_jsonl(filepath)
    total = len(records)

    # Check for language field
    has_language = [r for r in records if 'language' in r]
    no_language = total - len(has_language)

    # Count languages
    language_counter = Counter()
    for r in has_language:
        lang = r.get('language', 'unknown')
        language_counter[lang] += 1

    # Calculate percentages
    language_percentages = {
        lang: (count / total * 100) if total > 0 else 0
        for lang, count in language_counter.items()
    }

    # Sort by count descending
    sorted_languages = sorted(language_counter.items(), key=lambda x: x[1], reverse=True)

    # Print summary
    print(f"\nTotal examples: {total}")
    print(f"Examples with language field: {len(has_language)} ({len(has_language)/total*100:.1f}%)")
    print(f"Examples without language field: {no_language} ({no_language/total*100:.1f}%)")
    print(f"\nUnique languages found: {len(language_counter)}")

    print(f"\nLanguage breakdown:")
    print(f"{'Language':<15} {'Count':<10} {'Percentage':<12}")
    print("-" * 40)
    for lang, count in sorted_languages:
        print(f"{lang:<15} {count:<10} {language_percentages[lang]:<12.2f}%")

    # Check for non-ISO language codes
    non_iso = [lang for lang in language_counter.keys()
               if lang not in ['en', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'ar', 'hi']]
    if non_iso:
        print(f"\nNon-ISO language codes found: {non_iso}")

    return {
        'dataset_name': dataset_name,
        'filepath': filepath,
        'total_examples': total,
        'has_language_count': len(has_language),
        'no_language_count': no_language,
        'language_counter': dict(language_counter),
        'language_percentages': language_percentages,
        'unique_languages': list(language_counter.keys())
    }

def main():
    # Define datasets
    datasets = [
        ("/Users/Subho/run_42_transfer_minimal/data/train_merged.jsonl", "train_merged"),
        ("/Users/Subho/run_42_transfer_minimal/data/valid_merged.jsonl", "valid_merged"),
        ("/Users/Subho/run_42_transfer_minimal/data/test_merged.jsonl", "test_merged"),
        ("/Users/Subho/autonomous_laughter_prediction_essential/training/synthetic_comedy_data.jsonl", "synthetic_comedy_data"),
    ]

    # Analyze each dataset
    results = []
    for filepath, name in datasets:
        if not Path(filepath).exists():
            print(f"\n⚠️  WARNING: {filepath} does not exist!")
            continue
        result = analyze_dataset(filepath, name)
        results.append(result)

    # Overall summary
    print(f"\n\n{'='*60}")
    print("OVERALL SUMMARY ACROSS ALL DATASETS")
    print(f"{'='*60}")

    total_examples_all = sum(r['total_examples'] for r in results)
    total_with_language = sum(r['has_language_count'] for r in results)
    total_without_language = sum(r['no_language_count'] for r in results)

    # Aggregate language counts across all datasets
    all_languages = Counter()
    for r in results:
        all_languages.update(r['language_counter'])

    print(f"\nTotal examples across all datasets: {total_examples_all}")
    print(f"Total with language field: {total_with_language} ({total_with_language/total_examples_all*100:.1f}%)")
    print(f"Total without language field: {total_without_language} ({total_without_language/total_examples_all*100:.1f}%)")
    print(f"Total unique languages: {len(all_languages)}")

    print(f"\nCombined language distribution:")
    print(f"{'Language':<15} {'Count':<10} {'Percentage':<12}")
    print("-" * 40)
    for lang, count in all_languages.most_common():
        print(f"{lang:<15} {count:<10} {count/total_examples_all*100:<12.2f}%")

    # Dataset comparison
    print(f"\n\nDataset Comparison:")
    print(f"{'Dataset':<30} {'Total':<10} {'Has Lang':<10} {'Unique Langs':<15}")
    print("-" * 70)
    for r in results:
        print(f"{r['dataset_name']:<30} {r['total_examples']:<10} "
              f"{r['has_language_count']:<10} {len(r['unique_languages']):<15}")

    # Save results to JSON for report generation
    output_file = Path("/Users/Subho/autonomous_laughter_prediction_essential/docs/language_analysis_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'datasets': results,
            'summary': {
                'total_examples_all': total_examples_all,
                'total_with_language': total_with_language,
                'total_without_language': total_without_language,
                'all_languages': dict(all_languages),
                'all_language_percentages': {
                    lang: count/total_examples_all*100
                    for lang, count in all_languages.items()
                }
            }
        }, f, indent=2)

    print(f"\n\n✅ Analysis complete! Results saved to: {output_file}")

    # Print key findings
    print(f"\n\n{'='*60}")
    print("KEY FINDINGS")
    print(f"{'='*60}")
    print(f"1. Language coverage is {'GOOD' if len(all_languages) >= 3 else 'LIMITED'} - {len(all_languages)} languages total")
    print(f"2. Most datasets {'HAVE' if total_with_language/total_examples_all > 0.5 else 'LACK'} language metadata ({total_with_language/total_examples_all*100:.1f}%)")
    print(f"3. Dominant language: {all_languages.most_common(1)[0][0] if all_languages else 'NONE'} ({all_languages.most_common(1)[0][1]/total_examples_all*100:.1f}%)")
    print(f"4. Datasets without language field: synthetic_comedy_data")

if __name__ == "__main__":
    main()
