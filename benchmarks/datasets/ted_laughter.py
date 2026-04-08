"""
TED Laughter Corpus Dataset Implementation

TED Laughter Corpus contains laughter annotations from TED talks,
providing a more formal speaking context compared to comedy.

Dataset: Available through academic request
Paper: "Laughter in the TED Talks: A Corpus for Analysis"
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


class TEDLaughterDataset(BaseBenchmarkDataset):
    """
    TED Laughter Corpus Dataset loader.

    Contains laughter annotations from TED presentations with audio.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 use_audio: bool = True,
                 use_transcripts: bool = True,
                 **kwargs):
        """
        Initialize TED Laughter dataset.

        Args:
            data_path: Path to TED Laughter data directory
            split: Dataset split ('train', 'val', 'test')
            use_audio: Include audio modality
            use_transcripts: Include transcript text
        """
        self.use_audio = use_audio
        self.use_transcripts = use_transcripts

        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load TED Laughter data samples"""
        data_path = Path(self.data_path)

        # TED Laughter corpus typically has:
        # - audio_files/
        # - transcripts/
        # - annotations.csv or annotations.json

        # Load annotations
        annotation_file = data_path / 'annotations.csv'
        if not annotation_file.exists():
            annotation_file = data_path / 'annotations.json'

        if not annotation_file.exists():
            raise FileNotFoundError(f"TED Laughter annotation file not found")

        # Load annotations
        if annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)
        else:
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
            annotations = pd.DataFrame(annotations)

        # Filter by split if needed
        if 'split' in annotations.columns:
            annotations = annotations[annotations['split'] == self.split]

        # Load samples
        for _, row in annotations.iterrows():
            try:
                # Get basic info
                talk_id = row.get('talk_id', row.get('id', None))
                if talk_id is None:
                    continue

                # Get transcript text
                text = None
                if self.use_transcripts:
                    text = row.get('transcript', row.get('text', row.get('caption', '')))

                # Get audio path
                audio_path = None
                if self.use_audio:
                    audio_path = data_path / 'audio' / f'{talk_id}.wav'
                    if not audio_path.exists():
                        audio_path = data_path / 'audio' / f'{talk_id}.mp3'

                # Get label (laughter presence)
                label = None
                if 'laughter' in row:
                    label = int(row['laughter'])
                elif 'has_laughter' in row:
                    label = int(row['has_laughter'])
                elif 'laughter_segments' in row:
                    # If laughter segments are provided, use as positive label
                    label = 1 if row['laughter_segments'] else 0

                # Get metadata
                metadata = {
                    'speaker': row.get('speaker', row.get('presenter', 'unknown')),
                    'talk_title': row.get('title', row.get('talk_title', 'unknown')),
                    'talk_id': talk_id,
                    'timestamp': row.get('timestamp', None),
                    'duration': row.get('duration', None),
                    'year': row.get('year', None),
                    'dataset': 'TED_Laughter'
                }

                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}

                # Create sample
                sample = DataSample(
                    text=text or '',
                    audio_path=str(audio_path) if audio_path and audio_path.exists() else None,
                    video_path=None,  # TED Laughter typically audio-only
                    label=label,
                    speaker_id=metadata.get('speaker'),
                    show_id=metadata.get('talk_title'),
                    timestamp=metadata.get('timestamp'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load TED Laughter sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from TED Laughter {self.split} split")