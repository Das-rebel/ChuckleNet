"""
Multimodal Humor Detection Datasets (SCRIPTS, MHD, Kuznetsova)

Implementation of multiple academic humor detection benchmarks:
- SCRIPTS: Humor detection from TV show scripts
- MHD: Multimodal Humor Detection dataset
- Kuznetsova: Humor detection from various sources

These datasets focus on humor prediction in different contexts.
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


class SCRIPTSDataset(BaseBenchmarkDataset):
    """
    SCRIPTS Dataset loader.

    Contains humorous and non-humorous excerpts from TV show scripts.
    """

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        """Initialize SCRIPTS dataset"""
        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load SCRIPTS data samples"""
        data_path = Path(self.data_path)

        # SCRIPTS typically has:
        # - scripts_train.csv, scripts_val.csv, scripts_test.csv
        # - or JSON format with script excerpts

        annotation_file = data_path / f'{self.split}.csv'
        if not annotation_file.exists():
            annotation_file = data_path / f'scripts_{self.split}.json'

        if not annotation_file.exists():
            raise FileNotFoundError(f"SCRIPTS annotation file not found for {self.split} split")

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
                # Get script text
                text = row.get('text', row.get('dialogue', row.get('script', '')))
                if not text or text.isspace():
                    continue

                # Get label (humorous or not)
                label = int(row.get('humor', row.get('is_funny', row.get('label', 0))))

                # Get metadata
                metadata = {
                    'show': row.get('show', row.get('tv_show', 'unknown')),
                    'characters': row.get('characters', row.get('speakers', [])),
                    'season': row.get('season', None),
                    'episode': row.get('episode', None),
                    'dataset': 'SCRIPTS'
                }

                metadata = {k: v for k, v in metadata.items() if v is not None}

                # Create sample
                sample = DataSample(
                    text=text,
                    audio_path=None,
                    video_path=None,
                    label=label,
                    speaker_id=None,
                    show_id=metadata.get('show'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load SCRIPTS sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from SCRIPTS {self.split} split")


class MHDDataset(BaseBenchmarkDataset):
    """
    Multimodal Humor Detection (MHD) Dataset loader.

    Contains multimodal content (text, audio, video) for humor detection.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 use_audio: bool = True,
                 use_video: bool = True,
                 **kwargs):
        """Initialize MHD dataset"""
        self.use_audio = use_audio
        self.use_video = use_video

        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load MHD data samples"""
        data_path = Path(self.data_path)

        # MHD typically has:
        # - audio/
        # - video/
        # - annotations/

        annotation_file = data_path / 'annotations' / f'{self.split}.csv'
        if not annotation_file.exists():
            annotation_file = data_path / f'{self.split}.json'

        if not annotation_file.exists():
            raise FileNotFoundError(f"MHD annotation file not found for {self.split} split")

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
                text = row.get('text', row.get('caption', ''))

                # Get audio path
                audio_path = None
                if self.use_audio:
                    audio_path = data_path / 'audio' / f'{sample_id}.wav'

                # Get video path
                video_path = None
                if self.use_video:
                    video_path = data_path / 'video' / f'{sample_id}.mp4'

                # Get label
                label = int(row.get('humor', row.get('is_funny', row.get('label', 0))))

                # Get metadata
                metadata = {
                    'source': row.get('source', 'unknown'),
                    'style': row.get('style', None),
                    'dataset': 'MHD'
                }

                metadata = {k: v for k, v in metadata.items() if v is not None}

                # Create sample
                sample = DataSample(
                    text=text,
                    audio_path=str(audio_path) if audio_path and audio_path.exists() else None,
                    video_path=str(video_path) if video_path and video_path.exists() else None,
                    label=label,
                    speaker_id=None,
                    show_id=metadata.get('source'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load MHD sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from MHD {self.split} split")


class KuznetsovaDataset(BaseBenchmarkDataset):
    """
    Kuznetsova Humor Detection Dataset loader.

    Contains humorous texts from various sources (news, jokes, quotes).
    """

    def __init__(self, data_path: str, split: str = 'train', **kwargs):
        """Initialize Kuznetsova dataset"""
        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load Kuznetsova data samples"""
        data_path = Path(self.data_path)

        # Kuznetsova dataset typically has:
        # - humorous.txt, non_humorous.txt
        # - or combined CSV with labels

        annotation_file = data_path / f'{self.split}.csv'
        if not annotation_file.exists():
            annotation_file = data_path / 'data.csv'

        if not annotation_file.exists():
            # Try text files format
            humorous_file = data_path / 'humorous.txt'
            non_humorous_file = data_path / 'non_humorous.txt'

            if humorous_file.exists() and non_humorous_file.exists():
                self._load_text_format(humorous_file, non_humorous_file)
                return

        # Load annotations
        if annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)
        else:
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
            annotations = pd.DataFrame(annotations)

        # Filter by split
        if 'split' in annotations.columns:
            annotations = annotations[annotations['split'] == self.split]

        # Load samples
        for _, row in annotations.iterrows():
            try:
                text = row.get('text', row.get('content', ''))
                if not text or text.isspace():
                    continue

                label = int(row.get('humor', row.get('is_funny', row.get('label', 0))))

                # Get metadata
                metadata = {
                    'source': row.get('source', 'unknown'),
                    'category': row.get('category', None),
                    'dataset': 'Kuznetsova'
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
                print(f"Warning: Failed to load Kuznetsova sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from Kuznetsova {self.split} split")

    def _load_text_format(self, humorous_file: Path, non_humorous_file: Path):
        """Load Kuznetsova data from text file format"""
        # Load humorous samples
        with open(humorous_file, 'r', encoding='utf-8') as f:
            for line in f:
                text = line.strip()
                if text:
                    sample = DataSample(
                        text=text,
                        label=1,
                        metadata={'dataset': 'Kuznetsova'}
                    )
                    self.samples.append(sample)

        # Load non-humorous samples
        with open(non_humorous_file, 'r', encoding='utf-8') as f:
            for line in f:
                text = line.strip()
                if text:
                    sample = DataSample(
                        text=text,
                        label=0,
                        metadata={'dataset': 'Kuznetsova'}
                    )
                    self.samples.append(sample)

        print(f"Loaded {len(self.samples)} samples from Kuznetsova text files")