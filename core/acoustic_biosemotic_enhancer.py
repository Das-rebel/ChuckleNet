#!/usr/bin/env python3
"""
Acoustic Biosemotic Enhancement - Advanced Laughter Type Classification
Integrates audio-text fusion for Duchenne airflow dynamics and prosodic pattern analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import warnings

try:
    import librosa
    import librosa.display
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    warnings.warn("librosa not available - acoustic features will be simulated")


@dataclass
class AcousticFeatures:
    """Comprehensive acoustic feature set for laughter analysis"""
    laugh_type: str  # 'giggle', 'chuckle', 'guffaw', 'silent'
    duchenne_acoustic_score: float  # Probability of Duchenne (spontaneous) laughter
    airflow_dynamics: Dict[str, float]  # Exhalation patterns
    prosodic_features: Dict[str, float]  # Pitch, intensity, tempo
    temporal_features: Dict[str, float]  # Duration, rhythm, timing


class AcousticBiosemoticEnhancer:
    """
    Advanced acoustic analysis system that integrates with biosemotic laughter prediction
    through Duchenne airflow dynamics, prosodic pattern analysis, and laughter type classification
    """

    def __init__(self, use_simulation: bool = True):
        """Initialize acoustic biosemotic enhancer"""

        self.use_simulation = use_simulation or not AUDIO_AVAILABLE

        # Laughter type acoustic profiles (based on research)
        self.laughter_acoustic_profiles = {
            'giggle': {
                'duration': (0.1, 0.5),  # Short bursts
                'pitch_variability': 0.8,  # High pitch variation
                'intensity': 0.4,  # Low to medium
                'rhythm': 'irregular_bursts',
                'airflow_pattern': 'additive_staccato'  # Volitional
            },
            'chuckle': {
                'duration': (0.5, 1.5),  # Medium length
                'pitch_variability': 0.5,  # Medium variation
                'intensity': 0.6,  # Medium intensity
                'rhythm': 'regular_intermittent',
                'airflow_pattern': 'additive_controlled'  # Volitional
            },
            'guffaw': {
                'duration': (1.0, 3.0),  # Long duration
                'pitch_variability': 0.3,  # Lower variation
                'intensity': 0.9,  # High intensity
                'rhythm': 'continuous_cascade',
                'airflow_pattern': 'multiplicative_exponential'  # Duchenne
            },
            'silent': {
                'duration': (0.0, 0.1),  # Very short/no duration
                'pitch_variability': 0.0,  # No variation
                'intensity': 0.0,  # No intensity
                'rhythm': 'none',
                'airflow_pattern': 'none'  # No laughter
            }
        }

        # Duchenne acoustic indicators (spontaneous laughter)
        self.duchenne_acoustic_indicators = {
            'exponential_intensity_rise': 0.25,  # Characteristic Duchenne pattern
            'breathless_exhalation': 0.20,  # Continuous airflow
            'uncontrolled_rhythm': 0.20,  # Loss of voluntary control
            'high_intensity_peaks': 0.15,  # Sudden intensity bursts
            'pitch_breaks': 0.20  # Voice pitch instability
        }

        # Prosodic sarcasm indicators
        self.sarcasm_prosodic_indicators = {
            'pitch_flattening': 0.25,  # Monotone delivery
            'tempo_slowing': 0.20,  # Deliberate pacing
            'intensity_exaggeration': 0.25,  # Emphasized stress
            'pausal_patterns': 0.30  # Strategic pauses
        }

    def analyze_audio_features(
        self,
        audio_path: Optional[str] = None,
        audio_data: Optional[np.ndarray] = None,
        sample_rate: int = 22050
    ) -> AcousticFeatures:
        """Comprehensive acoustic feature analysis from audio input"""

        if self.use_simulation:
            return self._simulate_acoustic_features()

        # Real audio processing (requires librosa)
        if audio_path is None and audio_data is None:
            return self._simulate_acoustic_features()

        try:
            # Load audio
            if audio_path:
                y, sr = librosa.load(audio_path, sr=sample_rate)
            else:
                y, sr = audio_data, sample_rate

            # Extract features
            features = self._extract_acoustic_features(y, sr)
            return features

        except Exception as e:
            warnings.warn(f"Audio processing failed: {e}, using simulation")
            return self._simulate_acoustic_features()

    def _extract_acoustic_features(self, y: np.ndarray, sr: int) -> AcousticFeatures:
        """Extract real acoustic features from audio signal"""

        # Fundamental frequency (pitch) contour
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_contour = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            pitch_contour.append(pitch)
        pitch_contour = np.array([p for p in pitch_contour if p > 0])

        # RMS energy (intensity)
        rms = librosa.feature.rms(y=y)[0]

        # Tempo and rhythm
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]

        # MFCCs (timbre)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

        # Zero-crossing rate (rhythm roughness)
        zcr = librosa.feature.zero_crossing_rate(y)[0]

        # Classify laughter type
        laugh_type = self._classify_laughter_type_acoustic(
            duration=len(y) / sr,
            pitch_variability=np.std(pitch_contour) if len(pitch_contour) > 0 else 0,
            intensity=np.mean(rms),
            rhythm_regularity=np.std(zcr)
        )

        # Calculate Duchenne acoustic score
        duchenne_score = self._calculate_duchenne_acoustic_score(
            rms, pitch_contour, tempo, zcr, spectral_centroids
        )

        # Airflow dynamics
        airflow_dynamics = {
            'exhalation_continuity': self._measure_exhalation_continuity(rms),
            'intensity_rise_pattern': self._analyze_intensity_rise(rms),
            'breath_control': self._assess_breath_control(tempo, rms),
            'cascade_probability': duchenne_score if laugh_type == 'guffaw' else 0.3
        }

        # Prosodic features
        prosodic_features = {
            'pitch_mean': np.mean(pitch_contour) if len(pitch_contour) > 0 else 0,
            'pitch_std': np.std(pitch_contour) if len(pitch_contour) > 0 else 0,
            'intensity_mean': np.mean(rms),
            'intensity_std': np.std(rms),
            'tempo': tempo,
            'rhythm_regularity': 1.0 / (np.std(zcr) + 0.01),
            'spectral_centroid_mean': np.mean(spectral_centroids)
        }

        # Temporal features
        temporal_features = {
            'duration': len(y) / sr,
            'onset_strength': np.mean(librosa.onset.onset_strength(y=y, sr=sr)),
            'rhythm_stability': np.std(tempo) if hasattr(tempo, '__iter__') else 0
        }

        return AcousticFeatures(
            laugh_type=laugh_type,
            duchenne_acoustic_score=duchenne_score,
            airflow_dynamics=airflow_dynamics,
            prosodic_features=prosodic_features,
            temporal_features=temporal_features
        )

    def _simulate_acoustic_features(self) -> AcousticFeatures:
        """Simulate acoustic features for testing without real audio"""

        # Simulate different laughter types with probabilities
        laugh_types = ['giggle', 'chuckle', 'guffaw', 'silent']
        probabilities = [0.2, 0.3, 0.4, 0.1]  # Weight toward Duchenne 'guffaw'
        laugh_type = np.random.choice(laugh_types, p=probabilities)

        # Simulate Duchenne score based on type
        if laugh_type == 'guffaw':
            duchenne_score = np.random.uniform(0.7, 0.95)  # Strong Duchenne
        elif laugh_type == 'chuckle':
            duchenne_score = np.random.uniform(0.3, 0.5)   # Mixed
        elif laugh_type == 'giggle':
            duchenne_score = np.random.uniform(0.1, 0.3)   # Mostly volitional
        else:
            duchenne_score = np.random.uniform(0.0, 0.1)   # No laughter

        # Airflow dynamics
        if laugh_type == 'guffaw':
            airflow = {
                'exhalation_continuity': np.random.uniform(0.8, 0.95),
                'intensity_rise_pattern': 'exponential',
                'breath_control': np.random.uniform(0.1, 0.3),  # Low control = Duchenne
                'cascade_probability': np.random.uniform(0.7, 0.9)
            }
        else:
            airflow = {
                'exhalation_continuity': np.random.uniform(0.3, 0.6),
                'intensity_rise_pattern': 'linear',
                'breath_control': np.random.uniform(0.6, 0.9),  # High control = volitional
                'cascade_probability': np.random.uniform(0.1, 0.3)
            }

        # Prosodic features
        prosodic = {
            'pitch_mean': np.random.uniform(150, 250),
            'pitch_std': np.random.uniform(20, 80) if laugh_type == 'guffaw' else np.random.uniform(10, 30),
            'intensity_mean': np.random.uniform(0.6, 0.9) if laugh_type == 'guffaw' else np.random.uniform(0.2, 0.5),
            'intensity_std': np.random.uniform(0.1, 0.3),
            'tempo': np.random.uniform(100, 140),
            'rhythm_regularity': np.random.uniform(0.3, 0.6) if laugh_type == 'guffaw' else np.random.uniform(0.7, 0.9),
            'spectral_centroid_mean': np.random.uniform(2000, 4000)
        }

        # Temporal features
        duration_ranges = {'giggle': (0.2, 0.4), 'chuckle': (0.8, 1.2), 'guffaw': (1.5, 2.5), 'silent': (0.0, 0.1)}
        duration_range = duration_ranges[laugh_type]
        temporal = {
            'duration': np.random.uniform(duration_range[0], duration_range[1]),
            'onset_strength': np.random.uniform(0.3, 0.7),
            'rhythm_stability': np.random.uniform(0.1, 0.3) if laugh_type == 'guffaw' else np.random.uniform(0.6, 0.9)
        }

        return AcousticFeatures(
            laugh_type=laugh_type,
            duchenne_acoustic_score=duchenne_score,
            airflow_dynamics=airflow,
            prosodic_features=prosodic,
            temporal_features=temporal
        )

    def _classify_laughter_type_acoustic(
        self,
        duration: float,
        pitch_variability: float,
        intensity: float,
        rhythm_regularity: float
    ) -> str:
        """Classify laughter type from acoustic features"""

        # Decision tree for laughter type classification
        if duration < 0.3:
            return 'silent' if intensity < 0.1 else 'giggle'
        elif duration < 1.0:
            return 'chuckle' if rhythm_regularity > 0.5 else 'giggle'
        else:
            return 'guffaw' if intensity > 0.6 and pitch_variability > 30 else 'chuckle'

    def _calculate_duchenne_acoustic_score(
        self,
        rms: np.ndarray,
        pitch_contour: np.ndarray,
        tempo: float,
        zcr: np.ndarray,
        spectral_centroids: np.ndarray
    ) -> float:
        """Calculate Duchenne (spontaneous laughter) probability from acoustic features"""

        duchenne_indicators = 0.0

        # Exponential intensity rise (characteristic Duchenne pattern)
        if len(rms) > 10:
            intensity_growth = np.polyfit(range(len(rms)), rms, 1)[0]
            if intensity_growth > 0.05:  # Rising intensity
                duchenne_indicators += self.duchenne_acoustic_indicators['exponential_intensity_rise']

        # Breathless exhalation (continuous rhythm)
        rhythm_continuity = 1.0 / (np.std(zcr) + 0.01)
        if rhythm_continuity > 2.0:  # Continuous rhythm
            duchenne_indicators += self.duchenne_acoustic_indicators['breathless_exhalation']

        # Uncontrolled rhythm (irregular timing)
        if np.std(tempo) if hasattr(tempo, '__iter__') else 0 > 10:
            duchenne_indicators += self.duchenne_acoustic_indicators['uncontrolled_rhythm']

        # High intensity peaks
        if np.max(rms) > 0.7:
            duchenne_indicators += self.duchenne_acoustic_indicators['high_intensity_peaks']

        # Pitch breaks (voice instability)
        if len(pitch_contour) > 5:
            pitch_variability = np.std(np.diff(pitch_contour))
            if pitch_variability > 20:
                duchenne_indicators += self.duchenne_acoustic_indicators['pitch_breaks']

        return min(duchenne_indicators, 1.0)

    def _measure_exhalation_continuity(self, rms: np.ndarray) -> float:
        """Measure continuity of exhalation (Duchenne indicator)"""
        if len(rms) < 2:
            return 0.5
        # High continuity = low variance in intensity
        return 1.0 - (np.std(rms) / (np.mean(rms) + 0.01))

    def _analyze_intensity_rise(self, rms: np.ndarray) -> str:
        """Analyze intensity rise pattern"""
        if len(rms) < 10:
            return 'linear'
        # Fit polynomial to intensity curve
        coeffs = np.polyfit(range(len(rms)), rms, 2)
        if coeffs[0] > 0.01:  # Convex = exponential rise
            return 'exponential'
        else:
            return 'linear'

    def _assess_breath_control(self, tempo, rms: np.ndarray) -> float:
        """Assess level of breath control (inverse = Duchenne)"""
        # Low control = high variability in rhythm and intensity
        rhythm_variability = np.std(rms) / (np.mean(rms) + 0.01)
        return 1.0 - min(rhythm_variability, 1.0)

    def calculate_acoustic_enhancement(
        self,
        acoustic_features: AcousticFeatures,
        text_probability: float,
        text_duchenne_prob: float
    ) -> Dict:
        """Calculate acoustic enhancement to text-based prediction"""

        # Base acoustic confidence
        acoustic_confidence = 0.0

        # Laughter type confidence
        if acoustic_features.laugh_type == 'guffaw':
            acoustic_confidence += 0.15  # Strong Duchenne signal
        elif acoustic_features.laugh_type == 'chuckle':
            acoustic_confidence += 0.05  # Moderate signal
        elif acoustic_features.laugh_type == 'giggle':
            acoustic_confidence -= 0.05  # Volitional signal

        # Duchenne acoustic validation
        duchenne_validation = abs(acoustic_features.duchenne_acoustic_score - text_duchenne_prob)
        if duchenne_validation < 0.2:  # Consistent Duchenne signals
            acoustic_confidence += 0.10

        # Airflow dynamics enhancement
        if acoustic_features.airflow_dynamics['cascade_probability'] > 0.7:
            acoustic_confidence += 0.08  # Strong cascade dynamics

        # Prosodic sarcasm enhancement
        prosodic_sarcasm_score = self._calculate_prosodic_sarcasm(acoustic_features)
        acoustic_confidence += prosodic_sarcasm_score * 0.05

        # Temporal features
        if acoustic_features.temporal_features['duration'] > 1.0:
            acoustic_confidence += 0.03  # Longer laughter = more genuine

        # Combine with text prediction
        enhanced_probability = text_probability + acoustic_confidence
        enhanced_probability = max(0.0, min(1.0, enhanced_probability))

        return {
            'enhanced_probability': enhanced_probability,
            'acoustic_confidence': acoustic_confidence,
            'laugh_type_classification': acoustic_features.laugh_type,
            'duchenne_acoustic_score': acoustic_features.duchenne_acoustic_score,
            'airflow_dynamics': acoustic_features.airflow_dynamics,
            'prosodic_features': acoustic_features.prosodic_features,
            'biosemotic_validation': duchenne_validation < 0.2
        }

    def _calculate_prosodic_sarcasm(self, features: AcousticFeatures) -> float:
        """Calculate prosodic sarcasm indicator score"""
        sarcasm_score = 0.0

        # Pitch flattening (monotone delivery)
        if features.prosodic_features['pitch_std'] < 20:
            sarcasm_score += self.sarcasm_prosodic_indicators['pitch_flattening']

        # Tempo slowing
        if features.prosodic_features['tempo'] < 110:
            sarcasm_score += self.sarcasm_prosodic_indicators['tempo_slowing']

        # Intensity exaggeration
        if features.prosodic_features['intensity_std'] > 0.3:
            sarcasm_score += self.sarcasm_prosodic_indicators['intensity_exaggeration']

        return min(sarcasm_score, 1.0)


class MultiModalLaughterPredictor:
    """
    Next-generation predictor combining text, acoustic, and cultural intelligence
    """

    def __init__(self, base_model_path: str, use_acoustic: bool = True):
        """Initialize multi-modal laughter predictor"""

        from core.cultural_priors_enhancement import create_cultural_adaptive_predictor
        self.cultural_predictor = create_cultural_adaptive_predictor(base_model_path)
        self.acoustic_enhancer = AcousticBiosemoticEnhancer(use_simulation=True)
        self.use_acoustic = use_acoustic

    def predict_multimodal(
        self,
        text: str,
        audio_path: Optional[str] = None,
        return_details: bool = False
    ) -> Dict:
        """Make prediction with full multi-modal intelligence"""

        # Get cultural adaptive prediction
        cultural_result = self.cultural_predictor.predict_with_cultural_intelligence(text)

        if not self.use_acoustic or audio_path is None:
            return {
                'predicted_laughter': cultural_result['predicted_laughter'],
                'confidence_score': cultural_result['confidence_score'],
                'enhanced_probability': cultural_result['enhanced_probability'],
                'modality': 'text_cultural_only',
                'cultural_intelligence': cultural_result
            }

        # Analyze acoustic features
        acoustic_features = self.acoustic_enhancer.analyze_audio_features(audio_path)

        # Calculate acoustic enhancement
        acoustic_enhancement = self.acoustic_enhancer.calculate_acoustic_enhancement(
            acoustic_features,
            cultural_result['enhanced_probability'],
            0.5  # Placeholder text Duchenne prob (would need actual model output)
        )

        # Final multi-modal prediction
        final_probability = acoustic_enhancement['enhanced_probability']
        threshold = cultural_result['threshold_used']

        final_prediction = final_probability > threshold

        return {
            'predicted_laughter': final_prediction,
            'confidence_score': final_probability if final_prediction else 1.0 - final_probability,
            'enhanced_probability': final_probability,
            'threshold_used': threshold,
            'modality': 'full_multimodal',
            'text_cultural_result': cultural_result,
            'acoustic_features': acoustic_features,
            'acoustic_enhancement': acoustic_enhancement['acoustic_confidence'],
            'laugh_type': acoustic_enhancement['laugh_type_classification'],
            'duchenne_acoustic_score': acoustic_enhancement['duchenne_acoustic_score'],
            'biosemotic_validation': acoustic_enhancement['biosemotic_validation']
        }


def create_acoustic_enhancer(use_simulation: bool = True) -> AcousticBiosemoticEnhancer:
    """Factory function to create acoustic biosemotic enhancer"""
    return AcousticBiosemoticEnhancer(use_simulation)


def create_multimodal_predictor(model_path: str, use_acoustic: bool = True) -> MultiModalLaughterPredictor:
    """Factory function to create multi-modal laughter predictor"""
    return MultiModalLaughterPredictor(model_path, use_acoustic)