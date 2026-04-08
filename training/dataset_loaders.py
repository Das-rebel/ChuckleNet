#!/usr/bin/env python3
"""
Dataset Loaders for New Plan Datasets

Implements loaders for:
- StandUp4AI (EMNLP 2025) - 3,617 videos, 130K+ word-level labels
- TIC-TALK (2026) - Kinematic signals + Whisper-AT laughter
- UR-FUNNY - P2FA forced alignment
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LaughterExample:
    example_id: str
    language: str
    words: List[str]
    labels: List[int]
    metadata: Dict[str, Any]


class StandUp4AILoader:
    """Loader for StandUp4AI dataset (EMNLP 2025).

    Expected format from https://github.com/Standup4AI/dataset
    Contains word-level laughter labels with ASR-aligned timestamps.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def load(self) -> List[LaughterExample]:
        examples = []

        transcripts_file = self.data_dir / "transcripts.json"
        labels_file = self.data_dir / "laughter_labels.json"

        if not transcripts_file.exists():
            raise FileNotFoundError(f"StandUp4AI transcripts not found: {transcripts_file}")

        with open(transcripts_file) as f:
            transcripts = json.load(f)

        labels_map = {}
        if labels_file.exists():
            with open(labels_file) as f:
                labels_data = json.load(f)
                for item in labels_data:
                    video_id = item.get("video_id")
                    word_labels = item.get("laughter_labels", [])
                    labels_map[video_id] = word_labels

        for video_id, transcript_data in transcripts.items():
            words = transcript_data.get("words", [])
            labels = labels_map.get(video_id, [0] * len(words))

            if len(words) != len(labels):
                labels = self._interpolate_labels(words, labels)

            examples.append(LaughterExample(
                example_id=f"standup4ai_{video_id}",
                language=transcript_data.get("language", "en"),
                words=[str(w) for w in words],
                labels=[int(l) for l in labels],
                metadata={
                    "source": "StandUp4AI",
                    "video_id": video_id,
                    "laughter_type": "word_level"
                }
            ))

        return examples

    def _interpolate_labels(self, words: List, labels: List) -> List[int]:
        if not labels:
            return [0] * len(words)
        if len(labels) == len(words):
            return labels

        result = []
        for i in range(len(words)):
            label_idx = int(i * len(labels) / len(words))
            label_idx = min(label_idx, len(labels) - 1)
            result.append(labels[label_idx])
        return result


class TICTalkLoader:
    """Loader for TIC-TALK dataset (2026).

    Contains 5,400+ segments with kinematic signals (arm spread, trunk lean)
    and Whisper-AT laughter detection at 0.8-second resolution.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def load(self) -> List[LaughterExample]:
        examples = []

        segments_file = self.data_dir / "segments.json"
        kinematics_file = self.data_dir / "kinematics.json"

        if not segments_file.exists():
            raise FileNotFoundError(f"TIC-TALK segments not found: {segments_file}")

        with open(segments_file) as f:
            segments = json.load(f)

        kinematics = {}
        if kinematics_file.exists():
            with open(kinematics_file) as f:
                kinematics = json.load(f)

        for segment in segments:
            segment_id = segment.get("segment_id")
            words = segment.get("words", [])
            laughter_timestamps = segment.get("laughter_timestamps", [])

            labels = self._timestamps_to_labels(words, laughter_timestamps)

            examples.append(LaughterExample(
                example_id=f"tictalk_{segment_id}",
                language="en",
                words=[str(w) for w in words],
                labels=labels,
                metadata={
                    "source": "TIC-TALK",
                    "segment_id": segment_id,
                    "kinematics": kinematics.get(segment_id, {}),
                    "laughter_type": "continuous"
                }
            ))

        return examples

    def _timestamps_to_labels(self, words: List, timestamps: List, resolution: float = 0.8) -> List[int]:
        labels = [0] * len(words)
        for ts in timestamps:
            start = ts.get("start", 0)
            end = ts.get("end", 0)
            word_start = int(start / resolution)
            word_end = int(end / resolution)
            word_start = min(word_start, len(labels) - 1)
            word_end = min(word_end, len(labels) - 1)
            for i in range(word_start, word_end + 1):
                labels[i] = 1
        return labels


class URFunnyLoader:
    """Loader for UR-FUNNY dataset.

    TED talks with word-level forced alignment via P2FA.
    Contains punchline and context annotations.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def load(self) -> List[LaughterExample]:
        examples = []

        annotations_file = self.data_dir / "urfunny_annotations.json"

        if not annotations_file.exists():
            raise FileNotFoundError(f"UR-FUNNY annotations not found: {annotations_file}")

        with open(annotations_file) as f:
            data = json.load(f)

        for item in data:
            ted_id = item.get("ted_id")
            words = item.get("words", [])
            punchline_positions = item.get("punchline_positions", [])

            labels = self._punchlines_to_labels(words, punchline_positions)

            examples.append(LaughterExample(
                example_id=f"urfunny_{ted_id}",
                language="en",
                words=[str(w) for w in words],
                labels=labels,
                metadata={
                    "source": "UR-FUNNY",
                    "ted_id": ted_id,
                    "punchline_count": len(punchline_positions),
                    "laughter_type": "discrete"
                }
            ))

        return examples

    def _punchlines_to_labels(self, words: List, positions: List[int]) -> List[int]:
        labels = [0] * len(words)
        for pos in positions:
            if 0 <= pos < len(words):
                labels[pos] = 1
        return labels


def convert_to_jsonl(examples: List[LaughterExample], output_file: Path):
    with open(output_file, "w") as f:
        for ex in examples:
            record = {
                "example_id": ex.example_id,
                "language": ex.language,
                "words": ex.words,
                "labels": ex.labels,
                "metadata": ex.metadata
            }
            f.write(json.dumps(record) + "\n")


class HindiHinglishLoader:
    """Loader for Hindi/Hinglish comedy data from Indian YouTube channels.

    Target comedians: Abhishek Upmanyu, Aakash Gupta, Biswa Kalyan Rath, etc.
    Data collected via: collect_indian_comedy_youtube.py
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)

    def load(self) -> List[LaughterExample]:
        examples = []

        jsonl_files = list(self.data_dir.glob("**/*.jsonl"))
        for jsonl_file in jsonl_files:
            with open(jsonl_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        examples.append(LaughterExample(
                            example_id=data.get('example_id', 'unknown'),
                            language=data.get('language', 'hi'),
                            words=data.get('words', []),
                            labels=data.get('labels', []),
                            metadata=data.get('metadata', {})
                        ))
                    except json.JSONDecodeError:
                        continue

        return examples


def load_new_dataset(dataset_name: str, data_dir: Path) -> List[LaughterExample]:
    loaders = {
        "standup4ai": StandUp4AILoader,
        "tictalk": TICTalkLoader,
        "urfunny": URFunnyLoader,
        "hindi_hinglish": HindiHinglishLoader,
    }

    if dataset_name.lower() not in loaders:
        raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(loaders.keys())}")

    loader = loaders[dataset_name.lower()](data_dir)
    return loader.load()


if __name__ == "__main__":
    print("New Dataset Loaders Available:")
    print("- StandUp4AI: EMNLP 2025, 3,617 videos, 130K+ word-level labels")
    print("- TIC-TALK: 2026, 5,400+ segments, kinematic signals + Whisper-AT")
    print("- UR-FUNNY: TED talks, P2FA forced alignment")
    print("\nUsage:")
    print("  from dataset_loaders import load_new_dataset")
    print("  examples = load_new_dataset('standup4ai', Path('data/StandUp4AI'))")