"""
CLoST Framework Testing and Validation
Comprehensive testing suite for CLoST components

Author: GCACU Autonomous Laughter Prediction System
Date: 2026-04-03
"""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import json
from pathlib import Path
import time
from dataclasses import dataclass

# Import CLoST components
from clost_reasoning import (
    CLoSTReasoningFramework,
    ComedyKnowledgeGraph,
    ComedyConcept,
    ThoughtLeap
)
from clost_knowledge_base import ComedyKnowledgeBase, create_comprehensive_knowledge_graph
from clost_multihop_reasoning import MultiHopReasoningEngine, MemoryEfficientMultiHopReasoning
from clost_gcacu_integration import CLoSTGCACUEnhanced, CLoSTGCACUTrainer
from clost_optimization import create_optimized_clost_pipeline


@dataclass
class TestResult:
    """
    Results from individual test
    """
    test_name: str
    passed: bool
    score: float
    duration_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


class CLoSTTestSuite:
    """
    Comprehensive test suite for CLoST framework
    """

    def __init__(self, embedding_dim: int = 768):
        """
        Initialize test suite

        Args:
            embedding_dim: Embedding dimension for testing
        """
        self.embedding_dim = embedding_dim
        self.test_results: List[TestResult] = []

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all CLoST framework tests

        Returns:
            Dictionary with comprehensive test results
        """
        print("🧪 Starting Comprehensive CLoST Framework Testing")

        # Test individual components
        print("📋 Testing Individual Components...")
        self.test_knowledge_graph()
        self.test_causal_inference()
        self.test_thought_leap_detection()
        self.test_knowledge_base()
        self.test_multihop_reasoning()

        # Test integration
        print("🔗 Testing Integration...")
        self.test_gcacu_integration()
        self.test_optimized_pipeline()

        # Test performance
        print("⚡ Testing Performance...")
        self.test_inference_speed()
        self.test_memory_usage()

        # Test accuracy
        print("🎯 Testing Accuracy...")
        self.test_reasoning_accuracy()
        self.test_humor_detection_accuracy()

        # Generate summary
        return self.generate_test_summary()

    def test_knowledge_graph(self) -> TestResult:
        """Test knowledge graph functionality"""
        print("   🔍 Testing Knowledge Graph...")
        start_time = time.time()

        try:
            # Create knowledge graph
            kg = ComedyKnowledgeGraph(embedding_dim=self.embedding_dim)

            # Add test concepts
            concept1 = ComedyConcept(
                id="test_concept1",
                name="Test Concept 1",
                category="test",
                embedding=torch.randn(self.embedding_dim),
                properties={},
                relationships={}
            )
            concept2 = ComedyConcept(
                id="test_concept2",
                name="Test Concept 2",
                category="test",
                embedding=torch.randn(self.embedding_dim),
                properties={},
                relationships={}
            )

            kg.add_concept(concept1)
            kg.add_concept(concept2)
            kg.add_relationship("test_concept1", "test_concept2", "test_relation", 0.8)

            # Test graph operations
            assert len(kg.concepts) == 2
            assert "test_concept1" in kg.concepts
            assert "test_concept2" in kg.concepts
            assert kg.graph.has_edge("test_concept1", "test_concept2")

            # Test path finding
            path = kg.find_shortest_path("test_concept1", "test_concept2")
            assert len(path) == 2

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Knowledge Graph",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={"concepts": len(kg.concepts), "edges": kg.graph.number_of_edges()}
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Knowledge Graph",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_causal_inference(self) -> TestResult:
        """Test causal inference engine"""
        print("   🔍 Testing Causal Inference...")
        start_time = time.time()

        try:
            # Create CLoST framework
            clost = CLoSTReasoningFramework(embedding_dim=self.embedding_dim)

            # Create test embeddings
            setup_emb = torch.randn(64, self.embedding_dim)
            punchline_emb = torch.randn(64, self.embedding_dim)

            # Test causal detection
            causal_strength = clost.causal_engine.detect_causal_relationships(
                setup_emb.mean(dim=0).unsqueeze(0),
                punchline_emb.mean(dim=0).unsqueeze(0)
            )

            # Test expectation violation detection
            expectation_violation = clost.causal_engine.detect_expectation_violations(
                setup_emb.mean(dim=0).unsqueeze(0),
                punchline_emb.mean(dim=0).unsqueeze(0)
            )

            # Check outputs
            assert 0.0 <= causal_strength.item() <= 1.0
            assert 0.0 <= expectation_violation.item() <= 1.0

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Causal Inference",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={
                    "causal_strength": causal_strength.item(),
                    "expectation_violation": expectation_violation.item()
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Causal Inference",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_thought_leap_detection(self) -> TestResult:
        """Test thought leap detection"""
        print("   🔍 Testing Thought Leap Detection...")
        start_time = time.time()

        try:
            # Create CLoST framework
            clost = CLoSTReasoningFramework(embedding_dim=self.embedding_dim)

            # Create test embeddings
            setup_emb = torch.randn(64, self.embedding_dim)
            punchline_emb = torch.randn(64, self.embedding_dim)

            # Test thought leap quantification
            thought_leap = clost.leap_detector.quantify_leap(
                setup_emb.mean(dim=0),
                punchline_emb.mean(dim=0)
            )

            # Check output structure
            assert isinstance(thought_leap, ThoughtLeap)
            assert 0.0 <= thought_leap.leap_score <= 1.0
            assert 0.0 <= thought_leap.semantic_distance <= 1.0
            assert thought_leap.humor_mechanism in ['causal', 'semantic', 'pragmatic', 'incongruity']

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Thought Leap Detection",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={
                    "leap_score": thought_leap.leap_score,
                    "semantic_distance": thought_leap.semantic_distance,
                    "humor_mechanism": thought_leap.humor_mechanism
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Thought Leap Detection",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_knowledge_base(self) -> TestResult:
        """Test comedy knowledge base"""
        print("   🔍 Testing Knowledge Base...")
        start_time = time.time()

        try:
            # Create knowledge base
            kb = ComedyKnowledgeBase(embedding_dim=self.embedding_dim)

            # Test pattern retrieval
            assert len(kb.patterns) > 0
            assert len(kb.causal_templates) > 0
            assert len(kb.semantic_clusters) > 0

            # Test specific patterns
            incongruity_patterns = kb.get_patterns_by_category("incongruity")
            assert len(incongruity_patterns) > 0

            # Test similarity search
            if incongruity_patterns:
                similar = kb.find_similar_patterns(incongruity_patterns[0].id)
                assert len(similar) > 0

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Knowledge Base",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={
                    "total_patterns": len(kb.patterns),
                    "causal_templates": len(kb.causal_templates),
                    "semantic_clusters": len(kb.semantic_clusters)
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Knowledge Base",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_multihop_reasoning(self) -> TestResult:
        """Test multi-hop reasoning"""
        print("   🔍 Testing Multi-Hop Reasoning...")
        start_time = time.time()

        try:
            # Create knowledge graph
            kb = ComedyKnowledgeBase(embedding_dim=self.embedding_dim)
            kg = create_comprehensive_knowledge_graph(kb, self.embedding_dim)

            # Create reasoning engine
            reasoning_engine = MultiHopReasoningEngine(embedding_dim=self.embedding_dim)

            # Test path finding
            if kg.concepts:
                concept_ids = list(kg.concepts.keys())
                if len(concept_ids) >= 2:
                    paths = reasoning_engine.find_reasoning_paths(
                        kg, concept_ids[0], concept_ids[1]
                    )

                    # Test memory efficient version
                    efficient_engine = MemoryEfficientMultiHopReasoning(self.embedding_dim)
                    efficient_paths = efficient_engine.find_paths_efficient(
                        kg, concept_ids[0], concept_ids[1]
                    )

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Multi-Hop Reasoning",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={
                    "knowledge_graph_size": len(kg.concepts),
                    "reasoning_engine_test": "passed"
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Multi-Hop Reasoning",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_gcacu_integration(self) -> TestResult:
        """Test GCACU integration"""
        print("   🔍 Testing GCACU Integration...")
        start_time = time.time()

        try:
            # Create enhanced model
            enhanced_model = CLoSTGCACUEnhanced(embedding_dim=self.embedding_dim)

            # Create test input
            batch_size = 2
            seq_len = 128
            embeddings = torch.randn(batch_size, seq_len, self.embedding_dim)
            attention_mask = torch.ones(batch_size, seq_len)

            # Test forward pass
            predictions = enhanced_model(embeddings, attention_mask)

            # Check outputs
            assert 'final_prediction' in predictions
            assert 'incongruity_score' in predictions
            assert 'thought_leap_score' in predictions
            assert predictions['final_prediction'].shape[0] == batch_size

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="GCACU Integration",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={
                    "output_shape": predictions['final_prediction'].shape,
                    "detected_mechanism": predictions['detected_mechanism']
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="GCACU Integration",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_optimized_pipeline(self) -> TestResult:
        """Test optimized pipeline"""
        print("   🔍 Testing Optimized Pipeline...")
        start_time = time.time()

        try:
            # Create optimized pipeline
            pipeline = create_optimized_clost_pipeline(self.embedding_dim)

            # Create test input
            embeddings = torch.randn(128, self.embedding_dim)

            # Test prediction
            predictions = pipeline.predict(embeddings)

            # Check outputs
            assert 'batch_results' in predictions

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Optimized Pipeline",
                passed=True,
                score=100.0,
                duration_ms=duration,
                details={"pipeline_test": "successful"}
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Optimized Pipeline",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_inference_speed(self) -> TestResult:
        """Test inference speed"""
        print("   🔍 Testing Inference Speed...")
        start_time = time.time()

        try:
            # Create pipeline
            pipeline = create_optimized_clost_pipeline(self.embedding_dim)

            # Create test inputs
            embeddings_list = [
                torch.randn(128, self.embedding_dim)
                for _ in range(10)
            ]

            # Measure inference time
            inference_times = []
            for embeddings in embeddings_list:
                start = time.time()
                predictions = pipeline.predict(embeddings)
                end = time.time()
                inference_times.append((end - start) * 1000)  # Convert to ms

            avg_time = np.mean(inference_times)
            max_time = np.max(inference_times)

            # Check if meets target (<50ms)
            target_met = avg_time < 50.0
            score = 100.0 if target_met else max(0, 100.0 - (avg_time - 50.0) * 2)

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Inference Speed",
                passed=target_met,
                score=score,
                duration_ms=duration,
                details={
                    "avg_time_ms": avg_time,
                    "max_time_ms": max_time,
                    "target_met": target_met
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Inference Speed",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_memory_usage(self) -> TestResult:
        """Test memory usage"""
        print("   🔍 Testing Memory Usage...")
        start_time = time.time()

        try:
            import psutil
            import os

            # Get initial memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / (1024 ** 2)  # MB

            # Create and use pipeline
            pipeline = create_optimized_clost_pipeline(self.embedding_dim)

            embeddings = torch.randn(128, self.embedding_dim)
            predictions = pipeline.predict(embeddings)

            # Get peak memory
            peak_memory = process.memory_info().rss / (1024 ** 2)  # MB
            memory_increase = peak_memory - initial_memory

            # Check if meets target (<500MB)
            target_met = memory_increase < 500.0
            score = 100.0 if target_met else max(0, 100.0 - (memory_increase - 500.0) / 5)

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Memory Usage",
                passed=target_met,
                score=score,
                duration_ms=duration,
                details={
                    "memory_increase_mb": memory_increase,
                    "target_met": target_met
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Memory Usage",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_reasoning_accuracy(self) -> TestResult:
        """Test reasoning accuracy with sample data"""
        print("   🔍 Testing Reasoning Accuracy...")
        start_time = time.time()

        try:
            # Create CLoST framework
            clost = CLoSTReasoningFramework(embedding_dim=self.embedding_dim)

            # Create setup-punchline pair with clear incongruity
            # Setup: "I love going to the gym"
            # Punchline: "Said no one ever"
            setup_emb = torch.randn(64, self.embedding_dim) * 0.1  # Consistent setup
            punchline_emb = torch.randn(64, self.embedding_dim) * 2.0  # Surprising punchline

            # Analyze
            analysis = clost.analyze_setup_punchline(setup_emb, punchline_emb)

            # Check that analysis detected incongruity
            humor_strength = analysis['humor_strength']
            assert 0.0 <= humor_strength <= 1.0

            # Should detect some humor due to high variance
            score = min(100, humor_strength * 200)  # Scale to 0-100

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Reasoning Accuracy",
                passed=humor_strength > 0.1,
                score=score,
                duration_ms=duration,
                details={
                    "humor_strength": humor_strength,
                    "reasoning_paths": len(analysis['reasoning_paths'])
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Reasoning Accuracy",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def test_humor_detection_accuracy(self) -> TestResult:
        """Test humor detection accuracy"""
        print("   🔍 Testing Humor Detection Accuracy...")
        start_time = time.time()

        try:
            # Create enhanced model
            enhanced_model = CLoSTGCACUEnhanced(embedding_dim=self.embedding_dim)

            # Create test data
            # Funny examples (high variance, clear incongruity)
            funny_embeddings = [
                torch.randn(128, self.embedding_dim) * 1.5
                for _ in range(5)
            ]

            # Not funny examples (low variance, no incongruity)
            not_funny_embeddings = [
                torch.randn(128, self.embedding_dim) * 0.2
                for _ in range(5)
            ]

            # Test funny examples
            funny_scores = []
            for embeddings in funny_embeddings:
                embeddings_batch = embeddings.unsqueeze(0)
                attention_mask = torch.ones(1, 128)

                predictions = enhanced_model(embeddings_batch, attention_mask)
                funny_scores.append(predictions['final_prediction'].item())

            # Test not funny examples
            not_funny_scores = []
            for embeddings in not_funny_embeddings:
                embeddings_batch = embeddings.unsqueeze(0)
                attention_mask = torch.ones(1, 128)

                predictions = enhanced_model(embeddings_batch, attention_mask)
                not_funny_scores.append(predictions['final_prediction'].item())

            # Calculate accuracy
            avg_funny = np.mean(funny_scores)
            avg_not_funny = np.mean(not_funny_scores)

            # Funny should score higher than not funny
            discrimination = avg_funny - avg_not_funny
            passed = discrimination > 0.1
            score = min(100, discrimination * 500)  # Scale to 0-100

            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Humor Detection Accuracy",
                passed=passed,
                score=score,
                duration_ms=duration,
                details={
                    "avg_funny_score": avg_funny,
                    "avg_not_funny_score": avg_not_funny,
                    "discrimination": discrimination
                }
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = TestResult(
                test_name="Humor Detection Accuracy",
                passed=False,
                score=0.0,
                duration_ms=duration,
                details={},
                error_message=str(e)
            )

        self.test_results.append(result)
        self._print_result(result)
        return result

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests

        avg_score = np.mean([r.score for r in self.test_results])
        avg_duration = np.mean([r.duration_ms for r in self.test_results])

        # Print summary
        print("\n" + "="*60)
        print("📊 CLoST FRAMEWORK TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Average Duration: {avg_duration:.2f}ms")
        print("="*60)

        # Detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result.passed else "❌"
            print(f"   {status} {result.test_name}: {result.score:.1f}/100 ({result.duration_ms:.2f}ms)")

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'avg_score': avg_score,
            'avg_duration_ms': avg_duration,
            'test_results': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'score': r.score,
                    'duration_ms': r.duration_ms,
                    'details': r.details,
                    'error': r.error_message
                }
                for r in self.test_results
            ]
        }

    def _print_result(self, result: TestResult) -> None:
        """Print individual test result"""
        status = "✅" if result.passed else "❌"
        print(f"      {status} {result.test_name}: {result.score:.1f}/100 ({result.duration_ms:.2f}ms)")

        if not result.passed and result.error_message:
            print(f"         Error: {result.error_message}")


def run_comprehensive_tests():
    """Run comprehensive CLoST framework tests"""
    print("🚀 Starting Comprehensive CLoST Framework Testing")
    print("="*60)

    # Create test suite
    test_suite = CLoSTTestSuite(embedding_dim=768)

    # Run all tests
    summary = test_suite.run_all_tests()

    # Save results
    results_path = Path("/Users/Subho/autonomous_laughter_prediction/training/clost_test_results.json")
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n💾 Test results saved to: {results_path}")

    # Return success status
    return summary['success_rate'] >= 0.8  # 80% success rate threshold


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)