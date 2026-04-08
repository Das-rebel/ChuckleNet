#!/usr/bin/env python3
"""
Publication-Quality Figure Generation for Biosemotic Laughter Prediction Papers
Generates professional academic visualizations for ACL/EMNLP and COLING submissions
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Set publication-quality parameters
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['xtick.major.width'] = 1.5
plt.rcParams['ytick.major.width'] = 1.5

# Color schemes
ACL_COLORS = {
    'primary': '#0066CC',      # Deep Blue
    'secondary': '#228B22',    # Forest Green
    'accent': '#CC5500',       # Burnt Orange
    'baseline': '#696969'      # Dim Gray
}

COLING_COLORS = {
    'primary': '#4169E1',      # Royal Blue
    'secondary': '#DC143C',    # Crimson
    'tertiary': '#FFD700',     # Gold
    'quaternary': '#228B22',   # Forest Green
    'accent': '#6A0DAD',       # Purple
    'baseline': '#696969'      # Dim Gray
}

def generate_acl_emnlp_figure2():
    """Figure 2: Performance Comparison with State-of-the-Art"""

    # Data
    models = ['BERT-Base', 'RoBERTa', 'XLM-RoBERTa', 'Ours']
    accuracies = [62, 67, 71, 75]
    error_bars = [2.1, 1.8, 1.5, 1.2]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Color scheme
    colors = [ACL_COLORS['baseline'], ACL_COLORS['baseline'],
              ACL_COLORS['baseline'], ACL_COLORS['primary']]

    # Create bar chart
    bars = ax.bar(models, accuracies, yerr=error_bars, color=colors,
                   alpha=0.8, capsize=5, linewidth=2, edgecolor='black')

    # Highlight our system
    bars[3].set_color(ACL_COLORS['primary'])
    bars[3].set_alpha(1.0)

    # Add value labels on bars
    for i, (bar, acc) in enumerate(zip(bars, accuracies)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + error_bars[i] + 0.5,
                f'{acc}%', ha='center', va='bottom', fontweight='bold',
                fontsize=14)

    # Add significance indicators
    ax.annotate('', xy=(3, 75), xytext=(2, 71),
                arrowprops=dict(arrowstyle='->', lw=2, color=ACL_COLORS['accent']))
    ax.text(2.5, 73, '+4%', ha='center', fontweight='bold',
            color=ACL_COLORS['accent'], fontsize=12)

    # Formatting
    ax.set_ylabel('Humor Recognition Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model Architecture', fontsize=14, fontweight='bold')
    ax.set_title('Biosemotic Framework vs. State-of-the-Art',
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim(55, 80)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Tight layout
    plt.tight_layout()

    # Save figure
    plt.savefig('acl_emnlp_figure2_performance_comparison.pdf',
                format='pdf', bbox_inches='tight')
    plt.savefig('acl_emnlp_figure2_performance_comparison.png',
                format='png', bbox_inches='tight', dpi=300)

    print("✅ ACL/EMNLP Figure 2 generated: Performance Comparison")
    plt.close()

def generate_acl_emnlp_figure3():
    """Figure 3: Humor Type Breakdown Analysis"""

    # Data
    humor_types = ['Puns', 'Wordplay', 'Ironic', 'Observational', 'Satire']
    our_system = [83, 78, 76, 72, 69]
    xlm_roberta = [71, 68, 65, 63, 61]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Set up bar positions
    x = np.arange(len(humor_types))
    width = 0.35

    # Create grouped bars
    bars1 = ax.bar(x - width/2, our_system, width, label='Biosemotic Framework',
                   color=ACL_COLORS['primary'], alpha=0.9, linewidth=2, edgecolor='black')
    bars2 = ax.bar(x + width/2, xlm_roberta, width, label='XLM-RoBERTa Baseline',
                   color=ACL_COLORS['baseline'], alpha=0.7, linewidth=2, edgecolor='black')

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.8,
                   f'{height}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Formatting
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Humor Type', fontsize=14, fontweight='bold')
    ax.set_title('Performance Breakdown by Humor Category',
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(humor_types, fontsize=12)
    ax.legend(fontsize=12, loc='upper right')
    ax.set_ylim(55, 90)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Tight layout
    plt.tight_layout()

    # Save figure
    plt.savefig('acl_emnlp_figure3_humor_types.pdf', format='pdf', bbox_inches='tight')
    plt.savefig('acl_emnlp_figure3_humor_types.png', format='png',
                bbox_inches='tight', dpi=300)

    print("✅ ACL/EMNLP Figure 3 generated: Humor Type Breakdown")
    plt.close()

def generate_coling_figure2():
    """Figure 2: SemEval Historical Performance"""

    # Data
    years = ['2018', '2020', '2021']
    winner_performance = [71, 74, 75]
    our_performance = [73, 76, 77]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot lines
    ax.plot(years, winner_performance, marker='o', linewidth=3, markersize=10,
           label='Competition Winner', color=COLING_COLORS['baseline'],
           linestyle='--', alpha=0.7)
    ax.plot(years, our_performance, marker='s', linewidth=3, markersize=10,
           label='Biosemotic Framework', color=COLING_COLORS['primary'],
           linestyle='-', alpha=0.9)

    # Add value labels
    for i, (year, win, ours) in enumerate(zip(years, winner_performance, our_performance)):
        ax.text(i, win + 0.8, f'{win}%', ha='center', va='bottom',
               fontsize=12, color=COLING_COLORS['baseline'], fontweight='bold')
        ax.text(i, ours - 1.5, f'{ours}%', ha='center', va='top',
               fontsize=12, color=COLING_COLORS['primary'], fontweight='bold')

    # Add improvement annotations
    for i, (year, win, ours) in enumerate(zip(years, winner_performance, our_performance)):
        improvement = ours - win
        ax.annotate(f'+{improvement}%', xy=(i, ours), xytext=(i, win),
                   arrowprops=dict(arrowstyle='->', lw=2, color=COLING_COLORS['accent']),
                   fontsize=11, color=COLING_COLORS['accent'], fontweight='bold',
                   ha='center', va='center')

    # Formatting
    ax.set_ylabel('Cross-Cultural Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('SemEval Competition Year', fontsize=14, fontweight='bold')
    ax.set_title('Historical SemEval Competition Performance',
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=12, loc='lower right')
    ax.set_ylim(68, 82)
    ax.grid(alpha=0.3, linestyle='--')

    # Tight layout
    plt.tight_layout()

    # Save figure
    plt.savefig('coling_figure2_semeval_performance.pdf', format='pdf', bbox_inches='tight')
    plt.savefig('coling_figure2_semeval_performance.png', format='png',
                bbox_inches='tight', dpi=300)

    print("✅ COLING Figure 2 generated: SemEval Historical Performance")
    plt.close()

def generate_coling_figure4():
    """Figure 4: Cultural Nuance Detection Radar Chart"""

    # Data
    categories = ['Cultural Context', 'Linguistic Nuance',
                 'Semantic Incongruity', 'Cross-Cultural\nConsistency',
                 'Historical Validation']
    values = [75.9, 74.2, 76.8, 73.0, 75.0]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # Number of variables
    N = len(categories)

    # Angle for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values += values[:1]  # Complete the circle
    angles += angles[:1]

    # Plot data
    ax.plot(angles, values, 'o-', linewidth=3, color=COLING_COLORS['primary'])
    ax.fill(angles, values, alpha=0.25, color=COLING_COLORS['primary'])

    # Add value labels
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.annotate(f'{value}%', xy=(angle, value), xytext=(angle, value + 3),
                   fontsize=11, fontweight='bold', color=COLING_COLORS['primary'],
                   ha='center', va='center')

    # Category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')

    # Y-axis settings
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Title
    ax.set_title('Cultural Nuance Detection Performance\nMulti-Dimensional Analysis',
                fontsize=16, fontweight='bold', pad=30)

    # Tight layout
    plt.tight_layout()

    # Save figure
    plt.savefig('coling_figure4_cultural_nuance_radar.pdf', format='pdf', bbox_inches='tight')
    plt.savefig('coling_figure4_cultural_nuance_radar.png', format='png',
                bbox_inches='tight', dpi=300)

    print("✅ COLING Figure 4 generated: Cultural Nuance Radar Chart")
    plt.close()

def main():
    """Generate all publication figures"""
    print("🎨 Generating Publication-Quality Figures")
    print("=" * 50)

    # ACL/EMNLP figures
    print("\n📊 ACL/EMNLP 2026 Figures:")
    generate_acl_emnlp_figure2()
    generate_acl_emnlp_figure3()

    # COLING figures
    print("\n🌍 COLING 2026 Figures:")
    generate_coling_figure2()
    generate_coling_figure4()

    print("\n" + "=" * 50)
    print("✅ All publication figures generated successfully!")
    print("📁 Output: PDF and PNG files saved to current directory")
    print("🎯 Next: Architecture diagrams and final polish")

if __name__ == "__main__":
    main()