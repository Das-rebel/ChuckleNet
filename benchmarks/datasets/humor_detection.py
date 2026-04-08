"""
Additional Humor Detection Datasets (Bertero & Fung, MuSe-Humor, FunnyNet-W)

Implementation of additional academic humor detection benchmarks:
- Bertero & Fung: Humor detection from dialogue context
- MuSe-Humor: Multimodal sentiment and humor recognition
- FunnyNet-W: Web-based humor detection
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


class BerteroFungDataset(BaseBenchmarkDataset):
    """
    Bertero & Fung Humor Detection Dataset loader.

    Focuses on humor detection in conversational dialogue context.
    """

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        """Initialize Bertero & Fung dataset"""
        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load Bertero & Fung data samples"""
        data_path = Path(self.data_path)

        # Bertero & Fung typically has:
        # - conversations.json or similar
        # - split information in the data

        annotation_file = data_path / f'{self.split}.json'
        if not annotation_file.exists():
            annotation_file = data_path / 'conversations.json'

        if not annotation_file.exists():
            annotation_file = data_path / 'data.csv'

        if not annotation_file.exists():
            raise FileNotFoundError(f"Bertero & Fung annotation file not found for {self.split} split")

        # Load annotations
        if annotation_file.suffix == '.json':
            with open(annotation_file, 'r') as f:
                data = json.load(f)

            # Handle JSON structure (could be list of conversations)
            if isinstance(data, list):
                conversations = data
            elif isinstance(data, dict):
                conversations = data.get('conversations', data.get('data', []))
            else:
                raise ValueError("Unexpected JSON structure")

            # Process conversations
            for conv in conversations:
                try:
                    # Filter by split if present
                    if 'split' in conv and conv['split'] != self.split:
                        continue

                    # Get dialogue text
                    text = conv.get('text', conv.get('utterance', conv.get('dialogue', '')))
                    if not text or text.isspace():
                        continue

                    # Get label
                    label = int(conv.get('humor', conv.get('is_funny', conv.get('label', 0))))

                    # Get context (previous utterances)
                    context = conv.get('context', conv.get('previous_utterances', []))

                    # Get metadata
                    metadata = {
                        'conversation_id': conv.get('id', conv.get('conversation_id')),
                        'speaker': conv.get('speaker', 'unknown'),
                        'context_length': len(context),
                        'dataset': 'Bertero_Fung'
                    }

                    metadata = {k: v for k, v in metadata.items() if v is not None}

                    # Create sample
                    sample = DataSample(
                        text=text,
                        audio_path=None,
                        video_path=None,
                        label=label,
                        speaker_id=metadata.get('speaker'),
                        show_id=metadata.get('conversation_id'),
                        metadata=metadata
                    )

                    self.samples.append(sample)

                except Exception as e:
                    print(f"Warning: Failed to load Bertero & Fung conversation: {e}")
                    continue

        elif annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)

            # Filter by split
            if 'split' in annotations.columns:
                annotations = annotations[annotations['split'] == self.split]

            # Load samples
            for _, row in annotations.iterrows():
                try:
                    text = row.get('text', row.get('utterance', ''))
                    if not text or text.isspace():
                        continue

                    label = int(row.get('humor', row.get('is_funny', 0)))

                    metadata = {
                        'speaker': row.get('speaker', 'unknown'),
                        'conversation_id': row.get('conversation_id'),
                        'dataset': 'Bertero_Fung'
                    }

                    sample = DataSample(
                        text=text,
                        label=label,
                        speaker_id=metadata.get('speaker'),
                        metadata=metadata
                    )

                    self.samples.append(sample)

                except Exception as e:
                    print(f"Warning: Failed to load Bertero & Fung sample: {e}")
                    continue

        print(f"Loaded {len(self.samples)} samples from Bertero & Fung {self.split} split")


class MuSeHumorDataset(BaseBenchmarkDataset):
    """
    MuSe-Humor Dataset loader.

    Multimodal Sentiment and Humor recognition dataset with audio, video, and text.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 use_audio: bool = True,
                 use_video: bool = True,
                 use_text: bool = True,
                 **kwargs):
        """Initialize MuSe-Humor dataset"""
        self.use_audio = use_audio
        self.use_video = use_video
        self.use_text = use_text

        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load MuSe-Humor data samples"""
        data_path = Path(self.data_path)

        # MuSe-Humor typically has:
        # - audio/
        # - video/
        # - annotations/

        annotation_file = data_path / 'annotations' / f'{self.split}.csv'
        if not annotation_file.exists():
            annotation_file = data_path / f'{self.split}.json'

        if not annotation_file.exists():
            raise FileNotFoundError(f"MuSe-Humor annotation file not found for {self.split} split")

        # Load annotations
        if annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)
        else:
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
            annotations = pd.DataFrame(annotations)

        # Load samples
        for _, row in annotations.iterrows():
            try:
                sample_id = row.get('id', row.get('sample_id', None))
                if sample_id is None:
                    continue

                # Get text
                text = None
                if self.use_text:
                    text = row.get('text', row.get('transcript', row.get('caption', '')))

                # Get audio path
                audio_path = None
                if self.use_audio:
                    audio_path = data_path / 'audio' / f'{sample_id}.wav'
                    if not audio_path.exists():
                        audio_path = data_path / 'audio' / f'{sample_id}.mp3'

                # Get video path
                video_path = None
                if self.use_video:
                    video_path = data_path / 'video' / f'{sample_id}.mp4'

                # Get label (humor intensity)
                humor_score = row.get('humor', row.get('humor_intensity', row.get('label', 0)))
                if pd.isna(humor_score):
                    humor_score = 0

                # Convert to binary label if needed
                if isinstance(humor_score, (int, float)):
                    if humor_score > 0.5:  # Threshold for binary classification
                        label = 1
                    else:
                        label = 0
                else:
                    label = int(humor_score)

                # Get metadata
                metadata = {
                    'speaker_id': row.get('speaker', 'unknown'),
                    'video_id': sample_id,
                    'emotion': row.get('emotion', None),
                    'sentiment': row.get('sentiment', None),
                    'dataset': 'MuSe-Humor'
                }

                metadata = {k: v for k, v in metadata.items() if v is not None}

                # Create sample
                sample = DataSample(
                    text=text or '',
                    audio_path=str(audio_path) if audio_path and audio_path.exists() else None,
                    video_path=str(video_path) if video_path and video_path.exists() else None,
                    label=label,
                    speaker_id=metadata.get('speaker_id'),
                    show_id=metadata.get('video_id'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load MuSe-Humor sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from MuSe-Humor {self.split} split")


class FunnyNetWDataset(BaseBenchmarkDataset):
    """
    FunnyNet-W Dataset loader.

    Web-based humor detection dataset focusing on funny content from various sources.
    """

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        """Initialize FunnyNet-W dataset"""
        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load FunnyNet-W data samples"""
        data_path = Path(self.data_path)

        # FunnyNet-W typically has:
        # - funny_samples.json, non_funny_samples.json
        # - or combined dataset with labels

        annotation_file = data_path / f'{self.split}.json'
        if not annotation_file.exists():
            annotation_file = data_path / 'dataset.json'

        if not annotation_file.exists():
            annotation_file = data_path / 'data.csv'

        if not annotation_file.exists():
            raise FileNotFoundError(f"FunnyNet-W annotation file not found for {self.split} split")

        # Load annotations
        if annotation_file.suffix == '.json':
            with open(annotation_file, 'r') as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                samples = data
            elif isinstance(data, dict):
                # Could have separate lists for funny/non-funny
                if 'samples' in data:
                    samples = data['samples']
                elif 'funny' in data and 'not_funny' in data:
                    # Combine both categories
                    samples = []
                    for item in data['funny']:
                        item['label'] = 1
                        samples.append(item)
                    for item in data['not_funny']:
                        item['label'] = 0
                        samples.append(item)
                else:
                    samples = []
            else:
                raise ValueError("Unexpected JSON structure")

            # Process samples
            for sample_data in samples:
                try:
                    # Filter by split if present
                    if 'split' in sample_data and sample_data['split'] != self.split:
                        continue

                    # Get text
                    text = sample_data.get('text', sample_data.get('content', sample_data.get('joke', '')))
                    if not text or text.isspace():
                        continue

                    # Get label
                    label = sample_data.get('label', sample_data.get('is_funny', 0))
                    if isinstance(label, str):
                        label = 1 if label.lower() in ['funny', 'yes', 'true'] else 0
                    else:
                        label = int(label)

                    # Get metadata
                    metadata = {
                        'source': sample_data.get('source', 'unknown'),
                        'category': sample_data.get('category', None),
                        'url': sample_data.get('url', None),
                        'upvotes': sample_data.get('upvotes', None),
                        'dataset': 'FunnyNet-W'
                    }

                    metadata = {k: v for k, v in metadata.items() if v is not None}

                    # Create sample
                    sample = DataSample(
                        text=text,
                        audio_path=None,
                        video_path=None,
                        label=label,
                        speaker_id=None,
                        show_id=metadata.get('source'),
                        metadata=metadata
                    )

                    self.samples.append(sample)

                except Exception as e:
                    print(f"Warning: Failed to load FunnyNet-W sample: {e}")
                    continue

        elif annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)

            # Filter by split
            if 'split' in annotations.columns:
                annotations = annotations[annotations['split'] == self.split]

            # Load samples
            for _, row in annotations.iterrows():
                try:
                    text = row.get('text', row.get('content', ''))
                    if not text or text.isspace():
                        continue

                    label = int(row.get('label', row.get('is_funny', 0)))

                    metadata = {
                        'source': row.get('source', 'unknown'),
                        'category': row.get('category', None),
                        'dataset': 'FunnyNet-W'
                    }

                    sample = DataSample(
                        text=text,
                        label=label,
                        show_id=metadata.get('source'),
                        metadata=metadata
                    )

                    self.samples.append(sample)

                except Exception as e:
                    print(f"Warning: Failed to load FunnyNet-W sample: {e}")
                    continue

        print(f"Loaded {len(self.samples)} samples from FunnyNet-W {self.split} split")