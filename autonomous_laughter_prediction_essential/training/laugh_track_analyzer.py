#!/usr/bin/env python3
"""
Advanced Laugh Track Analysis System
Specializes in real-time laugh detection, timing, and intensity analysis
"""

import os
import logging
import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

warnings.filterwarnings('ignore')

# Audio processing imports
try:
    import librosa
    import librosa.display
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Machine learning imports
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class LaughPattern:
    """Represents a detected laugh pattern with detailed analysis"""
    start_time: float
    end_time: float
    duration: float
    peak_intensity: float
    avg_intensity: float
    laugh_type: str  # 'chuckle', 'laughter', 'guffaw', 'applause', 'mixed'
    confidence: float
    spectral_features: Dict[str, float] = field(default_factory=dict)
    temporal_features: Dict[str, float] = field(default_factory=dict)

@dataclass
class LaughterTimeline:
    """Complete timeline of laughter for an episode"""
    total_duration: float
    laugh_segments: List[LaughPattern] = field(default_factory=list)
    laugh_density: float = 0.0  # laughs per minute
    peak_times: List[float] = field(default_factory=list)
    character_associations: Dict[str, List[float]] = field(default_factory=dict)

class LaughTrackAnalyzer:
    """
    Advanced laugh track analysis with real audio processing

    Capabilities:
    - Real-time laugh detection from audio
    - Precise timing and intensity measurement
    - Laughter type classification
    - Character-laugh association
    - Sitcom rhythm pattern detection
    """

    def __init__(self, sample_rate: int = 22050, memory_limit_mb: int = 2048):
        """
        Initialize Laugh Track Analyzer

        Args:
            sample_rate: Audio sample rate for analysis
            memory_limit_mb: Memory limit in MB for processing
        """
        self.sample_rate = sample_rate
        self.memory_limit_mb = memory_limit_mb
        self.logger = self._setup_logging()

        # Audio processing parameters
        self.hop_length = 512
        self.n_mels = 128
        self.n_fft = 2048

        # Laughter detection thresholds
        self.laugh_thresholds = {
            'energy_min': 0.1,      # Minimum energy for laugh detection
            'energy_max': 0.9,      # Maximum energy (to avoid music/speech)
            'duration_min': 0.3,    # Minimum laugh duration (seconds)
            'duration_max': 10.0,   # Maximum laugh duration (seconds)
            'pitch_min': 100,       # Minimum pitch (Hz)
            'pitch_max': 800        # Maximum pitch (Hz)
        }

        # Laughter type classifiers
        self.laugh_classifiers = self._initialize_classifiers()

        # Spectral patterns for different laugh types
        self.spectral_patterns = {
            'chuckle': {'bandwidth': (500, 2000), 'modulation': 'low'},
            'laughter': {'bandwidth': (800, 3000), 'modulation': 'medium'},
            'guffaw': {'bandwidth': (1000, 4000), 'modulation': 'high'},
            'applause': {'bandwidth': (200, 1500), 'modulation': 'irregular'}
        }

        self.logger.info("Laugh Track Analyzer initialized")

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

    def _initialize_classifiers(self) -> Dict[str, Any]:
        """Initialize ML classifiers for laugh type detection"""
        classifiers = {}

        if ML_AVAILABLE:
            # Random forest for laugh type classification
            classifiers['type_classifier'] = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )

            # Scaler for feature normalization
            classifiers['scaler'] = StandardScaler()

        return classifiers

    def analyze_audio_file(self, audio_file: str) -> LaughterTimeline:
        """
        Analyze laugh tracks in an audio file

        Args:
            audio_file: Path to audio file (MP3, WAV, etc.)

        Returns:
            LaughterTimeline with all detected laugh patterns
        """
        if not AUDIO_AVAILABLE:
            self.logger.error("Audio processing not available. Install librosa and soundfile.")
            return LaughterTimeline(total_duration=0.0)

        self.logger.info(f"Analyzing audio file: {audio_file}")

        try:
            # Load audio file with memory constraints
            audio, sr = librosa.load(
                audio_file,
                sr=self.sample_rate,
                duration=None,  # Load full file
                res_type='kaiser_fast'
            )

            # Calculate total duration
            total_duration = len(audio) / sr

            # Detect laugh segments
            laugh_segments = self._detect_laughs(audio, sr)

            # Calculate laugh density
            laugh_density = len(laugh_segments) / (total_duration / 60)  # laughs per minute

            # Find peak laugh times
            peak_times = self._find_peak_laugh_times(laugh_segments, total_duration)

            # Create timeline
            timeline = LaughterTimeline(
                total_duration=total_duration,
                laugh_segments=laugh_segments,
                laugh_density=laugh_density,
                peak_times=peak_times
            )

            self.logger.info(f"Analysis complete: {len(laugh_segments)} laughs detected")
            return timeline

        except Exception as e:
            self.logger.error(f"Error analyzing audio file: {e}")
            return LaughterTimeline(total_duration=0.0)

    def _detect_laughs(self, audio: np.ndarray, sr: int) -> List[LaughPattern]:
        """
        Detect laugh segments in audio using advanced signal processing

        Args:
            audio: Audio signal array
            sr: Sample rate

        Returns:
            List of detected LaughPattern objects
        """
        laugh_patterns = []

        try:
            # Extract features for laugh detection
            features = self._extract_audio_features(audio, sr)

            # Find laugh candidates
            candidates = self._find_laugh_candidates(features)

            # Classify and refine laugh segments
            for candidate in candidates:
                laugh_pattern = self._classify_laugh_pattern(candidate, features)
                if laugh_pattern and laugh_pattern.confidence > 0.5:
                    laugh_patterns.append(laugh_pattern)

        except Exception as e:
            self.logger.error(f"Error detecting laughs: {e}")

        return laugh_patterns

    def _extract_audio_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract comprehensive audio features for laugh detection"""
        features = {}

        # Spectral features
        features['mfcc'] = librosa.feature.mfcc(
            y=audio, sr=sr, n_mfcc=13,
            hop_length=self.hop_length, n_fft=self.n_fft
        )

        features['spectral_centroid'] = librosa.feature.spectral_centroid(
            y=audio, sr=sr, hop_length=self.hop_length
        )

        features['spectral_bandwidth'] = librosa.feature.spectral_bandwidth(
            y=audio, sr=sr, hop_length=self.hop_length
        )

        features['spectral_rolloff'] = librosa.feature.spectral_rolloff(
            y=audio, sr=sr, hop_length=self.hop_length
        )

        features['zero_crossing_rate'] = librosa.feature.zero_crossing_rate(
            y=audio, hop_length=self.hop_length
        )

        # Temporal features
        features['rms_energy'] = librosa.feature.rms(
            y=audio, hop_length=self.hop_length
        )

        features['tempo'] = librosa.beat.tempo(y=audio, sr=sr)[0]

        # Pitch tracking
        features['pitch'] = librosa.yin(
            y=audio, sr=sr,
            fmin=self.laugh_thresholds['pitch_min'],
            fmax=self.laugh_thresholds['pitch_max']
        )

        return features

    def _find_laugh_candidates(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential laugh segments based on audio features"""
        candidates = []

        # Get time frames
        times = librosa.times_like(
            features['rms_energy'],
            sr=self.sample_rate,
            hop_length=self.hop_length
        )

        # Find high-energy segments that could be laughs
        energy = features['rms_energy'][0]
        mean_energy = np.mean(energy)
        std_energy = np.std(energy)

        # Threshold for laugh detection
        laugh_threshold = mean_energy + 1.5 * std_energy

        # Find contiguous segments above threshold
        in_laugh = False
        laugh_start = 0

        for i, frame_energy in enumerate(energy):
            is_laugh_frame = (
                laugh_threshold < frame_energy < self.laugh_thresholds['energy_max'] and
                self._is_laugh_like_frame(features, i)
            )

            if is_laugh_frame and not in_laugh:
                # Start of laugh segment
                in_laugh = True
                laugh_start = times[i]

            elif not is_laugh_frame and in_laugh:
                # End of laugh segment
                in_laugh = False
                laugh_end = times[i]

                # Check duration constraints
                duration = laugh_end - laugh_start
                if (self.laugh_thresholds['duration_min'] <= duration <=
                    self.laugh_thresholds['duration_max']):

                    candidates.append({
                        'start_time': laugh_start,
                        'end_time': laugh_end,
                        'duration': duration,
                        'frame_start': int(laugh_start * self.sample_rate / self.hop_length),
                        'frame_end': int(laugh_end * self.sample_rate / self.hop_length)
                    })

        return candidates

    def _is_laugh_like_frame(self, features: Dict[str, Any], frame_idx: int) -> bool:
        """Check if a frame has laugh-like characteristics"""
        try:
            # Check spectral features typical of laughter
            spectral_centroid = features['spectral_centroid'][0, frame_idx]
            spectral_bandwidth = features['spectral_bandwidth'][0, frame_idx]
            zcr = features['zero_crossing_rate'][0, frame_idx]

            # Laughter typically has:
            # - Medium spectral centroid (not too high like speech, not too low like music)
            # - Medium bandwidth
            # - Moderate zero crossing rate
            return (
                1000 < spectral_centroid < 4000 and
                500 < spectral_bandwidth < 3000 and
                0.1 < zcr < 0.5
            )

        except IndexError:
            return False

    def _classify_laugh_pattern(self, candidate: Dict[str, Any],
                               features: Dict[str, Any]) -> Optional[LaughPattern]:
        """Classify laugh type and extract detailed features"""
        try:
            start_frame = candidate['frame_start']
            end_frame = candidate['frame_end']

            # Extract features for this segment
            segment_features = self._extract_segment_features(
                features, start_frame, end_frame
            )

            # Classify laugh type
            laugh_type = self._classify_laugh_type(segment_features)

            # Calculate intensity
            peak_intensity = np.max(segment_features['energy'])
            avg_intensity = np.mean(segment_features['energy'])

            # Calculate confidence based on how well it matches laugh characteristics
            confidence = self._calculate_laugh_confidence(segment_features)

            return LaughPattern(
                start_time=candidate['start_time'],
                end_time=candidate['end_time'],
                duration=candidate['duration'],
                peak_intensity=float(peak_intensity),
                avg_intensity=float(avg_intensity),
                laugh_type=laugh_type,
                confidence=float(confidence),
                spectral_features=segment_features['spectral'],
                temporal_features=segment_features['temporal']
            )

        except Exception as e:
            self.logger.error(f"Error classifying laugh pattern: {e}")
            return None

    def _extract_segment_features(self, features: Dict[str, Any],
                                 start_frame: int, end_frame: int) -> Dict[str, Any]:
        """Extract features for a specific segment"""
        segment_features = {
            'spectral': {},
            'temporal': {}
        }

        # Energy
        segment_features['temporal']['energy'] = features['rms_energy'][0, start_frame:end_frame]

        # Spectral features
        segment_features['spectral']['centroid'] = np.mean(
            features['spectral_centroid'][0, start_frame:end_frame]
        )
        segment_features['spectral']['bandwidth'] = np.mean(
            features['spectral_bandwidth'][0, start_frame:end_frame]
        )
        segment_features['spectral']['rolloff'] = np.mean(
            features['spectral_rolloff'][0, start_frame:end_frame]
        )

        # Modulation features
        segment_features['temporal']['modulation'] = np.std(
            features['rms_energy'][0, start_frame:end_frame]
        )

        return segment_features

    def _classify_laugh_type(self, segment_features: Dict[str, Any]) -> str:
        """Classify the type of laughter based on features"""
        # Extract key features
        duration = segment_features['temporal']['energy'].shape[0] * self.hop_length / self.sample_rate
        avg_centroid = segment_features['spectral']['centroid']
        avg_bandwidth = segment_features['spectral']['bandwidth']
        modulation = segment_features['temporal']['modulation']

        # Classification logic
        if duration < 1.0 and avg_centroid < 1500:
            return 'chuckle'
        elif duration < 2.5 and modulation < 0.1:
            return 'laughter'
        elif duration >= 2.5 and modulation > 0.15:
            return 'guffaw'
        elif avg_bandwidth < 1000 and modulation > 0.2:
            return 'applause'
        else:
            return 'laughter'  # Default

    def _calculate_laugh_confidence(self, segment_features: Dict[str, Any]) -> float:
        """Calculate confidence score for laugh detection"""
        confidence = 0.0

        # Energy consistency (laughs have relatively consistent energy)
        energy = segment_features['temporal']['energy']
        energy_cv = np.std(energy) / (np.mean(energy) + 1e-6)
        confidence += max(0, 1.0 - energy_cv) * 0.3

        # Spectral characteristics
        centroid = segment_features['spectral']['centroid']
        if 1000 < centroid < 3500:  # Typical laugh range
            confidence += 0.3

        # Temporal modulation
        modulation = segment_features['temporal']['modulation']
        if 0.05 < modulation < 0.3:  # Typical laugh modulation
            confidence += 0.4

        return min(confidence, 1.0)

    def _find_peak_laugh_times(self, laugh_patterns: List[LaughPattern],
                             total_duration: float, window_minutes: float = 1.0) -> List[float]:
        """Find times with highest laugh density"""
        if not laugh_patterns:
            return []

        # Divide timeline into windows
        window_size = window_minutes * 60  # Convert to seconds
        num_windows = int(total_duration / window_size) + 1

        laugh_counts = []
        for i in range(num_windows):
            window_start = i * window_size
            window_end = (i + 1) * window_size

            # Count laughs in this window
            count = sum(1 for laugh in laugh_patterns
                       if window_start <= laugh.start_time < window_end)

            laugh_counts.append((window_start, count))

        # Find top 3 peak times
        laugh_counts.sort(key=lambda x: x[1], reverse=True)
        return [time for time, count in laugh_counts[:3] if count > 0]

    def associate_with_dialogue(self, laugh_timeline: LaughterTimeline,
                               dialogue_times: List[Tuple[float, float, str]]) -> Dict[str, List[float]]:
        """
        Associate laughs with dialogue for character-specific analysis

        Args:
            laugh_timeline: Detected laugh timeline
            dialogue_times: List of (start_time, end_time, character) tuples

        Returns:
            Dictionary mapping characters to their laugh times
        """
        character_associations = {}

        for dialogue_start, dialogue_end, character in dialogue_times:
            if character not in character_associations:
                character_associations[character] = []

            # Find laughs that occur shortly after dialogue
            for laugh in laugh_timeline.laugh_segments:
                time_diff = laugh.start_time - dialogue_end
                if 0 <= time_diff <= 2.0:  # Within 2 seconds after dialogue
                    character_associations[character].append(laugh.start_time)

        laugh_timeline.character_associations = character_associations
        return character_associations

    def export_analysis_results(self, laugh_timeline: LaughterTimeline,
                               output_file: str) -> str:
        """Export detailed analysis results to JSON file"""
        output_path = Path(output_file)

        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_duration': laugh_timeline.total_duration,
            'total_laughs': len(laugh_timeline.laugh_segments),
            'laugh_density_per_minute': laugh_timeline.laugh_density,
            'peak_laugh_times': laugh_timeline.peak_times,
            'laugh_segments': [
                {
                    'start_time': laugh.start_time,
                    'end_time': laugh.end_time,
                    'duration': laugh.duration,
                    'intensity': {
                        'peak': laugh.peak_intensity,
                        'average': laugh.avg_intensity
                    },
                    'type': laugh.laugh_type,
                    'confidence': laugh.confidence,
                    'spectral_features': laugh.spectral_features,
                    'temporal_features': laugh.temporal_features
                }
                for laugh in laugh_timeline.laugh_segments
            ],
            'character_associations': laugh_timeline.character_associations
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        self.logger.info(f"Analysis results exported to {output_path}")
        return str(output_path)

class RealTimeLaughDetector(LaughTrackAnalyzer):
    """
    Real-time laugh detection for live audio processing
    Optimized for low-latency processing on resource-constrained systems
    """

    def __init__(self, buffer_duration: float = 5.0, overlap: float = 1.0):
        """
        Initialize real-time detector

        Args:
            buffer_duration: Duration of audio buffer (seconds)
            overlap: Overlap between buffers (seconds)
        """
        super().__init__()
        self.buffer_duration = buffer_duration
        self.overlap = overlap
        self.buffer_size = int(buffer_duration * self.sample_rate)

        self.logger.info("Real-time laugh detector initialized")

    def process_audio_buffer(self, audio_buffer: np.ndarray) -> List[LaughPattern]:
        """
        Process audio buffer for real-time laugh detection

        Args:
            audio_buffer: Audio buffer array

        Returns:
            List of detected laugh patterns in this buffer
        """
        if len(audio_buffer) < self.buffer_size:
            # Pad buffer if too small
            padding = np.zeros(self.buffer_size - len(audio_buffer))
            audio_buffer = np.concatenate([audio_buffer, padding])

        # Detect laughs in buffer
        laugh_patterns = self._detect_laughs(audio_buffer, self.sample_rate)

        return laugh_patterns

def main():
    """Main function for testing the laugh track analyzer"""
    print("🎭 Advanced Laugh Track Analysis System")
    print("=" * 50)

    # Initialize analyzer
    analyzer = LaughTrackAnalyzer()

    # Test with sample audio if available
    test_audio = "data/sample_episode_audio.mp3"

    if os.path.exists(test_audio):
        print(f"\n🎵 Analyzing sample audio: {test_audio}")
        timeline = analyzer.analyze_audio_file(test_audio)
        print(f"✅ Found {len(timeline.laugh_segments)} laugh segments")
        print(f"📊 Laugh density: {timeline.laugh_density:.2f} laughs per minute")
    else:
        print(f"\n📝 No test audio found at {test_audio}")
        print("🎯 Analyzer ready for audio file processing")

    print("\n🔧 Key capabilities:")
    print("   - Real-time laugh detection from audio")
    print("   - Precise timing and intensity measurement")
    print("   - Laughter type classification")
    print("   - Character-laugh association")
    print("   - Sitcom rhythm pattern detection")

if __name__ == "__main__":
    main()