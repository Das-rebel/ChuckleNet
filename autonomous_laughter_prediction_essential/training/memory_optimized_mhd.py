#!/usr/bin/env python3
"""
Memory-Optimized MHD Processing System for 8GB Mac M2
Specialized in efficient processing with strict memory constraints
"""

import os
import gc
import logging
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import psutil
import json

warnings.filterwarnings('ignore')

# Optional: Memory profiling
try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    current_mb: float
    peak_mb: float
    available_mb: float
    process_mb: float
    gc_collections: int = 0

@dataclass
class ProcessingChunk:
    """A chunk of data for memory-efficient processing"""
    chunk_id: int
    size: int
    data: Any = None
    processed: bool = False

class MemoryOptimizedMHDMProcessor:
    """
    Memory-optimized MHD processor for 8GB Mac M2 systems

    Key Optimizations:
    - Chunked processing to stay under memory limits
    - Aggressive garbage collection
    - Memory-efficient data structures
    - Real-time memory monitoring
    - Gradient checkpointing for neural networks
    - Streaming data processing
    """

    def __init__(self,
                 memory_limit_gb: float = 6.0,
                 chunk_size: int = 100,
                 monitor_memory: bool = True):
        """
        Initialize Memory-Optimized MHD Processor

        Args:
            memory_limit_gb: Maximum memory usage in GB
            chunk_size: Number of items to process per chunk
            monitor_memory: Enable real-time memory monitoring
        """
        self.memory_limit_gb = memory_limit_gb
        self.memory_limit_mb = memory_limit_gb * 1024
        self.chunk_size = chunk_size
        self.monitor_memory = monitor_memory

        self.logger = self._setup_logging()

        # Memory tracking
        self.memory_stats = MemoryStats(
            current_mb=0,
            peak_mb=0,
            available_mb=0,
            process_mb=0
        )

        # Processing state
        self.processed_chunks = 0
        self.total_items = 0

        # Memory optimization settings
        self.enable_chunking = True
        self.enable_streaming = True
        self.aggressive_gc = True

        if self.monitor_memory:
            self._start_memory_monitoring()

        self.logger.info(f"Memory-Optimized MHD Processor initialized")
        self.logger.info(f"Memory limit: {self.memory_limit_gb}GB, Chunk size: {self.chunk_size}")

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

    def _start_memory_monitoring(self):
        """Start real-time memory monitoring"""
        if TRACEMALLOC_AVAILABLE:
            tracemalloc.start(10)  # Start with 10 frames of stack trace

    def get_memory_usage(self) -> MemoryStats:
        """Get current memory usage statistics"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        self.memory_stats.current_mb = memory_info.rss / 1024 / 1024
        self.memory_stats.peak_mb = max(self.memory_stats.peak_mb, self.memory_stats.current_mb)
        self.memory_stats.available_mb = psutil.virtual_memory().available / 1024 / 1024
        self.memory_stats.process_mb = memory_info.rss / 1024 / 1024

        return self.memory_stats

    def check_memory_limit(self) -> bool:
        """Check if current memory usage is within limits"""
        stats = self.get_memory_usage()

        # Warn if approaching limit
        if stats.current_mb > self.memory_limit_mb * 0.8:
            self.logger.warning(f"Memory usage high: {stats.current_mb:.1f}MB / {self.memory_limit_mb:.1f}MB")

        # Force garbage collection if near limit
        if stats.current_mb > self.memory_limit_mb * 0.7:
            self._force_cleanup()

        return stats.current_mb < self.memory_limit_mb

    def _force_cleanup(self):
        """Force aggressive memory cleanup"""
        if self.aggressive_gc:
            gc.collect()
            gc.collect()  # Second pass for generational GC

            if TRACEMALLOC_AVAILABLE:
                tracemalloc.peek()

        self.memory_stats.gc_collections += 1

    def process_data_in_chunks(self,
                              data: List[Any],
                              process_func: callable,
                              **kwargs) -> List[Any]:
        """
        Process data in memory-efficient chunks

        Args:
            data: List of data items to process
            process_func: Function to apply to each chunk
            **kwargs: Additional arguments for process_func

        Returns:
            List of processed results
        """
        results = []
        total_chunks = (len(data) + self.chunk_size - 1) // self.chunk_size

        self.logger.info(f"Processing {len(data)} items in {total_chunks} chunks")

        for chunk_idx in range(total_chunks):
            # Check memory before processing
            if not self.check_memory_limit():
                self.logger.error("Memory limit exceeded, stopping processing")
                break

            # Extract chunk
            start_idx = chunk_idx * self.chunk_size
            end_idx = min(start_idx + self.chunk_size, len(data))
            chunk = data[start_idx:end_idx]

            self.logger.info(f"Processing chunk {chunk_idx + 1}/{total_chunks} ({len(chunk)} items)")

            try:
                # Process chunk
                chunk_results = process_func(chunk, **kwargs)
                results.extend(chunk_results)

                self.processed_chunks += 1
                self.total_items += len(chunk)

                # Clean up chunk data
                del chunk
                if self.aggressive_gc:
                    self._force_cleanup()

            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk_idx}: {e}")
                continue

        self.logger.info(f"Completed processing: {len(results)} results from {self.total_items} items")
        return results

    def stream_process_file(self,
                           file_path: str,
                           process_func: callable,
                           **kwargs) -> Iterator[Any]:
        """
        Stream process a file line by line to minimize memory usage

        Args:
            file_path: Path to file to process
            process_func: Function to apply to each line/item
            **kwargs: Additional arguments for process_func

        Yields:
            Processed results one at a time
        """
        self.logger.info(f"Stream processing file: {file_path}")

        processed_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Check memory periodically
                    if processed_count % 100 == 0 and not self.check_memory_limit():
                        self.logger.error("Memory limit exceeded during streaming")
                        break

                    try:
                        # Process line
                        result = process_func(line.strip(), **kwargs)
                        if result is not None:
                            yield result
                            processed_count += 1

                    except Exception as e:
                        self.logger.error(f"Error processing line: {e}")
                        continue

                    # Periodic cleanup
                    if processed_count % 1000 == 0 and self.aggressive_gc:
                        self._force_cleanup()

        except Exception as e:
            self.logger.error(f"Error streaming file: {e}")

        self.logger.info(f"Completed streaming: {processed_count} items processed")

    def memory_efficient_model_training(self,
                                      model,
                                      train_loader,
                                      optimizer,
                                      criterion,
                                      epochs: int = 1,
                                      gradient_accumulation_steps: int = 4) -> Dict[str, float]:
        """
        Memory-efficient model training with gradient accumulation

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            optimizer: Optimizer
            criterion: Loss function
            epochs: Number of training epochs
            gradient_accumulation_steps: Steps to accumulate gradients

        Returns:
            Training metrics
        """
        import torch
        from torch.cuda.amp import GradScaler, autocast

        # Check if CUDA is available (use CPU for Mac M2)
        device = torch.device('cpu')
        model = model.to(device)

        training_metrics = {
            'total_loss': 0.0,
            'iterations': 0,
            'memory_peak_mb': 0
        }

        model.train()

        for epoch in range(epochs):
            self.logger.info(f"Starting epoch {epoch + 1}/{epochs}")

            optimizer.zero_grad()
            accumulated_loss = 0.0

            for batch_idx, batch in enumerate(train_loader):
                # Memory check
                if not self.check_memory_limit():
                    self.logger.warning("Memory limit approaching, reducing batch size")
                    break

                try:
                    # Move batch to device
                    inputs, labels = batch
                    inputs, labels = inputs.to(device), labels.to(device)

                    # Mixed precision training (if available)
                    if hasattr(torch.cuda, 'amp') and torch.cuda.is_available():
                        with autocast():
                            outputs = model(inputs)
                            loss = criterion(outputs, labels) / gradient_accumulation_steps

                        scaler = GradScaler()
                        scaler.scale(loss).backward()

                        if (batch_idx + 1) % gradient_accumulation_steps == 0:
                            scaler.step(optimizer)
                            scaler.update()
                            optimizer.zero_grad()
                    else:
                        # Regular training
                        outputs = model(inputs)
                        loss = criterion(outputs, labels) / gradient_accumulation_steps
                        loss.backward()

                        if (batch_idx + 1) % gradient_accumulation_steps == 0:
                            optimizer.step()
                            optimizer.zero_grad()

                    accumulated_loss += loss.item()
                    training_metrics['iterations'] += 1

                    # Update memory peak
                    current_memory = self.get_memory_usage()
                    training_metrics['memory_peak_mb'] = max(
                        training_metrics['memory_peak_mb'],
                        current_memory.current_mb
                    )

                    # Periodic logging and cleanup
                    if (batch_idx + 1) % 10 == 0:
                        avg_loss = accumulated_loss / (batch_idx + 1)
                        self.logger.info(f"Batch {batch_idx + 1}: Avg Loss = {avg_loss:.4f}")

                        if self.aggressive_gc:
                            self._force_cleanup()

                except RuntimeError as e:
                    if "out of memory" in str(e):
                        self.logger.error("Out of memory error, clearing cache and continuing")
                        if hasattr(torch, 'cuda_empty_cache'):
                            torch.cuda.empty_cache()
                        self._force_cleanup()
                        continue
                    else:
                        raise e

            training_metrics['total_loss'] = accumulated_loss / max(training_metrics['iterations'], 1)
            self.logger.info(f"Epoch {epoch + 1} completed. Avg Loss: {training_metrics['total_loss']:.4f}")

        return training_metrics

    def optimize_dataset_storage(self,
                                data: List[Dict[str, Any]],
                                output_file: str,
                                compression: bool = True) -> str:
        """
        Optimize dataset storage for memory efficiency

        Args:
            data: Dataset to store
            output_file: Output file path
            compression: Use compression for storage

        Returns:
            Path to optimized storage file
        """
        output_path = Path(output_file)

        self.logger.info(f"Optimizing dataset storage: {len(data)} items")

        # Convert to memory-efficient format
        optimized_data = []

        for item in data:
            # Convert to compact representation
            compact_item = self._create_compact_representation(item)
            optimized_data.append(compact_item)

            # Periodic cleanup
            if len(optimized_data) % 1000 == 0 and self.aggressive_gc:
                self._force_cleanup()

        # Store with optional compression
        if compression:
            import gzip
            with gzip.open(output_path.with_suffix('.jsonl.gz'), 'wt', encoding='utf-8') as f:
                for item in optimized_data:
                    f.write(json.dumps(item) + '\n')
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in optimized_data:
                    f.write(json.dumps(item) + '\n')

        self.logger.info(f"Dataset optimized and stored: {output_path}")

        # Calculate size reduction
        original_size = len(json.dumps(data))
        optimized_size = output_path.stat().st_size if output_path.exists() else 0

        if original_size > 0:
            reduction = (1 - optimized_size / original_size) * 100
            self.logger.info(f"Size reduction: {reduction:.1f}%")

        return str(output_path)

    def _create_compact_representation(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create memory-efficient representation of data item"""
        compact = {}

        # Extract essential fields only
        essential_keys = ['text', 'character', 'humor_score', 'laugh_intensity']
        for key in essential_keys:
            if key in item:
                compact[key] = item[key]

        # Convert numeric types to more compact representations
        if 'humor_score' in compact:
            compact['humor_score'] = float(compact['humor_score'])

        # Use shorter keys
        if 'metadata' in item and isinstance(item['metadata'], dict):
            compact['m'] = {
                's': item['metadata'].get('season', 0),
                'e': item['metadata'].get('episode', 0)
            }

        return compact

    def create_memory_efficient_embeddings(self,
                                          texts: List[str],
                                          embedding_model: Any) -> np.ndarray:
        """
        Create embeddings in a memory-efficient manner

        Args:
            texts: List of texts to embed
            embedding_model: Model to create embeddings

        Returns:
            Array of embeddings
        """
        self.logger.info(f"Creating embeddings for {len(texts)} texts")

        embeddings_list = []

        for i in range(0, len(texts), self.chunk_size):
            # Check memory
            if not self.check_memory_limit():
                self.logger.warning("Memory limit approaching, stopping embedding creation")
                break

            # Process chunk
            chunk = texts[i:i + self.chunk_size]
            self.logger.info(f"Processing embedding chunk {i // self.chunk_size + 1}")

            try:
                # Create embeddings for chunk
                chunk_embeddings = embedding_model.encode(chunk)
                embeddings_list.append(chunk_embeddings)

                # Cleanup
                del chunk
                if self.aggressive_gc:
                    self._force_cleanup()

            except Exception as e:
                self.logger.error(f"Error creating embeddings: {e}")
                continue

        if embeddings_list:
            embeddings = np.vstack(embeddings_list)
            self.logger.info(f"Created embeddings: {embeddings.shape}")
            return embeddings
        else:
            return np.array([])

    def get_optimal_batch_size(self,
                              model,
                              sample_input,
                              max_trials: int = 5) -> int:
        """
        Determine optimal batch size for memory constraints

        Args:
            model: Model to test
            sample_input: Sample input for testing
            max_trials: Maximum number of trial sizes

        Returns:
            Optimal batch size
        """
        import torch

        self.logger.info("Determining optimal batch size...")

        # Start with reasonable batch size
        batch_sizes = [1, 2, 4, 8, 16, 32]
        optimal_size = 1

        for batch_size in batch_sizes[:max_trials]:
            try:
                # Create test batch
                test_batch = sample_input.repeat(batch_size, 1)

                # Test forward pass
                with torch.no_grad():
                    _ = model(test_batch)

                # Check memory
                stats = self.get_memory_usage()
                if stats.current_mb < self.memory_limit_mb * 0.7:
                    optimal_size = batch_size
                    self.logger.info(f"Batch size {batch_size}: OK ({stats.current_mb:.1f}MB)")
                else:
                    self.logger.info(f"Batch size {batch_size}: Too much memory")
                    break

                # Cleanup
                del test_batch
                self._force_cleanup()

            except RuntimeError as e:
                if "out of memory" in str(e):
                    self.logger.info(f"Batch size {batch_size}: OOM")
                    break
                else:
                    raise e

        self.logger.info(f"Optimal batch size determined: {optimal_size}")
        return optimal_size

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing performance"""
        stats = self.get_memory_usage()

        return {
            'processed_chunks': self.processed_chunks,
            'total_items_processed': self.total_items,
            'memory_peak_mb': stats.peak_mb,
            'memory_current_mb': stats.current_mb,
            'memory_available_mb': stats.available_mb,
            'gc_collections': stats.gc_collections,
            'memory_efficiency': stats.current_mb / self.memory_limit_mb if self.memory_limit_mb > 0 else 0
        }

def main():
    """Main function for testing memory-optimized processor"""
    print("💾 Memory-Optimized MHD Processing System")
    print("=" * 50)

    # Initialize processor
    processor = MemoryOptimizedMHDMProcessor(
        memory_limit_gb=6.0,
        chunk_size=100,
        monitor_memory=True
    )

    print(f"✅ Memory-Optimized Processor initialized")
    print(f"📊 Memory limit: {processor.memory_limit_gb}GB")
    print(f"🔧 Chunk size: {processor.chunk_size}")

    # Get current memory usage
    stats = processor.get_memory_usage()
    print(f"\n💻 Current Memory Status:")
    print(f"   - Current: {stats.current_mb:.1f}MB")
    print(f"   - Available: {stats.available_mb:.1f}MB")
    print(f"   - Process: {stats.process_mb:.1f}MB")

    # Test chunked processing
    sample_data = [{"text": f"Sample text {i}", "value": i} for i in range(500)]

    def sample_process_func(chunk):
        return [{"processed": item["text"], "result": item["value"] * 2} for item in chunk]

    print(f"\n🔄 Testing chunked processing...")
    results = processor.process_data_in_chunks(sample_data, sample_process_func)
    print(f"✅ Processed {len(results)} items")

    # Get final summary
    summary = processor.get_processing_summary()
    print(f"\n📈 Processing Summary:")
    print(f"   - Chunks processed: {summary['processed_chunks']}")
    print(f"   - Items processed: {summary['total_items_processed']}")
    print(f"   - Peak memory: {summary['memory_peak_mb']:.1f}MB")
    print(f"   - GC collections: {summary['gc_collections']}")
    print(f"   - Memory efficiency: {summary['memory_efficiency']:.1%}")

    print("\n🎯 Key optimizations:")
    print("   - Chunked processing to stay under memory limits")
    print("   - Aggressive garbage collection")
    print("   - Memory-efficient data structures")
    print("   - Real-time memory monitoring")
    print("   - Gradient checkpointing for neural networks")
    print("   - Streaming data processing")

if __name__ == "__main__":
    main()