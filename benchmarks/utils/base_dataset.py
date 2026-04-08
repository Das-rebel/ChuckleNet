"""
Base Dataset Class for Autonomous Laughter Prediction Benchmarks

This module provides the foundation for all benchmark dataset loaders, ensuring
standardized interfaces and preprocessing across all 9 academic benchmarks.
"""

import os
import json
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import torchaudio
import torchvision
import transformers


@dataclass
class DataSample:
    """Standardized data sample format across all benchmarks"""
    # Input data
    text: str
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    features: Optional[torch.Tensor] = None

    # Labels and metadata
    label: Optional[Union[int, float]] = None  # Laughter presence/regression
    timestamp: Optional[float] = None
    speaker_id: Optional[str] = None
    show_id: Optional[str] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert sample to dictionary for serialization"""
        return {
            'text': self.text,
            'audio_path': self.audio_path,
            'video_path': self.video_path,
            'features': self.features.numpy() if self.features is not None else None,
            'label': self.label,
            'timestamp': self.timestamp,
            'speaker_id': self.speaker_id,
            'show_id': self.show_id,
            'metadata': self.metadata
        }


class BaseBenchmarkDataset(Dataset, ABC):
    """
    Abstract base class for all laughter prediction benchmark datasets.

    All benchmark-specific datasets must inherit from this class and implement
    the required methods to ensure standardized interfaces and preprocessing.
    """

    def __init__(self,
                 data_path: Union[str, Path],
                 split: str = 'train',
                 transform: Optional[Any] = None,
                 target_sample_rate: int = 16000,
                 max_text_length: int = 512,
                 max_audio_length: int = 10,
                 cache_preprocessed: bool = True):
        """
        Initialize base dataset.

        Args:
            data_path: Path to benchmark data directory
            split: Dataset split ('train', 'val', 'test')
            transform: Optional data augmentation/transformations
            target_sample_rate: Target audio sample rate
            max_text_length: Maximum text sequence length
            max_audio_length: Maximum audio clip length (seconds)
            cache_preprocessed: Whether to cache preprocessed data
        """
        self.data_path = Path(data_path)
        self.split = split
        self.transform = transform
        self.target_sample_rate = target_sample_rate
        self.max_text_length = max_text_length
        self.max_audio_length = max_audio_length
        self.cache_preprocessed = cache_preprocessed

        # Initialize tokenizer and processors
        self._setup_processors()

        # Load data samples
        self.samples = []
        self._load_data()

        # Apply data validation
        self._validate_data()

        # Preprocess and cache if enabled
        if self.cache_preprocessed:
            self._cache_preprocessed_data()

    def _setup_processors(self):
        """Setup text tokenizer and audio/video processors"""
        # Text tokenizer (using BERT base as default)
        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            'bert-base-uncased',
            do_lower_case=True
        )

        # Audio processor
        self.audio_processor = torchaudio.transforms.Resample(
            orig_freq=self.target_sample_rate,
            new_freq=self.target_sample_rate
        )

        # Video processor (for frame extraction)
        self.video_processor = torchvision.transforms.Compose([
            torchvision.transforms.Resize(256),
            torchvision.transforms.CenterCrop(224),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    @abstractmethod
    def _load_data(self):
        """
        Load data samples from benchmark-specific format.
        Must be implemented by each benchmark dataset class.

        Should populate self.samples with DataSample objects.
        """
        pass

    def _validate_data(self):
        """Validate data integrity and quality"""
        print(f"Validating {len(self.samples)} samples for {self.split} split...")

        valid_samples = []
        for sample in self.samples:
            try:
                # Validate required fields
                if not sample.text or sample.text.isspace():
                    continue

                # Validate file paths if provided
                if sample.audio_path and not Path(sample.audio_path).exists():
                    continue

                if sample.video_path and not Path(sample.video_path).exists():
                    continue

                # Validate label ranges
                if sample.label is not None:
                    if isinstance(sample.label, float):
                        if not 0.0 <= sample.label <= 1.0:
                            continue
                    elif isinstance(sample.label, int):
                        if sample.label not in [0, 1]:
                            continue

                valid_samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to validate sample: {e}")
                continue

        self.samples = valid_samples
        print(f"Validation complete. {len(self.samples)} valid samples.")

    def _cache_preprocessed_data(self):
        """Cache preprocessed data for faster loading"""
        cache_dir = self.data_path / 'cache' / self.split
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f'{self.__class__.__name__}_cache.pkl'

        if cache_file.exists():
            print(f"Loading cached preprocessed data from {cache_file}")
            with open(cache_file, 'rb') as f:
                self.cached_data = pickle.load(f)
        else:
            print("Preprocessing and caching data...")
            self.cached_data = []
            for idx in range(len(self)):
                try:
                    preprocessed = self._preprocess_sample(self.__getitem__(idx))
                    self.cached_data.append(preprocessed)
                except Exception as e:
                    print(f"Warning: Failed to preprocess sample {idx}: {e}")
                    self.cached_data.append(None)

            # Save cache
            with open(cache_file, 'wb') as f:
                pickle.dump(self.cached_data, f)
            print(f"Cached preprocessed data to {cache_file}")

    def _preprocess_sample(self, sample: DataSample) -> Dict[str, torch.Tensor]:
        """Preprocess a single data sample"""
        preprocessed = {}

        # Text preprocessing
        if sample.text:
            encoded = self.tokenizer(
                sample.text,
                max_length=self.max_text_length,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            preprocessed['text_input_ids'] = encoded['input_ids'].squeeze(0)
            preprocessed['text_attention_mask'] = encoded['attention_mask'].squeeze(0)

        # Audio preprocessing
        if sample.audio_path and Path(sample.audio_path).exists():
            try:
                waveform, sample_rate = torchaudio.load(sample.audio_path)
                if sample_rate != self.target_sample_rate:
                    resampler = torchaudio.transforms.Resample(
                        sample_rate, self.target_sample_rate
                    )
                    waveform = resampler(waveform)

                # Trim or pad to max length
                max_samples = self.max_audio_length * self.target_sample_rate
                if waveform.shape[1] > max_samples:
                    waveform = waveform[:, :max_samples]
                elif waveform.shape[1] < max_samples:
                    padding = max_samples - waveform.shape[1]
                    waveform = torch.nn.functional.pad(waveform, (0, padding))

                preprocessed['audio'] = waveform.squeeze(0)
                preprocessed['audio_sample_rate'] = self.target_sample_rate
            except Exception as e:
                print(f"Warning: Failed to load audio {sample.audio_path}: {e}")

        # Label preprocessing
        if sample.label is not None:
            if isinstance(sample.label, (int, bool)):
                preprocessed['label'] = torch.tensor(sample.label, dtype=torch.long)
            else:
                preprocessed['label'] = torch.tensor(sample.label, dtype=torch.float)

        # Metadata
        preprocessed['metadata'] = {
            'speaker_id': sample.speaker_id,
            'show_id': sample.show_id,
            'timestamp': sample.timestamp,
            **(sample.metadata or {})
        }

        return preprocessed

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get a single preprocessed sample"""
        if self.cache_preprocessed and hasattr(self, 'cached_data'):
            cached = self.cached_data[idx]
            if cached is not None:
                return cached

        sample = self.samples[idx]
        return self._preprocess_sample(sample)

    def get_split_info(self) -> Dict[str, Any]:
        """Get information about dataset splits"""
        return {
            'dataset_name': self.__class__.__name__,
            'split': self.split,
            'num_samples': len(self.samples),
            'num_speakers': len(set(s.speaker_id for s in self.samples if s.speaker_id)),
            'num_shows': len(set(s.show_id for s in self.samples if s.show_id)),
            'data_path': str(self.data_path)
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        labels = [s.label for s in self.samples if s.label is not None]

        stats = {
            'total_samples': len(self.samples),
            'num_with_audio': sum(1 for s in self.samples if s.audio_path),
            'num_with_video': sum(1 for s in self.samples if s.video_path),
            'num_with_labels': len(labels),
        }

        if labels:
            # Classification statistics
            if all(isinstance(l, (int, bool)) for l in labels):
                stats['label_distribution'] = {
                    'laughter': sum(int(l) for l in labels),
                    'no_laughter': len(labels) - sum(int(l) for l in labels)
                }
                stats['laughter_ratio'] = stats['label_distribution']['laughter'] / len(labels)
            # Regression statistics
            else:
                stats['label_stats'] = {
                    'mean': np.mean(labels),
                    'std': np.std(labels),
                    'min': np.min(labels),
                    'max': np.max(labels)
                }

        return stats


def create_data_loader(dataset: BaseBenchmarkDataset,
                      batch_size: int = 32,
                      shuffle: bool = True,
                      num_workers: int = 0) -> DataLoader:
    """
    Create a DataLoader with proper collation function.

    Args:
        dataset: Benchmark dataset instance
        batch_size: Batch size
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes

    Returns:
        Configured DataLoader
    """
    def collate_fn(batch):
        """Custom collate function to handle variable length sequences"""
        collated = {}

        # Stack text data
        if 'text_input_ids' in batch[0]:
            collated['text_input_ids'] = torch.stack([item['text_input_ids'] for item in batch])
            collated['text_attention_mask'] = torch.stack([item['text_attention_mask'] for item in batch])

        # Stack audio data (pad sequences)
        if 'audio' in batch[0]:
            audio_lengths = torch.tensor([item['audio'].shape[0] for item in batch])
            audio_padded = pad_sequence([item['audio'] for item in batch], batch_first=True)
            collated['audio'] = audio_padded
            collated['audio_lengths'] = audio_lengths

        # Stack labels
        if 'label' in batch[0]:
            collated['label'] = torch.stack([item['label'] for item in batch])

        # Collect metadata
        collated['metadata'] = [item['metadata'] for item in batch]

        return collated

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=torch.cuda.is_available()
    )