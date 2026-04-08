#!/usr/bin/env python3
"""
Comprehensive Benchmark Statistical Analyzer
Agent 9: Statistical Analysis and Significance Testing for Academic Publication
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
except ImportError:
    plt = None
    print("Warning: matplotlib not available, plots will be skipped")

from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from statistical_analysis_framework import (
    AdvancedStatisticalFramework,
    StatisticalTestResult,
    BenchmarkComparison
)


@dataclass
class BenchmarkReport:
    """Comprehensive benchmark analysis report"""
    benchmark_name: str
    baseline_results: Dict[str, float]
    our_results: Dict[str, float]
    statistical_tests: Dict[str, StatisticalTestResult]
    comparisons: Dict[str, BenchmarkComparison]
    significance_summary: Dict[str, bool]
    effect_sizes: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    power_analysis: Dict[str, float]
    reproducibility: Optional[StatisticalTestResult] = None
    overall_assessment: str = ""
    publication_ready: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ComprehensiveBenchmarkAnalyzer:
    """
    Comprehensive statistical analysis for all external benchmarks.

    Provides:
    - Statistical significance testing vs published baselines
    - Effect size calculations
    - Multiple comparison corrections
    - Power analysis
    - Reproducibility verification
    - Publication-ready reporting
    """

    # Published baseline results from literature
    BASELINE_RESULTS = {
        'StandUp4AI': {
            'F1@IoU=0.3': 0.58,
            'Precision@IoU=0.3': 0.56,
            'Recall@IoU=0.3': 0.60,
            'citation': 'Moorani et al., EMNLP 2025'
        },
        'UR-FUNNY': {
            'Accuracy': 65.23,
            'F1': 0.63,
            'citation': 'Hafeez et al., EMNLP 2019'
        },
        'TED-Laughter': {
            'F1': 0.606,
            'Accuracy': 0.72,
            'citation': 'Maged et al., ACL 2022'
        },
        'MHD': {
            'F1': 0.68,
            'Precision': 0.71,
            'Recall': 0.65,
            'citation': 'Ghosal et al., WACV 2021'
        },
        'SCRIPTS': {
            'Accuracy': 0.76,
            'F1': 0.74,
            'citation': 'Chatzakou et al., LREC 2022'
        }
    }

    def __init__(self, output_dir: str = None):
        """
        Initialize comprehensive benchmark analyzer.

        Args:
            output_dir: Directory for saving reports and plots
        """
        self.stat_framework = AdvancedStatisticalFramework()
        self.output_dir = Path(output_dir) if output_dir else Path("results/statistical_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("🔬 COMPREHENSIVE BENCHMARK STATISTICAL ANALYZER")
        print("=" * 80)
        print(f"Output directory: {self.output_dir}")
        print(f"Available benchmarks: {list(self.BASELINE_RESULTS.keys())}")
        print("=" * 80)

    def analyze_comprehensive_results(self,
                                     results_dict: Dict[str, Dict[str, np.ndarray]],
                                     correction_method: str = 'holm') -> Dict[str, BenchmarkReport]:
        """
        Perform comprehensive statistical analysis on all benchmark results.

        Args:
            results_dict: Dictionary of benchmark results
                Format: {'benchmark_name': {'metric_name': np.array([results])}}
            correction_method: Multiple comparison correction method

        Returns:
            Dictionary of comprehensive benchmark reports
        """
        print("\n🎯 PERFORMING COMPREHENSIVE STATISTICAL ANALYSIS")
        print("=" * 80)

        all_reports = {}

        for benchmark_name, benchmark_results in results_dict.items():
            print(f"\n📊 Analyzing {benchmark_name}")
            print("-" * 40)

            if benchmark_name not in self.BASELINE_RESULTS:
                print(f"⚠️  Warning: No baseline found for {benchmark_name}")
                continue

            report = self._analyze_single_benchmark(
                benchmark_name,
                benchmark_results,
                correction_method
            )

            all_reports[benchmark_name] = report

            # Print summary
            print(f"\n📈 SUMMARY for {benchmark_name}")
            print(f"Overall assessment: {report.overall_assessment}")
            print(f"Publication ready: {report.publication_ready}")
            print(f"Significant improvements: {sum(report.significance_summary.values())}/{len(report.significance_summary)}")

        # Generate overall analysis
        print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETE")
        print(f"Analyzed {len(all_reports)} benchmarks")
        print("=" * 80)

        return all_reports

    def _analyze_single_benchmark(self,
                                 benchmark_name: str,
                                 benchmark_results: Dict[str, np.ndarray],
                                 correction_method: str) -> BenchmarkReport:
        """
        Analyze a single benchmark with comprehensive statistics.
        """
        baseline = self.BASELINE_RESULTS[benchmark_name]

        # Initialize storage
        statistical_tests = {}
        comparisons = {}
        significance_summary = {}
        effect_sizes = {}
        confidence_intervals = {}
        power_analysis = {}

        # Perform statistical tests for each metric
        all_p_values = []

        for metric_name, our_results in benchmark_results.items():
            if metric_name not in baseline:
                continue

            print(f"  Testing {metric_name}: {np.mean(our_results):.4f} vs baseline {baseline[metric_name]:.4f}")

            # Compare vs baseline
            comparison = self.stat_framework.compare_vs_baseline(
                benchmark_name=f"{benchmark_name}_{metric_name}",
                our_results=our_results,
                baseline_value=baseline[metric_name]
            )

            comparisons[metric_name] = comparison
            statistical_tests[metric_name] = comparison.statistical_test
            all_p_values.append(comparison.statistical_test.p_value)

            # Store results
            effect_sizes[metric_name] = comparison.statistical_test.effect_size
            confidence_intervals[metric_name] = comparison.statistical_test.confidence_interval
            power_analysis[metric_name] = comparison.statistical_test.power

            # Check significance (before correction)
            significance_summary[metric_name] = comparison.statistical_test.is_significant

        # Apply multiple comparison correction
        if all_p_values:
            corrected_p_values = self._apply_correction(all_p_values, correction_method)

            # Update significance with corrected p-values
            for i, metric_name in enumerate(significance_summary.keys()):
                is_significant_corrected = corrected_p_values[i] < self.stat_framework.alpha
                significance_summary[metric_name] = is_significant_corrected

                # Update statistical test results with corrected p-values
                original_test = statistical_tests[metric_name]
                statistical_tests[metric_name] = StatisticalTestResult(
                    test_name=original_test.test_name,
                    statistic=original_test.statistic,
                    p_value=original_test.p_value,
                    effect_size=original_test.effect_size,
                    confidence_interval=original_test.confidence_interval,
                    corrected_p_value=corrected_p_values[i],
                    is_significant=is_significant_corrected,
                    power=original_test.power,
                    interpretation=f"{original_test.interpretation} (Corrected p={corrected_p_values[i]:.4f})",
                    metadata=original_test.metadata
                )

        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            benchmark_name,
            significance_summary,
            effect_sizes,
            power_analysis
        )

        # Check if publication ready
        publication_ready = self._check_publication_readiness(
            significance_summary,
            effect_sizes,
            power_analysis
        )

        return BenchmarkReport(
            benchmark_name=benchmark_name,
            baseline_results=baseline,
            our_results={k: float(np.mean(v)) for k, v in benchmark_results.items()},
            statistical_tests=statistical_tests,
            comparisons=comparisons,
            significance_summary=significance_summary,
            effect_sizes=effect_sizes,
            confidence_intervals=confidence_intervals,
            power_analysis=power_analysis,
            overall_assessment=overall_assessment,
            publication_ready=publication_ready,
            metadata={
                'correction_method': correction_method,
                'n_metrics_tested': len(significance_summary),
                'n_significant': sum(significance_summary.values()),
                'baseline_citation': baseline.get('citation', 'Unknown')
            }
        )

    def _apply_correction(self, p_values: List[float], method: str) -> List[float]:
        """Apply multiple comparison correction"""
        if method == 'bonferroni':
            return self.stat_framework.bonferroni_correction(p_values)
        elif method == 'holm':
            return self.stat_framework.holm_bonferroni_correction(p_values)
        elif method == 'fdr':
            return self.stat_framework.benjamini_hochberg_correction(p_values)
        else:
            return p_values

    def _generate_overall_assessment(self,
                                    benchmark_name: str,
                                    significance_summary: Dict[str, bool],
                                    effect_sizes: Dict[str, float],
                                    power_analysis: Dict[str, float]) -> str:
        """Generate overall assessment for a benchmark"""

        n_significant = sum(significance_summary.values())
        n_total = len(significance_summary)

        if n_total == 0:
            return "No metrics available for analysis"

        # Calculate average effect size
        avg_effect_size = np.mean(list(effect_sizes.values()))

        # Calculate average power
        avg_power = np.mean(list(power_analysis.values()))

        # Generate assessment
        if n_significant == n_total and avg_effect_size > 0.5:
            return f"EXCELLENT: All {n_total} metrics show significant improvement with large effect sizes"
        elif n_significant >= n_total * 0.7 and avg_effect_size > 0.3:
            return f"STRONG: {n_significant}/{n_total} metrics show significant improvement with medium-large effect sizes"
        elif n_significant >= n_total * 0.5:
            return f"MODERATE: {n_significant}/{n_total} metrics show significant improvement"
        elif n_significant > 0:
            return f"LIMITED: {n_significant}/{n_total} metrics show significant improvement"
        else:
            return f"INSUFFICIENT: No metrics show statistically significant improvement"

    def _check_publication_readiness(self,
                                    significance_summary: Dict[str, bool],
                                    effect_sizes: Dict[str, float],
                                    power_analysis: Dict[str, float]) -> bool:
        """
        Check if results meet academic publication standards.

        Criteria:
        1. At least 50% of metrics significant
        2. Average effect size > 0.3 (medium)
        3. Average power > 0.7 (adequate)
        """
        if not significance_summary:
            return False

        n_significant = sum(significance_summary.values())
        n_total = len(significance_summary)

        # Criterion 1: Significant improvements
        criterion1 = n_significant >= n_total * 0.5

        # Criterion 2: Meaningful effect sizes
        avg_effect_size = np.mean(list(effect_sizes.values()))
        criterion2 = avg_effect_size > 0.3

        # Criterion 3: Adequate power
        avg_power = np.mean(list(power_analysis.values()))
        criterion3 = avg_power > 0.7

        return criterion1 and criterion2 and criterion3

    def generate_publication_table(self,
                                  reports: Dict[str, BenchmarkReport],
                                  format: str = 'latex') -> str:
        """
        Generate publication-ready table from comprehensive analysis.

        Args:
            reports: Dictionary of benchmark reports
            format: 'latex', 'markdown', or 'json'

        Returns:
            Formatted table string
        """
        if format == 'latex':
            return self._generate_latex_table(reports)
        elif format == 'markdown':
            return self._generate_markdown_table(reports)
        elif format == 'json':
            return self._generate_json_table(reports)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_latex_table(self, reports: Dict[str, BenchmarkReport]) -> str:
        """Generate LaTeX formatted table for academic publication"""

        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\caption{Comprehensive Statistical Analysis of Benchmark Results}")
        latex.append("\\label{tab:statistical_analysis}")
        latex.append("\\begin{tabular}{llccc}")
        latex.append("\\toprule")
        latex.append("Benchmark & Metric & Baseline & Ours & Improvement \\\\")
        latex.append("\\midrule")

        for benchmark_name, report in reports.items():
            for metric_name, comparison in report.comparisons.items():
                baseline_val = comparison.baseline_metric
                our_val = comparison.our_metric
                improvement = comparison.improvement

                # Add significance stars
                sig_stars = ""
                if comparison.statistical_test.corrected_p_value:
                    p_val = comparison.statistical_test.corrected_p_value
                else:
                    p_val = comparison.statistical_test.p_value

                if p_val < 0.001:
                    sig_stars = "$^{***}$"
                elif p_val < 0.01:
                    sig_stars = "$^{**}$"
                elif p_val < 0.05:
                    sig_stars = "$^{*}$"

                # Format improvement
                if improvement > 0:
                    improvement_str = f"+{improvement:.4f}{sig_stars}"
                else:
                    improvement_str = f"{improvement:.4f}{sig_stars}"

                latex.append(f"{benchmark_name} & {metric_name} & {baseline_val:.4f} & {our_val:.4f} & {improvement_str} \\\\")

        latex.append("\\midrule")
        latex.append("\\multicolumn{5}{l}{\\footnotesize $^{***}p < 0.001$, $^{**}p < 0.01$, $^{*}p < 0.05$ (corrected for multiple comparisons)} \\\\")
        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append("\\end{table}")

        return "\n".join(latex)

    def _generate_markdown_table(self, reports: Dict[str, BenchmarkReport]) -> str:
        """Generate Markdown formatted table"""

        markdown = []
        markdown.append("# Comprehensive Statistical Analysis Results")
        markdown.append("")
        markdown.append("| Benchmark | Metric | Baseline | Ours | Improvement | Effect Size | P-value |")
        markdown.append("|-----------|--------|----------|------|-------------|-------------|---------|")

        for benchmark_name, report in reports.items():
            for metric_name, comparison in report.comparisons.items():
                baseline_val = comparison.baseline_metric
                our_val = comparison.our_metric
                improvement = comparison.improvement
                effect_size = comparison.statistical_test.effect_size
                p_val = comparison.statistical_test.corrected_p_value or comparison.statistical_test.p_value

                # Significance indicator
                sig_indicator = "✓" if p_val < 0.05 else "✗"

                markdown.append(f"| {benchmark_name} | {metric_name} | {baseline_val:.4f} | {our_val:.4f} | {improvement:+.4f} | {effect_size:.4f} | {p_val:.4f} {sig_indicator} |")

        return "\n".join(markdown)

    def _generate_json_table(self, reports: Dict[str, BenchmarkReport]) -> str:
        """Generate JSON formatted results"""

        # Convert dataclasses to dict with proper serialization
        reports_dict = {}
        for benchmark_name, report in reports.items():
            reports_dict[benchmark_name] = {
                'benchmark_name': report.benchmark_name,
                'baseline_results': report.baseline_results,
                'our_results': report.our_results,
                'overall_assessment': report.overall_assessment,
                'publication_ready': bool(report.publication_ready),  # Ensure bool serialization
                'significance_summary': {k: bool(v) for k, v in report.significance_summary.items()},
                'effect_sizes': report.effect_sizes,
                'power_analysis': report.power_analysis,
                'metadata': report.metadata
            }

        return json.dumps(reports_dict, indent=2)

    def save_comprehensive_report(self,
                                 reports: Dict[str, BenchmarkReport],
                                 filename: str = "comprehensive_statistical_analysis"):
        """
        Save comprehensive analysis report in multiple formats.

        Args:
            reports: Dictionary of benchmark reports
            filename: Base filename (without extension)
        """
        # Save JSON report
        json_path = self.output_dir / f"{filename}.json"
        with open(json_path, 'w') as f:
            json.dump(self._generate_json_table(reports), f, indent=2)
        print(f"✅ JSON report saved to {json_path}")

        # Save LaTeX table
        latex_path = self.output_dir / f"{filename}.tex"
        with open(latex_path, 'w') as f:
            f.write(self._generate_latex_table(reports))
        print(f"✅ LaTeX table saved to {latex_path}")

        # Save Markdown table
        md_path = self.output_dir / f"{filename}.md"
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown_table(reports))
        print(f"✅ Markdown table saved to {md_path}")

        # Generate and save summary report
        summary_path = self.output_dir / f"{filename}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(self._generate_summary_report(reports))
        print(f"✅ Summary report saved to {summary_path}")

    def _generate_summary_report(self, reports: Dict[str, BenchmarkReport]) -> str:
        """Generate comprehensive text summary"""

        summary = []
        summary.append("=" * 80)
        summary.append("COMPREHENSIVE STATISTICAL ANALYSIS SUMMARY")
        summary.append("=" * 80)
        summary.append("")

        # Overall statistics
        total_benchmarks = len(reports)
        publication_ready = sum(1 for r in reports.values() if r.publication_ready)

        summary.append(f"Total Benchmarks Analyzed: {total_benchmarks}")
        summary.append(f"Publication Ready: {publication_ready}/{total_benchmarks}")
        summary.append("")

        # Per-benchmark details
        for benchmark_name, report in reports.items():
            summary.append(f"\n{'=' * 80}")
            summary.append(f"BENCHMARK: {benchmark_name}")
            summary.append(f"Baseline: {report.metadata.get('baseline_citation', 'Unknown')}")
            summary.append(f"Overall Assessment: {report.overall_assessment}")
            summary.append(f"Publication Ready: {'YES ✓' if report.publication_ready else 'NO ✗'}")
            summary.append("-" * 80)

            for metric_name, comparison in report.comparisons.items():
                test_result = comparison.statistical_test
                summary.append(f"\n  Metric: {metric_name}")
                summary.append(f"    Baseline: {comparison.baseline_metric:.4f}")
                summary.append(f"    Ours: {comparison.our_metric:.4f}")
                summary.append(f"    Improvement: {comparison.improvement:+.4f} ({comparison.relative_improvement:+.2f}%)")
                summary.append(f"    Statistical Test: {test_result.test_name}")
                summary.append(f"    Statistic: {test_result.statistic:.4f}")
                summary.append(f"    P-value: {test_result.p_value:.4f}")

                if test_result.corrected_p_value:
                    summary.append(f"    Corrected P-value: {test_result.corrected_p_value:.4f}")

                summary.append(f"    Effect Size: {test_result.effect_size:.4f}")

                if test_result.confidence_interval:
                    summary.append(f"    95% CI: [{test_result.confidence_interval[0]:.4f}, {test_result.confidence_interval[1]:.4f}]")
                else:
                    summary.append(f"    95% CI: N/A")

                if test_result.power:
                    summary.append(f"    Power: {test_result.power:.4f}")
                else:
                    summary.append(f"    Power: N/A")
                summary.append(f"    Significant: {'YES ✓' if test_result.is_significant else 'NO ✗'}")
                summary.append(f"    Interpretation: {test_result.interpretation}")

        # Overall conclusions
        summary.append(f"\n{'=' * 80}")
        summary.append("OVERALL CONCLUSIONS")
        summary.append("=" * 80)

        significant_metrics = 0
        total_metrics = 0

        for report in reports.values():
            significant_metrics += sum(report.significance_summary.values())
            total_metrics += len(report.significance_summary)

        summary.append(f"Total Metrics Tested: {total_metrics}")
        summary.append(f"Significant Improvements: {significant_metrics} ({significant_metrics/total_metrics*100:.1f}%)")
        summary.append(f"Publication Ready Benchmarks: {publication_ready}/{total_benchmarks}")

        if publication_ready == total_benchmarks:
            summary.append("\n🎉 EXCELLENT: All benchmarks meet publication standards!")
        elif publication_ready >= total_benchmarks * 0.7:
            summary.append("\n✅ STRONG: Most benchmarks meet publication standards")
        elif publication_ready >= total_benchmarks * 0.5:
            summary.append("\n⚠️  MODERATE: Some benchmarks meet publication standards")
        else:
            summary.append("\n❌ INSUFFICIENT: Most benchmarks do not meet publication standards")

        summary.append("\n" + "=" * 80)

        return "\n".join(summary)

    def generate_visualization_plots(self, reports: Dict[str, BenchmarkReport]):
        """
        Generate publication-quality visualization plots.

        Args:
            reports: Dictionary of benchmark reports
        """
        if plt is None:
            print("\n⚠️  Skipping plot generation (matplotlib not available)")
            return

        print("\n📊 GENERATING VISUALIZATION PLOTS")

        try:
            # 1. Effect sizes plot
            self._plot_effect_sizes(reports)

            # 2. Confidence intervals plot
            self._plot_confidence_intervals(reports)

            # 3. Forest plot for meta-analysis
            self._plot_forest_plot(reports)

            # 4. Power analysis plot
            self._plot_power_analysis(reports)

            print("✅ All visualization plots saved")
        except Exception as e:
            print(f"⚠️  Error generating plots: {e}")

    def _plot_effect_sizes(self, reports: Dict[str, BenchmarkReport]):
        """Plot effect sizes across all benchmarks"""

        fig, ax = plt.subplots(figsize=(12, 6))

        # Collect effect sizes
        benchmark_names = []
        metric_names = []
        effect_sizes = []

        for benchmark_name, report in reports.items():
            for metric_name, effect_size in report.effect_sizes.items():
                benchmark_names.append(benchmark_name)
                metric_names.append(metric_name)
                effect_sizes.append(effect_size)

        # Color by effect size magnitude
        colors = ['green' if abs(es) > 0.8 else 'orange' if abs(es) > 0.5 else 'red' for es in effect_sizes]

        # Create bar plot
        x_pos = np.arange(len(effect_sizes))
        bars = ax.bar(x_pos, effect_sizes, color=colors, alpha=0.7)

        ax.set_xlabel('Metrics')
        ax.set_ylabel("Cohen's d")
        ax.set_title('Effect Sizes Across All Benchmarks')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([f"{bn}\n{mn}" for bn, mn in zip(benchmark_names, metric_names)],
                          rotation=45, ha='right', fontsize=8)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.axhline(y=0.2, color='gray', linestyle='--', linewidth=0.5, label='Small effect')
        ax.axhline(y=0.5, color='gray', linestyle='--', linewidth=0.5, label='Medium effect')
        ax.axhline(y=0.8, color='gray', linestyle='--', linewidth=0.5, label='Large effect')
        ax.legend()

        plt.tight_layout()
        plt.savefig(self.output_dir / 'effect_sizes.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_confidence_intervals(self, reports: Dict[str, BenchmarkReport]):
        """Plot confidence intervals for all comparisons"""

        fig, ax = plt.subplots(figsize=(12, 8))

        # Collect data
        y_positions = []
        means = []
        cis = []
        labels = []

        y_pos = 0
        for benchmark_name, report in reports.items():
            for metric_name, comparison in report.comparisons.items():
                y_positions.append(y_pos)
                means.append(comparison.our_metric)
                cis.append(comparison.statistical_test.confidence_interval)
                labels.append(f"{benchmark_name}\n{metric_name}")
                y_pos += 1

        # Plot confidence intervals
        for i, (y, mean, ci) in enumerate(zip(y_positions, means, cis)):
            color = 'green' if report.significance_summary.get(list(report.comparisons.keys())[i], False) else 'red'
            ax.plot([ci[0], ci[1]], [y, y], color=color, linewidth=2)
            ax.plot(mean, y, 'o', color=color, markersize=8)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('Metric Value')
        ax.set_title('95% Confidence Intervals for All Metrics')
        ax.grid(True, alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'confidence_intervals.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_forest_plot(self, reports: Dict[str, BenchmarkReport]):
        """Generate forest plot for meta-analysis"""

        fig, ax = plt.subplots(figsize=(10, 8))

        # Collect improvements
        improvements = []
        cis = []
        labels = []
        y_positions = []

        y_pos = 0
        for benchmark_name, report in reports.items():
            for metric_name, comparison in report.comparisons.items():
                improvements.append(comparison.improvement)
                cis.append(comparison.statistical_test.confidence_interval)
                labels.append(f"{benchmark_name} ({metric_name})")
                y_positions.append(y_pos)
                y_pos += 1

        # Plot forest plot
        for y, improvement, ci in zip(y_positions, improvements, cis):
            # Determine color based on significance
            color = 'green' if improvement > 0 else 'red'

            # Plot confidence interval
            ax.plot([ci[0], ci[1]], [y, y], color=color, linewidth=2)
            ax.plot(inprovement, y, 'o', color=color, markersize=8)

        # Reference line at 0
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1)

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel('Improvement over Baseline')
        ax.set_title('Forest Plot: Improvements with 95% Confidence Intervals')
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'forest_plot.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_power_analysis(self, reports: Dict[str, BenchmarkReport]):
        """Plot power analysis results"""

        fig, ax = plt.subplots(figsize=(10, 6))

        # Collect power values
        power_values = []
        labels = []

        for benchmark_name, report in reports.items():
            for metric_name, power in report.power_analysis.items():
                power_values.append(power)
                labels.append(f"{benchmark_name}\n{metric_name}")

        # Color by power level
        colors = ['green' if p >= 0.8 else 'orange' if p >= 0.7 else 'red' for p in power_values]

        # Create bar plot
        x_pos = np.arange(len(power_values))
        bars = ax.bar(x_pos, power_values, color=colors, alpha=0.7)

        ax.set_xlabel('Metrics')
        ax.set_ylabel('Statistical Power')
        ax.set_title('Power Analysis: Statistical Power for All Tests')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax.axhline(y=0.8, color='green', linestyle='--', linewidth=1, label='Excellent power (0.8)')
        ax.axhline(y=0.7, color='orange', linestyle='--', linewidth=1, label='Adequate power (0.7)')
        ax.legend()
        ax.set_ylim([0, 1.0])

        plt.tight_layout()
        plt.savefig(self.output_dir / 'power_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()


def main():
    """Demonstration of comprehensive benchmark analysis"""
    print("🔬 COMPREHENSIVE BENCHMARK STATISTICAL ANALYZER")
    print("=" * 80)

    analyzer = ComprehensiveBenchmarkAnalyzer()

    # Example: Generate synthetic benchmark results
    print("\n📊 GENERATING EXAMPLE BENCHMARK DATA")

    example_results = {
        'StandUp4AI': {
            'F1@IoU=0.3': np.random.normal(0.62, 0.03, 50),  # Our results
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

    # Run comprehensive analysis
    reports = analyzer.analyze_comprehensive_results(example_results)

    # Generate reports
    print("\n📈 GENERATING REPORTS")
    analyzer.save_comprehensive_report(reports)

    # Generate plots
    print("\n📊 GENERATING PLOTS")
    analyzer.generate_visualization_plots(reports)

    print("\n🎉 COMPREHENSIVE ANALYSIS COMPLETE")
    print(f"Results saved to: {analyzer.output_dir}")


if __name__ == "__main__":
    main()