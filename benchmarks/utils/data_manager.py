"""
Data Management and Caching System

Efficient data loading, caching, and management system for large-scale
benchmark datasets with memory optimization and fast access.
"""

import os
import json
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import numpy as np
import torch
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil


@dataclass
class CacheConfig:
    """Configuration for data caching system"""
    enable_cache: bool = True
    cache_dir: Union[str, Path] = None
    max_cache_size_gb: float = 10.0
    compression: bool = True
    parallel_loading: bool = True
    num_workers: int = 4
    cache_preprocessed: bool = True


class DataManager:
    """
    Efficient data management system with caching and memory optimization.

    Features:
    - Intelligent caching of preprocessed data
    - Memory-efficient data loading
    - Parallel preprocessing
    - Cache size management
    - Data integrity verification
    """

    def __init__(self,
                 config: CacheConfig,
                 dataset_name: str):
        """
        Initialize data manager.

        Args:
            config: Cache configuration
            dataset_name: Name of the dataset
        """
        self.config = config
        self.dataset_name = dataset_name

        # Setup cache directory
        if self.config.cache_dir is None:
            self.config.cache_dir = Path(tempfile.gettempdir()) / 'benchmark_cache' / dataset_name
        else:
            self.config.cache_dir = Path(self.config.cache_dir)

        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache management
        self.cache_index = {}
        self._load_cache_index()

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_data_size = 0

    def _load_cache_index(self):
        """Load cache index from disk"""
        index_file = self.config.cache_dir / 'cache_index.json'
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.cache_index = json.load(f)
        else:
            self.cache_index = {
                'version': '1.0',
                'dataset': self.dataset_name,
                'entries': {}
            }

    def _save_cache_index(self):
        """Save cache index to disk"""
        index_file = self.config.cache_dir / 'cache_index.json'
        with open(index_file, 'w') as f:
            json.dump(self.cache_index, f, indent=2)

    def _get_cache_key(self, sample_id: str, preprocessing_params: Dict[str, Any]) -> str:
        """Generate cache key for a sample"""
        # Create a deterministic key from sample ID and preprocessing parameters
        key_data = f"{sample_id}_{json.dumps(preprocessing_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a key"""
        return self.config.cache_dir / f'{cache_key}.pkl'

    def _estimate_cache_size(self) -> float:
        """Estimate current cache size in GB"""
        total_size = 0
        cache_files = list(self.config.cache_dir.glob('*.pkl'))

        for cache_file in cache_files:
            total_size += cache_file.stat().st_size

        return total_size / (1024 ** 3)  # Convert to GB

    def _cleanup_cache_if_needed(self):
        """Clean up cache if size exceeds limit"""
        current_size = self._estimate_cache_size()
        if current_size > self.config.max_cache_size_gb:
            print(f"Cache size ({current_size:.2f} GB) exceeds limit ({self.config.max_cache_size_gb} GB)")
            print("Cleaning up old cache entries...")

            # Get all cache files with their access times
            cache_files = []
            for cache_file in self.config.cache_dir.glob('*.pkl'):
                cache_files.append((
                    cache_file,
                    cache_file.stat().st_mtime,
                    cache_file.stat().st_size
                ))

            # Sort by access time (oldest first)
            cache_files.sort(key=lambda x: x[1])

            # Remove oldest files until under limit
            removed_size = 0
            for cache_file, _, size in cache_files:
                if current_size - removed_size < self.config.max_cache_size_gb * 0.8:  # Leave 20% buffer
                    break

                # Get cache key
                cache_key = cache_file.stem
                if cache_key in self.cache_index['entries']:
                    del self.cache_index['entries'][cache_key]

                cache_file.unlink()
                removed_size += size
                print(f"Removed cache file: {cache_file.name}")

            # Save updated index
            self._save_cache_index()

            new_size = self._estimate_cache_size()
            print(f"Cache cleanup complete. New size: {new_size:.2f} GB")

    def get_cached_data(self,
                       sample_id: str,
                       preprocessing_params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached preprocessed data if available.

        Args:
            sample_id: Unique sample identifier
            preprocessing_params: Parameters used for preprocessing

        Returns:
            Cached data or None if not in cache
        """
        if not self.config.enable_cache:
            return None

        cache_key = self._get_cache_key(sample_id, preprocessing_params)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)

                self.cache_hits += 1
                return data
            except Exception as e:
                print(f"Warning: Failed to load cache entry {cache_key}: {e}")
                # Remove corrupted cache entry
                if cache_key in self.cache_index['entries']:
                    del self.cache_index['entries'][cache_key]
                self._save_cache_index()
                if cache_path.exists():
                    cache_path.unlink()

        self.cache_misses += 1
        return None

    def cache_data(self,
                  sample_id: str,
                  preprocessing_params: Dict[str, Any],
                  data: Any) -> bool:
        """
        Cache preprocessed data.

        Args:
            sample_id: Unique sample identifier
            preprocessing_params: Parameters used for preprocessing
            data: Data to cache

        Returns:
            True if caching succeeded
        """
        if not self.config.enable_cache:
            return False

        # Check cache size and cleanup if needed
        self._cleanup_cache_if_needed()

        cache_key = self._get_cache_key(sample_id, preprocessing_params)
        cache_path = self._get_cache_path(cache_key)

        try:
            # Save data to cache
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)

            # Update cache index
            self.cache_index['entries'][cache_key] = {
                'sample_id': sample_id,
                'preprocessing_params': preprocessing_params,
                'cache_file': str(cache_path),
                'timestamp': np.datetime64('now').astype(int),
                'size': cache_path.stat().st_size
            }
            self._save_cache_index()

            return True

        except Exception as e:
            print(f"Warning: Failed to cache data for {sample_id}: {e}")
            return False

    def clear_cache(self):
        """Clear all cached data"""
        print(f"Clearing cache for {self.dataset_name}...")

        # Remove all cache files
        for cache_file in self.config.cache_dir.glob('*.pkl'):
            cache_file.unlink()

        # Reset cache index
        self.cache_index['entries'] = {}
        self._save_cache_index()

        # Reset statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_data_size = 0

        print("Cache cleared successfully")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_size = self._estimate_cache_size()
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0

        return {
            'dataset': self.dataset_name,
            'cache_dir': str(self.config.cache_dir),
            'cache_size_gb': cache_size,
            'cache_entries': len(self.cache_index['entries']),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def preload_dataset(self,
                       samples: List[Any],
                       preprocessing_fn: callable,
                       preprocessing_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preload and cache entire dataset.

        Args:
            samples: List of data samples
            preprocessing_fn: Function to preprocess samples
            preprocessing_params: Parameters for preprocessing

        Returns:
            Statistics about preloading
        """
        print(f"Preloading {len(samples)} samples for {self.dataset_name}...")

        if not self.config.parallel_loading:
            # Sequential loading
            results = []
            for i, sample in enumerate(samples):
                sample_id = getattr(sample, 'sample_id', f'sample_{i}')
                cached_data = self.get_cached_data(sample_id, preprocessing_params)

                if cached_data is None:
                    try:
                        preprocessed = preprocessing_fn(sample)
                        self.cache_data(sample_id, preprocessing_params, preprocessed)
                        results.append(preprocessed)
                    except Exception as e:
                        print(f"Warning: Failed to preprocess sample {sample_id}: {e}")
                        results.append(None)
                else:
                    results.append(cached_data)

                if (i + 1) % 100 == 0:
                    print(f"Preloaded {i + 1}/{len(samples)} samples...")

        else:
            # Parallel loading
            results = [None] * len(samples)

            with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
                futures = {}
                for i, sample in enumerate(samples):
                    sample_id = getattr(sample, 'sample_id', f'sample_{i}')
                    cached_data = self.get_cached_data(sample_id, preprocessing_params)

                    if cached_data is not None:
                        results[i] = cached_data
                    else:
                        future = executor.submit(self._safe_preload, sample, sample_id,
                                               preprocessing_fn, preprocessing_params)
                        futures[future] = (i, sample_id)

                # Process completed futures
                completed = 0
                for future in as_completed(futures):
                    i, sample_id = futures[future]
                    try:
                        preprocessed = future.result()
                        results[i] = preprocessed

                        completed += 1
                        if completed % 100 == 0:
                            print(f"Preloaded {completed}/{len(futures)} samples...")

                    except Exception as e:
                        print(f"Warning: Failed to preload sample {sample_id}: {e}")
                        results[i] = None

        # Calculate statistics
        successful = sum(1 for r in results if r is not None)
        failed = len(results) - successful

        stats = {
            'total_samples': len(samples),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(samples) if samples else 0,
            'cache_stats': self.get_cache_stats()
        }

        print(f"Preloading complete: {successful}/{len(samples)} samples cached successfully")

        return stats

    def _safe_preload(self,
                     sample: Any,
                     sample_id: str,
                     preprocessing_fn: callable,
                     preprocessing_params: Dict[str, Any]) -> Any:
        """Safely preload a sample with error handling"""
        try:
            preprocessed = preprocessing_fn(sample)
            self.cache_data(sample_id, preprocessing_params, preprocessed)
            return preprocessed
        except Exception as e:
            print(f"Warning: Failed to preprocess sample {sample_id}: {e}")
            return None

    def create_data_splits(self,
                          samples: List[Any],
                          split_manager,
                          split_type: str = 'train') -> List[Any]:
        """
        Create data splits using split manager and cache them.

        Args:
            samples: List of all samples
            split_manager: SplitManager instance
            split_type: Type of split ('train', 'val', 'test')

        Returns:
            List of samples for the requested split
        """
        # Get split indices from split manager
        if split_type == 'train':
            indices = split_manager.train_indices
        elif split_type == 'val':
            indices = split_manager.val_indices
        elif split_type == 'test':
            indices = split_manager.test_indices
        else:
            raise ValueError(f"Unknown split type: {split_type}")

        # Create split
        split_samples = [samples[i] for i in indices]

        print(f"Created {split_type} split: {len(split_samples)} samples")

        return split_samples

    def export_cache_index(self, export_path: Union[str, Path]):
        """Export cache index to file"""
        export_path = Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, 'w') as f:
            json.dump(self.cache_index, f, indent=2)

        print(f"Cache index exported to {export_path}")

    def import_cache_index(self, import_path: Union[str, Path]):
        """Import cache index from file"""
        import_path = Path(import_path)

        if not import_path.exists():
            raise FileNotFoundError(f"Cache index file not found: {import_path}")

        with open(import_path, 'r') as f:
            imported_index = json.load(f)

        # Verify compatibility
        if imported_index.get('dataset') != self.dataset_name:
            print(f"Warning: Imported cache index is for different dataset: {imported_index.get('dataset')}")

        # Merge indexes
        for key, entry in imported_index.get('entries', {}).items():
            if key not in self.cache_index['entries']:
                self.cache_index['entries'][key] = entry

        self._save_cache_index()
        print(f"Cache index imported from {import_path}")


class DataLoader:
    """
    Optimized data loader with caching and batch management.

    Provides efficient data loading with automatic caching,
    memory management, and batch creation.
    """

    def __init__(self,
                 data_manager: DataManager,
                 samples: List[Any],
                 batch_size: int = 32,
                 shuffle: bool = True,
                 preprocessing_fn: Optional[callable] = None,
                 preprocessing_params: Optional[Dict[str, Any]] = None):
        """
        Initialize data loader.

        Args:
            data_manager: DataManager instance
            samples: List of data samples
            batch_size: Batch size
            shuffle: Whether to shuffle data
            preprocessing_fn: Optional preprocessing function
            preprocessing_params: Parameters for preprocessing
        """
        self.data_manager = data_manager
        self.samples = samples
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.preprocessing_fn = preprocessing_fn
        self.preprocessing_params = preprocessing_params or {}

        self.current_index = 0
        self.indices = list(range(len(samples)))

        if self.shuffle:
            np.random.shuffle(self.indices)

    def __iter__(self):
        """Reset iteration"""
        self.current_index = 0
        if self.shuffle:
            np.random.shuffle(self.indices)
        return self

    def __next__(self) -> List[Any]:
        """Get next batch"""
        if self.current_index >= len(self.indices):
            raise StopIteration

        batch_indices = self.indices[self.current_index:self.current_index + self.batch_size]
        self.current_index += self.batch_size

        batch_samples = [self.samples[i] for i in batch_indices]
        batch_data = []

        for i, sample in enumerate(batch_samples):
            sample_id = getattr(sample, 'sample_id', f'sample_{batch_indices[i]}')

            # Try to get cached data
            cached_data = self.data_manager.get_cached_data(
                sample_id, self.preprocessing_params
            )

            if cached_data is not None:
                batch_data.append(cached_data)
            elif self.preprocessing_fn is not None:
                # Preprocess and cache
                try:
                    preprocessed = self.preprocessing_fn(sample)
                    self.data_manager.cache_data(sample_id, self.preprocessing_params, preprocessed)
                    batch_data.append(preprocessed)
                except Exception as e:
                    print(f"Warning: Failed to preprocess sample {sample_id}: {e}")
                    batch_data.append(None)
            else:
                batch_data.append(sample)

        # Filter out failed samples
        batch_data = [data for data in batch_data if data is not None]

        return batch_data

    def __len__(self) -> int:
        """Get number of batches"""
        return (len(self.samples) + self.batch_size - 1) // self.batch_size