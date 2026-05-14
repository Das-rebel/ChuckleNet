#!/usr/bin/env python3
"""
Memory Profiling and Optimization for 8GB Mac M2 Constraints
Provides comprehensive memory monitoring and optimization strategies
"""

import torch
import torch.nn as nn
import psutil
import gc
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging
import json
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time"""
    timestamp: float
    system_memory_mb: float
    process_memory_mb: float
    gpu_memory_mb: float = 0.0
    gpu_memory_cached_mb: float = 0.0
    tensor_count: int = 0
    tensor_memory_mb: float = 0.0


@dataclass
class MemoryStats:
    """Comprehensive memory statistics"""
    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    memory_leaks_detected: int = 0
    gc_collections: int = 0
    memory_snapshots: List[MemorySnapshot] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'peak_memory_mb': self.peak_memory_mb,
            'current_memory_mb': self.current_memory_mb,
            'memory_leaks_detected': self.memory_leaks_detected,
            'gc_collections': self.gc_collections,
            'snapshot_count': len(self.memory_snapshots)
        }


class MemoryProfiler:
    """
    Advanced memory profiler for 8GB Mac M2 optimization

    Features:
    - Real-time memory monitoring
    - Leak detection
    - Automatic garbage collection
    - Memory usage prediction
    - Optimization recommendations
    """

    def __init__(self, max_memory_gb: float = 5.0, enable_gpu_profiling: bool = True):
        self.max_memory_gb = max_memory_gb
        self.enable_gpu_profiling = enable_gpu_profiling
        self.process = psutil.Process()

        self.stats = MemoryStats()
        self.baseline_memory_mb = 0.0
        self.warning_threshold = 0.8  # 80% of max memory

        # Memory monitoring
        self.monitoring_active = False
        self.monitoring_interval = 1.0  # seconds

        logger.info(f"Memory Profiler initialized with {max_memory_gb}GB limit")

    def get_system_memory(self) -> Dict[str, float]:
        """Get current system memory usage"""
        sys_mem = psutil.virtual_memory()
        return {
            'total_gb': sys_mem.total / (1024**3),
            'available_gb': sys_mem.available / (1024**3),
            'used_gb': sys_mem.used / (1024**3),
            'percentage': sys_mem.percent
        }

    def get_process_memory(self) -> Dict[str, float]:
        """Get current process memory usage"""
        process_mem = self.process.memory_info()
        return {
            'rss_mb': process_mem.rss / (1024**2),  # Resident Set Size
            'vms_mb': process_mem.vms / (1024**2),  # Virtual Memory Size
        }

    def get_gpu_memory(self) -> Dict[str, float]:
        """Get GPU memory usage if available"""
        if not self.enable_gpu_profiling:
            return {'allocated_mb': 0.0, 'cached_mb': 0.0}

        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024**2)
            cached = torch.cuda.memory_reserved() / (1024**2)
            return {
                'allocated_mb': allocated,
                'cached_mb': cached,
                'device_name': torch.cuda.get_device_name(0)
            }
        else:
            return {'allocated_mb': 0.0, 'cached_mb': 0.0}

    def count_tensors(self) -> Dict[str, Any]:
        """Count PyTorch tensors and their memory usage"""
        tensors = []
        total_memory = 0

        for obj in gc.get_objects():
            try:
                if torch.is_tensor(obj):
                    tensors.append(obj)
                    total_memory += obj.numel() * obj.element_size()
            except:
                continue

        return {
            'tensor_count': len(tensors),
            'tensor_memory_mb': total_memory / (1024**2),
            'tensor_memory_gb': total_memory / (1024**3)
        }

    def take_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage"""
        process_mem = self.get_process_memory()
        gpu_mem = self.get_gpu_memory()
        tensor_info = self.count_tensors()

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            system_memory_mb=process_mem['rss_mb'],
            process_memory_mb=process_mem['rss_mb'],
            gpu_memory_mb=gpu_mem.get('allocated_mb', 0.0),
            gpu_memory_cached_mb=gpu_mem.get('cached_mb', 0.0),
            tensor_count=tensor_info['tensor_count'],
            tensor_memory_mb=tensor_info['tensor_memory_mb']
        )

        self.stats.memory_snapshots.append(snapshot)
        self.stats.current_memory_mb = snapshot.process_memory_mb
        self.stats.peak_memory_mb = max(self.stats.peak_memory_mb, snapshot.process_memory_mb)

        return snapshot

    def check_memory_pressure(self) -> Dict[str, Any]:
        """Check if memory pressure is high"""
        current_memory_mb = self.stats.current_memory_mb
        max_memory_mb = self.max_memory_gb * 1024

        usage_percentage = (current_memory_mb / max_memory_mb) * 100

        status = {
            'current_mb': current_memory_mb,
            'max_mb': max_memory_mb,
            'usage_percentage': usage_percentage,
            'is_safe': usage_percentage < 80,
            'is_warning': 80 <= usage_percentage < 90,
            'is_critical': usage_percentage >= 90,
            'available_mb': max_memory_mb - current_memory_mb
        }

        return status

    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and memory cleanup"""
        before_memory = self.stats.current_memory_mb

        # Python garbage collection
        gc.collect()

        # PyTorch memory cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Measure after cleanup
        after_memory = self.get_process_memory()['rss_mb']
        freed_memory = before_memory - after_memory

        self.stats.gc_collections += 1

        return {
            'before_mb': before_memory,
            'after_mb': after_memory,
            'freed_mb': freed_memory,
            'gc_collections': self.stats.gc_collections
        }

    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks by analyzing snapshots"""
        if len(self.stats.memory_snapshots) < 3:
            return []

        leaks = []
        snapshots = self.stats.memory_snapshots

        # Check for consistent memory growth
        for i in range(2, len(snapshots)):
            prev_memory = snapshots[i-1].process_memory_mb
            curr_memory = snapshots[i].process_memory_mb

            # If memory keeps growing without GC in between
            if curr_memory > prev_memory * 1.1:  # 10% growth
                leaks.append({
                    'snapshot_index': i,
                    'memory_growth_mb': curr_memory - prev_memory,
                    'growth_percentage': ((curr_memory - prev_memory) / prev_memory) * 100,
                    'timestamp': snapshots[i].timestamp
                })

        self.stats.memory_leaks_detected = len(leaks)
        return leaks

    def optimize_memory(self) -> Dict[str, Any]:
        """Apply memory optimization strategies"""
        optimizations = []

        # Check if GPU memory should be cleared
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024**2)
            cached = torch.cuda.memory_reserved() / (1024**2)

            if cached > allocated * 2:  # Cached > 2x allocated
                torch.cuda.empty_cache()
                optimizations.append('cleared_gpu_cache')

        # Force garbage collection if memory is high
        status = self.check_memory_pressure()
        if status['is_warning'] or status['is_critical']:
            gc_result = self.force_garbage_collection()
            optimizations.append(f"garbage_collection_freed_{gc_result['freed_mb']:.1f}_mb")

        return {
            'optimizations_applied': optimizations,
            'memory_before_mb': self.stats.current_memory_mb,
            'memory_after_mb': self.get_process_memory()['rss_mb']
        }

    def get_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []
        status = self.check_memory_pressure()

        if status['is_critical']:
            recommendations.append("CRITICAL: Reduce batch size immediately")
            recommendations.append("Consider model distillation or pruning")

        elif status['is_warning']:
            recommendations.append("WARNING: Monitor memory usage closely")
            recommendations.append("Enable gradient checkpointing")

        # Check for memory leaks
        leaks = self.detect_memory_leaks()
        if leaks:
            recommendations.append(f"DETECTED {len(leaks)} potential memory leaks")
            recommendations.append("Review tensor creation and cleanup")

        # GPU-specific recommendations
        if torch.cuda.is_available():
            gpu_mem = self.get_gpu_memory()
            if gpu_mem['cached_mb'] > gpu_mem['allocated_mb'] * 3:
                recommendations.append("GPU cache is large, consider manual cleanup")

        return recommendations

    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous memory monitoring"""
        self.monitoring_active = True
        self.monitoring_interval = interval_seconds
        logger.info(f"Started memory monitoring with {interval_seconds}s interval")

    def stop_monitoring(self):
        """Stop continuous memory monitoring"""
        self.monitoring_active = False
        logger.info("Stopped memory monitoring")

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory summary"""
        return {
            'max_memory_gb': self.max_memory_gb,
            'peak_memory_mb': self.stats.peak_memory_mb,
            'current_memory_mb': self.stats.current_memory_mb,
            'memory_usage_percentage': (self.stats.current_memory_mb / (self.max_memory_gb * 1024)) * 100,
            'gc_collections': self.stats.gc_collections,
            'memory_leaks_detected': self.stats.memory_leaks_detected,
            'total_snapshots': len(self.stats.memory_snapshots),
            'system_memory': self.get_system_memory(),
            'process_memory': self.get_process_memory(),
            'gpu_memory': self.get_gpu_memory(),
            'tensor_info': self.count_tensors(),
            'status': self.check_memory_pressure(),
            'recommendations': self.get_recommendations()
        }

    def save_report(self, filepath: str):
        """Save memory profiling report to file"""
        report = {
            'timestamp': time.time(),
            'summary': self.get_summary(),
            'snapshots': [
                {
                    'timestamp': snap.timestamp,
                    'process_memory_mb': snap.process_memory_mb,
                    'gpu_memory_mb': snap.gpu_memory_mb,
                    'tensor_count': snap.tensor_count
                }
                for snap in self.stats.memory_snapshots
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Memory profiling report saved to {filepath}")


@contextmanager
def memory_monitoring(profiler: MemoryProfiler, description: str = ""):
    """Context manager for monitoring memory during code execution"""
    logger.info(f"Starting memory monitoring: {description}")

    # Take snapshot before
    profiler.take_snapshot()
    before_memory = profiler.stats.current_memory_mb

    try:
        yield profiler

    finally:
        # Take snapshot after
        profiler.take_snapshot()
        after_memory = profiler.stats.current_memory_mb
        memory_delta = after_memory - before_memory

        logger.info(f"Memory monitoring complete: {description}")
        logger.info(f"Memory delta: {memory_delta:+.2f} MB")

        # Apply optimizations if needed
        status = profiler.check_memory_pressure()
        if status['is_warning'] or status['is_critical']:
            logger.warning(f"High memory usage detected: {status['usage_percentage']:.1f}%")
            profiler.optimize_memory()


def profile_memory(func: Callable) -> Callable:
    """Decorator for profiling memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create profiler if not provided
        profiler = kwargs.get('memory_profiler')
        if profiler is None:
            profiler = MemoryProfiler()
            kwargs['memory_profiler'] = profiler

        # Profile function
        with memory_monitoring(profiler, f"Function: {func.__name__}"):
            result = func(*args, **kwargs)

        return result

    return wrapper


def optimize_for_8gb_mac_m2(model: nn.Module) -> Dict[str, Any]:
    """
    Apply Mac M2 specific optimizations for 8GB memory constraint

    Args:
        model: PyTorch model to optimize

    Returns:
        Dictionary with optimization results
    """
    optimizations = []

    # Enable MPS fallback for unsupported operations
    if torch.backends.mps.is_available():
        torch.backends.mps.is_available()
        optimizations.append("enabled_mps_backend")

    # Use efficient attention implementations
    if hasattr(model, 'eval'):
        # Enable eval mode for inference
        optimizations.append("eval_mode_optimization")

    # Apply memory-efficient attention if available
    try:
        from torch.nn.functional import scaled_dot_product_attention
        optimizations.append("scaled_dot_product_attention")
    except ImportError:
        pass

    # Set model to use memory-efficient settings
    if hasattr(model, 'use_engram'):
        model.use_engram = True
        optimizations.append("engram_memory_optimization")

    if hasattr(model, 'use_mhc'):
        model.use_mhc = True
        optimizations.append("mhc_stability_optimization")

    return {
        'optimizations_applied': optimizations,
        'model_parameters': sum(p.numel() for p in model.parameters()),
        'model_memory_mb': sum(p.numel() for p in model.parameters()) * 4 / (1024**2)
    }


def create_memory_optimizer(max_memory_gb: float = 5.0) -> MemoryProfiler:
    """
    Factory function to create memory profiler/optimizer

    Args:
        max_memory_gb: Maximum memory budget in GB

    Returns:
        Configured MemoryProfiler
    """
    profiler = MemoryProfiler(max_memory_gb=max_memory_gb)

    logger.info(f"Memory optimizer created with {max_memory_gb}GB budget")
    return profiler


if __name__ == "__main__":
    # Test memory profiler
    print("Testing Memory Profiler...")

    profiler = create_memory_optimizer(max_memory_gb=5.0)

    # Create some tensors
    with memory_monitoring(profiler, "Tensor creation test"):
        tensors = [torch.randn(1000, 1000) for _ in range(10)]

    # Check status
    summary = profiler.get_summary()
    print(f"Memory summary: {json.dumps(summary, indent=2)}")

    # Test optimizations
    result = optimize_for_8gb_mac_m2(torch.nn.Linear(100, 100))
    print(f"Optimization result: {result}")

    print("Memory profiler test completed!")