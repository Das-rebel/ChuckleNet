#!/usr/bin/env python3
"""
Dialogue-Laugh Alignment System for Sitcom Humor Analysis
Specializes in character-specific humor patterns and laugh-track correlation
"""

import os
import logging
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json

warnings.filterwarnings('ignore')

# NLP for text analysis
try:
    import re
    from typing import Set
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Machine learning for pattern recognition
try:
    from sklearn.cluster import DBSCAN
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class CharacterHumorProfile:
    """Comprehensive humor profile for a sitcom character"""
    character_name: str
    total_dialogues: int = 0
    laugh_trigger_count: int = 0
    laugh_frequency: float = 0.0  # laughs per dialogue
    avg_laugh_intensity: float = 0.0
    avg_laugh_duration: float = 0.0

    # Humor themes and patterns
    humor_themes: Dict[str, int] = field(default_factory=dict)
    linguistic_patterns: Dict[str, int] = field(default_factory=dict)

    # Timing patterns
    peak_comedy_times: List[float] = field(default_factory=list)
    laugh_response_time: float = 0.0  # avg seconds to laugh response

    # Character-specific humor analysis
    comedy_style: str = "unknown"  # 'sarcastic', 'physical', 'intellectual', 'self-deprecating'
    audience_connection: float = 0.0  # how well audience connects with character

@dataclass
class DialogueLaughPair:
    """Represents a dialogue-laugh pair with detailed analysis"""
    dialogue_text: str
    character: str
    dialogue_start: float
    dialogue_end: float
    laugh_start: float
    laugh_end: float
    laugh_intensity: float
    laugh_duration: float
    response_time: float  # time from dialogue end to laugh start
    humor_features: Dict[str, float] = field(default_factory=dict)
    context_analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SitcomRhythmPattern:
    """Represents the overall rhythm and timing pattern of a sitcom"""
    avg_laughs_per_minute: float = 0.0
    laugh_interval_distribution: Dict[str, float] = field(default_factory=dict)
    peak_comedy_zones: List[Tuple[float, float]] = field(default_factory=list)  # (start, end)
    timing_patterns: Dict[str, float] = field(default_factory=dict)
    ensemble_dynamics: Dict[str, Dict[str, float]] = field(default_factory=dict)

class DialogueLaughAligner:
    """
    Advanced dialogue-laugh alignment system for character-specific humor analysis

    Capabilities:
    - Precise dialogue-laugh temporal alignment
    - Character humor profile generation
    - Sitcom rhythm pattern detection
    - Ensemble cast dynamics analysis
    - Cross-episode learning and adaptation
    """

    def __init__(self, time_tolerance: float = 2.0, min_confidence: float = 0.6):
        """
        Initialize Dialogue-Laugh Aligner

        Args:
            time_tolerance: Max seconds between dialogue and laugh for association
            min_confidence: Minimum confidence score for valid pairs
        """
        self.time_tolerance = time_tolerance
        self.min_confidence = min_confidence
        self.logger = self._setup_logging()

        # Character interaction patterns
        self.character_interactions = defaultdict(lambda: {
            'dialogue_exchanges': 0,
            'laugh_collaborations': 0,
            'timing_patterns': []
        })

        # Sitcom-specific humor patterns
        self.sitcom_patterns = {
            'setup_punchline': r'.*?(setup|buildup|premise).*?(punchline|callback|payoff)',
            'callback_joke': r'.*?(earlier|mentioned|said|remember).*?',
            'rule_of_three': r'(?:(.*?){2}.*?)(.*?).*?(.*?).*?',
            'misunderstanding': r'.*?(wrong|misunderstand|confused|mistake).*?'
        }

        # Linguistic humor markers
        self.humor_markers = {
            'incongruity': ['but', 'however', 'although', 'unexpectedly', 'surprisingly'],
            'exaggeration': ['literally', 'completely', 'absolutely', 'totally', 'exactly'],
            'irony': ['ironic', 'ironically', 'sarcastic', 'supposedly'],
            'wordplay': ['pun', 'play on words', 'double meaning', 'literally'],
            'timing': ['perfect timing', 'just', 'exactly', 'finally']
        }

        # Comedy style classifiers
        self.comedy_styles = {
            'sarcastic': ['sarcasm', 'sarcastic', 'ironic', 'mocking'],
            'intellectual': ['smart', 'genius', 'science', 'physics', 'math', 'theory'],
            'physical': ['falls', 'hits', 'slapstick', 'physical', 'action'],
            'self_deprecating': ['stupid', 'idiot', 'failure', 'loser', 'pathetic']
        }

        self.logger.info("Dialogue-Laugh Aligner initialized")

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

    def align_dialogues_with_laughs(self,
                                   dialogues: List[Dict[str, Any]],
                                   laugh_segments: List[Dict[str, Any]]) -> List[DialogueLaughPair]:
        """
        Align dialogue segments with laugh tracks for humor analysis

        Args:
            dialogues: List of dialogue dictionaries with timing and text
            laugh_segments: List of laugh segments with timing and intensity

        Returns:
            List of DialogueLaughPair objects with detailed analysis
        """
        aligned_pairs = []

        for dialogue in dialogues:
            # Find the best matching laugh for this dialogue
            best_laugh = self._find_best_matching_laugh(dialogue, laugh_segments)

            if best_laugh and self._validate_pair(dialogue, best_laugh):
                # Create detailed pair analysis
                pair = self._create_dialogue_laugh_pair(dialogue, best_laugh)
                if pair and pair.laugh_intensity >= self.min_confidence:
                    aligned_pairs.append(pair)

        self.logger.info(f"Aligned {len(aligned_pairs)} dialogue-laugh pairs")
        return aligned_pairs

    def _find_best_matching_laugh(self, dialogue: Dict[str, Any],
                                 laugh_segments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the laugh segment that best matches this dialogue"""
        dialogue_end = dialogue['end_time']

        best_laugh = None
        best_score = 0

        for laugh in laugh_segments:
            # Calculate response time
            response_time = laugh['start_time'] - dialogue_end

            # Score based on timing and laugh quality
            if 0 <= response_time <= self.time_tolerance:
                # Optimal response time is 0.5-1.5 seconds
                timing_score = self._calculate_timing_score(response_time)

                # Consider laugh intensity
                intensity_score = laugh.get('intensity', 0.5)

                # Combined score
                combined_score = 0.7 * timing_score + 0.3 * intensity_score

                if combined_score > best_score:
                    best_score = combined_score
                    best_laugh = laugh

        return best_laugh

    def _calculate_timing_score(self, response_time: float) -> float:
        """Calculate score based on laugh response time"""
        # Optimal timing is 0.5-1.5 seconds
        if 0.5 <= response_time <= 1.5:
            return 1.0
        elif 0.3 <= response_time <= 2.0:
            return 0.8
        elif 0 <= response_time <= self.time_tolerance:
            return 0.5
        else:
            return 0.0

    def _validate_pair(self, dialogue: Dict[str, Any], laugh: Dict[str, Any]) -> bool:
        """Validate that a dialogue-laugh pair makes sense"""
        # Check timing
        response_time = laugh['start_time'] - dialogue['end_time']
        if response_time < 0 or response_time > self.time_tolerance:
            return False

        # Check dialogue has content
        if not dialogue.get('text', '').strip():
            return False

        # Check laugh has minimum duration
        if laugh.get('duration', 0) < 0.3:
            return False

        return True

    def _create_dialogue_laugh_pair(self, dialogue: Dict[str, Any],
                                   laugh: Dict[str, Any]) -> DialogueLaughPair:
        """Create a detailed dialogue-laugh pair with feature extraction"""
        response_time = laugh['start_time'] - dialogue['end_time']

        # Extract humor features from dialogue
        humor_features = self._extract_humor_features(dialogue['text'])

        # Analyze context
        context_analysis = self._analyze_context(dialogue)

        return DialogueLaughPair(
            dialogue_text=dialogue['text'],
            character=dialogue.get('character', 'unknown'),
            dialogue_start=dialogue['start_time'],
            dialogue_end=dialogue['end_time'],
            laugh_start=laugh['start_time'],
            laugh_end=laugh['end_time'],
            laugh_intensity=laugh.get('intensity', 0.5),
            laugh_duration=laugh.get('duration', 0.0),
            response_time=response_time,
            humor_features=humor_features,
            context_analysis=context_analysis
        )

    def _extract_humor_features(self, dialogue_text: str) -> Dict[str, float]:
        """Extract humor-related features from dialogue text"""
        features = {}
        text_lower = dialogue_text.lower()

        # Check for humor markers
        for marker_type, markers in self.humor_markers.items():
            count = sum(1 for marker in markers if marker in text_lower)
            features[f'has_{marker_type}'] = float(count > 0)
            features[f'{marker_type}_count'] = float(count)

        # Check for comedy patterns
        for pattern_name, pattern in self.sitcom_patterns.items():
            features[f'has_{pattern_name}'] = float(bool(re.search(pattern, text_lower)))

        # Linguistic features
        features['word_count'] = float(len(dialogue_text.split()))
        features['has_question'] = float('?' in dialogue_text)
        features['has_exclamation'] = float('!' in dialogue_text)
        features['avg_word_length'] = np.mean([len(word) for word in dialogue_text.split()]) if dialogue_text.split() else 0.0

        return features

    def _analyze_context(self, dialogue: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the context of a dialogue"""
        context = {
            'position_in_scene': dialogue.get('position', 'unknown'),
            'speaking_order': dialogue.get('order', 0),
            'scene_duration': dialogue.get('scene_duration', 0.0)
        }

        return context

    def generate_character_profiles(self,
                                   aligned_pairs: List[DialogueLaughPair]) -> Dict[str, CharacterHumorProfile]:
        """
        Generate comprehensive humor profiles for each character

        Args:
            aligned_pairs: List of aligned dialogue-laugh pairs

        Returns:
            Dictionary mapping character names to their humor profiles
        """
        character_profiles = {}

        # Group pairs by character
        character_pairs = defaultdict(list)
        for pair in aligned_pairs:
            character_pairs[pair.character].append(pair)

        # Generate profile for each character
        for character, pairs in character_pairs.items():
            profile = self._create_character_profile(character, pairs)
            character_profiles[character] = profile

        self.logger.info(f"Generated {len(character_profiles)} character profiles")
        return character_profiles

    def _create_character_profile(self, character: str,
                                 pairs: List[DialogueLaughPair]) -> CharacterHumorProfile:
        """Create a detailed humor profile for a character"""
        profile = CharacterHumorProfile(character_name=character)

        # Basic statistics
        profile.total_dialogues = len(pairs)
        profile.laugh_trigger_count = len(pairs)

        if pairs:
            profile.laugh_frequency = 1.0  # All pairs have laughs by definition
            profile.avg_laugh_intensity = np.mean([p.laugh_intensity for p in pairs])
            profile.avg_laugh_duration = np.mean([p.laugh_duration for p in pairs])
            profile.laugh_response_time = np.mean([p.response_time for p in pairs])

            # Extract humor themes
            profile.humor_themes = self._extract_character_themes(pairs)

            # Identify linguistic patterns
            profile.linguistic_patterns = self._extract_linguistic_patterns(pairs)

            # Find peak comedy times
            profile.peak_comedy_times = [p.dialogue_end for p in pairs
                                        if p.laugh_intensity > np.percentile([p.laugh_intensity for p in pairs], 75)]

            # Determine comedy style
            profile.comedy_style = self._determine_comedy_style(pairs)

            # Calculate audience connection
            profile.audience_connection = self._calculate_audience_connection(pairs)

        return profile

    def _extract_character_themes(self, pairs: List[DialogueLaughPair]) -> Dict[str, int]:
        """Extract recurring humor themes for a character"""
        themes = defaultdict(int)

        for pair in pairs:
            # Analyze themes in dialogue text
            text_lower = pair.dialogue_text.lower()

            # Check for theme indicators
            if any(word in text_lower for word in ['science', 'physics', 'math', 'research']):
                themes['intellectual'] += 1
            if any(word in text_lower for word in ['stupid', 'dumb', 'idiot', 'crazy']):
                themes['insult'] += 1
            if any(word in text_lower for word in ['dating', 'relationship', 'girlfriend', 'boyfriend']):
                themes['romance'] += 1
            if any(word in text_lower for word in ['awkward', 'embarrassing', 'uncomfortable']):
                themes['social_awkwardness'] += 1

        return dict(themes)

    def _extract_linguistic_patterns(self, pairs: List[DialogueLaughPair]) -> Dict[str, int]:
        """Extract linguistic patterns for a character"""
        patterns = defaultdict(int)

        for pair in pairs:
            text = pair.dialogue_text.lower()

            # Check for question patterns
            if '?' in text:
                patterns['uses_questions'] += 1

            # Check for exclamation patterns
            if '!' in text:
                patterns['uses_exclamations'] += 1

            # Check for pauses (indicated by commas or periods)
            if ',' in text:
                patterns['uses_pauses'] += 1

            # Check for sentence complexity
            words = text.split()
            if len(words) > 15:
                patterns['complex_sentences'] += 1
            elif len(words) < 5:
                patterns['short_sentences'] += 1

        return dict(patterns)

    def _determine_comedy_style(self, pairs: List[DialogueLaughPair]) -> str:
        """Determine the primary comedy style for a character"""
        style_scores = defaultdict(int)

        for pair in pairs:
            text_lower = pair.dialogue_text.lower()

            for style, indicators in self.comedy_styles.items():
                if any(indicator in text_lower for indicator in indicators):
                    style_scores[style] += 1

        if style_scores:
            return max(style_scores.items(), key=lambda x: x[1])[0]
        return 'conversational'

    def _calculate_audience_connection(self, pairs: List[DialogueLaughPair]) -> float:
        """Calculate how well the audience connects with this character"""
        if not pairs:
            return 0.0

        # Factors: laugh intensity, consistency, timing
        avg_intensity = np.mean([p.laugh_intensity for p in pairs])
        intensity_variance = np.var([p.laugh_intensity for p in pairs])

        # Higher intensity and lower variance = better connection
        connection_score = avg_intensity * (1 - intensity_variance / (avg_intensity + 0.1))
        return min(max(connection_score, 0.0), 1.0)

    def analyze_sitcom_rhythm(self,
                             aligned_pairs: List[DialogueLaughPair],
                             episode_duration: float) -> SitcomRhythmPattern:
        """
        Analyze the overall rhythm and timing patterns of the sitcom

        Args:
            aligned_pairs: List of aligned dialogue-laugh pairs
            episode_duration: Total duration of the episode in seconds

        Returns:
            SitcomRhythmPattern with detailed rhythm analysis
        """
        rhythm = SitcomRhythmPattern()

        if not aligned_pairs:
            return rhythm

        # Calculate basic rhythm metrics
        rhythm.avg_laughs_per_minute = len(aligned_pairs) / (episode_duration / 60)

        # Analyze laugh intervals
        laugh_times = [p.laugh_start for p in aligned_pairs]
        laugh_times.sort()

        intervals = []
        for i in range(1, len(laugh_times)):
            interval = laugh_times[i] - laugh_times[i-1]
            intervals.append(interval)

        if intervals:
            # Classify intervals
            rhythm.laugh_interval_distribution = {
                'very_short': sum(1 for i in intervals if i < 2.0),
                'short': sum(1 for i in intervals if 2.0 <= i < 5.0),
                'medium': sum(1 for i in intervals if 5.0 <= i < 10.0),
                'long': sum(1 for i in intervals if i >= 10.0)
            }

        # Find peak comedy zones (periods with high laugh density)
        rhythm.peak_comedy_zones = self._find_peak_comedy_zones(aligned_pairs, episode_duration)

        # Analyze timing patterns
        rhythm.timing_patterns = self._analyze_timing_patterns(aligned_pairs)

        # Analyze ensemble dynamics
        rhythm.ensemble_dynamics = self._analyze_ensemble_dynamics(aligned_pairs)

        return rhythm

    def _find_peak_comedy_zones(self, pairs: List[DialogueLaughPair],
                               duration: float, window_minutes: float = 2.0) -> List[Tuple[float, float]]:
        """Find time periods with highest comedy density"""
        window_size = window_minutes * 60  # Convert to seconds
        num_windows = int(duration / window_size) + 1

        laugh_counts = []
        for i in range(num_windows):
            window_start = i * window_size
            window_end = (i + 1) * window_size

            # Count laughs in this window
            count = sum(1 for pair in pairs
                       if window_start <= pair.dialogue_end < window_end)

            laugh_counts.append((window_start, window_end, count))

        # Get top 3 windows
        laugh_counts.sort(key=lambda x: x[2], reverse=True)
        return [(start, end) for start, end, count in laugh_counts[:3] if count > 0]

    def _analyze_timing_patterns(self, pairs: List[DialogueLaughPair]) -> Dict[str, float]:
        """Analyze timing patterns in laugh responses"""
        patterns = {}

        response_times = [p.response_time for p in pairs]
        if response_times:
            patterns['avg_response_time'] = np.mean(response_times)
            patterns['median_response_time'] = np.median(response_times)
            patterns['std_response_time'] = np.std(response_times)

            # Categorize response times
            patterns['quick_responses'] = sum(1 for t in response_times if t < 1.0)
            patterns['optimal_responses'] = sum(1 for t in response_times if 1.0 <= t <= 2.0)
            patterns['delayed_responses'] = sum(1 for t in response_times if t > 2.0)

        return patterns

    def _analyze_ensemble_dynamics(self, pairs: List[DialogueLaughPair]) -> Dict[str, Dict[str, float]]:
        """Analyze how different characters work together"""
        dynamics = defaultdict(lambda: {
            'individual_laughs': 0,
            'total_intensity': 0.0,
            'avg_response_time': 0.0
        })

        # Group by character
        character_pairs = defaultdict(list)
        for pair in pairs:
            character_pairs[pair.character].append(pair)

        # Analyze each character's contribution
        for character, char_pairs in character_pairs.items():
            dynamics[character]['individual_laughs'] = len(char_pairs)
            dynamics[character]['total_intensity'] = sum(p.laugh_intensity for p in char_pairs)
            dynamics[character]['avg_response_time'] = np.mean([p.response_time for p in char_pairs])

        return dict(dynamics)

    def export_profiles(self, profiles: Dict[str, CharacterHumorProfile],
                       output_file: str) -> str:
        """Export character profiles to JSON file"""
        output_path = Path(output_file)

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_characters': len(profiles),
            'profiles': {}
        }

        for character, profile in profiles.items():
            export_data['profiles'][character] = {
                'character_name': profile.character_name,
                'total_dialogues': profile.total_dialogues,
                'laugh_frequency': profile.laugh_frequency,
                'avg_laugh_intensity': profile.avg_laugh_intensity,
                'avg_laugh_duration': profile.avg_laugh_duration,
                'humor_themes': profile.humor_themes,
                'linguistic_patterns': profile.linguistic_patterns,
                'comedy_style': profile.comedy_style,
                'audience_connection': profile.audience_connection,
                'laugh_response_time': profile.laugh_response_time
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        self.logger.info(f"Character profiles exported to {output_path}")
        return str(output_path)

def main():
    """Main function for testing the dialogue-laugh aligner"""
    print("🎭 Dialogue-Laugh Alignment System")
    print("=" * 50)

    # Initialize aligner
    aligner = DialogueLaughAligner()

    # Create sample data for testing
    sample_dialogues = [
        {
            'text': 'That is precisely what I was trying to explain!',
            'character': 'sheldon_cooper',
            'start_time': 10.5,
            'end_time': 14.2
        },
        {
            'text': 'Oh, sweetie, nobody understands what you are saying.',
            'character': 'penny',
            'start_time': 14.5,
            'end_time': 17.8
        }
    ]

    sample_laughs = [
        {
            'start_time': 14.5,
            'end_time': 16.0,
            'duration': 1.5,
            'intensity': 0.8
        },
        {
            'start_time': 18.0,
            'end_time': 20.5,
            'duration': 2.5,
            'intensity': 0.9
        }
    ]

    print("\n🔗 Testing dialogue-laugh alignment...")
    aligned_pairs = aligner.align_dialogues_with_laughs(sample_dialogues, sample_laughs)
    print(f"✅ Aligned {len(aligned_pairs)} dialogue-laugh pairs")

    if aligned_pairs:
        print("\n📊 Sample aligned pair:")
        pair = aligned_pairs[0]
        print(f"   Character: {pair.character}")
        print(f"   Dialogue: {pair.dialogue_text[:50]}...")
        print(f"   Laugh intensity: {pair.laugh_intensity:.2f}")
        print(f"   Response time: {pair.response_time:.2f}s")

    print("\n🎯 Key capabilities:")
    print("   - Precise dialogue-laugh temporal alignment")
    print("   - Character humor profile generation")
    print("   - Sitcom rhythm pattern detection")
    print("   - Ensemble cast dynamics analysis")

if __name__ == "__main__":
    main()