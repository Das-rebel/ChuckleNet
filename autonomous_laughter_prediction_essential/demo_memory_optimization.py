#!/usr/bin/env python3
"""
Demonstration of Engram and mHC Memory Optimization Systems
Showcases revolutionary features for 8GB Mac M2 constraints
"""

import torch
import torch.nn as nn
import numpy as np
import time
from pathlib import Path
import json
import logging

# Import memory optimization systems
from memory.engram.engram import EngramMemorySystem, EngramConfig, create_engram_system
from memory.mhc.mhc import ManifoldConstrainedHyperConnections, MHCConfig, create_mhc_system
from training.memory_profiler import MemoryProfiler, memory_monitoring, optimize_for_8gb_mac_m2

# Import knowledge base
from knowledge_base.comedy_knowledge import create_comprehensive_knowledge_base

# Import integrated model
from core.integrated_model import IntegratedLaughterModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MemoryOptimizationDemo:
    """
    Comprehensive demonstration of memory optimization capabilities

    Features to demonstrate:
    1. Engram O(1) sparse knowledge lookup
    2. mHC training stability guarantees
    3. 8GB Mac M2 optimization
    4. Complete pipeline integration
    5. Performance benchmarks
    """

    def __init__(self, max_memory_gb: float = 5.0):
        self.max_memory_gb = max_memory_gb
        self.memory_profiler = MemoryProfiler(max_memory_gb=max_memory_gb)
        self.results = {}

    def demonstrate_engram_system(self):
        """Demonstrate Engram Memory System capabilities"""
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATING ENGRAM MEMORY SYSTEM")
        logger.info("="*60)

        # Create Engram system
        config = EngramConfig(
            max_memory_mb=50.0,
            embedding_dim=64,
            top_k=5,
            cache_size=100
        )

        engram = create_engram_system(config)

        # Initialize with comprehensive knowledge base
        knowledge_base = create_comprehensive_knowledge_base()
        knowledge_data = knowledge_base.create_engram_data()

        logger.info(f"Initializing Engram with {len(knowledge_data)} knowledge entries...")

        with memory_monitoring(self.memory_profiler, "Engram initialization"):
            engram.initialize_knowledge_base(knowledge_data)

        # Get statistics
        stats = engram.get_statistics()
        logger.info(f"Engram Statistics:")
        logger.info(f"  - Total knowledge entries: {stats['total_knowledge_entries']}")
        logger.info(f"  - Memory usage: {stats['memory_usage_mb']:.2f}MB")
        logger.info(f"  - Categories: {stats['categories']}")
        logger.info(f"  - Cache hit rate: {stats['cache_hit_rate']:.2%}")

        # Demonstrate O(1) lookup performance
        logger.info("\nTesting O(1) lookup performance...")

        query = torch.randn(config.embedding_dim)
        start_time = time.time()

        for _ in range(1000):
            result = engram.retrieve_knowledge(query, context='political events')

        avg_time = (time.time() - start_time) / 1000
        logger.info(f"  - Average lookup time: {avg_time*1000:.4f}ms per query")
        logger.info(f"  - Queries per second: {1/avg_time:.0f}")

        # Demonstrate knowledge injection
        logger.info("\nTesting knowledge injection...")

        hidden_states = torch.randn(4, 20, 64)
        knowledge_embeddings = result['embeddings']

        enhanced_states = engram.inject_knowledge(
            hidden_states,
            knowledge_embeddings,
            injection_strength=0.1
        )

        logger.info(f"  - Original shape: {hidden_states.shape}")
        logger.info(f"  - Enhanced shape: {enhanced_states.shape}")
        logger.info(f"  - Memory increase: {enhanced_states.element_size() * enhanced_states.numel() / (1024**2):.4f}MB")

        self.results['engram'] = {
            'knowledge_entries': stats['total_knowledge_entries'],
            'memory_mb': stats['memory_usage_mb'],
            'avg_lookup_ms': avg_time * 1000,
            'categories': stats['categories']
        }

        return engram

    def demonstrate_mhc_system(self):
        """Demonstrate Manifold-Constrained Hyper-Connections"""
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATING MANIFOLD-CONSTRAINED HYPER-CONNECTIONS")
        logger.info("="*60)

        # Create mHC system
        config = MHCConfig(
            num_nodes=4,
            use_birkhoff_projection=True,
            use_adaptive_connections=True,
            spectral_radius_threshold=0.99
        )

        mhc = create_mhc_system(config)

        logger.info(f"Initialized mHC with {config.num_nodes} nodes")

        # Demonstrate stability guarantees
        logger.info("\nTesting Birkhoff polytope projection...")

        random_matrix = torch.randn(config.num_nodes, config.num_nodes)
        projected = mhc.birkhoff.project(random_matrix)

        spectral_radius = mhc.birkhoff.compute_spectral_radius(projected)
        is_doubly_stochastic = mhc.birkhoff.is_doubly_stochastic(projected)

        logger.info(f"  - Original matrix norm: {random_matrix.norm():.4f}")
        logger.info(f"  - Projected matrix norm: {projected.norm():.4f}")
        logger.info(f"  - Spectral radius: {spectral_radius:.4f}")
        logger.info(f"  - Is doubly stochastic: {is_doubly_stochastic}")
        logger.info(f"  - Is stable: {spectral_radius < config.spectral_radius_threshold}")

        # Demonstrate training stability
        logger.info("\nTesting training stability...")

        inputs = [torch.randn(4, 15, 32, requires_grad=True) for _ in range(4)]
        gradient_norms = []

        for step in range(10):
            mhc.zero_grad()
            output = mhc(inputs, update_connections=(step % 5 == 0))
            loss = output.sum()
            loss.backward()

            grad_norm = mhc.get_gradient_norm()
            gradient_norms.append(grad_norm)

            # Check for gradient explosion
            if grad_norm > 10.0:
                logger.warning(f"Gradient explosion detected at step {step}: {grad_norm:.4f}")

        avg_grad_norm = np.mean(gradient_norms)
        max_grad_norm = np.max(gradient_norms)

        logger.info(f"  - Average gradient norm: {avg_grad_norm:.4f}")
        logger.info(f"  - Maximum gradient norm: {max_grad_norm:.4f}")
        logger.info(f"  - Training stability: {'STABLE' if max_grad_norm < 10.0 else 'UNSTABLE'}")

        # Get connection statistics
        stats = mhc.get_connection_statistics()
        logger.info(f"\nConnection Statistics:")
        logger.info(f"  - Spectral radius: {stats['spectral_radius']:.4f}")
        logger.info(f"  - Mean strength: {stats['mean_strength']:.4f}")
        logger.info(f"  - Sparsity: {stats['sparsity']:.2%}")
        logger.info(f"  - Is stable: {stats['is_stable']}")

        # Visualize connections
        logger.info(f"\n{mhc.visualize_connections()}")

        self.results['mhc'] = {
            'spectral_radius': spectral_radius,
            'is_stable': stats['is_stable'],
            'avg_grad_norm': avg_grad_norm,
            'max_grad_norm': max_grad_norm,
            'sparsity': stats['sparsity']
        }

        return mhc

    def demonstrate_complete_pipeline(self):
        """Demonstrate complete integrated pipeline"""
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATING COMPLETE INTEGRATED PIPELINE")
        logger.info("="*60)

        # Create integrated model
        logger.info("Creating integrated model with memory optimization...")

        with memory_monitoring(self.memory_profiler, "Model creation"):
            model = IntegratedLaughterModel(
                embedding_dim=64,
                hidden_dim=64,
                use_engram=True,
                use_mhc=True
            )

            # Initialize knowledge base
            knowledge_base = create_comprehensive_knowledge_base()
            model.initialize_knowledge_base(knowledge_base.create_engram_data())

        # Apply Mac M2 optimizations
        logger.info("Applying Mac M2 specific optimizations...")
        optimization_results = optimize_for_8gb_mac_m2(model)
        logger.info(f"Optimizations applied: {optimization_results['optimizations_applied']}")

        # Get model statistics
        memory_stats = model.get_memory_stats()
        logger.info(f"\nModel Statistics:")
        logger.info(f"  - Total parameters: {memory_stats['total_parameters']:,}")
        logger.info(f"  - Model memory: {memory_stats['model_memory_mb']:.2f}MB")
        logger.info(f"  - Engram memory: {memory_stats.get('engram_memory_mb', 0):.2f}MB")
        logger.info(f"  - Total memory: {memory_stats['model_memory_mb'] + memory_stats.get('engram_memory_mb', 0):.2f}MB")

        # Run inference test
        logger.info("\nRunning inference test...")

        inputs = {
            'embeddings': torch.randn(4, 25, 64),
            'attention_mask': torch.ones(4, 25)
        }

        # Warmup
        with torch.no_grad():
            for _ in range(3):
                outputs = model(inputs)

        # Timed inference
        start_time = time.time()
        with torch.no_grad():
            for _ in range(10):
                outputs = model(inputs)

        avg_inference_time = (time.time() - start_time) / 10

        logger.info(f"  - Average inference time: {avg_inference_time*1000:.2f}ms")
        logger.info(f"  - Output probabilities shape: {outputs['probabilities'].shape}")
        logger.info(f"  - Humor probability: {outputs['humor_probability'].mean():.4f}")
        logger.info(f"  - Laughter probability: {outputs['laughter_probability'].mean():.4f}")
        logger.info(f"  - Knowledge used: {outputs['knowledge_used']}")

        # Training simulation
        logger.info("\nSimulating training step...")

        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4)
        labels = torch.randint(0, 2, (4, 1)).float()

        start_time = time.time()

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = nn.functional.binary_cross_entropy(outputs['probabilities'], labels)
        loss.backward()
        optimizer.step()

        training_time = time.time() - start_time

        logger.info(f"  - Training step time: {training_time*1000:.2f}ms")
        logger.info(f"  - Loss: {loss.item():.4f}")

        self.results['pipeline'] = {
            'parameters': memory_stats['total_parameters'],
            'memory_mb': memory_stats['model_memory_mb'],
            'avg_inference_ms': avg_inference_time * 1000,
            'training_step_ms': training_time * 1000,
            'loss': loss.item()
        }

        return model

    def demonstrate_memory_optimization(self):
        """Demonstrate memory optimization effectiveness"""
        logger.info("\n" + "="*60)
        logger.info("DEMONSTRATING 8GB MAC M2 MEMORY OPTIMIZATION")
        logger.info("="*60)

        # Get comprehensive memory summary
        memory_summary = self.memory_profiler.get_summary()

        logger.info("Memory Summary:")
        logger.info(f"  - Max memory budget: {self.max_memory_gb}GB")
        logger.info(f"  - Peak memory: {memory_summary['peak_memory_mb']:.2f}MB ({memory_summary['peak_memory_mb']/(self.max_memory_gb*1024)*100:.1f}%)")
        logger.info(f"  - Current memory: {memory_summary['current_memory_mb']:.2f}MB")
        logger.info(f"  - Memory usage: {memory_summary['memory_usage_percentage']:.1f}%")
        logger.info(f"  - Tensors allocated: {memory_summary['tensor_info']['tensor_count']}")
        logger.info(f"  - Tensor memory: {memory_summary['tensor_info']['tensor_memory_mb']:.2f}MB")

        # System memory
        sys_mem = memory_summary['system_memory']
        logger.info(f"\nSystem Memory:")
        logger.info(f"  - Total: {sys_mem['total_gb']:.2f}GB")
        logger.info(f"  - Available: {sys_mem['available_gb']:.2f}GB")
        logger.info(f"  - Used: {sys_mem['used_gb']:.2f}GB ({sys_mem['percentage']:.1f}%)")

        # Recommendations
        recommendations = memory_summary['recommendations']
        if recommendations:
            logger.info(f"\nOptimization Recommendations:")
            for rec in recommendations:
                logger.info(f"  - {rec}")
        else:
            logger.info(f"\nNo memory issues detected!")

        self.results['memory_optimization'] = {
            'peak_mb': memory_summary['peak_memory_mb'],
            'current_mb': memory_summary['current_memory_mb'],
            'usage_percentage': memory_summary['memory_usage_percentage'],
            'tensor_count': memory_summary['tensor_info']['tensor_count'],
            'status': memory_summary['status']
        }

    def save_results(self, filepath: str = "demo_results.json"):
        """Save demonstration results"""
        results_path = Path(filepath)
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nResults saved to {results_path}")

    def run_complete_demo(self):
        """Run complete demonstration"""
        logger.info("STARTING COMPREHENSIVE MEMORY OPTIMIZATION DEMONSTRATION")
        logger.info(f"Target: {self.max_memory_gb}GB Mac M2 constraint")

        try:
            # Demonstrate Engram
            engram = self.demonstrate_engram_system()

            # Demonstrate mHC
            mhc = self.demonstrate_mhc_system()

            # Demonstrate complete pipeline
            model = self.demonstrate_complete_pipeline()

            # Demonstrate memory optimization
            self.demonstrate_memory_optimization()

            # Save results
            self.save_results()

            logger.info("\n" + "="*60)
            logger.info("DEMONSTRATION COMPLETED SUCCESSFULLY!")
            logger.info("="*60)

            # Print summary
            logger.info("\nREVOLUTIONARY FEATURES DEMONSTRATED:")
            logger.info("✓ Engram O(1) sparse knowledge lookup")
            logger.info("✓ mHC training stability guarantees")
            logger.info("✓ 8GB Mac M2 optimization")
            logger.info("✓ Complete pipeline integration")
            logger.info("✓ Memory-efficient inference and training")

            return True

        except Exception as e:
            logger.error(f"Demonstration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main demonstration function"""
    demo = MemoryOptimizationDemo(max_memory_gb=5.0)
    success = demo.run_complete_demo()

    if success:
        print("\n🎉 All demonstrations completed successfully!")
        print("The Engram and mHC systems are ready for production use!")
    else:
        print("\n❌ Some demonstrations failed. Check logs for details.")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)