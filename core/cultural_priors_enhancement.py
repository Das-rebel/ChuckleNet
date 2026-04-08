#!/usr/bin/env python3
"""
Cultural Priors Enhancement for Regional Comedy Pattern Recognition
Enhances cross-cultural comedy intelligence through location-based and demographic adaptation
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
import re
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CulturalContext:
    """Rich cultural context for comedy analysis"""
    region: str
    comedy_tradition: str
    humor_style: str
    cultural_markers: List[str]
    audience_demographics: List[str]
    common_topics: List[str]


class CulturalPriorsEnhancer:
    """
    Advanced cultural intelligence system that enhances laughter prediction
    through regional comedy pattern recognition and demographic adaptation
    """

    def __init__(self):
        """Initialize cultural priors enhancement system"""

        # Regional comedy traditions database
        self.cultural_knowledge_base = {
            'US': {
                'comedy_tradition': 'observational_humor',
                'humor_style': 'direct_east_coast_west_coast',
                'cultural_markers': [
                    'dude', 'man', 'like', 'totally', 'awesome',
                    'whatever', 'literally', 'basically', 'honestly',
                    'y\'all', 'guys', 'folks', 'whatever', 'cool'
                ],
                'audience_demographics': ['diverse', 'urban', 'suburban', 'college_educated'],
                'common_topics': [
                    'dating', 'work_life', 'family_dynamics', 'technology',
                    'politics', 'social_media', 'pop_culture', 'everyday_life'
                ],
                'comedy_patterns': [
                    'setup_punchline_structure',
                    'observational_riffing',
                    'call_back_humor',
                    'rule_of_three'
                ]
            },
            'UK': {
                'comedy_tradition': 'ironic_wordplay',
                'humor_style': 'dry_sarcastic_understated',
                'cultural_markers': [
                    'quite', 'rather', 'actually', 'suppose', 'indeed',
                    'bloody', 'rubbish', 'brilliant', 'proper', 'sorted',
                    'cheers', 'mate', 'innit', 'fancy', 'reckon'
                ],
                'audience_demographics': ['traditional', 'pub_culture', 'working_class', 'middle_class'],
                'common_topics': [
                    'class_system', 'weather', 'queuing', 'politeness',
                    'british_life', 'irony', 'self_deprecation', 'social_norms'
                ],
                'comedy_patterns': [
                    'ironic_understatement',
                    'wordplay_puns',
                    'deadpan_delivery',
                    'british_sarcasm'
                ]
            },
            'Indian': {
                'comedy_tradition': 'family_social_observational',
                'humor_style': 'exaggerated_situational_family_oriented',
                'cultural_markers': [
                    'yaar', 'hai', 'nahi', 'kya', 'bahut', 'mast', 'theek',
                    'acha', 'arrey', 'waah', 'bhai', 'didi', 'paji',
                    'saala', 'machane', 'scene', 'jugaad', 'timepass'
                ],
                'audience_demographics': ['family_oriented', 'youth_culture', 'traditional', 'modern'],
                'common_topics': [
                    'family_dynamics', 'arranged_marriage', 'education_pressure',
                    'office_life', 'indian_parents', 'bollywood', 'cricket',
                    'festivals', 'food', 'social_expectations'
                ],
                'comedy_patterns': [
                    'family_exaggeration',
                    'situational_comedy',
                    'physical_comedy',
                    'social_satire',
                    'regional_stereotypes'
                ]
            }
        }

        # Cross-cultural comedy patterns
        self.universal_patterns = [
            'incongruity_resolution',
            'superiority_theory',
            'relief_theory',
            'benign_violation'
        ]

        # Demographic adaptation weights
        self.demographic_weights = {
            'youth_culture': 1.2,
            'family_oriented': 1.1,
            'urban': 1.0,
            'traditional': 0.9,
            'college_educated': 1.05
        }

    def detect_cultural_context(self, text: str, language: str) -> CulturalContext:
        """Enhanced cultural context detection with regional analysis"""

        text_lower = text.lower()

        # Count cultural markers per region
        cultural_scores = {}
        for region, knowledge in self.cultural_knowledge_base.items():
            score = sum(1 for marker in knowledge['cultural_markers']
                       if marker in text_lower)
            cultural_scores[region] = score

        # Get primary region
        primary_region = max(cultural_scores, key=cultural_scores.get)

        # Handle language-region mismatch
        if language == 'hindi' and primary_region != 'Indian':
            primary_region = 'Indian'  # Override for Hindi text
        elif language == 'hinglish' and primary_region != 'Indian':
            if primary_region == 'US' or cultural_scores['Indian'] == 0:
                primary_region = 'Indian'  # Default Hinglish to Indian

        knowledge = self.cultural_knowledge_base[primary_region]

        return CulturalContext(
            region=primary_region,
            comedy_tradition=knowledge['comedy_tradition'],
            humor_style=knowledge['humor_style'],
            cultural_markers=knowledge['cultural_markers'],
            audience_demographics=knowledge['audience_demographics'],
            common_topics=knowledge['common_topics']
        )

    def calculate_cultural_prior_boost(
        self,
        text: str,
        cultural_context: CulturalContext,
        detected_region: str,
        expected_region: str
    ) -> float:
        """Calculate cultural prior enhancement to laughter probability"""

        boost = 0.0

        # Regional match boost
        if detected_region == expected_region:
            boost += 0.08  # Strong boost for correct cultural context
        elif detected_region in ['US', 'UK'] and expected_region in ['US', 'UK']:
            boost += 0.04  # Partial boost for Western cultural match

        # Cultural marker density
        text_lower = text.lower()
        marker_count = sum(1 for marker in cultural_context.cultural_markers
                          if marker in text_lower)

        if marker_count >= 3:
            boost += 0.06  # High cultural marker density
        elif marker_count >= 2:
            boost += 0.04  # Medium cultural marker density
        elif marker_count >= 1:
            boost += 0.02  # Low cultural marker density

        # Comedy pattern recognition
        comedy_boost = self.detect_comedy_patterns(text, cultural_context)
        boost += comedy_boost

        # Topic relevance
        topic_boost = self.detect_topic_relevance(text, cultural_context)
        boost += topic_boost

        return min(boost, 0.20)  # Cap maximum cultural boost

    def detect_comedy_patterns(self, text: str, context: CulturalContext) -> float:
        """Detect region-specific comedy patterns"""

        text_lower = text.lower()
        pattern_score = 0.0

        if context.region == 'US':
            # Setup-punchline structure
            if re.search(r'so.*you know|let me tell you|here\'s the thing', text_lower):
                pattern_score += 0.03
            # Rule of three
            if re.search(r'.*,.*,.*', text_lower):
                pattern_score += 0.02

        elif context.region == 'UK':
            # Ironic understatement
            if re.search(r'quite|rather|suppose|actually', text_lower):
                pattern_score += 0.03
            # British sarcasm markers
            if re.search(r'cheers|mate|brilliant|rubbish', text_lower):
                pattern_score += 0.02

        elif context.region == 'Indian':
            # Family exaggeration
            if re.search(r'mummy|papa|aunty|uncle|beta|beti', text_lower):
                pattern_score += 0.03
            # Social satire
            if re.search(r'yaar|hai.*nahi|kya.*baat', text_lower):
                pattern_score += 0.02
            # Indian social situations
            if re.search(r'arranged|marriage|education|pressure|jugaad', text_lower):
                pattern_score += 0.02

        return pattern_score

    def detect_topic_relevance(self, text: str, context: CulturalContext) -> float:
        """Detect relevance to region-specific comedy topics"""

        text_lower = text.lower()
        topic_score = 0.0

        for topic in context.common_topics:
            if topic.replace('_', ' ') in text_lower:
                topic_score += 0.01

        return min(topic_score, 0.05)  # Cap topic relevance boost

    def get_demographic_adaptation(self, context: CulturalContext) -> float:
        """Calculate demographic adaptation factor"""

        adaptations = []
        for demographic in context.audience_demographics:
            weight = self.demographic_weights.get(demographic, 1.0)
            adaptations.append(weight)

        return np.mean(adaptations) if adaptations else 1.0

    def analyze_cultural_comedy_fit(
        self,
        text: str,
        language: str,
        base_probability: float
    ) -> Dict:
        """Comprehensive cultural comedy fit analysis"""

        # Detect cultural context
        cultural_context = self.detect_cultural_context(text, language)

        # Expected region based on language
        expected_regions = {
            'hindi': 'Indian',
            'hinglish': 'Indian',
            'english': ['US', 'UK']
        }

        expected_region = expected_regions.get(language, 'US')

        # Calculate cultural prior boost
        cultural_boost = self.calculate_cultural_prior_boost(
            text, cultural_context, cultural_context.region, expected_region
        )

        # Get demographic adaptation
        demographic_adaptation = self.get_demographic_adaptation(cultural_context)

        # Calculate cultural fit score
        cultural_fit_score = base_probability + cultural_boost
        cultural_fit_score = max(0.0, min(1.0, cultural_fit_score))

        return {
            'cultural_context': cultural_context,
            'cultural_boost': cultural_boost,
            'demographic_adaptation': demographic_adaptation,
            'cultural_fit_score': cultural_fit_score,
            'region_match': cultural_context.region == expected_region,
            'comedy_tradition': cultural_context.comedy_tradition,
            'humor_style': cultural_context.humor_style
        }

    def enhance_with_cultural_priors(
        self,
        text: str,
        language: str,
        base_probability: float,
        biosemotic_enhancement: float
    ) -> Dict:
        """Enhance prediction with cultural priors"""

        # Analyze cultural comedy fit
        cultural_analysis = self.analyze_cultural_comedy_fit(text, language, base_probability)

        # Combine enhancements
        total_enhancement = biosemotic_enhancement + cultural_analysis['cultural_boost']
        enhanced_probability = base_probability + total_enhancement
        enhanced_probability = max(0.0, min(1.0, enhanced_probability))

        return {
            'enhanced_probability': enhanced_probability,
            'biosemotic_enhancement': biosemotic_enhancement,
            'cultural_enhancement': cultural_analysis['cultural_boost'],
            'total_enhancement': total_enhancement,
            'cultural_context': cultural_analysis['cultural_context'],
            'demographic_adaptation': cultural_analysis['demographic_adaptation'],
            'comedy_tradition': cultural_analysis['comedy_tradition'],
            'humor_style': cultural_analysis['humor_style'],
            'region_match': cultural_analysis['region_match']
        }


class CulturalAdaptivePredictor:
    """
    Next-generation predictor combining adaptive thresholds with cultural intelligence
    """

    def __init__(self, base_model_path: str):
        """Initialize cultural adaptive predictor"""

        from core.adaptive_threshold_predictor import AdaptiveThresholdPredictor
        self.adaptive_predictor = AdaptiveThresholdPredictor(base_model_path)
        self.cultural_enhancer = CulturalPriorsEnhancer()

    def predict_with_cultural_intelligence(
        self,
        text: str,
        return_details: bool = False
    ) -> Dict:
        """Make prediction with full cultural intelligence"""

        # Get base adaptive prediction
        adaptive_result = self.adaptive_predictor.predict_with_adaptive_threshold(text)

        # Enhance with cultural priors
        cultural_enhancement = self.cultural_enhancer.enhance_with_cultural_priors(
            text,
            adaptive_result.language,
            adaptive_result.base_probability,
            adaptive_result.biosemotic_enhancement
        )

        # Recalculate prediction with cultural enhancement
        enhanced_probability = cultural_enhancement['enhanced_probability']
        threshold = adaptive_result.threshold_used

        # Adjust threshold based on demographic adaptation
        demographic_factor = cultural_enhancement['demographic_adaptation']
        adjusted_threshold = threshold / demographic_factor

        final_prediction = enhanced_probability > adjusted_threshold

        return {
            'predicted_laughter': final_prediction,
            'confidence_score': enhanced_probability if final_prediction else 1.0 - enhanced_probability,
            'enhanced_probability': enhanced_probability,
            'base_probability': adaptive_result.base_probability,
            'biosemotic_enhancement': cultural_enhancement['biosemotic_enhancement'],
            'cultural_enhancement': cultural_enhancement['cultural_enhancement'],
            'total_enhancement': cultural_enhancement['total_enhancement'],
            'threshold_used': adjusted_threshold,
            'language': adaptive_result.language,
            'cultural_context': cultural_enhancement['cultural_context'],
            'demographic_adaptation': demographic_factor,
            'comedy_tradition': cultural_enhancement['comedy_tradition'],
            'humor_style': cultural_enhancement['humor_style'],
            'region_match': cultural_enhancement['region_match']
        }


def create_cultural_adaptive_predictor(model_path: str) -> CulturalAdaptivePredictor:
    """Factory function to create cultural adaptive predictor"""
    return CulturalAdaptivePredictor(model_path)