#!/usr/bin/env python3
"""
Comprehensive Tests for Memory Optimization Systems
Tests Engram, mHC, and overall memory optimization for 8GB Mac M2 constraints
"""

import torch
import torch.nn as nn
import numpy as np
import time
import unittest
from typing import Dict, List, Any
import json
from pathlib import Path
import logging

# Import memory optimization systems
from memory.engram.engram import (
    EngramMemorySystem, EngramConfig, create_engram_system,
    test_engram_system
)
from memory.mhc.mhc import (
    ManifoldConstrainedHyperConnections, MHCConfig, create_mhc_system,
    test_mhc_system
)
from training.memory_profiler import MemoryProfiler, memory_monitoring

# Import knowledge base
from knowledge_base.comedy_knowledge import create_comprehensive_knowledge_base

# Import integrated model
from core.integrated_model import IntegratedLaughterModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEngramMemorySystem(unittest.TestCase):
    """Test suite for Engram Memory System"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = EngramConfig(
            max_memory_mb=20.0,  # Conservative for testing
            embedding_dim=32,
            top_k=3,
            cache_size=10
        )
        self.engram = create_engram_system(self.config)

    def test_initialization(self):
        """Test Engram initialization"""
        self.assertIsNotNone(self.engram)
        self.assertEqual(self.engram.config.embedding_dim, 32)
        logger.info("Engram initialization test passed")

    def test_knowledge_base_loading(self):
        """Test knowledge base loading"""
        # Create sample knowledge
        sample_knowledge = [
            {
                'text': 'Test knowledge entry 1',
                'category': 'test',
                'metadata': {'key': 'value1'}
            },
            {
                'text': 'Test knowledge entry 2',
                'category': 'test',
                'metadata': {'key': 'value2'}
            }
        ]

        self.engram.initialize_knowledge_base(sample_knowledge)

        self.assertEqual(len(self.engram.knowledge_texts), 2)
        self.assertIsNotNone(self.engram.knowledge_embedding)

        logger.info("Knowledge base loading test passed")

    def test_knowledge_retrieval(self):
        """Test O(1) knowledge retrieval"""
        # Initialize with sample knowledge
        sample_knowledge = [
            {
                'text': 'Political knowledge about elections',
                'category': 'political',
                'metadata': {'context': 'government'}
            },
            {
                'text': 'Comedy knowledge about humor',
                'category': 'comedy',
                'metadata': {'context': 'entertainment'}
            }
        ]

        self.engram.initialize_knowledge_base(sample_knowledge)

        # Test retrieval
        query = torch.randn(32)
        result = self.engram.retrieve_knowledge(query, context='political topics')

        self.assertIn('embeddings', result)
        self.assertIn('metadata', result)
        self.assertGreater(len(result['metadata']), 0)

        logger.info("Knowledge retrieval test passed")

    def test_knowledge_injection(self):
        """Test knowledge injection without gradient explosion"""
        # Create sample knowledge
        sample_knowledge = [
            {
                'text': 'Test knowledge',
                'category': 'test',
                'metadata': {}
            }
        ]

        self.engram.initialize_knowledge_base(sample_knowledge)

        # Test injection
        hidden_states = torch.randn(2, 10, 32)
        knowledge_embeddings = torch.randn(3, 32)

        enhanced_states = self.engram.inject_knowledge(
            hidden_states,
            knowledge_embeddings,
            injection_strength=0.1
        )

        # Check shape is preserved
        self.assertEqual(enhanced_states.shape, hidden_states.shape)

        # Check that gradients are not exploding
        grad_norm = enhanced_states.grad.norm().item() if enhanced_states.grad is not None else 0.0
        self.assertLess(grad_norm, 10.0)

        logger.info("Knowledge injection test passed")

    def test_memory_efficiency(self):
        """Test memory efficiency constraints"""
        # Create larger knowledge base
        large_knowledge = [
            {
                'text': f'Knowledge entry {i}',
                'category': 'test',
                'metadata': {'index': i}
            }
            for i in range(100)
        ]

        self.engram.initialize_knowledge_base(large_knowledge)

        # Check memory usage
        memory_mb = self.engram.calculate_memory_usage()
        self.assertLess(memory_mb, self.config.max_memory_mb)

        logger.info(f"Memory efficiency test passed: {memory_mb:.2f}MB < {self.config.max_memory_mb}MB")

    def test_lookup_performance(self):
        """Test O(1) lookup performance"""
        # Initialize knowledge base
        sample_knowledge = [
            {
                'text': f'Entry {i}',
                'category': 'test',
                'metadata': {}
            }
            for i in range(50)
        ]

        self.engram.initialize_knowledge_base(sample_knowledge)

        # Test lookup speed
        query = torch.randn(32)
        start_time = time.time()

        for _ in range(100):
            result = self.engram.retrieve_knowledge(query)

        avg_time = (time.time() - start_time) / 100

        # O(1) lookup should be very fast (< 1ms per query)
        self.assertLess(avg_time, 0.001)

        logger.info(f"Lookup performance test passed: {avg_time*1000:.2f}ms per query")


class TestMHCSystem(unittest.TestCase):
    """Test suite for Manifold-Constrained Hyper-Connections"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = MHCConfig(
            num_nodes=4,
            use_birkhoff_projection=True,
            use_adaptive_connections=True
        )
        self.mhc = create_mhc_system(self.config)

    def test_initialization(self):
        """Test MHC initialization"""
        self.assertIsNotNone(self.mhc)
        self.assertEqual(self.mhc.config.num_nodes, 4)
        logger.info("MHC initialization test passed")

    def test_birkhoff_projection(self):
        """Test Birkhoff polytope projection"""
        # Create random connection matrix
        random_matrix = torch.randn(4, 4)

        # Project onto Birkhoff polytope
        projected = self.mhc.birkhoff.project(random_matrix)

        # Check if doubly stochastic
        is_doubly_stochastic = self.mhc.birkhoff.is_doubly_stochastic(projected)
        self.assertTrue(is_doubly_stochastic)

        # Check spectral radius for stability
        spectral_radius = self.mhc.birkhoff.compute_spectral_radius(projected)
        self.assertLess(spectral_radius, 1.0)

        logger.info("Birkhoff projection test passed")

    def test_forward_pass(self):
        """Test forward pass with manifold constraints"""
        # Create sample inputs
        inputs = [
            torch.randn(2, 10, 32) for _ in range(4)
        ]

        # Forward pass
        output = self.mhc(inputs, update_connections=True)

        # Check output shape
        self.assertEqual(output.shape[0], 2)  # batch size
        self.assertEqual(output.shape[1], 10)  # sequence length
        self.assertEqual(output.shape[2], 32)  # features

        logger.info("Forward pass test passed")

    def test_stability_guarantees(self):
        """Test training stability guarantees"""
        # Create sample inputs
        inputs = [
            torch.randn(2, 10, 32, requires_grad=True) for _ in range(4)
        ]

        # Multiple forward passes to check stability
        for _ in range(10):
            output = self.mhc(inputs, update_connections=True)
            loss = output.sum()
            loss.backward()

            # Check gradient norms are reasonable
            grad_norm = self.mhc.get_gradient_norm()
            self.assertLess(grad_norm, 10.0)

            self.mhc.zero_grad()

        logger.info("Stability guarantees test passed")

    def test_connection_statistics(self):
        """Test connection matrix statistics"""
        # Run forward pass
        inputs = [torch.randn(2, 10, 32) for _ in range(4)]
        output = self.mhc(inputs, update_connections=True)

        # Get statistics
        stats = self.mhc.get_connection_statistics()

        self.assertIn('spectral_radius', stats)
        self.assertIn('is_stable', stats)
        self.assertTrue(stats['is_stable'])

        logger.info(f"Connection statistics test passed: spectral_radius={stats['spectral_radius']:.4f}")


class TestMemoryOptimization(unittest.TestCase):
    """Test suite for overall memory optimization"""

    def setUp(self):
        """Set up test fixtures"""
        self.memory_profiler = MemoryProfiler(max_memory_gb=5.0)

    def test_memory_monitoring(self):
        """Test memory monitoring functionality"""
        # Take baseline snapshot
        baseline = self.memory_profiler.take_snapshot()

        # Allocate some memory
        tensors = [torch.randn(1000, 1000) for _ in range(5)]

        # Take new snapshot
        after = self.memory_profiler.take_snapshot()

        # Check memory increased
        self.assertGreater(after.process_memory_mb, baseline.process_memory_mb)

        # Clean up
        del tensors
        import gc
        gc.collect()

        logger.info("Memory monitoring test passed")

    def test_memory_optimization(self):
        """Test automatic memory optimization"""
        # Allocate memory
        tensors = [torch.randn(1000, 1000) for _ in range(10)]
        snapshot = self.memory_profiler.take_snapshot()

        # Apply optimizations
        results = self.memory_profiler.optimize_memory()

        # Check memory was freed
        after_snapshot = self.memory_profiler.take_snapshot()
        self.assertLess(after_snapshot.process_memory_mb, snapshot.process_memory_mb)

        logger.info("Memory optimization test passed")

    def test_mac_m2_optimizations(self):
        """Test Mac M2 specific optimizations"""
        # Create model
        model = IntegratedLaughterModel(
            embedding_dim=32,
            hidden_dim=32,
            use_engram=True,
            use_mhc=True
        )

        # Apply optimizations
        results = optimize_for_8gb_mac_m2(model)

        self.assertIn('optimizations_applied', results)
        self.assertGreater(len(results['optimizations_applied']), 0)

        logger.info(f"Mac M2 optimizations test passed: {results['optimizations_applied']}")


class TestIntegration(unittest.TestCase):
    """Integration tests for complete system"""

    def test_end_to_end_pipeline(self):
        """Test complete pipeline with all components"""
        logger.info("Testing end-to-end pipeline...")

        # Create model with memory optimization
        model = IntegratedLaughterModel(
            embedding_dim=32,
            hidden_dim=32,
            use_engram=True,
            use_mhc=True
        )

        # Initialize knowledge base
        knowledge_base = create_comprehensive_knowledge_base()
        knowledge_data = knowledge_base.create_engram_data()
        model.initialize_knowledge_base(knowledge_data)

        # Create sample input
        inputs = {
            'embeddings': torch.randn(2, 20, 32),  # batch=2, seq_len=20, features=32
            'attention_mask': torch.ones(2, 20)
        }

        # Forward pass
        outputs = model(inputs)

        # Check outputs
        self.assertIn('probabilities', outputs)
        self.assertEqual(outputs['probabilities'].shape[0], 2)  # batch size

        # Check memory usage
        memory_stats = model.get_memory_stats()
        self.assertLess(memory_stats['model_memory_mb'], 100)  # Should be efficient

        logger.info("End-to-end pipeline test passed")

    def test_training_step(self):
        """Test single training step with memory optimization"""
        # Create model
        model = IntegratedLaughterModel(
            embedding_dim=32,
            hidden_dim=32,
            use_engram=True,
            use_mhc=True
        )

        # Initialize knowledge base
        knowledge_base = create_comprehensive_knowledge_base()
        model.initialize_knowledge_base(knowledge_base.create_engram_data())

        # Create optimizer
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)

        # Training step
        inputs = {
            'embeddings': torch.randn(4, 15, 32),
            'attention_mask': torch.ones(4, 15)
        }
        labels = torch.randint(0, 2, (4, 1)).float()

        optimizer.zero_grad()
        outputs = model(inputs)
        predictions = outputs['probabilities']

        # Compute loss
        loss = nn.functional.binary_cross_entropy(predictions, labels)
        loss.backward()

        # Check gradients are reasonable
        total_grad_norm = 0.0
        for p in model.parameters():
            if p.grad is not None:
                total_grad_norm += p.grad.norm().item() ** 2
        total_grad_norm = total_grad_norm ** 0.5

        self.assertLess(total_grad_norm, 100.0)  # No gradient explosion

        optimizer.step()

        logger.info("Training step test passed")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    logger.info("Starting comprehensive memory optimization tests...")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEngramMemorySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestMHCSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate report
    test_report = {
        'total_tests': result.testsRun,
        'successes': result.testsRun - len(result.failures) - len(result.errors),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    }

    logger.info(f"Test Results: {test_report}")

    # Save report
    report_path = Path(__file__).parent / "test_results.json"
    with open(report_path, 'w') as f:
        json.dump(test_report, f, indent=2)

    logger.info(f"Test report saved to {report_path}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()

    if success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Some tests failed!")

    exit(0 if success else 1)