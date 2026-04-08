#!/usr/bin/env python3
"""
Adaptive Threshold Predictor for Enhanced Biosemotic Laughter Prediction
Addresses conservative calibration issue through language-specific and content-aware thresholds
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
import re
from dataclasses import dataclass


@dataclass
class PredictionResult:
    """Enhanced prediction result with adaptive confidence"""
    predicted_laughter: bool
    confidence_score: float
    adjusted_probability: float
    base_probability: float
    language: str
    threshold_used: float
    biosemotic_enhancement: float
    cultural_context: str


class AdaptiveThresholdPredictor:
    """
    Advanced adaptive threshold system that addresses conservative calibration
    through multi-dimensional analysis and biosemotic feature integration
    """

    def __init__(self, base_model_path: str):
        """Initialize adaptive threshold predictor with enhanced model"""

        from core.biosemotic_enhancement import create_enhanced_model
        self.model = create_enhanced_model(base_model_path)
        self.model.eval()

        # Optimized language-specific thresholds based on analysis
        self.language_thresholds = {
            'hindi': 0.45,      # Current best performer
            'english': 0.35,    # Conservative calibration needed
            'hinglish': 0.40,   # Middle ground
            'default': 0.40     # Universal fallback
        }

        # Content-type specific adjustments
        self.content_modifiers = {
            'classic_joke': 0.15,      # "Why did the chicken..." patterns
            'audience_reaction': 0.12,  # "[laughter]", "[audience laughing]"
            'comedy_setup': 0.10,       # "So I walked into a bank..."
            'conversational': -0.05,    # Normal speech patterns
            'statement': -0.08          # Factual statements
        }

        # Biosemotic enhancement weights
        self.biosemotic_weights = {
            'duchenne_confidence': 0.08,
            'sarcasm_detection': 0.06,
            'emotional_intensity': 0.05,
            'cultural_match': 0.04
        }

    def detect_language(self, text: str) -> str:
        """Enhanced language detection for Hindi, English, Hinglish"""

        # Check for Hindi (Devanagari script)
        if re.search(r'[\u0900-\u097F]', text):
            # Check if it's pure Hindi or Hinglish
            english_word_ratio = len(re.findall(r'\b[a-zA-Z]{2,}\b', text)) / max(len(text.split()), 1)
            if english_word_ratio > 0.3:
                return 'hinglish'
            return 'hindi'

        # Check for Hinglish patterns (Latin script with Hindi words)
        hinglish_indicators = [
            r'\bkya\b', r'\bkyun\b', r'\bbhai\b', r'\bbhai\b',
            r'\byaar\b', r'\bah\b', r'\bho\b',
            r'\btheek\b', r'\bmast\b', r'\bbahut\b'
        ]

        hinglish_score = sum(1 for pattern in hinglish_indicators
                            if re.search(pattern, text, re.IGNORECASE))

        if hinglish_score >= 2:
            return 'hinglish'

        return 'english'

    def classify_content_type(self, text: str) -> str:
        """Classify content type for threshold adjustment"""

        text_lower = text.lower()

        # Audience reactions
        if re.search(r'\[laugh(ter)?\]|\[audience.*laugh\]|\[applause\]', text_lower):
            return 'audience_reaction'

        # Classic joke structures
        if re.search(r'why did the|how many|what do you call|knock knock', text_lower):
            return 'classic_joke'

        # Comedy setup patterns
        if re.search(r'so i|you know|here\'s the thing|let me tell you', text_lower):
            return 'comedy_setup'

        # Conversational markers
        if re.search(r'^so basically|^actually|^you know|^like', text_lower):
            return 'conversational'

        # Default to statement
        return 'statement'

    def calculate_biosemotic_enhancement(
        self,
        duchenne_prob: float,
        sarcasm_prob: float,
        emotion_intensity: float,
        cultural_match: bool
    ) -> float:
        """Calculate biosemotic feature enhancement to base probability"""

        enhancement = 0.0

        # Duchenne confidence boost
        if duchenne_prob > 0.6:
            enhancement += self.biosemotic_weights['duchenne_confidence']
        elif duchenne_prob < 0.4:
            enhancement -= self.biosemotic_weights['duchenne_confidence'] * 0.5

        # Sarcasm detection boost
        if sarcasm_prob > 0.6:
            enhancement += self.biosemotic_weights['sarcasm_detection']

        # Emotional intensity boost
        if emotion_intensity > 0.7:
            enhancement += self.biosemotic_weights['emotional_intensity']
        elif emotion_intensity > 0.5:
            enhancement += self.biosemotic_weights['emotional_intensity'] * 0.5

        # Cultural context match
        if cultural_match:
            enhancement += self.biosemotic_weights['cultural_match']

        return enhancement

    def predict_with_adaptive_threshold(
        self,
        text: str,
        return_details: bool = False
    ) -> PredictionResult:
        """
        Make prediction with adaptive threshold based on language, content, and biosemotic features
        """

        # Detect language
        language = self.detect_language(text)

        # Classify content type
        content_type = self.classify_content_type(text)

        # Get base model prediction
        words = text.split()
        encoding = self.model.tokenizer(
            words,
            is_split_into_words=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        with torch.no_grad():
            outputs = self.model(encoding['input_ids'], encoding['attention_mask'])

        # Extract features
        num_words = len(words)
        base_laugh_probs = outputs.base_laughter_probability[0, :num_words]
        duchenne_probs = outputs.duchenne_probability[0, :num_words]
        sarcasm_probs = outputs.sarcasm_probability[0, :num_words]
        emotion_intensities = outputs.emotional_intensity[0, :num_words]

        # Calculate averages
        base_probability = base_laugh_probs.mean().item()
        max_base_probability = base_laugh_probs.max().item()
        duchenne_prob = duchenne_probs.mean().item()
        sarcasm_prob = sarcasm_probs.mean().item()
        emotion_intensity = emotion_intensities.mean().item()

        # Get cultural context
        cultural_idx = outputs.cultural_nuance[0, :num_words].mean(dim=0).argmax().item()
        cultural_names = ['US', 'UK', 'Indian']
        detected_culture = cultural_names[cultural_idx]

        # Cultural match check
        expected_cultures = {
            'hindi': 'Indian',
            'hinglish': 'Indian',
            'english': ['US', 'UK']
        }
        cultural_match = detected_culture in (expected_cultures.get(language, [])
                                              if isinstance(expected_cultures.get(language), list)
                                              else [expected_cultures.get(language, detected_culture)])

        # Calculate adaptive threshold
        base_threshold = self.language_thresholds.get(language, 0.40)
        content_modifier = self.content_modifiers.get(content_type, 0.0)
        adaptive_threshold = base_threshold - content_modifier

        # Calculate biosemotic enhancement
        biosemotic_enhancement = self.calculate_biosemotic_enhancement(
            duchenne_prob, sarcasm_prob, emotion_intensity, cultural_match
        )

        # Adjust probability
        adjusted_probability = base_probability + biosemotic_enhancement + content_modifier
        adjusted_probability = max(0.0, min(1.0, adjusted_probability))  # Clamp to [0, 1]

        # Make prediction
        predicted_laughter = adjusted_probability > adaptive_threshold

        # Calculate confidence score
        if predicted_laughter:
            confidence_score = adjusted_probability
        else:
            confidence_score = 1.0 - adjusted_probability

        result = PredictionResult(
            predicted_laughter=predicted_laughter,
            confidence_score=confidence_score,
            adjusted_probability=adjusted_probability,
            base_probability=base_probability,
            language=language,
            threshold_used=adaptive_threshold,
            biosemotic_enhancement=biosemotic_enhancement,
            cultural_context=detected_culture
        )

        return result

    def batch_predict(
        self,
        texts: List[str],
        expected_laughter: Optional[List[bool]] = None
    ) -> Dict:
        """Batch prediction with comprehensive metrics"""

        results = []
        correct = 0
        total = len(texts)

        for text in texts:
            result = self.predict_with_adaptive_threshold(text)
            results.append(result)

        if expected_laughter:
            for result, expected in zip(results, expected_laughter):
                if result.predicted_laughter == expected:
                    correct += 1

            accuracy = correct / total if total > 0 else 0.0

            return {
                'results': results,
                'accuracy': accuracy,
                'correct': correct,
                'total': total
            }

        return {'results': results}

    def analyze_threshold_performance(
        self,
        test_examples: Dict[str, List[dict]]
    ) -> Dict:
        """Analyze performance across languages with adaptive thresholds"""

        analysis = {}

        for language, examples in test_examples.items():
            language_results = []

            for example in examples:
                text = example['text']
                expected = example['expected_laughter']

                result = self.predict_with_adaptive_threshold(text)
                is_correct = result.predicted_laughter == expected

                language_results.append({
                    'text': text,
                    'expected': expected,
                    'predicted': result.predicted_laughter,
                    'correct': is_correct,
                    'confidence': result.confidence_score,
                    'base_prob': result.base_probability,
                    'adjusted_prob': result.adjusted_probability,
                    'threshold': result.threshold_used,
                    'biosemotic_boost': result.biosemotic_enhancement
                })

            correct_count = sum(1 for r in language_results if r['correct'])
            accuracy = correct_count / len(language_results) if language_results else 0.0

            analysis[language] = {
                'results': language_results,
                'accuracy': accuracy,
                'correct': correct_count,
                'total': len(language_results),
                'avg_confidence': np.mean([r['confidence'] for r in language_results]),
                'avg_threshold': np.mean([r['threshold'] for r in language_results]),
                'avg_biosemotic_boost': np.mean([r['biosemotic_boost'] for r in language_results])
            }

        return analysis


def create_adaptive_predictor(model_path: str) -> AdaptiveThresholdPredictor:
    """Factory function to create adaptive threshold predictor"""
    return AdaptiveThresholdPredictor(model_path)