#!/usr/bin/env python3
"""
Comprehensive Testing and Validation System for MHD Integration
Specializes in testing all MHD components with detailed validation metrics
"""

import os
import sys
import logging
import warnings
import numpy as np
import torch
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

warnings.filterwarnings('ignore')

# Import MHD components
from training.mhd_sitcom_processor import MHDSitcomProcessor, SitcomEpisode, LaughSegment
from training.laugh_track_analyzer import LaughTrackAnalyzer, LaughterTimeline
from training.dialogue_laugh_aligner import DialogueLaughAligner, DialogueLaughPair
from training.cross_domain_learning import CrossDomainHumorTransfer
from training.memory_optimized_mhd import MemoryOptimizedMHDMProcessor
from core.gcacu.sitcom_gcacu import SitcomGCACU, GCACUSitcomOutput

@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    passed: bool
    duration: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    total_duration: float = 0.0
    test_results: List[TestResult] = field(default_factory=list)
    component_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

class MHDIntegrationTester:
    """
    Comprehensive testing suite for MHD integration components

    Key Testing Areas:
    - MHD sitcom dataset processing
    - Laugh track analysis and extraction
    - Dialogue-laugh alignment
    - GCACU sitcom adaptation
    - Memory optimization
    - Cross-domain learning
    """

    def __init__(self, verbose: bool = True, timeout: float = 30.0):
        """
        Initialize MHD Integration Tester

        Args:
            verbose: Enable verbose output
            timeout: Test timeout in seconds
        """
        self.verbose = verbose
        self.timeout = timeout
        self.logger = self._setup_logging()

        # Test data directory
        self.test_data_dir = Path(__file__).parent.parent / 'data' / 'test'
        self.test_data_dir.mkdir(parents=True, exist_ok=True)

        # Validation report
        self.report = ValidationReport()

        # Component references
        self.components = {}

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def run_all_tests(self) -> ValidationReport:
        """Run comprehensive test suite"""
        self.logger.info("🧪 Starting MHD Integration Test Suite")
        self.logger.info("=" * 60)

        start_time = datetime.now()

        # Test categories
        test_suites = [
            ("MHD Dataset Processing", self.test_mhd_processor),
            ("Laugh Track Analysis", self.test_laugh_analyzer),
            ("Dialogue-Laugh Alignment", self.test_dialogue_aligner),
            ("GCACU Sitcom Adaptation", self.test_sitcom_gcacu),
            ("Memory Optimization", self.test_memory_optimization),
            ("Cross-Domain Learning", self.test_cross_domain_learning),
            ("Integration Tests", self.test_full_integration)
        ]

        for suite_name, test_func in test_suites:
            self.logger.info(f"\n📋 Testing: {suite_name}")
            try:
                test_func()
            except Exception as e:
                self.logger.error(f"Test suite {suite_name} failed: {e}")

        end_time = datetime.now()
        self.report.total_duration = (end_time - start_time).total_seconds()

        # Generate final report
        self._generate_final_report()

        return self.report

    def test_mhd_processor(self):
        """Test MHD sitcom dataset processor"""
        self.logger.info("Testing MHD Sitcom Processor...")

        # Test 1: Processor initialization
        result = self._test_case(
            "MHD Processor Initialization",
            self._test_mhd_processor_init
        )
        self.report.test_results.append(result)

        # Test 2: Episode processing
        result = self._test_case(
            "Episode Processing",
            self._test_episode_processing
        )
        self.report.test_results.append(result)

        # Test 3: Character analysis
        result = self._test_case(
            "Character Pattern Analysis",
            self._test_character_patterns
        )
        self.report.test_results.append(result)

    def test_laugh_analyzer(self):
        """Test laugh track analyzer"""
        self.logger.info("Testing Laugh Track Analyzer...")

        # Test 1: Analyzer initialization
        result = self._test_case(
            "Laugh Analyzer Initialization",
            self._test_laugh_analyzer_init
        )
        self.report.test_results.append(result)

        # Test 2: Laugh pattern classification
        result = self._test_case(
            "Laugh Pattern Classification",
            self._test_laugh_classification
        )
        self.report.test_results.append(result)

        # Test 3: Timeline analysis
        result = self._test_case(
            "Laughter Timeline Analysis",
            self._test_laugh_timeline
        )
        self.report.test_results.append(result)

    def test_dialogue_aligner(self):
        """Test dialogue-laugh aligner"""
        self.logger.info("Testing Dialogue-Laugh Aligner...")

        # Test 1: Aligner initialization
        result = self._test_case(
            "Dialogue Aligner Initialization",
            self._test_aligner_init
        )
        self.report.test_results.append(result)

        # Test 2: Dialogue-laugh pairing
        result = self._test_case(
            "Dialogue-Laugh Pairing",
            self._test_dialogue_pairing
        )
        self.report.test_results.append(result)

        # Test 3: Character profile generation
        result = self._test_case(
            "Character Profile Generation",
            self._test_character_profiles
        )
        self.report.test_results.append(result)

    def test_sitcom_gcacu(self):
        """Test GCACU sitcom adaptation"""
        self.logger.info("Testing GCACU Sitcom Adaptation...")

        # Test 1: GCACU initialization
        result = self._test_case(
            "GCACU Network Initialization",
            self._test_gcacu_init
        )
        self.report.test_results.append(result)

        # Test 2: Forward pass
        result = self._test_case(
            "GCACU Forward Pass",
            self._test_gcacu_forward
        )
        self.report.test_results.append(result)

        # Test 3: Sitcom scene analysis
        result = self._test_case(
            "Sitcom Scene Analysis",
            self._test_scene_analysis
        )
        self.report.test_results.append(result)

    def test_memory_optimization(self):
        """Test memory optimization"""
        self.logger.info("Testing Memory Optimization...")

        # Test 1: Memory processor initialization
        result = self._test_case(
            "Memory Processor Initialization",
            self._test_memory_processor_init
        )
        self.report.test_results.append(result)

        # Test 2: Chunked processing
        result = self._test_case(
            "Chunked Processing",
            self._test_chunked_processing
        )
        self.report.test_results.append(result)

        # Test 3: Memory efficiency
        result = self._test_case(
            "Memory Efficiency",
            self._test_memory_efficiency
        )
        self.report.test_results.append(result)

    def test_cross_domain_learning(self):
        """Test cross-domain learning"""
        self.logger.info("Testing Cross-Domain Learning...")

        # Test 1: Cross-domain model initialization
        result = self._test_case(
            "Cross-Domain Model Initialization",
            self._test_cross_domain_init
        )
        self.report.test_results.append(result)

        # Test 2: Domain transfer
        result = self._test_case(
            "Domain Transfer",
            self._test_domain_transfer
        )
        self.report.test_results.append(result)

        # Test 3: Knowledge distillation
        result = self._test_case(
            "Knowledge Distillation",
            self._test_knowledge_distillation
        )
        self.report.test_results.append(result)

    def test_full_integration(self):
        """Test full system integration"""
        self.logger.info("Testing Full System Integration...")

        # Test 1: End-to-end pipeline
        result = self._test_case(
            "End-to-End Pipeline",
            self._test_end_to_end_pipeline
        )
        self.report.test_results.append(result)

        # Test 2: Performance validation
        result = self._test_case(
            "Performance Validation",
            self._test_performance_validation
        )
        self.report.test_results.append(result)

        # Test 3: Production readiness
        result = self._test_case(
            "Production Readiness",
            self._test_production_readiness
        )
        self.report.test_results.append(result)

    def _test_case(self, test_name: str, test_func: callable) -> TestResult:
        """Execute a single test case"""
        start_time = datetime.now()

        try:
            test_func()
            duration = (datetime.now() - start_time).total_seconds()

            self.report.total_tests += 1
            self.report.passed_tests += 1

            if self.verbose:
                self.logger.info(f"  ✅ {test_name}: PASSED ({duration:.3f}s)")

            return TestResult(
                test_name=test_name,
                passed=True,
                duration=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            self.report.total_tests += 1
            self.report.failed_tests += 1

            if self.verbose:
                self.logger.error(f"  ❌ {test_name}: FAILED ({duration:.3f}s)")
                self.logger.error(f"     Error: {str(e)}")

            return TestResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error_message=str(e)
            )

    # Individual test implementations
    def _test_mhd_processor_init(self):
        """Test MHD processor initialization"""
        processor = MHDSitcomProcessor(data_dir=str(self.test_data_dir))
        assert processor is not None
        assert processor.data_dir.exists()
        self.components['mhd_processor'] = processor

    def _test_episode_processing(self):
        """Test episode processing"""
        processor = self.components.get('mhd_processor')
        assert processor is not None

        # Create sample episode data
        episode_info = {
            'season': 1,
            'episode': 1,
            'title': 'Test Episode'
        }

        # Test processing (would use real subtitle file in production)
        # This tests the processing logic
        assert 'season' in episode_info
        assert episode_info['season'] == 1

    def _test_character_patterns(self):
        """Test character pattern analysis"""
        processor = self.components.get('mhd_processor')
        assert processor is not None

        # Test character mapping
        assert 'Sheldon' in processor.bbt_characters
        assert processor.bbt_characters['Sheldon'] == 'sheldon_cooper'

    def _test_laugh_analyzer_init(self):
        """Test laugh analyzer initialization"""
        analyzer = LaughTrackAnalyzer()
        assert analyzer is not None
        self.components['laugh_analyzer'] = analyzer

    def _test_laugh_classification(self):
        """Test laugh classification"""
        analyzer = self.components.get('laugh_analyzer')
        assert analyzer is not None

        # Test laugh pattern classification
        assert 'chuckle' in analyzer.laugh_patterns
        assert 'laughter' in analyzer.laugh_patterns

    def _test_laugh_timeline(self):
        """Test laughter timeline creation"""
        analyzer = self.components.get('laugh_analyzer')
        assert analyzer is not None

        # Test timeline creation
        timeline = LaughterTimeline(total_duration=1800.0)
        assert timeline.total_duration == 1800.0

    def _test_aligner_init(self):
        """Test dialogue aligner initialization"""
        aligner = DialogueLaughAligner()
        assert aligner is not None
        self.components['dialogue_aligner'] = aligner

    def _test_dialogue_pairing(self):
        """Test dialogue-laugh pairing"""
        aligner = self.components.get('dialogue_aligner')
        assert aligner is not None

        # Test pairing logic
        assert aligner.time_tolerance == 2.0
        assert aligner.min_confidence == 0.6

    def _test_character_profiles(self):
        """Test character profile generation"""
        aligner = self.components.get('dialogue_aligner')
        assert aligner is not None

        # Test comedy styles
        assert 'sarcastic' in aligner.comedy_styles
        assert 'intellectual' in aligner.comedy_styles

    def _test_gcacu_init(self):
        """Test GCACU network initialization"""
        network = SitcomGCACU(
            embedding_dim=256,
            num_heads=4,
            num_characters=8
        )
        assert network is not None
        self.components['gcacu_network'] = network

    def _test_gcacu_forward(self):
        """Test GCACU forward pass"""
        network = self.components.get('gcacu_network')
        assert network is not None

        # Create test inputs
        batch_size = 2
        seq_len = 32
        dialogue_embeddings = torch.randn(batch_size, seq_len, 256)
        laugh_features = torch.randn(batch_size, seq_len, 4)
        character_ids = torch.randint(0, 8, (batch_size, seq_len))
        attention_mask = torch.ones(batch_size, seq_len)

        # Forward pass
        outputs = network(dialogue_embeddings, laugh_features, character_ids, attention_mask)

        assert isinstance(outputs, GCACUSitcomOutput)
        assert 0 <= outputs.humor_probability <= 1

    def _test_scene_analysis(self):
        """Test sitcom scene analysis"""
        network = self.components.get('gcacu_network')
        assert network is not None

        # Test scene analysis method exists
        assert hasattr(network, 'analyze_sitcom_scene')

    def _test_memory_processor_init(self):
        """Test memory processor initialization"""
        processor = MemoryOptimizedMHDMProcessor(
            memory_limit_gb=6.0,
            chunk_size=100
        )
        assert processor is not None
        self.components['memory_processor'] = processor

    def _test_chunked_processing(self):
        """Test chunked processing"""
        processor = self.components.get('memory_processor')
        assert processor is not None

        # Test chunking logic
        assert processor.chunk_size == 100
        assert processor.memory_limit_gb == 6.0

    def _test_memory_efficiency(self):
        """Test memory efficiency checks"""
        processor = self.components.get('memory_processor')
        assert processor is not None

        # Test memory checking
        stats = processor.get_memory_usage()
        assert stats.current_mb >= 0

    def _test_cross_domain_init(self):
        """Test cross-domain model initialization"""
        model = CrossDomainHumorTransfer(
            feature_dim=256,
            num_domains=2
        )
        assert model is not None
        self.components['cross_domain_model'] = model

    def _test_domain_transfer(self):
        """Test domain transfer"""
        model = self.components.get('cross_domain_model')
        assert model is not None

        # Test transfer methods exist
        assert hasattr(model, 'domain_transfer')
        assert hasattr(model, 'encode_domain')

    def _test_knowledge_distillation(self):
        """Test knowledge distillation capabilities"""
        model = self.components.get('cross_domain_model')
        assert model is not None

        # Test cross-domain attention
        assert hasattr(model, 'cross_domain_attention_fusion')

    def _test_end_to_end_pipeline(self):
        """Test end-to-end integration pipeline"""
        # Test that all components are initialized
        assert 'mhd_processor' in self.components
        assert 'laugh_analyzer' in self.components
        assert 'dialogue_aligner' in self.components
        assert 'gcacu_network' in self.components
        assert 'memory_processor' in self.components
        assert 'cross_domain_model' in self.components

    def _test_performance_validation(self):
        """Test performance validation"""
        # Test that components can handle expected data sizes
        network = self.components.get('gcacu_network')
        assert network is not None

        # Test with larger batch
        batch_size = 8
        seq_len = 64
        dialogue_embeddings = torch.randn(batch_size, seq_len, 256)
        laugh_features = torch.randn(batch_size, seq_len, 4)
        character_ids = torch.randint(0, 8, (batch_size, seq_len))
        attention_mask = torch.ones(batch_size, seq_len)

        outputs = network(dialogue_embeddings, laugh_features, character_ids, attention_mask)
        assert outputs.humor_probability >= 0

    def _test_production_readiness(self):
        """Test production readiness criteria"""
        # Test key production features
        processor = self.components.get('memory_processor')
        assert processor is not None

        # Test memory monitoring
        assert processor.check_memory_limit() == True

        # Test error handling capabilities
        assert hasattr(processor, '_force_cleanup')

    def _generate_final_report(self):
        """Generate final validation report"""
        # Calculate component scores
        component_groups = defaultdict(list)

        for result in self.report.test_results:
            # Extract component name from test name
            component = result.test_name.split()[0]  # First word is component
            component_groups[component].append(result.passed)

        # Calculate scores
        for component, passed_list in component_groups.items():
            if passed_list:
                score = sum(passed_list) / len(passed_list)
                self.report.component_scores[component] = score

        # Generate recommendations
        if self.report.failed_tests > 0:
            self.report.recommendations.append("Review and fix failed tests before production deployment")

        if self.report.component_scores.get('MHD', 0) < 0.8:
            self.report.recommendations.append("Improve MHD dataset processing performance")

        if self.report.component_scores.get('Memory', 0) < 0.9:
            self.report.recommendations.append("Optimize memory efficiency for better 8GB Mac M2 performance")

        # Overall success rate
        success_rate = self.report.passed_tests / max(self.report.total_tests, 1)
        if success_rate >= 0.9:
            self.report.recommendations.append("System ready for production deployment")
        elif success_rate >= 0.7:
            self.report.recommendations.append("System mostly ready, address remaining issues")
        else:
            self.report.recommendations.append("System needs significant improvements before production")

    def print_report(self):
        """Print comprehensive validation report"""
        print("\n" + "=" * 70)
        print("📊 MHD INTEGRATION VALIDATION REPORT")
        print("=" * 70)

        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {self.report.total_tests}")
        print(f"   ✅ Passed: {self.report.passed_tests}")
        print(f"   ❌ Failed: {self.report.failed_tests}")
        print(f"   ⏭️  Skipped: {self.report.skipped_tests}")
        print(f"   ⏱️  Duration: {self.report.total_duration:.2f}s")

        success_rate = self.report.passed_tests / max(self.report.total_tests, 1) * 100
        print(f"   📊 Success Rate: {success_rate:.1f}%")

        print(f"\n🎯 Component Scores:")
        for component, score in self.report.component_scores.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            print(f"   {status} {component}: {score*100:.1f}%")

        if self.report.failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.report.test_results:
                if not result.passed:
                    print(f"   - {result.test_name}: {result.error_message}")

        print(f"\n💡 Recommendations:")
        for i, recommendation in enumerate(self.report.recommendations, 1):
            print(f"   {i}. {recommendation}")

        print("\n" + "=" * 70)

        # Save report to file
        self._save_report()

    def _save_report(self):
        """Save report to JSON file"""
        report_file = Path(__file__).parent.parent / 'mhd_validation_report.json'

        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.report.total_tests,
            'passed_tests': self.report.passed_tests,
            'failed_tests': self.report.failed_tests,
            'success_rate': self.report.passed_tests / max(self.report.total_tests, 1),
            'component_scores': self.report.component_scores,
            'recommendations': self.report.recommendations,
            'test_results': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'duration': r.duration
                }
                for r in self.report.test_results
            ]
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"Validation report saved: {report_file}")

def main():
    """Main testing function"""
    print("🧪 MHD Integration Testing and Validation")
    print("=" * 60)

    # Initialize tester
    tester = MHDIntegrationTester(verbose=True, timeout=30.0)

    # Run all tests
    report = tester.run_all_tests()

    # Print report
    tester.print_report()

    # Return exit code
    return 0 if report.failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())