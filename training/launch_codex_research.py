#!/usr/bin/env python3
"""
Launch Script for Codex Autonomous Research Loop
Complete testing and deployment system for autonomous AI research
"""

import os
import sys
import json
import time
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import argparse

# Setup paths
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
os.chdir(str(PROJECT_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('codex_research.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a test"""
    name: str
    success: bool
    duration: float
    message: str
    details: Dict[str, Any] = None


class CodexResearchLauncher:
    """
    Complete launch and test system for Codex autonomous research
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.training_dir = project_dir / "training"
        self.experiments_dir = project_dir / "experiments" / "codex_autoresearch"
        self.reports_dir = project_dir / "research_reports"

        # Create directories
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Import after path setup
        try:
            from training.codex_autoresearch_loop import (
                CodexAutoresearchLoop, HypothesisGenerator,
                CompilationEngine, TrainingPipeline,
                EvaluationSystem, GitCommitSystem
            )
            from training.memory_optimized_trainer import (
                MemoryOptimizer, TurboQuantOptimizer,
                GradientAccumulator, MemoryEfficientDataLoader
            )
            from training.research_monitor import (
                PerformanceTracker, AlertSystem,
                ResourceMonitor, ResearchReporter,
                ResearchDashboard
            )

            self.CodexAutoresearchLoop = CodexAutoresearchLoop
            self.HypothesisGenerator = HypothesisGenerator
            self.CompilationEngine = CompilationEngine
            self.TrainingPipeline = TrainingPipeline
            self.EvaluationSystem = EvaluationSystem
            self.GitCommitSystem = GitCommitSystem
            self.MemoryOptimizer = MemoryOptimizer
            self.TurboQuantOptimizer = TurboQuantOptimizer
            self.GradientAccumulator = GradientAccumulator
            self.MemoryEfficientDataLoader = MemoryEfficientDataLoader
            self.PerformanceTracker = PerformanceTracker
            self.AlertSystem = AlertSystem
            self.ResourceMonitor = ResourceMonitor
            self.ResearchReporter = ResearchReporter
            self.ResearchDashboard = ResearchDashboard

            self.modules_loaded = True
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            self.modules_loaded = False

    def run_comprehensive_tests(self) -> List[TestResult]:
        """
        Run comprehensive tests of all components

        Returns:
            List of test results
        """
        print("\n" + "=" * 80)
        print("🧪 RUNNING COMPREHENSIVE CODEX RESEARCH TESTS")
        print("=" * 80 + "\n")

        test_results = []

        # Test 1: Memory Optimization
        test_results.append(self._test_memory_optimization())

        # Test 2: Hypothesis Generation
        test_results.append(self._test_hypothesis_generation())

        # Test 3: Compilation Engine
        test_results.append(self._test_compilation_engine())

        # Test 4: Monitoring System
        test_results.append(self._test_monitoring_system())

        # Test 5: Integration Test
        test_results.append(self._test_integration())

        # Print test summary
        self._print_test_summary(test_results)

        return test_results

    def _test_memory_optimization(self) -> TestResult:
        """Test memory optimization system"""
        print("🧠 Testing Memory Optimization System...")

        start_time = time.time()

        try:
            # Initialize memory optimizer
            optimizer = self.MemoryOptimizer(target_memory_gb=6.0)

            # Test memory snapshot
            snapshot = optimizer.get_memory_snapshot()
            assert snapshot.used_memory_gb > 0, "Memory snapshot failed"

            # Test optimization
            result = optimizer.optimize_memory()
            assert 'strategy' in result['optimizations'], "Optimization failed"

            # Test batch size calculation
            batch_size = optimizer.get_optimal_batch_size(base_batch_size=2)
            assert batch_size >= 1, "Batch size calculation failed"

            duration = time.time() - start_time

            return TestResult(
                name="Memory Optimization",
                success=True,
                duration=duration,
                message="All memory optimization tests passed",
                details={
                    'memory_gb': snapshot.used_memory_gb,
                    'optimal_batch_size': batch_size,
                    'strategy': result['optimizations']['strategy']
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Memory Optimization",
                success=False,
                duration=duration,
                message=f"Test failed: {e}"
            )

    def _test_hypothesis_generation(self) -> TestResult:
        """Test hypothesis generation system"""
        print("🔬 Testing Hypothesis Generation System...")

        start_time = time.time()

        try:
            # Initialize hypothesis generator
            generator = self.HypothesisGenerator()

            # Test hypothesis generation
            current_metrics = {'test_f1': 0.71, 'test_iou_f1': 0.65}
            hypotheses = generator.generate_hypotheses(
                current_metrics=current_metrics,
                baseline_f1=0.7222,
                max_hypotheses=3
            )

            assert len(hypotheses) > 0, "No hypotheses generated"

            # Validate hypotheses
            for hypothesis in hypotheses:
                assert hypothesis.name, "Hypothesis missing name"
                assert hypothesis.rationale, "Hypothesis missing rationale"
                assert 0 < hypothesis.expected_improvement < 1, "Invalid expected improvement"
                assert 0 < hypothesis.confidence <= 1, "Invalid confidence"

            duration = time.time() - start_time

            return TestResult(
                name="Hypothesis Generation",
                success=True,
                duration=duration,
                message=f"Generated {len(hypotheses)} valid hypotheses",
                details={
                    'hypotheses': [h.name for h in hypotheses],
                    'categories': [h.category for h in hypotheses]
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Hypothesis Generation",
                success=False,
                duration=duration,
                message=f"Test failed: {e}"
            )

    def _test_compilation_engine(self) -> TestResult:
        """Test compilation engine"""
        print("⚙️  Testing Compilation Engine...")

        start_time = time.time()

        try:
            # Initialize compilation engine
            compiler = self.CompilationEngine(self.project_dir)

            # Create test hypothesis
            from training.codex_autoresearch_loop import Hypothesis
            test_hypothesis = Hypothesis(
                name="test_compilation",
                rationale="Test compilation",
                modifications={'test_param': 'test_value'},
                expected_improvement=0.01,
                confidence=0.7,
                category="testing"
            )

            # Test compilation
            test_dir = self.experiments_dir / "test_compilation"
            result = compiler.compile_experiment(test_hypothesis, test_dir)

            assert result['success'], "Compilation failed"
            assert 'config' in result, "Config missing from result"

            # Verify config file created
            config_file = test_dir / "experiment_config.json"
            assert config_file.exists(), "Config file not created"

            duration = time.time() - start_time

            return TestResult(
                name="Compilation Engine",
                success=True,
                duration=duration,
                message="Compilation successful",
                details={
                    'compilation_time': result['compilation_time'],
                    'config_file': str(config_file)
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Compilation Engine",
                success=False,
                duration=duration,
                message=f"Test failed: {e}"
            )

    def _test_monitoring_system(self) -> TestResult:
        """Test monitoring system"""
        print("📊 Testing Monitoring System...")

        start_time = time.time()

        try:
            # Initialize monitoring components
            performance_tracker = self.PerformanceTracker()
            alert_system = self.AlertSystem()
            resource_monitor = self.ResourceMonitor()
            reporter = self.ResearchReporter(
                self.reports_dir,
                performance_tracker,
                alert_system,
                resource_monitor
            )
            dashboard = self.ResearchDashboard(
                performance_tracker,
                alert_system,
                resource_monitor
            )

            # Test metric recording
            performance_tracker.record_metric('test_f1', 0.73, self.PerformanceTracker.MetricType.PERFORMANCE)

            # Test alert system
            alert_system.check_thresholds('memory_usage', 6.5)
            recent_alerts = alert_system.get_recent_alerts(hours=1)

            # Test resource monitoring
            resource_monitor.start_monitoring()
            resources = resource_monitor.sample_resources()
            resource_monitor.stop_monitoring()

            # Test report generation
            cycle_data = {
                'success': True,
                'duration': 300,
                'test_f1': 0.73,
                'test_iou_f1': 0.68,
                'hypotheses_tested': ['test_hypothesis'],
                'successful_experiments': 1,
                'failed_experiments': 0,
                'hypothesis_time': 30,
                'compilation_time': 30,
                'training_time': 180,
                'evaluation_time': 30,
                'git_commit_time': 30
            }

            report = reporter.generate_cycle_report(1, cycle_data)

            duration = time.time() - start_time

            return TestResult(
                name="Monitoring System",
                success=True,
                duration=duration,
                message="All monitoring components working",
                details={
                    'metrics_tracked': len(performance_tracker.metrics),
                    'alerts_triggered': len(recent_alerts),
                    'resource_samples': 1,
                    'reports_generated': 1
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Monitoring System",
                success=False,
                duration=duration,
                message=f"Test failed: {e}"
            )

    def _test_integration(self) -> TestResult:
        """Test full system integration"""
        print("🔧 Testing System Integration...")

        start_time = time.time()

        try:
            # Initialize main research loop
            research_loop = self.CodexAutoresearchLoop(self.project_dir)

            # Test research state management
            research_loop._save_research_state()
            assert (self.experiments_dir / "research_state.json").exists(), "State file not created"

            # Test hypothesis generation
            current_metrics = {'test_f1': 0.71, 'test_iou_f1': 0.65}
            hypotheses = research_loop.hypothesis_generator.generate_hypotheses(
                current_metrics=current_metrics,
                baseline_f1=0.7222,
                max_hypotheses=2
            )

            assert len(hypotheses) > 0, "No hypotheses generated in integration test"

            # Test time budget calculation
            time_budget = research_loop._calculate_time_budget(5)  # 5 minutes
            assert sum(time_budget.values()) == 300, "Time budget calculation failed"

            duration = time.time() - start_time

            return TestResult(
                name="System Integration",
                success=True,
                duration=duration,
                message="Full system integration successful",
                details={
                    'hypotheses_generated': len(hypotheses),
                    'time_budget_minutes': 5,
                    'components_tested': 5
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="System Integration",
                success=False,
                duration=duration,
                message=f"Test failed: {e}"
            )

    def _print_test_summary(self, test_results: List[TestResult]):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)

        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.success)
        failed_tests = total_tests - passed_tests

        for result in test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} | {result.name:20s} | {result.duration:.2f}s | {result.message}")

        print("=" * 80)
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        print("=" * 80 + "\n")

    def launch_research(self,
                       max_cycles: int = 100,
                       cycle_duration_minutes: int = 5,
                       dry_run: bool = False) -> bool:
        """
        Launch autonomous research loop

        Args:
            max_cycles: Maximum number of research cycles
            cycle_duration_minutes: Target duration per cycle
            dry_run: If True, run in dry-run mode

        Returns:
            True if launch successful
        """
        print("\n" + "=" * 80)
        print("🚀 LAUNCHING CODEX AUTONOMOUS RESEARCH LOOP")
        print("=" * 80)

        if not self.modules_loaded:
            print("❌ Required modules not loaded. Cannot launch research.")
            return False

        # Run tests first
        test_results = self.run_comprehensive_tests()
        if not all(r.success for r in test_results):
            print("⚠️  Some tests failed. Launch anyway? (y/n): ", end='')
            response = input().strip().lower()
            if response != 'y':
                print("❌ Launch cancelled.")
                return False

        print("\n🎯 RESEARCH CONFIGURATION")
        print("-" * 80)
        print(f"Max Cycles: {max_cycles}")
        print(f"Cycle Duration: {cycle_duration_minutes} minutes")
        print(f"Target F1: 0.7222")
        print(f"Dry Run: {dry_run}")
        print("-" * 80)

        # Initialize research loop
        try:
            research_loop = self.CodexAutoresearchLoop(self.project_dir)

            if dry_run:
                print("🔍 DRY RUN MODE - Running single test cycle...")
                result = research_loop.run_research_cycle(cycle_duration_minutes)
                print(f"Test cycle completed: {result['success']}")
                return result['success']
            else:
                print("🚀 STARTING CONTINUOUS RESEARCH...")
                research_loop.run_continuous_research(
                    max_cycles=max_cycles,
                    cycle_duration_minutes=cycle_duration_minutes,
                    cycles_before_save=5
                )
                return True

        except KeyboardInterrupt:
            print("\n⚠️  Research interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Research failed: {e}")
            logger.exception("Research launch failed")
            return False

    def create_quick_start_guide(self):
        """Create quick start guide for users"""
        guide_path = self.project_dir / "CODEX_QUICK_START.md"

        guide_content = """# Codex Autonomous Research Loop - Quick Start Guide

## Overview
The Codex Autonomous Research Loop is a revolutionary AI system that continuously improves the GCACU autonomous laughter prediction architecture through automated scientific experimentation.

## Key Features
- **5-Minute Innovation Cycles**: Rapid hypothesis testing
- **Autonomous AI Research**: AI improves itself automatically
- **Resource-Efficient**: Optimized for 8GB Mac M2
- **Scientific Method**: Hypothesis → Experiment → Analysis → Conclusion

## Prerequisites
- Python 3.8+
- 8GB Mac M2 (or similar system)
- Git (for version control)

## Quick Start

### 1. Run Tests
```bash
python training/launch_codex_research.py --test
```

### 2. Dry Run (Single Test Cycle)
```bash
python training/launch_codex_research.py --dry-run
```

### 3. Launch Full Research
```bash
python training/launch_codex_research.py --cycles 100 --duration 5
```

### 4. Monitor Progress
```bash
tail -f codex_research.log
```

## Research Process

Each 5-minute cycle consists of:
1. **Hypothesis Generation** (30s): AI generates improvement hypotheses
2. **Compilation** (30s): Optimize MLX + TurboQuant + mHC settings
3. **Training** (3min): Train model with new configuration
4. **Evaluation** (30s): Test against 0.7222 baseline
5. **Git Commit** (30s): Save successful improvements

## Memory Optimization

The system automatically manages memory for 8GB constraint:
- **Conservative** (< 4GB): Can increase batch size
- **Moderate** (4-6GB): Optimal for training
- **Aggressive** (6-7GB): Reduce memory usage
- **Critical** (> 7GB): Emergency optimization

## Monitoring

Real-time monitoring includes:
- Performance metrics (F1, IoU-F1)
- Resource usage (memory, CPU)
- Alert system for threshold breaches
- Comprehensive cycle reports

## Expected Results

- **Baseline**: 0.7222 Test F1
- **Target**: > 0.75 Test F1 (3.8% improvement)
- **Cycle Time**: ~5 minutes per iteration
- **Success Rate**: 20-30% of experiments improve performance

## Troubleshooting

### Out of Memory
- System automatically optimizes memory usage
- Reduce batch size in configuration
- Close other applications

### Slow Training
- Check system resources
- Verify MLX installation
- Consider longer cycle duration

### Poor Performance
- Review research reports
- Check hypothesis generation
- Verify data quality

## Files Generated

- `experiments/codex_autoresearch/`: Experiment results
- `research_reports/`: Cycle reports and summaries
- `research_state.json`: Persistent research state
- `codex_research.log`: Research log file

## Advanced Usage

### Custom Hypotheses
Edit `HypothesisGenerator` class to add custom improvement strategies.

### Memory Settings
Modify `MemoryOptimizer` target for your system constraints.

### Monitoring Thresholds
Adjust alert thresholds in `AlertSystem` class.

## Support

For issues or questions:
1. Check log files: `codex_research.log`
2. Review research reports: `research_reports/`
3. Examine memory usage: `research_monitor.log`

## Citation

If you use this system in your research, please cite:
```
Codex Autonomous Research Loop for AI Self-Improvement
Autonomous Laughter Prediction System
2026
```

---

**Revolutionary AI Research**: The Codex system represents a paradigm shift in AI development, enabling systems to continuously improve themselves through autonomous scientific experimentation.
"""

        with open(guide_path, 'w') as f:
            f.write(guide_content)

        print(f"✅ Quick start guide created: {guide_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Launch Codex Autonomous Research Loop"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run comprehensive tests'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run single test cycle'
    )
    parser.add_argument(
        '--cycles',
        type=int,
        default=100,
        help='Maximum number of research cycles (default: 100)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=5,
        help='Target cycle duration in minutes (default: 5)'
    )
    parser.add_argument(
        '--guide',
        action='store_true',
        help='Create quick start guide'
    )

    args = parser.parse_args()

    # Initialize launcher
    launcher = CodexResearchLauncher(PROJECT_DIR)

    if args.guide:
        launcher.create_quick_start_guide()
        return

    if args.test:
        # Run tests only
        test_results = launcher.run_comprehensive_tests()
        success = all(r.success for r in test_results)
        sys.exit(0 if success else 1)

    # Launch research
    success = launcher.launch_research(
        max_cycles=args.cycles,
        cycle_duration_minutes=args.duration,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()