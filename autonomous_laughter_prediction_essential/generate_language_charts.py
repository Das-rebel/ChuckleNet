#!/usr/bin/env python3
"""
Generate language distribution charts for the report.
"""
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

# Load analysis results
results_file = Path("/Users/Subho/autonomous_laughter_prediction_essential/docs/language_analysis_results.json")
with open(results_file, 'r') as f:
    data = json.load(f)

# Create output directory
output_dir = Path("/Users/Subho/autonomous_laughter_prediction_essential/docs/charts")
output_dir.mkdir(parents=True, exist_ok=True)

# Chart 1: Dataset Language Coverage
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: Dataset sizes
datasets = [d['dataset_name'] for d in data['datasets']]
totals = [d['total_examples'] for d in data['datasets']]
with_lang = [d['has_language_count'] for d in data['datasets']]

x = range(len(datasets))
width = 0.35

ax1.bar([i - width/2 for i in x], totals, width, label='Total Examples', color='#2ecc71')
ax1.bar([i + width/2 for i in x], with_lang, width, label='With Language Field', color='#3498db')
ax1.set_xlabel('Dataset', fontsize=12, fontweight='bold')
ax1.set_ylabel('Number of Examples', fontsize=12, fontweight='bold')
ax1.set_title('Dataset Size vs. Language Metadata Coverage', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(datasets, rotation=45, ha='right')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Right: Language metadata percentage
percentages = [d['has_language_count']/d['total_examples']*100 for d in data['datasets']]
colors = ['#e74c3c' if p < 50 else '#f39c12' if p < 100 else '#27ae60' for p in percentages]

bars = ax2.bar(datasets, percentages, color=colors)
ax2.set_xlabel('Dataset', fontsize=12, fontweight='bold')
ax2.set_ylabel('Language Metadata Coverage (%)', fontsize=12, fontweight='bold')
ax2.set_title('Language Metadata Coverage by Dataset', fontsize=14, fontweight='bold')
ax2.set_xticklabels(datasets, rotation=45, ha='right')
ax2.set_ylim(0, 105)

# Add value labels on bars
for bar, pct in zip(bars, percentages):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')

# Add legend for colors
red_patch = mpatches.Patch(color='#e74c3c', label='Critical (<50%)')
orange_patch = mpatches.Patch(color='#f39c12', label='Warning (50-99%)')
green_patch = mpatches.Patch(color='#27ae60', label='Good (100%)')
ax2.legend(handles=[red_patch, orange_patch, green_patch], loc='upper right')
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'dataset_language_coverage.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {output_dir / 'dataset_language_coverage.png'}")
plt.close()

# Chart 2: Language Distribution (Labeled Data Only)
fig, ax = plt.subplots(figsize=(10, 8))

# Get language data from summary
lang_counts = data['summary']['all_languages']
lang_percentages = data['summary']['all_language_percentages']

# Sort by count
sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
langs = [l[0] for l in sorted_langs]
counts = [l[1] for l in sorted_langs]
pcts = [lang_percentages[l] for l in langs]

# Create horizontal bar chart
bars = ax.barh(langs, counts, color=['#3498db' if l == 'en' else '#9b59b6' for l in langs])
ax.set_xlabel('Number of Examples', fontsize=12, fontweight='bold')
ax.set_ylabel('Language', fontsize=12, fontweight='bold')
ax.set_title('Language Distribution (Labeled Data Only: 1,890 examples)', fontsize=14, fontweight='bold')

# Add value labels
for i, (bar, count, pct) in enumerate(zip(bars, counts, pcts)):
    width = bar.get_width()
    ax.text(width + 10, bar.get_y() + bar.get_height()/2,
            f'{count} ({pct:.1f}%)', va='center', fontweight='bold')

ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir / 'language_distribution_labeled.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {output_dir / 'language_distribution_labeled.png'}")
plt.close()

# Chart 3: Overall Data Composition (Labeled vs Unlabeled)
fig, ax = plt.subplots(figsize=(10, 8))

# Calculate composition
labeled_count = sum(data['summary']['all_languages'].values())
unlabeled_count = data['summary']['total_without_language']
total = data['summary']['total_examples_all']

# Data for pie chart
labels = [
    f'English (en)\n{data["summary"]["all_languages"]["en"]} examples\n({data["summary"]["all_language_percentages"]["en"]:.1f}%)',
    f'Chinese (zh)\n{data["summary"]["all_languages"]["zh"]} examples\n({data["summary"]["all_language_percentages"]["zh"]:.1f}%)',
    f'Unlabeled\n{unlabeled_count} examples\n({unlabeled_count/total*100:.1f}%)'
]
sizes = [
    data['summary']['all_languages']['en'],
    data['summary']['all_languages']['zh'],
    unlabeled_count
]
colors = ['#3498db', '#9b59b6', '#e74c3c']
explode = (0.05, 0.05, 0.05)

wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                   autopct='%1.1f%%', shadow=True, startangle=90,
                                   textprops={'fontsize': 11, 'fontweight': 'bold'})

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')

ax.set_title('Overall Training Data Composition (10,375 examples)', fontsize=14, fontweight='bold', pad=20)
ax.axis('equal')

plt.tight_layout()
plt.savefig(output_dir / 'overall_data_composition.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {output_dir / 'overall_data_composition.png'}")
plt.close()

# Chart 4: STANDUP4AI Claims vs Reality
fig, ax = plt.subplots(figsize=(10, 8))

# Data
categories = ['Languages', 'Priority Languages\n(hi, es, fr, de)', 'Multilingual\nTest Set']
claimed = [100, 4, 1]
actual = [2, 0, 0]
x = range(len(categories))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], claimed, width, label='Claimed', color='#2ecc71')
bars2 = ax.bar([i + width/2 for i in x], actual, width, label='Actual', color='#e74c3c')

ax.set_xlabel('Metric', fontsize=12, fontweight='bold')
ax.set_ylabel('Count / Binary', fontsize=12, fontweight='bold')
ax.set_title('STANDUP4AI Claims vs. Reality', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.legend()
ax.set_yscale('log')
ax.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height}', ha='center', va='bottom', fontweight='bold')

for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'claims_vs_reality.png', dpi=300, bbox_inches='tight')
print(f"✅ Saved: {output_dir / 'claims_vs_reality.png'}")
plt.close()

print(f"\n✅ All charts generated successfully!")
print(f"📁 Output directory: {output_dir}")
print(f"\n📊 Charts created:")
print(f"   1. dataset_language_coverage.png")
print(f"   2. language_distribution_labeled.png")
print(f"   3. overall_data_composition.png")
print(f"   4. claims_vs_reality.png")
