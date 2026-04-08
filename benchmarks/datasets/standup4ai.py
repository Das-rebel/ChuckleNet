"""
StandUp4AI Dataset Implementation

StandUp4AI is a comprehensive dataset for laughter prediction in stand-up comedy,
containing audio, video, and text annotations from live comedy performances.

Dataset: https://github.com/StandUp4AI/standup4ai
Paper: "StandUp4AI: A Multimodal Dataset for Laughter Detection in Stand-Up Comedy"
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


class StandUp4AIDataset(BaseBenchmarkDataset):
    """
    StandUp4AI Dataset loader.

    Contains ~50 hours of stand-up comedy with laughter annotations.
    Supports audio-only, video-only, and multimodal evaluation.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 use_audio: bool = True,
                 use_video: bool = False,
                 use_text: bool = True,
                 **kwargs):
        """
        Initialize StandUp4AI dataset.

        Args:
            data_path: Path to StandUp4AI data directory
            split: Dataset split ('train', 'val', 'test')
            use_audio: Include audio modality
            use_video: Include video modality
            use_text: Include text modality
        """
        self.use_audio = use_audio
        self.use_video = use_video
        self.use_text = use_text

        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load StandUp4AI data samples"""
        data_path = Path(self.data_path)

        # StandUp4AI typically has this structure:
        # - data/
        #   - audio/
        #   - video/
        #   - transcripts/
        #   - annotations/
        # - splits/

        # Load annotations
        annotation_file = data_path / 'annotations' / f'{self.split}.csv'

        if not annotation_file.exists():
            # Try alternative annotation formats
            annotation_file = data_path / 'annotations' / f'{self.split}.json'

        if not annotation_file.exists():
            raise FileNotFoundError(f"Annotation file not found for {self.split} split")

        # Load annotations based on file type
        if annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)
        elif annotation_file.suffix == '.json':
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
            annotations = pd.DataFrame(annotations)
        else:
            raise ValueError(f"Unsupported annotation format: {annotation_file.suffix}")

        # Load samples
        for _, row in annotations.iterrows():
            try:
                # Extract basic information
                sample_id = row.get('sample_id', row.get('id', None))
                if sample_id is None:
                    continue

                # Get text/transcript
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
                    if not video_path.exists():
                        video_path = data_path / 'video' / f'{sample_id}.avi'

                # Get label (laughter presence/regression)
                label = None
                if 'laughter' in row:
                    label = int(row['laughter'])
                elif 'label' in row:
                    label = row['label']
                elif 'laughter_probability' in row:
                    label = float(row['laughter_probability'])
                elif 'laughter_intensity' in row:
                    label = float(row['laughter_intensity'])

                # Get metadata
                metadata = {
                    'comedian': row.get('comedian', row.get('speaker', 'unknown')),
                    'show': row.get('show', row.get('performance', 'unknown')),
                    'timestamp': row.get('timestamp', row.get('time', None)),
                    'duration': row.get('duration', None),
                    'dataset': 'StandUp4AI'
                }

                # Remove None values from metadata
                metadata = {k: v for k, v in metadata.items() if v is not None}

                # Create sample
                sample = DataSample(
                    text=text or '',
                    audio_path=str(audio_path) if audio_path and audio_path.exists() else None,
                    video_path=str(video_path) if video_path and video_path.exists() else None,
                    label=label,
                    speaker_id=metadata.get('comedian'),
                    show_id=metadata.get('show'),
                    timestamp=metadata.get('timestamp'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load sample {row.get('sample_id', 'unknown')}: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from StandUp4AI {self.split} split")


class StandUp4AIAudioOnlyDataset(StandUp4AIDataset):
    """StandUp4AI audio-only variant"""

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        super().__init__(data_path, split, use_audio=True, use_video=False, use_text=False, **kwargs)


class StandUp4AIVideoOnlyDataset(StandUp4AIDataset):
    """StandUp4AI video-only variant"""

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        super().__init__(data_path, split, use_audio=False, use_video=True, use_text=False, **kwargs)


class StandUp4AIMultimodalDataset(StandUp4AIDataset):
    """StandUp4AI full multimodal variant"""

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        super().__init__(data_path, split, use_audio=True, use_video=True, use_text=True, **kwargs)