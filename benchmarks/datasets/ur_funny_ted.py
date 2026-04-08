"""
UR-FUNNY TED Dataset Implementation

UR-FUNNY is a large-scale dataset for humor detection in TED talks,
with multimodal features (text + audio + visual) from 1,866 videos.

Paper: "UR-FUNNY: A Large-Scale Dataset for Humor Detection in TED Talks"
Published Baseline: 65.23% accuracy (C-MFN)
Human Performance: 82.5% accuracy

This is the TED talk version, not the stand-up comedy version.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch
import numpy as np
from dataclasses import dataclass

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


@dataclass
class TEDVideoSample:
    """TED video sample with multimodal features"""
    video_id: str
    text: str
    audio_features: Optional[np.ndarray] = None
    visual_features: Optional[np.ndarray] = None
    label: int = 0  # Binary humor label
    speaker: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class URFunnyTEDDataset(BaseBenchmarkDataset):
    """
    UR-FUNNY TED Dataset loader for multimodal humor detection.

    Dataset characteristics:
    - 1,866 TED videos
    - 16,514 humor-labeled instances
    - Multimodal: text + audio + visual features
    - Binary classification task (humorous vs not humorous)
    - Published baseline: 65.23% accuracy
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 feature_type: str = 'multimodal',
                 use_precomputed_features: bool = True,
                 **kwargs):
        """
        Initialize UR-FUNNY TED dataset.

        Args:
            data_path: Path to UR-FUNNY TED data directory
            split: Dataset split ('train', 'val', 'test')
            feature_type: Type of features ('text', 'audio', 'visual', 'multimodal')
            use_precomputed_features: Use precomputed features if available
        """
        self.feature_type = feature_type
        self.use_precomputed_features = use_precomputed_features

        super().__init__(data_path, split, **kwargs)

        # Load dataset statistics
        self.dataset_stats = self._compute_dataset_statistics()

    def _load_data(self):
        """Load UR-FUNNY TED data samples"""
        data_path = Path(self.data_path)

        # UR-FUNNY TED dataset structure
        # Expected structure:
        # - annotations/train.csv, val.csv, test.csv
        # - features/audio_features.npy
        # - features/visual_features.npy
        # - videos/ (optional, for processing)

        # Load annotations
        annotation_file = data_path / 'annotations' / f'{self.split}.csv'

        if not annotation_file.exists():
            # Try alternative structure
            annotation_file = data_path / f'{self.split}.csv'
            if not annotation_file.exists():
                raise FileNotFoundError(f"UR-FUNNY TED annotation file not found for {self.split} split")

        # Load annotations
        annotations = pd.read_csv(annotation_file)

        print(f"Loading {len(annotations)} annotations from {annotation_file}")

        # Load precomputed features if available
        audio_features = None
        visual_features = None

        if self.use_precomputed_features:
            features_dir = data_path / 'features'
            if features_dir.exists():
                # Load audio features (e.g., MFCC, spectrograms)
                audio_feat_file = features_dir / 'audio_features.npy'
                if audio_feat_file.exists():
                    audio_features = np.load(audio_feat_file)
                    print(f"Loaded audio features: {audio_features.shape}")

                # Load visual features (e.g., facial expressions, scene features)
                visual_feat_file = features_dir / 'visual_features.npy'
                if visual_feat_file.exists():
                    visual_features = np.load(visual_feat_file)
                    print(f"Loaded visual features: {visual_features.shape}")

        # Load samples
        for idx, row in annotations.iterrows():
            try:
                # Get text content
                text = row.get('text', row.get('transcript', row.get('caption', '')))
                if not text or text.isspace():
                    continue

                # Get binary humor label
                humor_label = row.get('humor', row.get('funny', row.get('label', 0)))
                label = int(humor_label)

                # Get metadata
                video_id = row.get('video_id', row.get('id', f'video_{idx}'))
                speaker = row.get('speaker', row.get('presenter', 'unknown'))
                title = row.get('title', row.get('description', ''))
                url = row.get('url', '')

                # Get feature indices if using precomputed features
                sample_audio_features = None
                sample_visual_features = None

                if self.use_precomputed_features:
                    feat_idx = row.get('audio_feature_idx', row.get('feature_idx', idx))

                    if audio_features is not None and feat_idx < len(audio_features):
                        sample_audio_features = audio_features[feat_idx]

                    if visual_features is not None and feat_idx < len(visual_features):
                        sample_visual_features = visual_features[feat_idx]

                # Get file paths (if available)
                audio_path = None
                video_path = None

                if 'audio_path' in row and pd.notna(row['audio_path']):
                    audio_path = data_path / row['audio_path']

                if 'video_path' in row and pd.notna(row['video_path']):
                    video_path = data_path / row['video_path']

                # Create metadata
                metadata = {
                    'video_id': video_id,
                    'speaker': speaker,
                    'title': title,
                    'url': url,
                    'dataset': 'UR-FUNNY-TED',
                    'feature_type': self.feature_type,
                    'split': self.split
                }

                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None and not pd.isna(v)}

                # Create sample
                sample = DataSample(
                    text=text,
                    audio_path=str(audio_path) if audio_path and audio_path.exists() else None,
                    video_path=str(video_path) if video_path and video_path.exists() else None,
                    label=label,
                    speaker_id=speaker,
                    show_id=video_id,  # Use video_id as show_id
                    metadata=metadata
                )

                # Add precomputed features if available
                if sample_audio_features is not None:
                    sample.features = torch.tensor(sample_audio_features, dtype=torch.float)

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load UR-FUNNY TED sample {idx}: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from UR-FUNNY TED {self.split} split")

    def _compute_dataset_statistics(self) -> Dict[str, Any]:
        """Compute dataset statistics for UR-FUNNY TED"""
        stats = {
            'dataset_name': 'UR-FUNNY-TED',
            'total_videos': 1866,
            'total_instances': 16514,
            'splits': {
                'train': 0,  # Will be updated
                'val': 0,
                'test': 0
            },
            'baseline_accuracy': 65.23,  # C-MFN baseline
            'human_performance': 82.5,
            'task_type': 'binary_classification',
            'feature_types': ['text', 'audio', 'visual', 'multimodal']
        }

        # Update split counts
        stats['splits'][self.split] = len(self.samples)

        return stats

    def get_baseline_comparison(self) -> Dict[str, float]:
        """Get baseline performance metrics for comparison"""
        return {
            'c_mfn_baseline': 65.23,  # Published C-MFN baseline
            'human_performance': 82.5,
            'random_guess': 50.0,  # Binary classification baseline
            'majority_class': self._get_majority_baseline()
        }

    def _get_majority_baseline(self) -> float:
        """Calculate majority class baseline"""
        if not self.samples:
            return 50.0

        labels = [s.label for s in self.samples if s.label is not None]
        if not labels:
            return 50.0

        majority_ratio = max(labels.count(0), labels.count(1)) / len(labels)
        return majority_ratio * 100

    def get_multimodal_features(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get multimodal features for a sample.

        Returns:
            Dictionary with 'text', 'audio', 'visual' features
        """
        sample = self.samples[idx]
        features = {}

        # Get text features (using tokenizer)
        if sample.text:
            encoded = self.tokenizer(
                sample.text,
                max_length=self.max_text_length,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            features['text'] = {
                'input_ids': encoded['input_ids'].squeeze(0),
                'attention_mask': encoded['attention_mask'].squeeze(0)
            }

        # Get audio features (either precomputed or extract from file)
        if sample.audio_path:
            try:
                waveform, sample_rate = torchaudio.load(sample.audio_path)
                # Resample if needed
                if sample_rate != self.target_sample_rate:
                    resampler = torchaudio.transforms.Resample(
                        sample_rate, self.target_sample_rate
                    )
                    waveform = resampler(waveform)

                features['audio'] = {
                    'waveform': waveform,
                    'sample_rate': self.target_sample_rate
                }
            except Exception as e:
                print(f"Warning: Failed to load audio for sample {idx}: {e}")

        # Get visual features (from precomputed or extract from video)
        if sample.features is not None:
            features['visual'] = {
                'features': sample.features
            }

        return features

    def create_multimodal_batch(self, indices: List[int]) -> Dict[str, torch.Tensor]:
        """
        Create a multimodal batch from multiple samples.

        Args:
            indices: List of sample indices

        Returns:
            Dictionary with batched multimodal features
        """
        batch = {
            'text_input_ids': [],
            'text_attention_mask': [],
            'audio': [],
            'visual': [],
            'labels': [],
            'metadata': []
        }

        for idx in indices:
            features = self.get_multimodal_features(idx)

            # Add text features
            if 'text' in features:
                batch['text_input_ids'].append(features['text']['input_ids'])
                batch['text_attention_mask'].append(features['text']['attention_mask'])

            # Add audio features
            if 'audio' in features:
                batch['audio'].append(features['audio']['waveform'])

            # Add visual features
            if 'visual' in features:
                batch['visual'].append(features['visual']['features'])

            # Add label
            sample = self.samples[idx]
            batch['labels'].append(sample.label)

            # Add metadata
            batch['metadata'].append(sample.metadata)

        # Convert to tensors
        if batch['text_input_ids']:
            batch['text_input_ids'] = torch.stack(batch['text_input_ids'])
            batch['text_attention_mask'] = torch.stack(batch['text_attention_mask'])

        if batch['audio']:
            batch['audio'] = torch.cat(batch['audio'], dim=0)

        if batch['visual']:
            batch['visual'] = torch.stack(batch['visual'])

        batch['labels'] = torch.tensor(batch['labels'], dtype=torch.long)

        return batch


class URFunnyTEDProcessor:
    """
    Processor for UR-FUNNY TED dataset to extract and prepare multimodal features.
    """

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.features_dir = self.data_path / 'features'
        self.features_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio_features(self,
                               audio_path: str,
                               feature_type: str = 'mfcc') -> np.ndarray:
        """
        Extract audio features from audio file.

        Args:
            audio_path: Path to audio file
            feature_type: Type of features ('mfcc', 'spectrogram', 'mel')

        Returns:
            Audio features as numpy array
        """
        try:
            import torchaudio
            import torchaudio.compliance.kaldi as kaldi

            # Load audio
            waveform, sample_rate = torchaudio.load(audio_path)

            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000

            # Extract features based on type
            if feature_type == 'mfcc':
                # Extract MFCC features
                mfcc_transform = torchaudio.transforms.MFCC(
                    sample_rate=sample_rate,
                    n_mfcc=13,
                    melkwargs={'n_fft': 400, 'hop_length': 160, 'n_mels': 40}
                )
                features = mfcc_transform(waveform)

            elif feature_type == 'spectrogram':
                # Extract spectrogram
                spectrogram_transform = torchaudio.transforms.Spectrogram(
                    n_fft=400, hop_length=160, power=2.0
                )
                features = spectrogram_transform(waveform)

            elif feature_type == 'mel':
                # Extract mel spectrogram
                mel_transform = torchaudio.transforms.MelSpectrogram(
                    sample_rate=sample_rate,
                    n_fft=400, hop_length=160, n_mels=80
                )
                features = mel_transform(waveform)

            else:
                raise ValueError(f"Unknown feature type: {feature_type}")

            # Average over time dimension to get fixed-size features
            features = features.mean(dim=2).squeeze(0).numpy()

            return features

        except Exception as e:
            print(f"Error extracting audio features from {audio_path}: {e}")
            return np.zeros(128)  # Return zero features on error

    def extract_visual_features(self,
                                video_path: str,
                                num_frames: int = 10) -> np.ndarray:
        """
        Extract visual features from video file.

        Args:
            video_path: Path to video file
            num_frames: Number of frames to sample

        Returns:
            Visual features as numpy array
        """
        try:
            import cv2
            import torchvision.transforms as transforms

            # Open video
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Sample frames uniformly
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

            frames = []
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Resize and normalize
                    transform = transforms.Compose([
                        transforms.ToPILImage(),
                        transforms.Resize(256),
                        transforms.CenterCrop(224),
                        transforms.ToTensor(),
                        transforms.Normalize(
                            mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225]
                        )
                    ])
                    frame_tensor = transform(frame)
                    frames.append(frame_tensor)

            cap.release()

            if not frames:
                return np.zeros(512)  # Return zero features on error

            # Stack frames and extract features
            frames_tensor = torch.stack(frames)  # [num_frames, 3, 224, 224]

            # Here you would typically use a pre-trained model like ResNet
            # For simplicity, we'll flatten the frames
            features = frames_tensor.flatten().numpy()

            return features

        except Exception as e:
            print(f"Error extracting visual features from {video_path}: {e}")
            return np.zeros(512)  # Return zero features on error

    def preprocess_dataset(self,
                          annotation_file: str,
                          output_dir: str = None) -> Dict[str, np.ndarray]:
        """
        Preprocess entire UR-FUNNY TED dataset and extract features.

        Args:
            annotation_file: Path to annotation CSV file
            output_dir: Directory to save features (default: self.features_dir)

        Returns:
            Dictionary with extracted features
        """
        if output_dir is None:
            output_dir = self.features_dir
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Load annotations
        annotations = pd.read_csv(annotation_file)

        audio_features = []
        visual_features = []

        print(f"Processing {len(annotations)} samples...")

        for idx, row in annotations.iterrows():
            print(f"Processing sample {idx + 1}/{len(annotations)}")

            # Extract audio features
            if 'audio_path' in row and pd.notna(row['audio_path']):
                audio_path = self.data_path / row['audio_path']
                if audio_path.exists():
                    audio_feat = self.extract_audio_features(str(audio_path))
                    audio_features.append(audio_feat)
                else:
                    audio_features.append(np.zeros(128))
            else:
                audio_features.append(np.zeros(128))

            # Extract visual features
            if 'video_path' in row and pd.notna(row['video_path']):
                video_path = self.data_path / row['video_path']
                if video_path.exists():
                    visual_feat = self.extract_visual_features(str(video_path))
                    visual_features.append(visual_feat)
                else:
                    visual_features.append(np.zeros(512))
            else:
                visual_features.append(np.zeros(512))

        # Convert to numpy arrays and save
        audio_features = np.array(audio_features)
        visual_features = np.array(visual_features)

        np.save(output_dir / 'audio_features.npy', audio_features)
        np.save(output_dir / 'visual_features.npy', visual_features)

        print(f"Saved audio features: {audio_features.shape}")
        print(f"Saved visual features: {visual_features.shape}")

        return {
            'audio': audio_features,
            'visual': visual_features
        }


def create_ur_funny_ted_dataloaders(data_path: str,
                                    batch_size: int = 32,
                                    num_workers: int = 4) -> Dict[str, DataLoader]:
    """
    Create train/val/test dataloaders for UR-FUNNY TED dataset.

    Args:
        data_path: Path to UR-FUNNY TED data directory
        batch_size: Batch size for dataloaders
        num_workers: Number of worker processes

    Returns:
        Dictionary with train, val, test dataloaders
    """
    from torch.utils.data import DataLoader

    dataloaders = {}

    for split in ['train', 'val', 'test']:
        try:
            dataset = URFunnyTEDDataset(
                data_path=data_path,
                split=split,
                feature_type='multimodal'
            )

            dataloader = DataLoader(
                dataset,
                batch_size=batch_size,
                shuffle=(split == 'train'),
                num_workers=num_workers,
                pin_memory=torch.cuda.is_available()
            )

            dataloaders[split] = dataloader

            print(f"Created {split} dataloader: {len(dataset)} samples")

        except Exception as e:
            print(f"Warning: Failed to create {split} dataloader: {e}")

    return dataloaders


if __name__ == "__main__":
    # Example usage
    data_path = "/path/to/ur_funny_ted"

    # Create dataset
    dataset = URFunnyTEDDataset(
        data_path=data_path,
        split='train',
        feature_type='multimodal'
    )

    print(f"Dataset info: {dataset.get_split_info()}")
    print(f"Dataset statistics: {dataset.get_statistics()}")
    print(f"Baseline comparison: {dataset.get_baseline_comparison()}")