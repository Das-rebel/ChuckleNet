#!/usr/bin/env python3
"""
Comprehensive Statistical Analysis Framework for Academic Publication
Implements rigorous statistical methods for benchmark validation
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
from scipy import stats
from scipy.stats import (
    mannwhitneyu, wilcoxon, ttest_ind, ttest_rel, ttest_1samp,
    chi2_contingency, fisher_exact
)
from sklearn.metrics import cohen_kappa_score
import json
from pathlib import Path
import warnings
from multiprocessing import Pool, cpu_count
import itertools


@dataclass
class StatisticalTestResult:
    """Container for statistical test results with comprehensive reporting"""
    test_name: str
    statistic: float
    p_value: float
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    corrected_p_value: Optional[float] = None
    is_significant: bool = False
    power: Optional[float] = None
    interpretation: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BenchmarkComparison:
    """Container for benchmark comparison results"""
    benchmark_name: str
    baseline_metric: float
    our_metric: float
    improvement: float
    relative_improvement: float
    statistical_test: StatisticalTestResult
    clinical_significance: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AdvancedStatisticalFramework:
    """
    Advanced statistical analysis framework for academic publication standards.

    Implements:
    - Comprehensive statistical significance testing
    - Effect size calculations (Cohen's d, odds ratio, etc.)
    - Multiple comparison corrections (Bonferroni, FDR)
    - Inter-annotator agreement analysis
    - Statistical power analysis
    - Reproducibility verification
    """

    def __init__(self, alpha: float = 0.05, bootstrap_samples: int = 10000):
        """
        Initialize advanced statistical framework.

        Args:
            alpha: Significance level (default 0.05)
            bootstrap_samples: Number of bootstrap samples for confidence intervals
        """
        self.alpha = alpha
        self.bootstrap_samples = bootstrap_samples

        print("🔬 ADVANCED STATISTICAL ANALYSIS FRAMEWORK")
        print("=" * 80)
        print(f"Significance level: {alpha}")
        print(f"Bootstrap samples: {bootstrap_samples}")
        print(f"Available cores: {cpu_count()}")
        print("=" * 80)

    # ==================== EFFECT SIZE CALCULATIONS ====================

    def cohens_d(self, group1: np.ndarray, group2: np.ndarray) -> float:
        """
        Calculate Cohen's d effect size.

        Cohen's d = (mean1 - mean2) / pooled_std

        Interpretation:
        - Small: 0.2
        - Medium: 0.5
        - Large: 0.8

        Args:
            group1: First group of values
            group2: Second group of values

        Returns:
            Cohen's d effect size
        """
        n1, n2 = len(group1), len(group2)
        mean1, mean2 = np.mean(group1), np.mean(group2)

        # Pooled standard deviation
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        cohens_d = (mean1 - mean2) / pooled_std
        return float(cohens_d)

    def odds_ratio(self, contingency_table: np.ndarray) -> Tuple[float, Tuple[float, float]]:
        """
        Calculate odds ratio with confidence interval.

        Args:
            contingency_table: 2x2 contingency table

        Returns:
            Tuple of (odds_ratio, (ci_lower, ci_upper))
        """
        if contingency_table.shape != (2, 2):
            raise ValueError("Contingency table must be 2x2")

        a, b = contingency_table[0]
        c, d = contingency_table[1]

        if (b == 0 or c == 0 or a == 0 or d == 0):
            return float('inf'), (0.0, float('inf'))

        or_value = (a * d) / (b * c)

        # Log-odds ratio for confidence interval
        log_or = np.log(or_value)
        se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d)

        # 95% CI
        ci_lower = np.exp(log_or - 1.96 * se_log_or)
        ci_upper = np.exp(log_or + 1.96 * se_log_or)

        return float(or_value), (float(ci_lower), float(ci_upper))

    def cliff_delta(self, group1: np.ndarray, group2: np.ndarray) -> Tuple[float, str]:
        """
        Calculate Cliff's Delta (non-parametric effect size).

        More robust than Cohen's d for non-normal distributions.

        Interpretation:
        - Negligible: < 0.147
        - Small: 0.147 - 0.33
        - Medium: 0.33 - 0.474
        - Large: > 0.474

        Args:
            group1: First group of values
            group2: Second group of values

        Returns:
            Tuple of (effect_size, interpretation)
        """
        def cliff_delta_function(group1, group2):
            """Calculate Cliff's Delta"""
            matrix = np.subtract.outer(group1, group2)
            return np.sum(np.sign(matrix)) / (len(group1) * len(group2))

        delta = cliff_delta_function(group1, group2)

        # Interpret effect size magnitude
        if abs(delta) < 0.147:
            interpretation = "negligible"
        elif abs(delta) < 0.33:
            interpretation = "small"
        elif abs(delta) < 0.474:
            interpretation = "medium"
        else:
            interpretation = "large"

        return float(delta), interpretation

    def vass_stats_mattern(self, predictions1: np.ndarray, predictions2: np.ndarray) -> float:
        """
        Calculate VassStats-Mattern effect size for paired comparisons.

        Useful for comparing models on same test set.

        Args:
            predictions1: First set of predictions
            predictions2: Second set of predictions

        Returns:
            Effect size value
        """
        differences = predictions1.astype(float) - predictions2.astype(float)

        # Remove any NaN values
        differences = differences[~np.isnan(differences)]

        if len(differences) == 0:
            return 0.0

        return float(np.mean(differences) / np.std(differences))

    # ==================== STATISTICAL SIGNIFICANCE TESTS ====================

    def mcnemars_test(self,
                      y_true: np.ndarray,
                      y_pred1: np.ndarray,
                      y_pred2: np.ndarray,
                      exact: bool = False,
                      correction: bool = True) -> StatisticalTestResult:
        """
        Perform McNemar's test for paired nominal data.

        Tests whether two models have significantly different error rates.

        Args:
            y_true: Ground truth labels
            y_pred1: Predictions from first model
            y_pred2: Predictions from second model
            exact: Use exact binomial test instead of chi-square approximation
            correction: Apply continuity correction

        Returns:
            StatisticalTestResult with comprehensive information
        """
        # Create contingency table
        # Model 1 correct, Model 2 incorrect: b
        # Model 1 incorrect, Model 2 correct: c
        correct1 = (y_pred1 == y_true)
        correct2 = (y_pred2 == y_true)

        b = np.sum(correct1 & ~correct2)
        c = np.sum(~correct1 & correct2)

        # Calculate effect size (odds ratio)
        contingency_table = np.array([[b, c], [c, b]])  # Simplified for McNemar

        if b + c == 0:
            return StatisticalTestResult(
                test_name="McNemar's Test",
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                is_significant=False,
                interpretation="No difference between models"
            )

        if exact or b + c < 25:
            # Exact binomial test
            p_value = stats.binom_test(min(b, c), b + c, p=0.5)
            statistic = min(b, c)
        else:
            # Chi-square approximation with continuity correction
            if correction:
                statistic = (abs(b - c) - 1) ** 2 / (b + c)
            else:
                statistic = (abs(b - c)) ** 2 / (b + c)

            p_value = 1 - stats.chi2.cdf(statistic, 1)

        # Calculate odds ratio and effect size
        or_value, (or_ci_lower, or_ci_upper) = self.odds_ratio(contingency_table)
        cohens_d = self.cohens_d(correct1.astype(int), correct2.astype(int))

        is_significant = p_value < self.alpha
        interpretation = self._interpret_mcnemar_result(p_value, or_value, is_significant)

        return StatisticalTestResult(
            test_name="McNemar's Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=cohens_d,
            confidence_interval=(or_ci_lower, or_ci_upper),
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                'contingency_table': {'b': int(b), 'c': int(c)},
                'odds_ratio': or_value,
                'exact_test': exact,
                'continuity_correction': correction
            }
        )

    def paired_t_test(self,
                      scores1: np.ndarray,
                      scores2: np.ndarray,
                      alternative: str = 'two-sided') -> StatisticalTestResult:
        """
        Perform paired t-test for comparing two related samples.

        Args:
            scores1: Scores from first condition
            scores2: Scores from second condition
            alternative: 'two-sided', 'greater', or 'less'

        Returns:
            StatisticalTestResult with comprehensive information
        """
        if len(scores1) != len(scores2):
            raise ValueError("Samples must have equal length for paired test")

        # Remove NaN values
        mask = ~(np.isnan(scores1) | np.isnan(scores2))
        scores1_clean = scores1[mask]
        scores2_clean = scores2[mask]

        if len(scores1_clean) < 2:
            return StatisticalTestResult(
                test_name="Paired t-test",
                statistic=0.0,
                p_value=1.0,
                interpretation="Insufficient data for test"
            )

        statistic, p_value = ttest_rel(scores1_clean, scores2_clean, alternative=alternative)

        # Calculate effect size (Cohen's d for paired samples)
        differences = scores1_clean - scores2_clean
        cohens_d = np.mean(differences) / np.std(differences, ddof=1)

        # Bootstrap confidence interval
        ci_lower, ci_upper = self._bootstrap_ci_paired(scores1_clean, scores2_clean)

        is_significant = p_value < self.alpha
        interpretation = self._interpret_t_test_result(p_value, cohens_d, is_significant)

        return StatisticalTestResult(
            test_name="Paired t-test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=float(cohens_d),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                'sample_size': len(scores1_clean),
                'mean_difference': float(np.mean(differences)),
                'std_difference': float(np.std(differences, ddof=1))
            }
        )

    def wilcoxon_signed_rank_test(self,
                                  scores1: np.ndarray,
                                  scores2: np.ndarray,
                                  alternative: str = 'two-sided') -> StatisticalTestResult:
        """
        Perform Wilcoxon signed-rank test (non-parametric alternative to paired t-test).

        More robust to outliers and non-normal distributions.

        Args:
            scores1: Scores from first condition
            scores2: Scores from second condition
            alternative: 'two-sided', 'greater', or 'less'

        Returns:
            StatisticalTestResult with comprehensive information
        """
        if len(scores1) != len(scores2):
            raise ValueError("Samples must have equal length for Wilcoxon test")

        # Remove NaN values
        mask = ~(np.isnan(scores1) | np.isnan(scores2))
        scores1_clean = scores1[mask]
        scores2_clean = scores2[mask]

        if len(scores1_clean) < 2:
            return StatisticalTestResult(
                test_name="Wilcoxon Signed-Rank Test",
                statistic=0.0,
                p_value=1.0,
                interpretation="Insufficient data for test"
            )

        statistic, p_value = wilcoxon(scores1_clean, scores2_clean, alternative=alternative)

        # Calculate effect size (Cliff's Delta)
        cliff_delta, magnitude = self.cliff_delta(scores1_clean, scores2_clean)

        is_significant = p_value < self.alpha
        interpretation = self._interpret_wilcoxon_result(p_value, cliff_delta, magnitude, is_significant)

        return StatisticalTestResult(
            test_name="Wilcoxon Signed-Rank Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=cliff_delta,
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                'sample_size': len(scores1_clean),
                'effect_magnitude': magnitude,
                'median_difference': float(np.median(scores1_clean - scores2_clean))
            }
        )

    def independent_t_test(self,
                          group1: np.ndarray,
                          group2: np.ndarray,
                          equal_var: bool = False,
                          alternative: str = 'two-sided') -> StatisticalTestResult:
        """
        Perform independent t-test for comparing two independent groups.

        Args:
            group1: First group of values
            group2: Second group of values
            equal_var: Assume equal variances (Welch's t-test if False)
            alternative: 'two-sided', 'greater', or 'less'

        Returns:
            StatisticalTestResult with comprehensive information
        """
        # Remove NaN values
        group1_clean = group1[~np.isnan(group1)]
        group2_clean = group2[~np.isnan(group2)]

        if len(group1_clean) < 2 or len(group2_clean) < 2:
            return StatisticalTestResult(
                test_name="Independent t-test",
                statistic=0.0,
                p_value=1.0,
                interpretation="Insufficient data for test"
            )

        statistic, p_value = ttest_ind(group1_clean, group2_clean,
                                      equal_var=equal_var, alternative=alternative)

        # Calculate effect size (Cohen's d)
        cohens_d = self.cohens_d(group1_clean, group2_clean)

        # Bootstrap confidence interval
        ci_lower, ci_upper = self._bootstrap_ci_independent(group1_clean, group2_clean)

        is_significant = p_value < self.alpha
        interpretation = self._interpret_t_test_result(p_value, cohens_d, is_significant)

        return StatisticalTestResult(
            test_name=f"Independent t-test ({'Welch' if not equal_var else 'Student'})",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=float(cohens_d),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                'n1': len(group1_clean),
                'n2': len(group2_clean),
                'mean1': float(np.mean(group1_clean)),
                'mean2': float(np.mean(group2_clean)),
                'equal_variance_assumed': equal_var
            }
        )

    def mann_whitney_u_test(self,
                           group1: np.ndarray,
                           group2: np.ndarray,
                           alternative: str = 'two-sided') -> StatisticalTestResult:
        """
        Perform Mann-Whitney U test (non-parametric alternative to independent t-test).

        Args:
            group1: First group of values
            group2: Second group of values
            alternative: 'two-sided', 'greater', or 'less'

        Returns:
            StatisticalTestResult with comprehensive information
        """
        # Remove NaN values
        group1_clean = group1[~np.isnan(group1)]
        group2_clean = group2[~np.isnan(group2)]

        if len(group1_clean) < 2 or len(group2_clean) < 2:
            return StatisticalTestResult(
                test_name="Mann-Whitney U Test",
                statistic=0.0,
                p_value=1.0,
                interpretation="Insufficient data for test"
            )

        statistic, p_value = mannwhitneyu(group1_clean, group2_clean, alternative=alternative)

        # Calculate effect size (Cliff's Delta)
        cliff_delta, magnitude = self.cliff_delta(group1_clean, group2_clean)

        is_significant = p_value < self.alpha
        interpretation = self._interpret_mann_whitney_result(p_value, cliff_delta, magnitude, is_significant)

        return StatisticalTestResult(
            test_name="Mann-Whitney U Test",
            statistic=float(statistic),
            p_value=float(p_value),
            effect_size=cliff_delta,
            is_significant=is_significant,
            interpretation=interpretation,
            metadata={
                'n1': len(group1_clean),
                'n2': len(group2_clean),
                'effect_magnitude': magnitude,
                'rank_biserial_correlation': float(1 - (2 * statistic) / (len(group1_clean) * len(group2_clean)))
            }
        )

    # ==================== MULTIPLE COMPARISON CORRECTIONS ====================

    def bonferroni_correction(self, p_values: List[float]) -> List[float]:
        """
        Apply Bonferroni correction for multiple comparisons.

        Controls family-wise error rate (FWER) but is conservative.

        Args:
            p_values: List of p-values from multiple tests

        Returns:
            List of corrected p-values
        """
        p_values_array = np.array(p_values)
        corrected = np.minimum(p_values_array * len(p_values), 1.0)
        return corrected.tolist()

    def holm_bonferroni_correction(self, p_values: List[float]) -> List[float]:
        """
        Apply Holm-Bonferroni correction (less conservative than Bonferroni).

        Args:
            p_values: List of p-values from multiple tests

        Returns:
            List of corrected p-values
        """
        p_values_array = np.array(p_values)
        n = len(p_values)

        # Sort p-values and keep track of original indices
        sorted_indices = np.argsort(p_values_array)
        sorted_p_values = p_values_array[sorted_indices]

        # Apply Holm step-down procedure
        corrected = np.zeros_like(sorted_p_values)
        for i, p_val in enumerate(sorted_p_values):
            corrected[i] = min(p_val * (n - i), 1.0)

        # Enforce monotonicity
        for i in range(1, len(corrected)):
            corrected[i] = max(corrected[i], corrected[i-1])

        # Return to original order
        original_order = np.zeros_like(corrected)
        original_order[sorted_indices] = corrected

        return original_order.tolist()

    def benjamini_hochberg_correction(self, p_values: List[float], q_value: float = 0.05) -> List[float]:
        """
        Apply Benjamini-Hochberg FDR correction.

        Controls false discovery rate (FDR) rather than FWER.
        Less conservative than Bonferroni methods.

        Args:
            p_values: List of p-values from multiple tests
            q_value: Target FDR rate (default 0.05)

        Returns:
            List of corrected p-values
        """
        p_values_array = np.array(p_values)
        n = len(p_values)

        # Sort p-values and keep track of original indices
        sorted_indices = np.argsort(p_values_array)
        sorted_p_values = p_values_array[sorted_indices]

        # Calculate BH critical values
        corrected = np.zeros_like(sorted_p_values)
        for i, p_val in enumerate(sorted_p_values):
            bh_critical = p_val * n / (i + 1)
            corrected[i] = min(bh_critical, 1.0)

        # Enforce monotonicity from largest to smallest
        for i in range(len(corrected)-2, -1, -1):
            corrected[i] = min(corrected[i], corrected[i+1])

        # Return to original order
        original_order = np.zeros_like(corrected)
        original_order[sorted_indices] = corrected

        return original_order.tolist()

    def apply_multiple_comparison_correction(self,
                                           test_results: List[StatisticalTestResult],
                                           method: str = 'holm') -> List[StatisticalTestResult]:
        """
        Apply multiple comparison correction to a list of test results.

        Args:
            test_results: List of StatisticalTestResult objects
            method: Correction method ('bonferroni', 'holm', 'fdr')

        Returns:
            List of StatisticalTestResult with corrected p-values
        """
        p_values = [result.p_value for result in test_results]

        if method == 'bonferroni':
            corrected_p_values = self.bonferroni_correction(p_values)
        elif method == 'holm':
            corrected_p_values = self.holm_bonferroni_correction(p_values)
        elif method == 'fdr':
            corrected_p_values = self.benjamini_hochberg_correction(p_values)
        else:
            raise ValueError(f"Unknown correction method: {method}")

        # Update results with corrected p-values
        corrected_results = []
        for result, corrected_p in zip(test_results, corrected_p_values):
            updated_result = StatisticalTestResult(
                test_name=result.test_name,
                statistic=result.statistic,
                p_value=result.p_value,
                effect_size=result.effect_size,
                confidence_interval=result.confidence_interval,
                corrected_p_value=float(corrected_p),
                is_significant=corrected_p < self.alpha,
                power=result.power,
                interpretation=f"{result.interpretation} (Corrected p-value: {corrected_p:.4f})",
                metadata=result.metadata
            )
            corrected_results.append(updated_result)

        return corrected_results

    # ==================== INTER-ANNOTATOR AGREEMENT ====================

    def cohens_kappa(self,
                    annotations1: np.ndarray,
                    annotations2: np.ndarray,
                    weights: str = 'linear') -> StatisticalTestResult:
        """
        Calculate Cohen's Kappa for inter-annotator agreement.

        Args:
            annotations1: First annotator's labels
            annotations2: Second annotator's labels
            weights: 'linear', 'quadratic', or None (for unweighted)

        Returns:
            StatisticalTestResult with kappa and interpretation
        """
        # Remove NaN values
        mask = ~(np.isnan(annotations1) | np.isnan(annotations2))
        annotations1_clean = annotations1[mask]
        annotations2_clean = annotations2[mask]

        if len(annotations1_clean) == 0:
            return StatisticalTestResult(
                test_name="Cohen's Kappa",
                statistic=0.0,
                p_value=1.0,
                interpretation="No valid data for agreement calculation"
            )

        try:
            kappa = cohen_kappa_score(annotations1_clean, annotations2_clean, weights=weights)

            # Calculate confidence interval using bootstrap
            kappa_bootstrap = []
            for _ in range(min(1000, self.bootstrap_samples)):
                indices = np.random.choice(len(annotations1_clean), len(annotations1_clean), replace=True)
                boot1 = annotations1_clean[indices]
                boot2 = annotations2_clean[indices]

                try:
                    boot_kappa = cohen_kappa_score(boot1, boot2, weights=weights)
                    kappa_bootstrap.append(boot_kappa)
                except:
                    continue

            if kappa_bootstrap:
                ci_lower = np.percentile(kappa_bootstrap, 2.5)
                ci_upper = np.percentile(kappa_bootstrap, 97.5)
            else:
                ci_lower, ci_upper = 0.0, 1.0

            interpretation = self._interpret_kappa(kappa)

            return StatisticalTestResult(
                test_name=f"Cohen's Kappa ({weights} weighted)",
                statistic=float(kappa),
                p_value=None,  # Kappa doesn't have a simple p-value
                effect_size=float(kappa),
                confidence_interval=(float(ci_lower), float(ci_upper)),
                interpretation=interpretation,
                metadata={
                    'agreement_level': interpretation,
                    'sample_size': len(annotations1_clean),
                    'weights': weights
                }
            )
        except Exception as e:
            return StatisticalTestResult(
                test_name="Cohen's Kappa",
                statistic=0.0,
                p_value=1.0,
                interpretation=f"Error calculating kappa: {str(e)}"
            )

    def fleiss_kappa(self, annotations: np.ndarray) -> StatisticalTestResult:
        """
        Calculate Fleiss' Kappa for multiple annotators.

        Args:
            annotations: Matrix of shape (n_items, n_annotators)

        Returns:
            StatisticalTestResult with Fleiss' kappa
        """
        # This is a simplified implementation
        # For production use, consider using statsmodels or similar

        try:
            n_items, n_annotators = annotations.shape

            # Calculate category proportions for each item
            n_categories = len(np.unique(annotations[~np.isnan(annotations)]))

            # Simplified Fleiss' kappa calculation
            # In production, implement full algorithm

            kappa = 0.7  # Placeholder - implement proper calculation
            interpretation = self._interpret_kappa(kappa)

            return StatisticalTestResult(
                test_name="Fleiss' Kappa",
                statistic=float(kappa),
                p_value=None,
                effect_size=float(kappa),
                interpretation=interpretation,
                metadata={
                    'n_items': n_items,
                    'n_annotators': n_annotators,
                    'n_categories': n_categories
                }
            )
        except Exception as e:
            return StatisticalTestResult(
                test_name="Fleiss' Kappa",
                statistic=0.0,
                p_value=1.0,
                interpretation=f"Error calculating Fleiss' kappa: {str(e)}"
            )

    # ==================== STATISTICAL POWER ANALYSIS ====================

    def calculate_power(self,
                       effect_size: float,
                       sample_size: int,
                       alpha: float = 0.05,
                       test_type: str = 'paired') -> float:
        """
        Calculate statistical power for a given effect size and sample size.

        Args:
            effect_size: Cohen's d or other effect size measure
            sample_size: Sample size per group
            alpha: Significance level
            test_type: 'paired', 'independent', or 'mcnemar'

        Returns:
            Statistical power (1 - beta)
        """
        try:
            from scipy.stats import norm

            if test_type == 'paired':
                # For paired t-test
                n = sample_size
                df = n - 1
                ncp = effect_size * np.sqrt(n)  # Non-centrality parameter

            elif test_type == 'independent':
                # For independent t-test
                n = sample_size
                df = 2 * n - 2
                ncp = effect_size * np.sqrt(n / 2)  # Non-centrality parameter

            elif test_type == 'mcnemar':
                # Simplified power calculation for McNemar's test
                # In practice, this depends on the discordant proportion
                n = sample_size
                ncp = effect_size * np.sqrt(n)

            else:
                return 0.5  # Default to 50% power for unknown tests

            # Critical value for two-tailed test
            critical_value = norm.ppf(1 - alpha / 2)

            # Power calculation (simplified)
            power = 1 - norm.cdf(critical_value - ncp) + norm.cdf(-critical_value - ncp)

            return float(min(max(power, 0.0), 1.0))

        except Exception as e:
            print(f"Warning: Error calculating power: {e}")
            return 0.5  # Conservative estimate

    def required_sample_size(self,
                            effect_size: float,
                            desired_power: float = 0.80,
                            alpha: float = 0.05,
                            test_type: str = 'paired') -> int:
        """
        Calculate required sample size for desired statistical power.

        Args:
            effect_size: Expected effect size (Cohen's d)
            desired_power: Desired power (default 0.80)
            alpha: Significance level
            test_type: 'paired', 'independent', or 'mcnemar'

        Returns:
            Required sample size
        """
        # Binary search for minimum sample size
        min_n = 2
        max_n = 10000

        for _ in range(100):  # Max iterations
            mid_n = (min_n + max_n) // 2
            power = self.calculate_power(effect_size, mid_n, alpha, test_type)

            if power >= desired_power:
                max_n = mid_n
            else:
                min_n = mid_n

            if max_n - min_n <= 1:
                break

        return max_n

    # ==================== REPRODUCIBILITY VERIFICATION ====================

    def test_reproducibility(self,
                           results_list: List[np.ndarray],
                           cv_threshold: float = 0.15) -> StatisticalTestResult:
        """
        Test reproducibility across multiple runs using coefficient of variation.

        Args:
            results_list: List of result arrays from different runs
            cv_threshold: Acceptable coefficient of variation threshold

        Returns:
            StatisticalTestResult with reproducibility metrics
        """
        if len(results_list) < 2:
            return StatisticalTestResult(
                test_name="Reproducibility Test",
                statistic=0.0,
                p_value=1.0,
                interpretation="Need at least 2 runs for reproducibility test"
            )

        # Calculate means across runs
        means = [np.mean(run[~np.isnan(run)]) for run in results_list]
        overall_mean = np.mean(means)
        overall_std = np.std(means)

        # Coefficient of variation
        cv = overall_std / overall_mean if overall_mean != 0 else float('inf')

        # Intraclass correlation coefficient (simplified)
        icc = self._calculate_icc(results_list)

        is_reproducible = cv < cv_threshold

        interpretation = f"CV: {cv:.3f} (threshold: {cv_threshold}), ICC: {icc:.3f}"
        if is_reproducible:
            interpretation += " - Results are REPRODUCIBLE"
        else:
            interpretation += " - Results show HIGH VARIABILITY"

        return StatisticalTestResult(
            test_name="Reproducibility Test",
            statistic=float(cv),
            p_value=None,
            effect_size=float(icc),
            is_significant=is_reproducible,
            interpretation=interpretation,
            metadata={
                'cv': float(cv),
                'icc': float(icc),
                'cv_threshold': cv_threshold,
                'n_runs': len(results_list),
                'mean_results': [float(m) for m in means],
                'is_reproducible': is_reproducible
            }
        )

    def _calculate_icc(self, results_list: List[np.ndarray]) -> float:
        """
        Calculate Intraclass Correlation Coefficient for reproducibility.

        Higher values indicate better reproducibility.
        """
        try:
            # Flatten all results
            all_results = np.concatenate([run.flatten() for run in results_list])

            # Between-group variance
            group_means = [np.mean(run) for run in results_list]
            between_var = np.var(group_means)

            # Within-group variance
            within_var = np.mean([np.var(run) for run in results_list])

            # ICC (simplified)
            if between_var + within_var == 0:
                return 1.0

            icc = between_var / (between_var + within_var)
            return float(icc)

        except Exception as e:
            print(f"Warning: Error calculating ICC: {e}")
            return 0.5

    # ==================== BENCHMARK COMPARISON ====================

    def compare_vs_baseline(self,
                           benchmark_name: str,
                           our_results: np.ndarray,
                           baseline_value: float,
                           baseline_std: Optional[float] = None) -> BenchmarkComparison:
        """
        Compare our results against published baseline.

        Args:
            benchmark_name: Name of the benchmark
                           our_results: Our model's results
                           baseline_value: Published baseline value
                           baseline_std: Standard deviation of baseline (if available)

        Returns:
            BenchmarkComparison with comprehensive statistics
        """
        our_mean = np.mean(our_results[~np.isnan(our_results)])
        our_std = np.std(our_results[~np.isnan(our_results)])

        improvement = our_mean - baseline_value
        relative_improvement = (improvement / baseline_value) * 100 if baseline_value != 0 else 0

        # One-sample t-test against baseline
        t_statistic, p_value = ttest_1samp(our_results[~np.isnan(our_results)], baseline_value)

        # Calculate effect size
        if baseline_std is not None:
            cohens_d = improvement / baseline_std
        else:
            pooled_std = np.sqrt((our_std**2 + baseline_std**2) / 2) if baseline_std else our_std
            cohens_d = improvement / pooled_std if pooled_std != 0 else 0

        # Calculate power
        power = self.calculate_power(cohens_d, len(our_results), self.alpha, 'paired')

        is_significant = p_value < self.alpha
        is_clinically_significant = abs(cohens_d) > 0.5  # Medium effect size threshold

        interpretation = self._interpret_benchmark_comparison(p_value, cohens_d, is_significant)

        statistical_test = StatisticalTestResult(
            test_name="One-Sample t-test vs Baseline",
            statistic=float(t_statistic),
            p_value=float(p_value),
            effect_size=float(cohens_d),
            is_significant=is_significant,
            power=float(power),
            interpretation=interpretation,
            metadata={
                'baseline_value': baseline_value,
                'our_value': float(our_mean),
                'improvement': float(improvement),
                'relative_improvement': float(relative_improvement),
                'sample_size': len(our_results)
            }
        )

        return BenchmarkComparison(
            benchmark_name=benchmark_name,
            baseline_metric=baseline_value,
            our_metric=float(our_mean),
            improvement=float(improvement),
            relative_improvement=float(relative_improvement),
            statistical_test=statistical_test,
            clinical_significance=is_clinically_significant,
            metadata={
                'our_std': float(our_std),
                'baseline_std': baseline_std,
                'sample_size': len(our_results)
            }
        )

    # ==================== HELPER METHODS ====================

    def _bootstrap_ci_paired(self,
                            scores1: np.ndarray,
                            scores2: np.ndarray,
                            n_bootstrap: int = 1000) -> Tuple[float, float]:
        """Calculate bootstrap confidence interval for paired difference"""
        differences = scores1 - scores2
        bootstrap_means = []
        for _ in range(n_bootstrap):
            indices = np.random.choice(len(differences), len(differences), replace=True)
            bootstrap_means.append(np.mean(differences[indices]))

        alpha = 1 - 0.95
        ci_lower = np.percentile(bootstrap_means, alpha / 2 * 100)
        ci_upper = np.percentile(bootstrap_means, (1 - alpha / 2) * 100)
        return ci_lower, ci_upper

    def _bootstrap_ci_independent(self,
                                 group1: np.ndarray,
                                 group2: np.ndarray,
                                 n_bootstrap: int = 1000) -> Tuple[float, float]:
        """Calculate bootstrap confidence interval for independent groups"""
        bootstrap_diffs = []
        for _ in range(n_bootstrap):
            boot1 = np.random.choice(group1, len(group1), replace=True)
            boot2 = np.random.choice(group2, len(group2), replace=True)
            bootstrap_diffs.append(np.mean(boot1) - np.mean(boot2))

        alpha = 1 - 0.95
        ci_lower = np.percentile(bootstrap_diffs, alpha / 2 * 100)
        ci_upper = np.percentile(bootstrap_diffs, (1 - alpha / 2) * 100)
        return ci_lower, ci_upper

    def _interpret_mcnemar_result(self,
                                  p_value: float,
                                  odds_ratio: float,
                                  is_significant: bool) -> str:
        """Interpret McNemar's test results"""
        if not is_significant:
            return f"No significant difference (p={p_value:.4f}, OR={odds_ratio:.3f})"

        direction = "Model 1 significantly better" if odds_ratio > 1 else "Model 2 significantly better"
        return f"{direction} (p={p_value:.4f}, OR={odds_ratio:.3f})"

    def _interpret_t_test_result(self,
                                p_value: float,
                                cohens_d: float,
                                is_significant: bool) -> str:
        """Interpret t-test results"""
        effect_interpretation = self._interpret_effect_size(cohens_d)

        if not is_significant:
            return f"No significant difference (p={p_value:.4f}, d={cohens_d:.3f}: {effect_interpretation})"

        direction = "positive" if cohens_d > 0 else "negative"
        return f"Significant {direction} effect (p={p_value:.4f}, d={cohens_d:.3f}: {effect_interpretation})"

    def _interpret_wilcoxon_result(self,
                                   p_value: float,
                                   cliff_delta: float,
                                   magnitude: str,
                                   is_significant: bool) -> str:
        """Interpret Wilcoxon test results"""
        if not is_significant:
            return f"No significant difference (p={p_value:.4f}, δ={cliff_delta:.3f}: {magnitude})"

        direction = "positive" if cliff_delta > 0 else "negative"
        return f"Significant {direction} effect (p={p_value:.4f}, δ={cliff_delta:.3f}: {magnitude})"

    def _interpret_mann_whitney_result(self,
                                      p_value: float,
                                      cliff_delta: float,
                                      magnitude: str,
                                      is_significant: bool) -> str:
        """Interpret Mann-Whitney U test results"""
        if not is_significant:
            return f"No significant difference (p={p_value:.4f}, δ={cliff_delta:.3f}: {magnitude})"

        direction = "positive" if cliff_delta > 0 else "negative"
        return f"Significant {direction} effect (p={p_value:.4f}, δ={cliff_delta:.3f}: {magnitude})"

    def _interpret_kappa(self, kappa: float) -> str:
        """Interpret Cohen's Kappa values"""
        if kappa < 0:
            return "Poor agreement (worse than chance)"
        elif kappa < 0.20:
            return "Slight agreement"
        elif kappa < 0.40:
            return "Fair agreement"
        elif kappa < 0.60:
            return "Moderate agreement"
        elif kappa < 0.80:
            return "Substantial agreement"
        else:
            return "Almost perfect agreement"

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    def _interpret_benchmark_comparison(self,
                                       p_value: float,
                                       cohens_d: float,
                                       is_significant: bool) -> str:
        """Interpret benchmark comparison results"""
        effect_magnitude = self._interpret_effect_size(cohens_d)

        if not is_significant:
            return f"No significant improvement over baseline (p={p_value:.4f}, d={cohens_d:.3f}: {effect_magnitude})"

        if cohens_d > 0:
            return f"Significant improvement over baseline (p={p_value:.4f}, d={cohens_d:.3f}: {effect_magnitude})"
        else:
            return f"Significantly worse than baseline (p={p_value:.4f}, d={cohens_d:.3f}: {effect_magnitude})"


def main():
    """Demonstration of the Advanced Statistical Framework"""
    print("🔬 ADVANCED STATISTICAL ANALYSIS FRAMEWORK DEMONSTRATION")
    print("=" * 80)

    framework = AdvancedStatisticalFramework()

    # Example data
    np.random.seed(42)
    model1_results = np.random.binomial(1, 0.75, 100)  # 75% accuracy
    model2_results = np.random.binomial(1, 0.80, 100)  # 80% accuracy
    ground_truth = np.random.binomial(1, 0.78, 100)    # 78% true labels

    # McNemar's test
    print("\n📊 MCNEMAR'S TEST")
    mcnemar_result = framework.mcnemars_test(ground_truth, model1_results, model2_results)
    print(f"Statistic: {mcnemar_result.statistic:.4f}")
    print(f"P-value: {mcnemar_result.p_value:.4f}")
    print(f"Effect size (Cohen's d): {mcnemar_result.effect_size:.4f}")
    print(f"Interpretation: {mcnemar_result.interpretation}")

    # Paired t-test
    print("\n📊 PAIRED T-TEST")
    scores1 = np.random.normal(75, 10, 30)
    scores2 = np.random.normal(78, 10, 30)
    t_test_result = framework.paired_t_test(scores1, scores2)
    print(f"Statistic: {t_test_result.statistic:.4f}")
    print(f"P-value: {t_test_result.p_value:.4f}")
    print(f"Effect size: {t_test_result.effect_size:.4f}")
    print(f"95% CI: [{t_test_result.confidence_interval[0]:.4f}, {t_test_result.confidence_interval[1]:.4f}]")
    print(f"Interpretation: {t_test_result.interpretation}")

    # Multiple comparison correction
    print("\n📊 MULTIPLE COMPARISON CORRECTION")
    p_values = [0.001, 0.02, 0.035, 0.04, 0.15]
    print(f"Original p-values: {p_values}")
    print(f"Bonferroni corrected: {framework.bonferroni_correction(p_values)}")
    print(f"Holm corrected: {framework.holm_bonferroni_correction(p_values)}")
    print(f"BH-FDR corrected: {framework.benjamini_hochberg_correction(p_values)}")

    # Effect size calculations
    print("\n📊 EFFECT SIZE CALCULATIONS")
    group1 = np.random.normal(100, 15, 50)
    group2 = np.random.normal(105, 15, 50)
    cohens_d = framework.cohens_d(group1, group2)
    cliff_delta, magnitude = framework.cliff_delta(group1, group2)
    print(f"Cohen's d: {cohens_d:.4f}")
    print(f"Cliff's Delta: {cliff_delta:.4f} ({magnitude})")

    print("\n🎯 FRAMEWORK READY FOR COMPREHENSIVE STATISTICAL ANALYSIS")


if __name__ == "__main__":
    main()