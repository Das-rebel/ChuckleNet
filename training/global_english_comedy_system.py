"""
Global English Comedy System - Comprehensive Cultural Humor Understanding
=========================================================================

A revolutionary system that understands English comedy across US, UK, and Indian cultural contexts.
Processes comedian-specific patterns, cultural nuances, and cross-cultural humor adaptation.

Author: Global Comedy AI Team
Date: 2026-04-03
Version: 1.0.0
"""

import re
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from collections import Counter
import hashlib
import pickle
from pathlib import Path

# Cultural Comedy Contexts
class ComedyCulture(Enum):
    """Major English comedy cultures"""
    US = "american"
    UK = "british"
    INDIAN = "indian"
    CROSS_CULTURAL = "cross_cultural"
    INTERNATIONAL = "international"

# Comedian Categories
class ComedianStyle(Enum):
    """Comedian style categories"""
    PROVOCATIVE_STORYTELLING = "provocative_storytelling"  # Dave Chappelle
    HIGH_ENERGY_OBSERVATIONAL = "high_energy_observational"  # Kevin Hart
    SOCIAL_CRITIQUE = "social_critique"  # Chris Rock, Trevor Noah
    CLEAN_OBSERVATIONAL = "clean_observational"  # Jerry Seinfeld
    CRINGE_COMEDY = "cringe_comedy"  # Ricky Gervais
    BRITISH_ABSURDITY = "british_absurdity"  # John Cleese
    SURREAL_HISTORICAL = "surreal_historical"  # Eddie Izzard
    QUICK_ONE_LINERS = "quick_one_liners"  # Lee Mack
    CROSS_CULTURAL_OBSERVATIONAL = "cross_cultural_observational"  # Vir Das
    POLITICAL_IMMIGRANT = "political_immigrant"  # Hasan Minhaj
    CULTURAL_IDENTITY = "cultural_identity"  # Mindy Kaling, Aziz Ansari
    MUSICAL_OBSERVATIONAL = "musical_observational"  # Kenny Sebastian

@dataclass
class ComedianProfile:
    """Detailed comedian profile with cultural markers"""
    name: str
    nationality: ComedyCulture
    style: ComedianStyle
    key_themes: List[str]
    delivery_patterns: List[str]
    cultural_references: List[str]
    signature_techniques: List[str]
    audience_demographics: Dict[str, float]
    cross_cultural_appeal: float
    tempo_analysis: Dict[str, float]
    dark_humor_tolerance: float
    political_correctness_level: float

@dataclass
class ComedyCulturalFeatures:
    """Extracted cultural features from comedy content"""
    culture_type: ComedyCulture
    directness_score: float  # US: high, UK: medium, Indian: variable
    sarcasm_level: float  # UK: high, US: medium, Indian: low-medium
    self_deprecation: float  # UK: high, others: variable
    physical_comedy: float  # US: high, UK: medium, Indian: low
    pop_culture_refs: float  # US: high, all: variable
    political_commentary: float  # Variable across cultures
    cultural_identity_refs: float  # Indian/cross-cultural: high
    family_dynamics: float  # Indian: high, all: variable
    bollywood_refs: float  # Indian: high, others: low
    class_commentary: float  # UK: high, US: medium, Indian: low
    immigrant_experience: float  # Cross-cultural: high
    irony_level: float  # UK: very high
    timing_patterns: Dict[str, float]
    language_complexity: float

@dataclass
class JokeCulturalAnalysis:
    """Complete cultural analysis of a joke"""
    original_culture: ComedyCulture
    target_culture: ComedyCulture
    cultural_adaptation_score: float
    humor_preservation_score: float
    required_adaptations: List[str]
    cultural_barriers: List[str]
    universal_elements: List[str]
    adaptation_suggestions: List[str]

class GlobalEnglishComedyProcessor:
    """
    Main processor for global English comedy understanding and adaptation.

    Revolutionary capabilities:
    - Multi-cultural comedy pattern recognition
    - Comedian-specific style analysis
    - Cross-cultural joke adaptation
    - Cultural appropriateness evaluation
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the Global English Comedy Processor"""
        self.cultural_profiles = self._initialize_comedian_profiles()
        self.cultural_features = self._initialize_cultural_features()
        self.cross_cultural_patterns = self._initialize_cross_cultural_patterns()

        # Load or initialize ML models
        self.culture_classifier = None
        self.comedian_identifier = None
        self.adaptation_engine = None

        if model_path:
            self._load_models(model_path)

    def _initialize_comedian_profiles(self) -> Dict[str, ComedianProfile]:
        """Initialize detailed profiles for major comedians"""
        profiles = {}

        # US Comedians
        profiles['dave_chappelle'] = ComedianProfile(
            name="Dave Chappelle",
            nationality=ComedyCulture.US,
            style=ComedianStyle.PROVOCATIVE_STORYTELLING,
            key_themes=["race", "politics", "celebrity", "social justice", "controversy"],
            delivery_patterns=["conversational", "provocative", "storytelling", "improv"],
            cultural_references=["american_pop_culture", "african_american_experience", "politics"],
            signature_techniques=["call_and_response", "audience_interaction", "controversial_premises"],
            audience_demographics={"urban_adults": 0.7, "international": 0.3},
            cross_cultural_appeal=0.6,
            tempo_analysis={"words_per_minute": 150, "pause_frequency": 0.3, "emphasis_variance": 0.7},
            dark_humor_tolerance=0.9,
            political_correctness_level=0.2
        )

        profiles['ricky_gervais'] = ComedianProfile(
            name="Ricky Gervais",
            nationality=ComedyCulture.UK,
            style=ComedianStyle.CRINGE_COMEDY,
            key_themes=["awkwardness", "mortality", "religion", "celebrity", "political_correctness"],
            delivery_patterns=["awkward_pauses", "cringe_humor", "dark_humor", "sarcastic"],
            cultural_references=["british_culture", "class_system", "british_media"],
            signature_techniques=["awkward_silence", "inappropriate_questions", "deadpan_delivery"],
            audience_demographics={"british_adults": 0.6, "international": 0.4},
            cross_cultural_appeal=0.5,
            tempo_analysis={"words_per_minute": 120, "pause_frequency": 0.5, "emphasis_variance": 0.4},
            dark_humor_tolerance=0.95,
            political_correctness_level=0.1
        )

        profiles['vir_das'] = ComedianProfile(
            name="Vir Das",
            nationality=ComedyCulture.INDIAN,
            style=ComedianStyle.CROSS_CULTURAL_OBSERVATIONAL,
            key_themes=["india_vs_west", "cultural_differences", "immigration", "identity", "modernity_vs_tradition"],
            delivery_patterns=["energetic", "character_switching", "musical", "improv"],
            cultural_references=["indian_culture", "bollywood", "american_culture", "global_issues"],
            signature_techniques=["cultural_comparison", "accent_switching", "musical_comedy", "audience_participation"],
            audience_demographics={"indian_diaspora": 0.5, "western_international": 0.3, "indian_resident": 0.2},
            cross_cultural_appeal=0.8,
            tempo_analysis={"words_per_minute": 160, "pause_frequency": 0.2, "emphasis_variance": 0.8},
            dark_humor_tolerance=0.6,
            political_correctness_level=0.5
        )

        # Additional US comedians
        profiles['kevin_hart'] = ComedianProfile(
            name="Kevin Hart",
            nationality=ComedyCulture.US,
            style=ComedianStyle.HIGH_ENERGY_OBSERVATIONAL,
            key_themes=["relationships", "family", "everyday_situations", "self_deprecation"],
            delivery_patterns=["high_energy", "physical_comedy", "squeaky_voice", "animated"],
            cultural_references=["american_family_life", "pop_culture", "urban_culture"],
            signature_techniques=["physical_comedy", "voice_changes", "audience_interaction"],
            audience_demographics={"mainstream_us": 0.8, "international": 0.2},
            cross_cultural_appeal=0.7,
            tempo_analysis={"words_per_minute": 180, "pause_frequency": 0.1, "emphasis_variance": 0.9},
            dark_humor_tolerance=0.4,
            political_correctness_level=0.6
        )

        profiles['jerry_seinfeld'] = ComedianProfile(
            name="Jerry Seinfeld",
            nationality=ComedyCulture.US,
            style=ComedianStyle.CLEAN_OBSERVATIONAL,
            key_themes=["everyday_life", "social_conventions", "language", "minor_annoyances"],
            delivery_patterns=["clean", "observational", "precise", "rhythmic"],
            cultural_references=["american_suburban_life", "consumer_culture", "social_norms"],
            signature_techniques=["what's_the_deal", "observational_details", "call_backs"],
            audience_demographics={"mainstream_us": 0.9, "international": 0.1},
            cross_cultural_appeal=0.5,
            tempo_analysis={"words_per_minute": 140, "pause_frequency": 0.4, "emphasis_variance": 0.5},
            dark_humor_tolerance=0.2,
            political_correctness_level=0.8
        )

        # Additional UK comedians
        profiles['john_cleese'] = ComedianProfile(
            name="John Cleese",
            nationality=ComedyCulture.UK,
            style=ComedianStyle.BRITISH_ABSURDITY,
            key_themes=["absurdity", "authority", "british_institutions", "surreal_situations"],
            delivery_patterns=["upper_class", "physical_comedy", "deadpan", "sarcastic"],
            cultural_references=["british_class_system", "monty_python", "british_institutions"],
            signature_techniques=["physical_comedy", "absurd_premises", "surreal_transitions"],
            audience_demographics={"british_intellectual": 0.6, "international": 0.4},
            cross_cultural_appeal=0.6,
            tempo_analysis={"words_per_minute": 130, "pause_frequency": 0.3, "emphasis_variance": 0.6},
            dark_humor_tolerance=0.7,
            political_correctness_level=0.5
        )

        profiles['eddie_izzard'] = ComedianProfile(
            name="Eddie Izzard",
            nationality=ComedyCulture.UK,
            style=ComedianStyle.SURREAL_HISTORICAL,
            key_themes=["history", "language", "technology", "human_behavior", "surreal_scenarios"],
            delivery_patterns=["stream_of_consciousness", "historical_impressions", "surreal", "improv"],
            cultural_references=["european_history", "british_culture", "american_culture"],
            signature_techniques=["historical_reenactments", "surreal_narratives", "language_play"],
            audience_demographics={"british_intellectual": 0.5, "international": 0.5},
            cross_cultural_appeal=0.7,
            tempo_analysis={"words_per_minute": 145, "pause_frequency": 0.2, "emphasis_variance": 0.7},
            dark_humor_tolerance=0.6,
            political_correctness_level=0.6
        )

        # Indian comedians
        profiles['hasan_minhaj'] = ComedianProfile(
            name="Hasan Minhaj",
            nationality=ComedyCulture.INDIAN,
            style=ComedianStyle.POLITICAL_IMMIGRANT,
            key_themes=["politics", "immigration", "identity", "race", "american_dream"],
            delivery_patterns=["high_energy", "political_commentary", "personal_stories", "investigative"],
            cultural_references=["american_politics", "indian_immigrant_experience", "pop_culture"],
            signature_techniques=["powerpoint_presentations", "audience_interaction", "personal_narrative"],
            audience_demographics={"second_gen_immigrants": 0.6, "liberal_us": 0.3, "international": 0.1},
            cross_cultural_appeal=0.7,
            tempo_analysis={"words_per_minute": 165, "pause_frequency": 0.15, "emphasis_variance": 0.85},
            dark_humor_tolerance=0.5,
            political_correctness_level=0.4
        )

        profiles['aziz_ansari'] = ComedianProfile(
            name="Aziz Ansari",
            nationality=ComedyCulture.INDIAN,
            style=ComedianStyle.CULTURAL_IDENTITY,
            key_themes=["technology", "relationships", "food", "cultural_expectations", "modern_life"],
            delivery_patterns=["observational", "character_work", "enthusiastic", "detailed"],
            cultural_references=["modern_technology", "indian_parents", "food_culture", "social_media"],
            signature_techniques=["detailed_observations", "character_impressions", "audience_interaction"],
            audience_demographics={"millennial_international": 0.7, "mainstream_us": 0.2, "south_asian": 0.1},
            cross_cultural_appeal=0.8,
            tempo_analysis={"words_per_minute": 155, "pause_frequency": 0.25, "emphasis_variance": 0.75},
            dark_humor_tolerance=0.4,
            political_correctness_level=0.7
        )

        return profiles

    def _initialize_cultural_features(self) -> Dict[ComedyCulture, ComedyCulturalFeatures]:
        """Initialize baseline cultural features for each comedy culture"""
        features = {}

        # US Comedy Features
        features[ComedyCulture.US] = ComedyCulturalFeatures(
            culture_type=ComedyCulture.US,
            directness_score=0.8,
            sarcasm_level=0.5,
            self_deprecation=0.4,
            physical_comedy=0.7,
            pop_culture_refs=0.9,
            political_commentary=0.7,
            cultural_identity_refs=0.3,
            family_dynamics=0.6,
            bollywood_refs=0.0,
            class_commentary=0.4,
            immigrant_experience=0.3,
            irony_level=0.4,
            timing_patterns={"setup_punch_ratio": 0.7, "average_pause_duration": 0.3, "callback_frequency": 0.5},
            language_complexity=0.5
        )

        # UK Comedy Features
        features[ComedyCulture.UK] = ComedyCulturalFeatures(
            culture_type=ComedyCulture.UK,
            directness_score=0.5,
            sarcasm_level=0.9,
            self_deprecation=0.8,
            physical_comedy=0.5,
            pop_culture_refs=0.6,
            political_commentary=0.8,
            cultural_identity_refs=0.4,
            family_dynamics=0.5,
            bollywood_refs=0.0,
            class_commentary=0.9,
            immigrant_experience=0.2,
            irony_level=0.95,
            timing_patterns={"setup_punch_ratio": 0.8, "average_pause_duration": 0.5, "callback_frequency": 0.7},
            language_complexity=0.7
        )

        # Indian Comedy Features
        features[ComedyCulture.INDIAN] = ComedyCulturalFeatures(
            culture_type=ComedyCulture.INDIAN,
            directness_score=0.6,
            sarcasm_level=0.4,
            self_deprecation=0.6,
            physical_comedy=0.3,
            pop_culture_refs=0.7,
            political_commentary=0.5,
            cultural_identity_refs=0.9,
            family_dynamics=0.9,
            bollywood_refs=0.8,
            class_commentary=0.3,
            immigrant_experience=0.7,
            irony_level=0.5,
            timing_patterns={"setup_punch_ratio": 0.6, "average_pause_duration": 0.25, "callback_frequency": 0.4},
            language_complexity=0.6
        )

        return features

    def _initialize_cross_cultural_patterns(self) -> Dict[Tuple[ComedyCulture, ComedyCulture], Dict[str, float]]:
        """Initialize cross-cultural adaptation patterns"""
        patterns = {}

        # US to UK adaptation
        patterns[(ComedyCulture.US, ComedyCulture.UK)] = {
            "directness_reduction": 0.3,
            "sarcasm_increase": 0.4,
            "irony_enhancement": 0.5,
            "physical_comedy_reduction": 0.2,
            "cultural_ref_replacement": 0.6
        }

        # UK to US adaptation
        patterns[(ComedyCulture.UK, ComedyCulture.US)] = {
            "directness_increase": 0.4,
            "sarcasm_reduction": 0.3,
            "irony_reduction": 0.3,
            "physical_comedy_increase": 0.2,
            "pop_culture_localization": 0.5
        }

        # US/UK to Indian adaptation
        patterns[(ComedyCulture.US, ComedyCulture.INDIAN)] = {
            "family_dynamics_addition": 0.7,
            "cultural_identity_enhancement": 0.8,
            "bollywood_integration": 0.6,
            "directness_adjustment": 0.2,
            "immigrant_perspective_addition": 0.5
        }

        patterns[(ComedyCulture.UK, ComedyCulture.INDIAN)] = {
            "family_dynamics_addition": 0.6,
            "cultural_identity_enhancement": 0.7,
            "irony_reduction": 0.3,
            "class_commentary_reduction": 0.4,
            "immigrant_perspective_addition": 0.5
        }

        # Indian to US/UK adaptation
        patterns[(ComedyCulture.INDIAN, ComedyCulture.US)] = {
            "cultural_explanation_addition": 0.6,
            "family_universality_emphasis": 0.5,
            "bollywood_explanation": 0.7,
            "directness_increase": 0.2,
            "pop_culture_localization": 0.4
        }

        patterns[(ComedyCulture.INDIAN, ComedyCulture.UK)] = {
            "irony_enhancement": 0.3,
            "self_deprecation_increase": 0.4,
            "cultural_explanation_addition": 0.5,
            "class_commentary_addition": 0.3,
            "sarcasm_increase": 0.3
        }

        return patterns

    def detect_cultural_context(self, text: str) -> Tuple[ComedyCulture, float]:
        """
        Detect the cultural context of comedy content.

        Args:
            text: Comedy transcript or text

        Returns:
            Tuple of (detected_culture, confidence_score)
        """
        # Cultural markers for each region
        us_markers = [
            "america", "american", "congress", "senate", "republican", "democrat",
            "new york", "los angeles", "hollywood", "baseball", "football", "nba",
            "thanksgiving", "july 4th", "high school", "prom", "sorority", "fraternity"
        ]

        uk_markers = [
            "british", "britain", "english", "london", "uk", "united kingdom",
            "parliament", "tory", "labour", "bbc", "tea", "cricket", "rugby",
            "football", "chelsea", "manchester", "liverpool", "pub", "royal family"
        ]

        indian_markers = [
            "india", "indian", "delhi", "mumbai", "bollywood", "cricket",
            "arranged marriage", "indian parents", "desi", "curry", "hindu", "muslim",
            "sikh", "punjabi", "tamil", "telugu", "auntie", "uncle", "iit"
        ]

        # Count markers
        text_lower = text.lower()
        us_count = sum(1 for marker in us_markers if marker in text_lower)
        uk_count = sum(1 for marker in uk_markers if marker in text_lower)
        indian_count = sum(1 for marker in indian_markers if marker in text_lower)

        # Calculate scores
        total_markers = us_count + uk_count + indian_count + 1  # Avoid division by zero

        us_score = us_count / total_markers
        uk_score = uk_count / total_markers
        indian_score = indian_count / total_markers

        # Determine dominant culture
        scores = {
            ComedyCulture.US: us_score,
            ComedyCulture.UK: uk_score,
            ComedyCulture.INDIAN: indian_score
        }

        dominant_culture = max(scores.items(), key=lambda x: x[1])
        confidence = dominant_culture[1]

        # Check for cross-cultural content
        if sum(1 for score in scores.values() if score > 0.1) >= 2:
            return ComedyCulture.CROSS_CULTURAL, confidence * 0.8

        return dominant_culture[0], confidence

    def identify_comedian_style(self, text: str, cultural_context: ComedyCulture) -> List[Tuple[str, float]]:
        """
        Identify likely comedian styles based on text patterns.

        Args:
            text: Comedy content
            cultural_context: Detected cultural context

        Returns:
            List of (comedian_name, similarity_score) tuples
        """
        scores = []

        for comedian_name, profile in self.cultural_profiles.items():
            # Skip if cultural context doesn't match
            if profile.nationality != cultural_context and cultural_context != ComedyCulture.CROSS_CULTURAL:
                continue

            similarity_score = self._calculate_style_similarity(text, profile)
            scores.append((comedian_name, similarity_score))

        # Sort by similarity score
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:5]  # Return top 5 matches

    def _calculate_style_similarity(self, text: str, profile: ComedianProfile) -> float:
        """Calculate similarity between text and comedian profile"""
        text_lower = text.lower()
        score = 0.0

        # Theme matching
        theme_matches = sum(1 for theme in profile.key_themes if theme in text_lower)
        score += (theme_matches / len(profile.key_themes)) * 0.3

        # Cultural reference matching
        ref_matches = sum(1 for ref in profile.cultural_references if ref in text_lower)
        score += (ref_matches / len(profile.cultural_references)) * 0.2

        # Delivery pattern estimation (word analysis)
        words = text_lower.split()
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Tempo analysis based on word count and punctuation
        punctuation_count = text.count(',') + text.count('.') + text.count('!')
        pause_estimate = punctuation_count / (len(words) + 1)

        # Compare with profile tempo
        tempo_diff = abs(pause_estimate - profile.tempo_analysis['pause_frequency'])
        score += max(0, 0.3 - tempo_diff) * 0.3

        # Signature technique detection
        technique_matches = 0
        if profile.style == ComedianStyle.CRINGE_COMEDY:
            # Detect awkward pauses, inappropriate questions
            awkward_indicators = ['awkward', 'uncomfortable', 'weird', 'strange']
            technique_matches = sum(1 for indicator in awkward_indicators if indicator in text_lower)

        elif profile.style == ComedianStyle.PROVOCATIVE_STORYTELLING:
            # Detect storytelling markers and provocative content
            story_indicators = ['so i was', 'let me tell you', 'story', 'happened']
            provocative_indicators = ['controversial', 'politics', 'race', 'gender']
            technique_matches = (sum(1 for ind in story_indicators if ind in text_lower) +
                               sum(1 for ind in provocative_indicators if ind in text_lower)) / 2

        elif profile.style == ComedianStyle.CROSS_CULTURAL_OBSERVATIONAL:
            # Detect cultural comparisons
            comparison_indicators = ['in india', 'in america', 'in the west', 'back home', 'here vs']
            technique_matches = sum(1 for ind in comparison_indicators if ind in text_lower)

        score += min(technique_matches / 3, 0.2) * 0.2

        return score

    def extract_cultural_features(self, text: str, cultural_context: ComedyCulture) -> ComedyCulturalFeatures:
        """
        Extract detailed cultural features from comedy content.

        Args:
            text: Comedy content
            cultural_context: Detected cultural context

        Returns:
            Detailed cultural features
        """
        text_lower = text.lower()
        words = text_lower.split()

        # Initialize features based on cultural baseline
        base_features = self.cultural_features.get(cultural_context,
                                                   self.cultural_features[ComedyCulture.US])

        # Calculate specific features
        directness_score = self._calculate_directness(text_lower)
        sarcasm_level = self._calculate_sarcasm(text_lower)
        self_deprecation = self._calculate_self_deprecation(text_lower)
        irony_level = self._calculate_irony(text_lower)

        # Cultural references
        pop_culture_count = self._count_pop_culture_refs(text_lower)
        political_count = self._count_political_refs(text_lower)
        cultural_identity_count = self._count_cultural_identity_refs(text_lower)

        # Create updated features
        features = ComedyCulturalFeatures(
            culture_type=cultural_context,
            directness_score=directness_score,
            sarcasm_level=sarcasm_level,
            self_deprecation=self_deprecation,
            physical_comedy=self._estimate_physical_comedy(text_lower),
            pop_culture_refs=pop_culture_count,
            political_commentary=political_count,
            cultural_identity_refs=cultural_identity_count,
            family_dynamics=self._count_family_refs(text_lower),
            bollywood_refs=self._count_bollywood_refs(text_lower),
            class_commentary=self._count_class_refs(text_lower),
            immigrant_experience=self._count_immigrant_refs(text_lower),
            irony_level=irony_level,
            timing_patterns=self._analyze_timing_patterns(text),
            language_complexity=self._calculate_language_complexity(words)
        )

        return features

    def _calculate_directness(self, text: str) -> float:
        """Calculate directness score (higher = more direct)"""
        # Direct language indicators
        direct_phrases = ['i think', 'i believe', 'honestly', 'frankly', 'straight up']
        indirect_phrases = ['maybe', 'perhaps', 'one might say', 'it could be argued']

        direct_count = sum(1 for phrase in direct_phrases if phrase in text)
        indirect_count = sum(1 for phrase in indirect_phrases if phrase in text)

        total = direct_count + indirect_count + 1
        return direct_count / total

    def _calculate_sarcasm(self, text: str) -> float:
        """Calculate sarcasm level"""
        # Sarcasm indicators (challenging to detect accurately)
        sarcasm_indicators = ['yeah right', 'oh sure', 'totally', 'great', 'just what i needed']

        # Look for contrast markers
        contrast_markers = ['but', 'however', 'although', 'yet']
        contrast_count = sum(1 for marker in contrast_markers if marker in text)

        # Exaggeration markers
        exaggeration_markers = ['literally', 'totally', 'absolutely', 'completely']
        exaggeration_count = sum(1 for marker in exaggeration_markers if marker in text)

        # Combine signals
        sarcasm_score = (contrast_count * 0.5 + exaggeration_count * 0.3) / 10
        return min(sarcasm_score, 1.0)

    def _calculate_self_deprecation(self, text: str) -> float:
        """Calculate self-deprecation level"""
        self_deprecating_phrases = [
            'i\'m such an', 'i\'m so', 'i can\'t believe i', 'why am i',
            'i\'m terrible at', 'i\'m bad at', 'i\'m horrible at', 'i\'m an idiot'
        ]

        count = sum(1 for phrase in self_deprecating_phrases if phrase in text)
        return min(count / 5, 1.0)

    def _calculate_irony(self, text: str) -> float:
        """Calculate irony level"""
        # Irony often involves saying the opposite of what's meant
        irony_indicators = [
            'interestingly', 'ironically', 'of course', 'naturally',
            'as expected', 'surprisingly', 'funny enough'
        ]

        count = sum(1 for indicator in irony_indicators if indicator in text)

        # Look for situational contrast
        situation_contrast = ['but actually', 'turns out', 'in reality', 'actually']
        contrast_count = sum(1 for marker in situation_contrast if marker in text)

        return min((count + contrast_count * 0.5) / 5, 1.0)

    def _count_pop_culture_refs(self, text: str) -> float:
        """Count pop culture references"""
        pop_culture_terms = [
            'iphone', 'google', 'facebook', 'twitter', 'instagram', 'tiktok',
            'netflix', 'spotify', 'youtube', 'amazon', 'tesla', 'elon musk',
            'kardashian', 'taylor swift', 'bieber', 'movie', 'show', 'series'
        ]

        count = sum(1 for term in pop_culture_terms if term in text)
        return min(count / 10, 1.0)

    def _count_political_refs(self, text: str) -> float:
        """Count political references"""
        political_terms = [
            'president', 'congress', 'senate', 'election', 'vote', 'political',
            'government', 'policy', 'republican', 'democrat', 'conservative', 'liberal'
        ]

        count = sum(1 for term in political_terms if term in text)
        return min(count / 8, 1.0)

    def _count_cultural_identity_refs(self, text: str) -> float:
        """Count cultural identity references"""
        identity_terms = [
            'american', 'indian', 'british', 'culture', 'heritage',
            'tradition', 'immigrant', 'desi', 'western', 'eastern'
        ]

        count = sum(1 for term in identity_terms if term in text)
        return min(count / 8, 1.0)

    def _count_family_refs(self, text: str) -> float:
        """Count family references"""
        family_terms = [
            'mom', 'dad', 'mother', 'father', 'parents', 'family',
            'sister', 'brother', 'auntie', 'uncle', 'grandma', 'grandpa'
        ]

        count = sum(1 for term in family_terms if term in text)
        return min(count / 6, 1.0)

    def _count_bollywood_refs(self, text: str) -> float:
        """Count Bollywood references"""
        bollywood_terms = [
            'bollywood', 'shah rukh', 'aamir', 'salman', 'priyanka', 'deepika',
            'khan', 'kapoor', 'movies', 'item song', 'masala'
        ]

        count = sum(1 for term in bollywood_terms if term in text)
        return min(count / 5, 1.0)

    def _count_class_refs(self, text: str) -> float:
        """Count class commentary references"""
        class_terms = [
            'rich', 'poor', 'wealthy', 'working class', 'middle class',
            'upper class', 'posh', 'privileged', 'struggle', 'money'
        ]

        count = sum(1 for term in class_terms if term in text)
        return min(count / 6, 1.0)

    def _count_immigrant_refs(self, text: str) -> float:
        """Count immigrant experience references"""
        immigrant_terms = [
            'immigrant', 'visa', 'citizenship', 'green card', 'assimilation',
            'acculturation', 'first generation', 'second generation', 'diaspora'
        ]

        count = sum(1 for term in immigrant_terms if term in text)
        return min(count / 5, 1.0)

    def _estimate_physical_comedy(self, text: str) -> float:
        """Estimate physical comedy content from text"""
        physical_indicators = [
            'then i', 'i was like', 'gestures', 'mimes', 'acts out',
            'demonstrates', 'shows', 'physical', 'movement'
        ]

        count = sum(1 for indicator in physical_indicators if indicator in text)
        return min(count / 8, 1.0)

    def _analyze_timing_patterns(self, text: str) -> Dict[str, float]:
        """Analyze timing patterns from text structure"""
        sentences = text.split('.')
        words = text.split()

        # Setup-to-punchline ratio estimation
        question_marks = text.count('?')
        exclamation_marks = text.count('!')

        setup_punch_ratio = question_marks / (len(sentences) + 1)

        # Pause duration estimation (based on punctuation)
        total_pauses = text.count(',') + text.count('.') + text.count('?') + text.count('!')
        avg_pause_estimate = total_pauses / (len(words) + 1)

        # Callback frequency (repeated themes)
        word_freq = Counter(words)
        repeated_words = sum(1 for word, count in word_freq.items() if count >= 3)
        callback_frequency = repeated_words / len(word_freq)

        return {
            "setup_punch_ratio": min(setup_punch_ratio, 1.0),
            "average_pause_duration": min(avg_pause_estimate, 1.0),
            "callback_frequency": min(callback_frequency, 1.0)
        }

    def _calculate_language_complexity(self, words: List[str]) -> float:
        """Calculate language complexity score"""
        if not words:
            return 0.0

        # Average word length
        avg_length = sum(len(word) for word in words) / len(words)

        # Vocabulary diversity
        unique_ratio = len(set(words)) / len(words)

        # Complex word usage (words > 6 characters)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_ratio = complex_words / len(words)

        # Combine metrics
        complexity = (avg_length / 10) + (unique_ratio * 0.4) + (complex_ratio * 0.3)
        return min(complexity, 1.0)

    def adapt_joke_cross_cultural(self, joke_text: str, target_culture: ComedyCulture) -> JokeCulturalAnalysis:
        """
        Analyze and provide adaptation suggestions for cross-cultural joke translation.

        Args:
            joke_text: Original joke content
            target_culture: Target cultural context

        Returns:
            Detailed cultural adaptation analysis
        """
        # Detect original culture
        original_culture, confidence = self.detect_cultural_context(joke_text)

        # Extract original features
        original_features = self.extract_cultural_features(joke_text, original_culture)

        # Get target culture baseline
        target_features = self.cultural_features.get(target_culture,
                                                     self.cultural_features[ComedyCulture.US])

        # Analyze adaptability
        adaptation_score = self._calculate_cultural_adaptation_score(
            original_features, target_features, original_culture, target_culture
        )

        # Identify cultural barriers
        cultural_barriers = self._identify_cultural_barriers(
            joke_text, original_culture, target_culture
        )

        # Find universal elements
        universal_elements = self._find_universal_humor_elements(joke_text)

        # Generate adaptation suggestions
        adaptation_suggestions = self._generate_adaptation_suggestions(
            joke_text, original_culture, target_culture, cultural_barriers
        )

        return JokeCulturalAnalysis(
            original_culture=original_culture,
            target_culture=target_culture,
            cultural_adaptation_score=adaptation_score,
            humor_preservation_score=adaptation_score * 0.8,  # Conservative estimate
            required_adaptations=self._get_required_adaptations(original_culture, target_culture),
            cultural_barriers=cultural_barriers,
            universal_elements=universal_elements,
            adaptation_suggestions=adaptation_suggestions
        )

    def _calculate_cultural_adaptation_score(self, original_features: ComedyCulturalFeatures,
                                           target_features: ComedyCulturalFeatures,
                                           original_culture: ComedyCulture,
                                           target_culture: ComedyCulture) -> float:
        """Calculate how well a joke can be adapted between cultures"""

        # Get cross-cultural adaptation patterns
        adaptation_key = (original_culture, target_culture)
        patterns = self.cross_cultural_patterns.get(adaptation_key, {})

        # Calculate feature differences
        feature_diffs = {
            'directness': abs(original_features.directness_score - target_features.directness_score),
            'sarcasm': abs(original_features.sarcasm_level - target_features.sarcasm_level),
            'irony': abs(original_features.irony_level - target_features.irony_level),
            'pop_culture': abs(original_features.pop_culture_refs - target_features.pop_culture_refs)
        }

        # Base adaptability score
        base_score = 1.0 - sum(feature_diffs.values()) / len(feature_diffs)

        # Apply adaptation pattern multipliers
        if patterns:
            adaptation_ease = sum(patterns.values()) / len(patterns)
            base_score *= adaptation_ease

        # Universal themes boost adaptability
        if original_features.family_dynamics > 0.5:
            base_score *= 1.1  # Family dynamics are relatively universal

        return min(max(base_score, 0.0), 1.0)

    def _identify_cultural_barriers(self, text: str, original_culture: ComedyCulture,
                                   target_culture: ComedyCulture) -> List[str]:
        """Identify cultural barriers in joke adaptation"""
        barriers = []
        text_lower = text.lower()

        # US-specific barriers
        if original_culture == ComedyCulture.US:
            us_barriers = ['congress', 'senate', 'republican', 'democrat', 'baseball', 'thanksgiving']
            if any(barrier in text_lower for barrier in us_barriers):
                barriers.append("US-specific political/sports references")

        # UK-specific barriers
        if original_culture == ComedyCulture.UK:
            uk_barriers = ['parliament', 'tory', 'labour', 'british class', 'pub culture']
            if any(barrier in text_lower for barrier in uk_barriers):
                barriers.append("UK-specific class/political references")

        # Indian-specific barriers
        if original_culture == ComedyCulture.INDIAN:
            indian_barriers = ['bollywood', 'arranged marriage', 'indian parents', 'desi']
            if any(barrier in text_lower for barrier in indian_barriers):
                barriers.append("Indian-specific cultural references")

        # Language barriers
        if original_features := self.cultural_features.get(original_culture):
            if original_features.language_complexity > 0.7:
                barriers.append("High language complexity")

        return barriers

    def _find_universal_humor_elements(self, text: str) -> List[str]:
        """Identify universally understandable humor elements"""
        universal_elements = []
        text_lower = text.lower()

        # Universal themes
        universal_themes = {
            'family': ['mom', 'dad', 'family', 'parents', 'children'],
            'relationships': ['girlfriend', 'boyfriend', 'wife', 'husband', 'dating'],
            'everyday life': ['work', 'job', 'money', 'food', 'sleep'],
            'human behavior': ['awkward', 'embarrassing', 'weird', 'strange', 'funny']
        }

        for theme, keywords in universal_themes.items():
            if any(keyword in text_lower for keyword in keywords):
                universal_elements.append(theme)

        # Universal techniques
        if '?' in text:
            universal_elements.append('question-answer format')

        if text.count('!') > 2:
            universal_elements.append('emphasized delivery')

        return universal_elements

    def _get_required_adaptations(self, original_culture: ComedyCulture,
                                 target_culture: ComedyCulture) -> List[str]:
        """Get required adaptations for cultural translation"""
        adaptations = []

        if original_culture == ComedyCulture.US and target_culture == ComedyCulture.UK:
            adaptations = [
                "Reduce directness levels",
                "Increase sarcasm and irony",
                "Replace US-specific pop culture references",
                "Add self-deprecating elements",
                "Adjust timing for longer pauses"
            ]
        elif original_culture == ComedyCulture.UK and target_culture == ComedyCulture.US:
            adaptations = [
                "Increase directness",
                "Reduce irony levels",
                "Add more physical comedy descriptors",
                "Localize cultural references",
                "Speed up delivery pace"
            ]
        elif original_culture in [ComedyCulture.US, ComedyCulture.UK] and target_culture == ComedyCulture.INDIAN:
            adaptations = [
                "Add family dynamics context",
                "Include immigrant perspective if applicable",
                "Add cultural identity elements",
                "Explain Western cultural references",
                "Include cross-cultural comparisons"
            ]
        elif original_culture == ComedyCulture.INDIAN and target_culture in [ComedyCulture.US, ComedyCulture.UK]:
            adaptations = [
                "Provide cultural context for Indian references",
                "Emphasize universal family themes",
                "Explain Bollywood references",
                "Highlight immigrant experience universality",
                "Bridge cultural gaps with comparisons"
            ]

        return adaptations

    def _generate_adaptation_suggestions(self, text: str, original_culture: ComedyCulture,
                                       target_culture: ComedyCulture,
                                       barriers: List[str]) -> List[str]:
        """Generate specific adaptation suggestions"""
        suggestions = []

        # Address cultural barriers
        if 'US-specific' in ' '.join(barriers):
            suggestions.append("Replace US political references with equivalent UK/Indian institutions")

        if 'UK-specific' in ' '.join(barriers):
            suggestions.append("Translate British class references to universal social dynamics")

        if 'Indian-specific' in ' '.join(barriers):
            suggestions.append("Explain Indian cultural context or find Western equivalents")

        # Culture-specific suggestions
        if target_culture == ComedyCulture.UK:
            suggestions.append("Add ironic twists and cynical perspective")
            suggestions.append("Incorporate self-deprecating humor")

        if target_culture == ComedyCulture.US:
            suggestions.append("Add more direct punchlines and clear callbacks")
            suggestions.append("Include physical comedy descriptors")

        if target_culture == ComedyCulture.INDIAN:
            suggestions.append("Emphasize family relatability and cultural identity")
            suggestions.append("Add cross-cultural comparison elements")

        return suggestions

    def evaluate_cultural_appropriateness(self, text: str, target_audience: ComedyCulture) -> Dict[str, float]:
        """
        Evaluate cultural appropriateness for target audience.

        Args:
            text: Comedy content
            target_audience: Target cultural audience

        Returns:
            Dictionary with appropriateness metrics
        """
        # Extract features
        detected_culture, _ = self.detect_cultural_context(text)
        features = self.extract_cultural_features(text, detected_culture)
        target_baseline = self.cultural_features.get(target_audience,
                                                     self.cultural_features[ComedyCulture.US])

        # Calculate appropriateness scores
        scores = {}

        # Cultural alignment score
        scores['cultural_alignment'] = self._calculate_cultural_alignment(features, target_baseline)

        # Humor preservation score
        scores['humor_preservation'] = self._calculate_humor_preservation(features, target_baseline)

        # Offense risk score
        scores['offense_risk'] = self._calculate_offense_risk(features, target_audience)

        # Audience engagement prediction
        scores['engagement_prediction'] = self._predict_engagement(features, target_baseline)

        # Overall appropriateness
        scores['overall_appropriateness'] = (
            scores['cultural_alignment'] * 0.3 +
            scores['humor_preservation'] * 0.3 +
            (1 - scores['offense_risk']) * 0.2 +
            scores['engagement_prediction'] * 0.2
        )

        return scores

    def _calculate_cultural_alignment(self, features: ComedyCulturalFeatures,
                                    target_baseline: ComedyCulturalFeatures) -> float:
        """Calculate alignment with target culture"""
        alignments = [
            1 - abs(features.directness_score - target_baseline.directness_score),
            1 - abs(features.sarcasm_level - target_baseline.sarcasm_level),
            1 - abs(features.irony_level - target_baseline.irony_level),
            1 - abs(features.self_deprecation - target_baseline.self_deprecation)
        ]
        return sum(alignments) / len(alignments)

    def _calculate_humor_preservation(self, features: ComedyCulturalFeatures,
                                    target_baseline: ComedyCulturalFeatures) -> float:
        """Calculate how well humor will be preserved"""
        # Universal elements preservation
        universal_score = min(features.family_dynamics + 0.3, 1.0)

        # Timing compatibility
        timing_diff = abs(features.timing_patterns['setup_punch_ratio'] -
                        target_baseline.timing_patterns['setup_punch_ratio'])
        timing_score = 1 - timing_diff

        return (universal_score + timing_score) / 2

    def _calculate_offense_risk(self, features: ComedyCulturalFeatures,
                              target_audience: ComedyCulture) -> float:
        """Calculate potential offense risk"""
        risk_factors = []

        # Political sensitivity varies by culture
        if features.political_commentary > 0.7:
            if target_audience == ComedyCulture.US:
                risk_factors.append(0.6)  # US has high political polarization
            elif target_audience == ComedyCulture.UK:
                risk_factors.append(0.4)  # UK more tolerant of political comedy
            else:
                risk_factors.append(0.5)

        # Dark humor estimation based on irony and sarcasm
        dark_humor_estimate = (features.irony_level + features.sarcasm_level) / 2
        if dark_humor_estimate > 0.7:
            risk_factors.append(0.5)

        # Cultural sensitivity
        if features.cultural_identity_refs > 0.8 and target_audience != ComedyCulture.INDIAN:
            risk_factors.append(0.4)

        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.1

    def _predict_engagement(self, features: ComedyCulturalFeatures,
                          target_baseline: ComedyCulturalFeatures) -> float:
        """Predict audience engagement"""
        engagement_factors = []

        # Pop culture relevance
        if abs(features.pop_culture_refs - target_baseline.pop_culture_refs) < 0.3:
            engagement_factors.append(0.8)
        else:
            engagement_factors.append(0.5)

        # Timing compatibility
        timing_compatibility = 1 - abs(features.timing_patterns['average_pause_duration'] -
                                      target_baseline.timing_patterns['average_pause_duration'])
        engagement_factors.append(timing_compatibility)

        # Language accessibility
        language_accessibility = 1 - abs(features.language_complexity -
                                        target_baseline.language_complexity)
        engagement_factors.append(language_accessibility)

        return sum(engagement_factors) / len(engagement_factors)

    def create_comedian_dataset(self, output_dir: str) -> Dict[str, List[str]]:
        """
        Create comprehensive dataset curation guide for each comedian style.

        Args:
            output_dir: Directory to save dataset guides

        Returns:
            Dictionary mapping comedian names to data source recommendations
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        dataset_sources = {}

        # US Comedy Sources
        us_sources = {
            'dave_chappelle': [
                "Netflix: 'Killin\' Them Softly', 'The Bird Revelation', 'Sticks & Stones'",
                "HBO: 'Killin\' Them Softly' (2000)",
                "Comedy Central: 'Chappelle\'s Show' episodes",
                "YouTube: Official Netflix Comedy specials",
                "Transcript sources: HBO official transcripts, comedy databases"
            ],
            'kevin_hart': [
                "Netflix: 'Laugh at My Pain', 'Let Me Explain', 'Irresponsible'",
                "Comedy Central: 'Seriously Funny' series",
                "YouTube: Official Kevin Hart channel clips",
                "Audio: Spotify comedy specials",
                "Social media: Instagram comedy clips"
            ],
            'jerry_seinfeld': [
                "Netflix: 'Jerry Before Seinfeld', '23 Hours to Kill'",
                "HBO: 'I'm Telling You for the Last Time' (1998)",
                "Amazon Prime: 'Seinfeld' stand-up clips",
                "YouTube: Official Jerry Seinfeld channel",
                "Books: 'Seinlanguage' for written comedy style"
            ]
        }

        # UK Comedy Sources
        uk_sources = {
            'ricky_gervais': [
                "Netflix: 'Humanity', 'After Life', 'SuperNature'",
                "HBO: 'Animals' (2002), 'Politics' (2004)",
                "BBC: 'The Office' UK series director's commentary",
                "YouTube: Official Ricky Gervais channel",
                "Podcasts: 'The Ricky Gervais Show' transcripts"
            ],
            'john_cleese': [
                "BBC: 'Monty Python's Flying Circus' episodes",
                "Netflix: 'Monty Python' compilations",
                "YouTube: 'Monty Python' official channel",
                "Books: 'The Pythons' autobiography",
                "Documentaries: 'Monty Python: The Meaning of Live'"
            ],
            'eddie_izzard': [
                "Netflix: 'Dressed to Kill', 'Circle', 'Sexie'",
                "HBO: 'Dressed to Kill' (1998)",
                "YouTube: Eddie Izzard stand-up specials",
                "Audio: Spotify comedy albums",
                "Live recordings: Various venue performances"
            ]
        }

        # Indian Comedy Sources
        indian_sources = {
            'vir_das': [
                "Netflix: 'Abroad Understanding', 'Losing It', 'Vir Das: For India'",
                "Amazon Prime: 'Vir Das: Has It Come to This?'",
                "YouTube: Vir Das official channel clips",
                "TED Talks: 'Vir Das: The essence of comedy'",
                "Spotify: 'Vir Das' comedy albums"
            ],
            'hasan_minhaj': [
                "Netflix: 'Homecoming King', 'The King's Jester'",
                "YouTube: 'Patriot Act' transcripts",
                "Podcast: 'Pod Save the People' guest appearances",
                "Social media: Instagram comedy clips",
                "News interviews: Political commentary segments"
            ],
            'aziz_ansari': [
                "Netflix: 'Buried Alive', 'Right Now', 'Nightclub Comedian'",
                "YouTube: 'Aziz Ansari: Live at Madison Square Garden'",
                "Audio: 'Dangerously Delicious' album",
                "TV: 'Master of None' stand-up segments",
                "Podcast appearances and interviews"
            ]
        }

        # Cross-Cultural Sources
        cross_cultural_sources = {
            'international_comedy_festivals': [
                "Just for Laughs (Montreal) - Best of specials",
                "Edinburgh Comedy Festival - Award winners",
                "Melbourne International Comedy Festival",
                "Netflix Comedy Festival compilations",
                "Comedy Central Stand-Up specials"
            ],
            'global_platforms': [
                "Netflix International - 'Comedians of the World' series",
                "Amazon Prime Video - Global comedy collections",
                "HBO Max - International stand-up showcase",
                "YouTube Premium - Original comedy content",
                "Spotify - Global comedy album collection"
            ]
        }

        # Combine all sources
        dataset_sources.update(us_sources)
        dataset_sources.update(uk_sources)
        dataset_sources.update(indian_sources)
        dataset_sources.update(cross_cultural_sources)

        # Save dataset curation guide
        guide_file = output_path / "dataset_sources_guide.json"
        with open(guide_file, 'w') as f:
            json.dump(dataset_sources, f, indent=2)

        # Create preprocessing guide
        preprocessing_guide = {
            'audio_preprocessing': {
                'us_comedy': {
                    'sample_rate': 44100,
                    'quality_threshold': 'high',
                    'accent_normalization': False,
                    'laughter_detection': True,
                    'audience_interaction': True
                },
                'uk_comedy': {
                    'sample_rate': 44100,
                    'quality_threshold': 'high',
                    'accent_normalization': False,
                    'laughter_detection': True,
                    'audience_interaction': True
                },
                'indian_comedy': {
                    'sample_rate': 44100,
                    'quality_threshold': 'medium_high',
                    'accent_normalization': False,
                    'laughter_detection': True,
                    'audience_interaction': True,
                    'code_switching_detection': True
                }
            },
            'transcript_processing': {
                'accent_preservation': True,
                'cultural_references': True,
                'timing_information': True,
                'audience_reactions': True,
                'non_verbal_cues': True
            },
            'cultural_markup': {
                'us_markers': True,
                'uk_markers': True,
                'indian_markers': True,
                'pop_culture_refs': True,
                'political_refs': True
            }
        }

        preprocessing_file = output_path / "preprocessing_guide.json"
        with open(preprocessing_file, 'w') as f:
            json.dump(preprocessing_guide, f, indent=2)

        return dataset_sources

    def save_model(self, save_path: str):
        """Save the processor state"""
        model_data = {
            'cultural_profiles': self.cultural_profiles,
            'cultural_features': self.cultural_features,
            'cross_cultural_patterns': self.cross_cultural_patterns
        }

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)

    def load_models(self, model_path: str):
        """Load the processor state"""
        model_path = Path(model_path)

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.cultural_profiles = model_data['cultural_profiles']
        self.cultural_features = model_data['cultural_features']
        self.cross_cultural_patterns = model_data['cross_cultural_patterns']

# Demo and Testing Functions
def demo_global_english_comedy_system():
    """Demonstrate the Global English Comedy System capabilities"""

    print("🎭 Global English Comedy System Demo")
    print("=" * 50)

    # Initialize processor
    processor = GlobalEnglishComedyProcessor()

    # Test samples from different cultures
    test_samples = {
        'us_comedy': """
        So I was at this restaurant in New York, right? And the waitress comes over,
        and I'm like, "Can I get some extra napkins?" She looks at me like I just
        asked for her kidney! I'm thinking, "It's just napkins, not a marriage proposal!"
        Sometimes I think customer service in America is like playing Russian roulette
        with politeness.
        """,

        'uk_comedy': """
        It's quite funny, really. I went to the local pub in London, ordered a pint,
        and the barman looks at me with this utterly bored expression. You know that
        look British people have when they're judging your life choices? Yes, quite.
        He says, "That'll be £6.50, then." Six pounds fifty! For a pint of beer!
        I stood there wondering if the beer was brewed by the Queen herself or if
        I was paying for the privilege of breathing British air.
        """,

        'indian_comedy': """
        You know, when I first moved to America from India, I didn't understand
        the concept of "roommate." In India, we live with our parents until marriage,
        sometimes even after. I called my mom and said, "Mom, I have a roommate."
        She panicked! "Roommate? Is it a girl? Is it a boy? What will people say?"
        I had to explain, "No Mom, it's just a guy who shares the rent."
        She was like, "Oh, so like a joint family but without the family part.
        Why would anyone do that voluntarily?"
        """
    }

    # Process each sample
    for culture, sample in test_samples.items():
        print(f"\n🎭 Processing {culture.upper()} Comedy Sample:")
        print("-" * 40)

        # Detect cultural context
        detected_culture, confidence = processor.detect_cultural_context(sample)
        print(f"Detected Culture: {detected_culture.value} (confidence: {confidence:.2f})")

        # Identify comedian style
        similar_comedians = processor.identify_comedian_style(sample, detected_culture)
        print(f"\nSimilar Comedians:")
        for comedian, score in similar_comedians:
            print(f"  - {comedian}: {score:.2f}")

        # Extract cultural features
        features = processor.extract_cultural_features(sample, detected_culture)
        print(f"\nCultural Features:")
        print(f"  - Directness: {features.directness_score:.2f}")
        print(f"  - Sarcasm: {features.sarcasm_level:.2f}")
        print(f"  - Irony: {features.irony_level:.2f}")
        print(f"  - Family Dynamics: {features.family_dynamics:.2f}")
        print(f"  - Cultural Identity: {features.cultural_identity_refs:.2f}")

    # Test cross-cultural adaptation
    print("\n🎭 Cross-Cultural Adaptation Test:")
    print("-" * 40)

    indian_joke = test_samples['indian_comedy']
    analysis = processor.adapt_joke_cross_cultural(indian_joke, ComedyCulture.US)

    print(f"Original Culture: {analysis.original_culture.value}")
    print(f"Target Culture: {analysis.target_culture.value}")
    print(f"Adaptation Score: {analysis.cultural_adaptation_score:.2f}")
    print(f"Humor Preservation: {analysis.humor_preservation_score:.2f}")
    print(f"\nRequired Adaptations:")
    for adaptation in analysis.required_adaptations:
        print(f"  - {adaptation}")
    print(f"\nCultural Barriers:")
    for barrier in analysis.cultural_barriers:
        print(f"  - {barrier}")
    print(f"\nUniversal Elements:")
    for element in analysis.universal_elements:
        print(f"  - {element}")

if __name__ == "__main__":
    demo_global_english_comedy_system()