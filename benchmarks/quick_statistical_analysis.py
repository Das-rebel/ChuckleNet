#!/usr/bin/env python3
"""
Quick Start Script for Agent 9 Statistical Analysis
Run comprehensive statistical analysis on your benchmark results
"""

import numpy as np
import json
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from comprehensive_benchmark_analyzer import ComprehensiveBenchmarkAnalyzer


def load_example_results():
    """Generate example benchmark results for demonstration"""
    np.random.seed(42)

    return {
        'StandUp4AI': {
            'F1@IoU=0.3': np.random.normal(0.62, 0.03, 50),
            'Precision@IoU=0.3': np.random.normal(0.60, 0.03, 50),
            'Recall@IoU=0.3': np.random.normal(0.64, 0.03, 50),
        },
        'UR-FUNNY': {
            'Accuracy': np.random.normal(68.0, 2.0, 100),
            'F1': np.random.normal(0.66, 0.02, 100),
        },
        'TED-Laughter': {
            'F1': np.random.normal(0.63, 0.02, 80),
        }
    }


def load_your_results(file_path):
    """Load your benchmark results from JSON file

    Expected format:
    {
        "BenchmarkName": {
            "metric_name": [value1, value2, ...],
            "metric2": [value1, value2, ...]
        }
    }
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Convert lists to numpy arrays
    results = {}
    for benchmark, metrics in data.items():
        results[benchmark] = {
            metric: np.array(values) for metric, values in metrics.items()
        }

    return results


def main():
    """Run comprehensive statistical analysis"""

    print("🔬 AGENT 9: COMPREHENSIVE STATISTICAL ANALYSIS")
    print("=" * 80)

    # Check for command line arguments
    if len(sys.argv) > 1:
        # Load results from file
        results_file = sys.argv[1]
        print(f"Loading results from: {results_file}")

        try:
            results = load_your_results(results_file)
            print(f"✅ Loaded results for {len(results)} benchmarks")
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            print("Using example results instead...")
            results = load_example_results()
    else:
        # Use example results
        print("No results file provided. Using example results...")
        print("Usage: python3 quick_statistical_analysis.py <your_results.json>")
        print("")
        results = load_example_results()

    # Initialize analyzer
    analyzer = ComprehensiveBenchmarkAnalyzer(
        output_dir="results/statistical_analysis"
    )

    # Run comprehensive analysis
    print("\n🎯 RUNNING COMPREHENSIVE STATISTICAL ANALYSIS")
    print("=" * 80)

    try:
        reports = analyzer.analyze_comprehensive_results(
            results_dict=results,
            correction_method='holm'  # Holm-Bonferroni correction
        )

        # Generate reports
        print("\n📈 GENERATING REPORTS")
        analyzer.save_comprehensive_report(reports)

        # Generate plots (if matplotlib available)
        print("\n📊 GENERATING PLOTS")
        analyzer.generate_visualization_plots(reports)

        # Print summary
        print("\n🎉 ANALYSIS COMPLETE!")
        print("=" * 80)

        # Count statistics
        total_benchmarks = len(reports)
        publication_ready = sum(1 for r in reports.values() if r.publication_ready)
        total_metrics = sum(len(r.significance_summary) for r in reports.values())
        significant_metrics = sum(sum(r.significance_summary.values()) for r in reports.values())

        print(f"📊 STATISTICAL SUMMARY")
        print(f"   Total Benchmarks: {total_benchmarks}")
        print(f"   Publication Ready: {publication_ready}/{total_benchmarks}")
        print(f"   Total Metrics: {total_metrics}")
        print(f"   Significant Improvements: {significant_metrics}/{total_metrics} ({significant_metrics/total_metrics*100:.1f}%)")
        print("")

        if publication_ready == total_benchmarks:
            print("🎉 EXCELLENT: All benchmarks meet publication standards!")
        elif publication_ready >= total_benchmarks * 0.7:
            print("✅ STRONG: Most benchmarks meet publication standards")
        elif publication_ready >= total_benchmarks * 0.5:
            print("⚠️  MODERATE: Some benchmarks meet publication standards")
        else:
            print("❌ INSUFFICIENT: Most benchmarks do not meet publication standards")

        print("")
        print(f"📁 Results saved to: {analyzer.output_dir}")
        print("   - comprehensive_statistical_analysis.json")
        print("   - comprehensive_statistical_analysis.tex")
        print("   - comprehensive_statistical_analysis.md")
        print("   - comprehensive_statistical_analysis_summary.txt")
        print("   - Visualization plots (if matplotlib available)")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())