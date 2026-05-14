#!/usr/bin/env python3
"""
MHD (Multimodal Humor Dataset) Sitcom Processor for Big Bang Theory
Specializes in extracting laugh tracks and sitcom-specific humor patterns
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Audio processing for laugh track detection
try:
    import librosa
    import librosa.display
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Librosa not available - audio processing will be limited")

# Video processing for episode analysis
try:
    import cv2
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    logging.warning("OpenCV not available - video processing will be limited")

# Machine learning for pattern recognition
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Scikit-learn not available - ML features will be limited")

@dataclass
class LaughSegment:
    """Represents a laugh track segment with timing and intensity"""
    start_time: float
    end_time: float
    duration: float
    intensity: float  # 0.0 to 1.0
    laugh_type: str  # 'chuckle', 'laughter', 'guffaw', 'applause'
    confidence: float

@dataclass
class CharacterDialogue:
    """Represents character dialogue with associated laugh tracks"""
    character: str
    dialogue: str
    start_time: float
    end_time: float
    laugh_segments: List[LaughSegment] = field(default_factory=list)
    context: str = ""
    humor_score: float = 0.0

@dataclass
class SitcomEpisode:
    """Represents a complete sitcom episode with processed data"""
    episode_id: str
    season: int
    episode: int
    title: str
    dialogues: List[CharacterDialogue] = field(default_factory=list)
    laugh_tracks: List[LaughSegment] = field(default_factory=list)
    character_patterns: Dict[str, Any] = field(default_factory=dict)
    sitcom_tropes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class MHDSitcomProcessor:
    """
    Main processor for MHD sitcom dataset specializing in Big Bang Theory

    Key Capabilities:
    - Laugh track extraction and timing analysis
    - Character-specific humor pattern recognition
    - Sitcom trope identification
    - Cross-domain learning integration
    """

    def __init__(self, data_dir: str = "data/mhd_sitcom", memory_limit_gb: float = 6.0):
        """
        Initialize MHD Sitcom Processor

        Args:
            data_dir: Directory for storing processed sitcom data
            memory_limit_gb: Memory limit in GB (conservative for 8GB Mac M2)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.memory_limit_gb = memory_limit_gb
        self.logger = self._setup_logging()

        # Big Bang Theory character mapping
        self.bbt_characters = {
            'Sheldon': 'sheldon_cooper',
            'Leonard': 'leonard_hofstadter',
            'Penny': 'penny',
            'Howard': 'howard_wolowitz',
            'Raj': 'raj_koothrappali',
            'Amy': 'amy_fowler',
            'Bernadette': 'bernadette_rostenkowski',
            'Stuart': 'stuart_bloom'
        }

        # Sitcom-specific trope patterns
        self.sitcom_tropes = {
            'nerd_culture': ['physics', 'star_trek', 'comic_books', 'science_fiction'],
            'social_awkwardness': ['awkward', 'uncomfortable', 'embarrassing'],
            'intellectual_humor': ['quantum', 'equation', 'theorem', 'experiment'],
            'relationship_comedy': ['dating', 'breakup', 'marriage', 'jealousy'],
            'roommate_conflicts': ['apartment', 'roommate', 'agreement', 'boundary']
        }

        # Laugh track patterns
        self.laugh_patterns = {
            'chuckle': {'duration_range': (0.5, 2.0), 'intensity_range': (0.1, 0.4)},
            'laughter': {'duration_range': (1.5, 4.0), 'intensity_range': (0.3, 0.7)},
            'guffaw': {'duration_range': (2.0, 5.0), 'intensity_range': (0.5, 0.9)},
            'applause': {'duration_range': (3.0, 8.0), 'intensity_range': (0.4, 0.8)}
        }

        self.logger.info("MHD Sitcom Processor initialized")

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

    def process_episode_from_subtitle(self, subtitle_file: str, episode_info: Dict[str, Any]) -> SitcomEpisode:
        """
        Process a sitcom episode from subtitle file

        Args:
            subtitle_file: Path to subtitle file (SRT or VTT format)
            episode_info: Episode metadata (season, episode, title)

        Returns:
            Processed SitcomEpisode object
        """
        self.logger.info(f"Processing episode: {episode_info.get('title', 'Unknown')}")

        # Parse subtitle file
        dialogues = self._parse_subtitles(subtitle_file)

        # Extract character dialogues
        character_dialogues = self._extract_character_dialogues(dialogues)

        # Simulate laugh track detection (would use audio in production)
        laugh_segments = self._detect_laugh_tracks(character_dialogues)

        # Associate laughs with dialogues
        self._associate_laughs_with_dialogues(character_dialogues, laugh_segments)

        # Create episode object
        episode = SitcomEpisode(
            episode_id=f"S{episode_info['season']:02d}E{episode_info['episode']:02d}",
            season=episode_info['season'],
            episode=episode_info['episode'],
            title=episode_info['title'],
            dialogues=character_dialogues,
            laugh_tracks=laugh_segments
        )

        # Analyze character patterns
        episode.character_patterns = self._analyze_character_patterns(character_dialogues)

        # Identify sitcom tropes
        episode.sitcom_tropes = self._identify_sitcom_tropes(character_dialogues)

        # Add metadata
        episode.metadata = {
            'processing_date': datetime.now().isoformat(),
            'total_dialogues': len(character_dialogues),
            'total_laughs': len(laugh_segments),
            'characters_present': list(set(d.character for d in character_dialogues))
        }

        self.logger.info(f"Processed {len(character_dialogues)} dialogues with {len(laugh_segments)} laugh segments")

        return episode

    def _parse_subtitles(self, subtitle_file: str) -> List[Dict[str, Any]]:
        """Parse subtitle file (SRT or VTT format)"""
        dialogues = []

        try:
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple SRT parser
            pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
            matches = re.findall(pattern, content, re.DOTALL)

            for match in matches:
                index, start_time, end_time, text = match

                # Parse timing
                start_seconds = self._parse_timestamp(start_time)
                end_seconds = self._parse_timestamp(end_time)

                dialogues.append({
                    'index': int(index),
                    'start_time': start_seconds,
                    'end_time': end_seconds,
                    'text': text.strip()
                })

        except Exception as e:
            self.logger.error(f"Error parsing subtitles: {e}")

        return dialogues

    def _parse_timestamp(self, timestamp: str) -> float:
        """Parse SRT timestamp to seconds"""
        # Format: HH:MM:SS,mmm
        time_part, ms = timestamp.split(',')
        hours, minutes, seconds = time_part.split(':')

        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(ms) / 1000

    def _extract_character_dialogues(self, dialogues: List[Dict[str, Any]]) -> List[CharacterDialogue]:
        """Extract character-specific dialogues from subtitles"""
        character_dialogues = []

        for dialogue in dialogues:
            # Try to identify character from dialogue text
            character = self._identify_character(dialogue['text'])

            # Clean dialogue text
            clean_text = self._clean_dialogue_text(dialogue['text'])

            if clean_text:  # Only add non-empty dialogues
                char_dialogue = CharacterDialogue(
                    character=character,
                    dialogue=clean_text,
                    start_time=dialogue['start_time'],
                    end_time=dialogue['end_time']
                )
                character_dialogues.append(char_dialogue)

        return character_dialogues

    def _identify_character(self, text: str) -> str:
        """Identify character from dialogue text"""
        # Simple pattern matching for character identification
        text_lower = text.lower()

        # Check for character names
        for name, identifier in self.bbt_characters.items():
            if name.lower() in text_lower:
                return identifier

        # Check for common patterns
        if ':' in text:
            potential_name = text.split(':')[0].strip()
            if potential_name in self.bbt_characters:
                return self.bbt_characters[potential_name]

        # Default to unknown
        return 'unknown'

    def _clean_dialogue_text(self, text: str) -> str:
        """Clean dialogue text by removing timestamps, speaker names, etc."""
        # Remove speaker names at the beginning
        text = re.sub(r'^[A-Z][a-z]+:\s*', '', text)

        # Remove sound effects
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)

        # Remove music tags
        text = re.sub(r'♪.*?♪', '', text)

        # Clean up whitespace
        text = ' '.join(text.split())

        return text.strip()

    def _detect_laugh_tracks(self, dialogues: List[CharacterDialogue]) -> List[LaughSegment]:
        """
        Detect laugh tracks in dialogues
        In production, this would use audio analysis
        """
        laugh_segments = []

        # Simulate laugh track detection based on dialogue patterns
        # In production, this would use librosa for audio analysis
        for i, dialogue in enumerate(dialogues):
            # Simple heuristic: laughs occur after potentially funny dialogues
            humor_probability = self._estimate_humor_probability(dialogue.dialogue)

            if humor_probability > 0.3 and np.random.random() < humor_probability:
                # Generate laugh segment
                duration = np.random.uniform(1.0, 4.0)
                intensity = humor_probability * np.random.uniform(0.7, 1.0)

                # Determine laugh type
                laugh_type = self._classify_laugh_type(duration, intensity)

                laugh_segment = LaughSegment(
                    start_time=dialogue.end_time,
                    end_time=dialogue.end_time + duration,
                    duration=duration,
                    intensity=intensity,
                    laugh_type=laugh_type,
                    confidence=humor_probability
                )

                laugh_segments.append(laugh_segment)

        return laugh_segments

    def _estimate_humor_probability(self, dialogue: str) -> float:
        """Estimate probability that dialogue is humorous based on content"""
        humor_score = 0.0

        # Check for humor indicators
        humor_indicators = [
            'joke', 'funny', 'hilarious', 'ridiculous', 'absurd',
            'irony', 'sarcasm', 'pun', 'prank', 'tease'
        ]

        for indicator in humor_indicators:
            if indicator in dialogue.lower():
                humor_score += 0.1

        # Check for incongruity (unexpected combinations)
        if any(word in dialogue.lower() for word in ['but', 'however', 'although', 'unexpectedly']):
            humor_score += 0.2

        # Check for exaggeration
        if any(word in dialogue.lower() for word in ['literally', 'completely', 'absolutely', 'totally']):
            humor_score += 0.15

        # Check for pop culture references
        if any(word in dialogue.lower() for word in ['star trek', 'star wars', 'comic', 'science']):
            humor_score += 0.1

        return min(humor_score, 1.0)

    def _classify_laugh_type(self, duration: float, intensity: float) -> str:
        """Classify laugh type based on duration and intensity"""
        if duration < 1.5 and intensity < 0.4:
            return 'chuckle'
        elif duration < 3.0 and intensity < 0.7:
            return 'laughter'
        elif duration >= 3.0:
            return 'guffaw'
        else:
            return 'laughter'

    def _associate_laughs_with_dialogues(self, dialogues: List[CharacterDialogue],
                                       laugh_segments: List[LaughSegment]) -> None:
        """Associate laugh segments with nearby dialogues"""
        for dialogue in dialogues:
            # Find laughs that occur shortly after dialogue
            for laugh in laugh_segments:
                time_diff = laugh.start_time - dialogue.end_time
                if 0 <= time_diff <= 2.0:  # Laughs within 2 seconds after dialogue
                    dialogue.laugh_segments.append(laugh)
                    dialogue.humor_score = max(dialogue.humor_score, laugh.intensity)

    def _analyze_character_patterns(self, dialogues: List[CharacterDialogue]) -> Dict[str, Any]:
        """Analyze humor patterns for each character"""
        character_patterns = {}

        # Group dialogues by character
        character_dialogues = {}
        for dialogue in dialogues:
            if dialogue.character not in character_dialogues:
                character_dialogues[dialogue.character] = []
            character_dialogues[dialogue.character].append(dialogue)

        # Analyze patterns for each character
        for character, char_dialogues in character_dialogues.items():
            # Calculate humor statistics
            laugh_counts = [len(d.laugh_segments) for d in char_dialogues]
            humor_scores = [d.humor_score for d in char_dialogues]

            # Find common themes
            all_text = ' '.join(d.dialogue for d in char_dialogues)
            themes = self._extract_themes(all_text)

            character_patterns[character] = {
                'total_dialogues': len(char_dialogues),
                'avg_humor_score': np.mean(humor_scores) if humor_scores else 0.0,
                'laugh_frequency': np.mean(laugh_counts) if laugh_counts else 0.0,
                'themes': themes,
                'peak_humor_moments': sorted(
                    [(d.humor_score, d.dialogue[:50]) for d in char_dialogues if d.humor_score > 0.5],
                    reverse=True
                )[:5]
            }

        return character_patterns

    def _extract_themes(self, text: str) -> List[str]:
        """Extract common themes from character dialogue"""
        themes = []

        # Check for sitcom trope themes
        for trope, keywords in self.sitcom_tropes.items():
            if any(keyword in text.lower() for keyword in keywords):
                themes.append(trope)

        return themes

    def _identify_sitcom_tropes(self, dialogues: List[CharacterDialogue]) -> List[str]:
        """Identify sitcom tropes present in the episode"""
        tropes_found = []

        all_text = ' '.join(d.dialogue for d in dialogues)

        for trope, keywords in self.sitcom_tropes.items():
            keyword_count = sum(1 for kw in keywords if kw in all_text.lower())
            if keyword_count >= 2:  # Need at least 2 mentions
                tropes_found.append(trope)

        return tropes_found

    def create_training_dataset(self, episodes: List[SitcomEpisode],
                              output_file: str = "mhd_sitcom_dataset.jsonl") -> str:
        """
        Create training dataset from processed episodes

        Args:
            episodes: List of processed sitcom episodes
            output_file: Output file path

        Returns:
            Path to created dataset file
        """
        output_path = self.data_dir / output_file

        self.logger.info(f"Creating training dataset with {len(episodes)} episodes")

        with open(output_path, 'w', encoding='utf-8') as f:
            for episode in episodes:
                for dialogue in episode.dialogues:
                    # Create training sample
                    sample = {
                        'text': dialogue.dialogue,
                        'character': dialogue.character,
                        'context': dialogue.context,
                        'humor_score': dialogue.humor_score,
                        'laugh_count': len(dialogue.laugh_segments),
                        'laugh_intensity': sum(l.intensity for l in dialogue.laugh_segments) / max(len(dialogue.laugh_segments), 1),
                        'sitcom_tropes': episode.sitcom_tropes,
                        'episode_id': episode.episode_id,
                        'metadata': {
                            'season': episode.season,
                            'episode': episode.episode,
                            'character_patterns': episode.character_patterns.get(dialogue.character, {})
                        }
                    }

                    f.write(json.dumps(sample) + '\n')

        self.logger.info(f"Dataset created: {output_path}")
        return str(output_path)

    def analyze_laugh_patterns(self, episodes: List[SitcomEpisode]) -> Dict[str, Any]:
        """
        Analyze laugh track patterns across episodes

        Args:
            episodes: List of processed episodes

        Returns:
            Analysis results with laugh patterns and insights
        """
        self.logger.info("Analyzing laugh patterns across episodes")

        # Collect all laugh segments
        all_laughs = []
        for episode in episodes:
            all_laughs.extend(episode.laugh_tracks)

        if not all_laughs:
            return {'error': 'No laugh segments found'}

        # Analyze timing patterns
        durations = [l.duration for l in all_laughs]
        intensities = [l.intensity for l in all_laughs]

        # Analyze laugh types
        laugh_types = {}
        for laugh in all_laughs:
            laugh_types[laugh.laugh_type] = laugh_types.get(laugh.laugh_type, 0) + 1

        # Analyze temporal patterns
        laugh_intervals = []
        for episode in episodes:
            episode_times = [l.start_time for l in episode.laugh_tracks]
            episode_times.sort()
            for i in range(1, len(episode_times)):
                laugh_intervals.append(episode_times[i] - episode_times[i-1])

        analysis = {
            'total_laughs': len(all_laughs),
            'avg_duration': np.mean(durations),
            'avg_intensity': np.mean(intensities),
            'laugh_type_distribution': laugh_types,
            'avg_laughs_per_minute': len(all_laughs) / (sum(ep.metadata.get('total_dialogues', 0) for ep in episodes) / 10),  # Approximate
            'temporal_patterns': {
                'avg_interval_between_laughs': np.mean(laugh_intervals) if laugh_intervals else 0,
                'peak_laugh_times': self._find_peak_laugh_times(episodes)
            },
            'sitcom_specific_patterns': {
                'character_specific_laughs': self._analyze_character_laugh_patterns(episodes),
                'trope_based_laughs': self._analyze_trope_laugh_patterns(episodes)
            }
        }

        return analysis

    def _find_peak_laugh_times(self, episodes: List[SitcomEpisode]) -> List[str]:
        """Find times with highest laugh density"""
        # Simplified peak detection
        peak_times = []
        for episode in episodes:
            if episode.laugh_tracks:
                # Find period with most laughs
                laugh_times = [l.start_time for l in episode.laugh_tracks]
                laugh_times.sort()

                # Simple sliding window to find peak
                window_size = 60  # 1 minute windows
                max_density = 0
                peak_time = 0

                for i, time in enumerate(laugh_times):
                    window_laughs = sum(1 for t in laugh_times if time <= t < time + window_size)
                    if window_laughs > max_density:
                        max_density = window_laughs
                        peak_time = time

                peak_times.append(f"{episode.episode_id}: {peak_time/60:.1f}min")

        return peak_times

    def _analyze_character_laugh_patterns(self, episodes: List[SitcomEpisode]) -> Dict[str, Any]:
        """Analyze laugh patterns for each character"""
        character_laughs = {}

        for episode in episodes:
            for dialogue in episode.dialogues:
                character = dialogue.character
                if character not in character_laughs:
                    character_laughs[character] = {
                        'total_laughs': 0,
                        'total_intensity': 0.0,
                        'dialogue_count': 0
                    }

                character_laughs[character]['total_laughs'] += len(dialogue.laugh_segments)
                character_laughs[character]['total_intensity'] += sum(l.intensity for l in dialogue.laugh_segments)
                character_laughs[character]['dialogue_count'] += 1

        # Calculate averages
        for character in character_laughs:
            stats = character_laughs[character]
            stats['avg_laughs_per_dialogue'] = stats['total_laughs'] / max(stats['dialogue_count'], 1)
            stats['avg_intensity'] = stats['total_intensity'] / max(stats['total_laughs'], 1)

        return character_laughs

    def _analyze_trope_laugh_patterns(self, episodes: List[SitcomEpisode]) -> Dict[str, Any]:
        """Analyze laugh patterns based on sitcom tropes"""
        trope_laughs = {}

        for episode in episodes:
            for trope in episode.sitcom_tropes:
                if trope not in trope_laughs:
                    trope_laughs[trope] = {'laugh_count': 0, 'intensity_sum': 0.0}

                # Count laughs associated with this trope
                for dialogue in episode.dialogues:
                    if any(keyword in dialogue.dialogue.lower()
                          for keyword in self.sitcom_tropes[trope]):
                        trope_laughs[trope]['laugh_count'] += len(dialogue.laugh_segments)
                        trope_laughs[trope]['intensity_sum'] += sum(l.intensity for l in dialogue.laugh_segments)

        return trope_laughs

    def export_for_cross_domain_learning(self, episodes: List[SitcomEpisode],
                                       output_file: str = "mhd_cross_domain.json") -> str:
        """
        Export processed sitcom data for cross-domain learning with stand-up comedy

        Args:
            episodes: Processed sitcom episodes
            output_file: Output file path

        Returns:
            Path to export file
        """
        output_path = self.data_dir / output_file

        cross_domain_data = {
            'domain': 'sitcom',
            'source': 'Big Bang Theory',
            'total_episodes': len(episodes),
            'episodes': []
        }

        for episode in episodes:
            episode_data = {
                'episode_id': episode.episode_id,
                'metadata': episode.metadata,
                'character_patterns': episode.character_patterns,
                'sitcom_tropes': episode.sitcom_tropes,
                'dialogues': [
                    {
                        'text': d.dialogue,
                        'character': d.character,
                        'humor_score': d.humor_score,
                        'laugh_data': {
                            'count': len(d.laugh_segments),
                            'avg_intensity': np.mean([l.intensity for l in d.laugh_segments]) if d.laugh_segments else 0,
                            'total_duration': sum(l.duration for l in d.laugh_segments)
                        }
                    }
                    for d in episode.dialogues
                ]
            }
            cross_domain_data['episodes'].append(episode_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cross_domain_data, f, indent=2)

        self.logger.info(f"Cross-domain data exported: {output_path}")
        return str(output_path)

def main():
    """Main function for testing the MHD processor"""
    print("🎭 MHD Sitcom Processor for Big Bang Theory")
    print("=" * 50)

    # Initialize processor
    processor = MHDSitcomProcessor()

    # Example usage (would use real subtitle files in production)
    print("\n📝 Processing sample episode...")

    # Create sample episode data
    sample_episodes = [
        {
            'season': 1,
            'episode': 1,
            'title': 'Pilot',
            'subtitle_file': 'data/bbt_s01e01.srt'  # Would be real file
        }
    ]

    print("\n✅ MHD Sitcom Processor initialized successfully!")
    print("📊 Ready to process Big Bang Theory episodes")
    print("🎯 Key capabilities:")
    print("   - Laugh track extraction and timing")
    print("   - Character-specific humor patterns")
    print("   - Sitcom trope identification")
    print("   - Cross-domain learning integration")

if __name__ == "__main__":
    main()