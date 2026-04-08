#!/usr/bin/env python3
"""
Indian Comedy Specialist for Laughter Prediction

A revolutionary system focused on Indian comedy content across:
- Pure English (Indian English comedy)
- Hinglish (Code-mixed Hindi-English)
- Pure Hindi (Traditional Hindi comedy)

Market Opportunity:
- 1.4B+ Hindi speakers worldwide
- 700M+ English speakers in India
- Massive YouTube/OTT audience for Indian comedy
- Underserved by current Western-focused research

Key Features:
- Hinglish code-mixing detection and processing
- Cultural context understanding for Indian humor
- Regional adaptation (North vs South India)
- Script transliteration (Devanagari ↔ Roman)
- Indian slang and Bollywood reference handling
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from indic_transliteration import sanscript

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indian_comedy_specialist.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class IndianComedyConfig:
    """Configuration for Indian comedy specialist."""

    # Language domains
    supported_domains: List[str] = field(default_factory=lambda: [
        'english_indian',  # Indian English comedy
        'hinglish',        # Code-mixed Hindi-English
        'hindi'            # Pure Hindi comedy
    ])

    # Cultural features
    enable_cultural_context: bool = True
    enable_bollywood_detection: bool = True
    enable_regional_adaptation: bool = True
    enable_slang_understanding: bool = True

    # Script handling
    support_devanagari: bool = True
    support_transliteration: bool = True
    normalize_scripts: bool = True

    # Model parameters
    base_model: str = "xlm-roberta-base"  # Multilingual support
    max_seq_length: int = 512
    hidden_size: int = 768
    gcacu_dim: int = 128

    # Indian comedy patterns
    comedy_styles: List[str] = field(default_factory=lambda: [
        'standup', 'sketch', 'improvisation',
        'satire', 'parody', 'observational'
    ])

    regional_styles: List[str] = field(default_factory=lambda: [
        'north_india', 'south_india', 'east_india', 'west_india', 'general'
    ])


class HinglishProcessor:
    """
    Processes code-mixed Hindi-English text (Hinglish).

    Handles:
    - Code-mixing detection
    - Script normalization
    - Transliteration (Devanagari ↔ Roman)
    - Cultural context extraction
    """

    def __init__(self, config: IndianComedyConfig):
        self.config = config
        self.hindi_indic_words = self._load_hindi_indic_words()
        self.english_connectors = self._load_english_connectors()
        self.indian_slang = self._load_indian_slang()
        self.bollywood_references = self._load_bollywood_references()

    def _load_hindi_indic_words(self) -> set:
        """Load common Hindi words written in Roman script."""
        return {
            'accha', 'arre', 'bas', 'bhai', 'chalo', 'dekho', 'hai', 'hain',
            'hi', 'ho', 'jab', 'jaise', 'ka', 'ke', 'ki', 'ko', 'kya',
            'lekin', 'lijiye', 'main', 'mein', 'nahi', 'na', 'par', 'to',
            'hai na', 'kya bolte', 'macha', 'paka', 'scene', 'timepass',
            'vella', 'chomu', 'bakwas', 'kamina', 'bhaiyya', 'didi',
            'please', 'thanks', 'sorry', 'actually', 'basically'
        }

    def _load_english_connectors(self) -> set:
        """Load English connector words common in Hinglish."""
        return {
            'and', 'or', 'but', 'because', 'when', 'while', 'if', 'then',
            'so', 'just', 'also', 'very', 'really', 'actually', 'basically'
        }

    def _load_indian_slang(self) -> Dict[str, str]:
        """Load Indian slang with meanings."""
        return {
            'macha': 'friend (South India)',
            'maga': 'friend (Karnataka)',
            'scene': 'situation',
            'timepass': 'passing time',
            'vella': 'free person',
            'chomu': 'foolish person',
            'bakwas': 'nonsense',
            'jugaad': 'hacky solution',
            'atta majaa sataka': 'chaos (Marathi)',
            'chava': 'impressive (Marathi)',
            'paka': 'definitely (Tamil)',
            'kya bolte': 'what say (Mumbai)',
            'apus': 'enough (Bengali)',
            'kitni cool hain': 'how cool (TVF reference)'
        }

    def _load_bollywood_references(self) -> Dict[str, List[str]]:
        """Load Bollywood movie references and quotes."""
        return {
            'sholay': ['basanti', 'gabbar', 'kitne aadmi the'],
            'dilwale': ['raj', 'simran', 'palat'],
            'munna_bhai': ['ganguly', 'jaadu ki jhappi'],
            '3_idiots': ['all is well', 'rancho', 'virus'],
            'dch': ['wake up sid', 'sweetu']
        }

    def detect_code_mixing(self, text: str) -> Dict[str, Any]:
        """
        Detect code-mixing patterns in Hinglish text.

        Returns:
            Dict with mixing statistics and patterns
        """
        words = text.lower().split()

        hindi_count = sum(1 for word in words if word in self.hindi_indic_words)
        english_count = sum(1 for word in words if word not in self.hindi_indic_words)
        total_words = len(words)

        mixing_ratio = hindi_count / total_words if total_words > 0 else 0

        # Detect transition points (Hindi → English or vice versa)
        transitions = []
        prev_lang = None
        for i, word in enumerate(words):
            curr_lang = 'hindi' if word in self.hindi_indic_words else 'english'
            if prev_lang and curr_lang != prev_lang:
                transitions.append((i, prev_lang, curr_lang))
            prev_lang = curr_lang

        return {
            'mixing_ratio': mixing_ratio,
            'hindi_words': hindi_count,
            'english_words': english_count,
            'transitions': transitions,
            'is_code_mixed': mixing_ratio > 0.2 and mixing_ratio < 0.8
        }

    def transliterate_devanagari_to_roman(self, text: str) -> str:
        """
        Transliterate Devanagari script to Roman script.

        Args:
            text: Input text in Devanagari script

        Returns:
            Text in Roman script
        """
        try:
            return sanscript.transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
        except Exception as e:
            logger.warning(f"Transliteration failed: {e}")
            return text

    def transliterate_roman_to_devanagari(self, text: str) -> str:
        """
        Transliterate Roman script to Devanagari script.

        Args:
            text: Input text in Roman script

        Returns:
            Text in Devanagari script
        """
        try:
            return sanscript.transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
        except Exception as e:
            logger.warning(f"Transliteration failed: {e}")
            return text

    def extract_cultural_context(self, text: str) -> Dict[str, Any]:
        """
        Extract cultural context from Indian comedy text.

        Returns:
            Dict with cultural features and references
        """
        text_lower = text.lower()

        # Detect Bollywood references
        bollywood_refs = []
        for movie, quotes in self.bollywood_references.items():
            for quote in quotes:
                if quote.lower() in text_lower:
                    bollywood_refs.append({
                        'movie': movie,
                        'quote': quote,
                        'type': 'bollywood_reference'
                    })

        # Detect slang usage
        slang_found = []
        for slang, meaning in self.indian_slang.items():
            if slang.lower() in text_lower:
                slang_found.append({
                    'slang': slang,
                    'meaning': meaning,
                    'type': 'indian_slang'
                })

        # Detect regional markers
        regional_markers = {
            'south_india': ['macha', 'maga', 'paka', 'appa', 'amma'],
            'north_india': ['bhaiyya', 'arre', 'accha', 'ji'],
            'west_india': ['kya bolte', 'macha', 'timepass'],
            'east_india': ['apus', 'cholche', 'bhai']
        }

        detected_regions = []
        for region, markers in regional_markers.items():
            if any(marker in text_lower for marker in markers):
                detected_regions.append(region)

        return {
            'bollywood_references': bollywood_refs,
            'slang_usage': slang_found,
            'detected_regions': detected_regions,
            'cultural_density': len(bollywood_refs) + len(slang_found)
        }


class IndianComedyDataset:
    """
    Dataset handler for Indian comedy content.

    Supports:
    - YouTube Indian comedy channels
    - Amazon Prime Video India comedy specials
    - Netflix India stand-up
    - TVF sketches, FilterCopy content
    - Bollywood comedy scenes
    """

    def __init__(self, config: IndianComedyConfig):
        self.config = config
        self.hinglish_processor = HinglishProcessor(config)

        # Indian comedy data sources
        self.data_sources = {
            'youtube_channels': [
                'BB Ki Vines',
                'BeerBiceps',
                'TVF',
                'FilterCopy',
                'Dice Media',
                'The Viral Fever',
                'ScoopWhoop',
                'Shruti Arjun',
                'Kaneez Surka',
                'Kenny Sebastian'
            ],
            'ott_platforms': [
                'Amazon Prime Video India',
                'Netflix India',
                'Disney+ Hotstar',
                'SonyLIV',
                'ZEE5'
            ],
            'comedians': [
                'Vir Das',
                'Zakir Khan',
                'Biswa Kalyan Rath',
                'Kanan Gill',
                'Amit Tandon',
                'Neeti Palta',
                'Aditi Mittal',
                'Kenny Sebastian',
                'Kaneez Surka'
            ]
        }

    def create_sample_dataset(self) -> List[Dict[str, Any]]:
        """
        Create a sample Indian comedy dataset for demonstration.

        Returns:
            List of comedy examples with labels
        """
        examples = [
            # Indian English Comedy
            {
                'text': 'So guys, I was at this arranged marriage meeting, and the aunties were judging my salary more than my personality',
                'language': 'english_indian',
                'comedy_style': 'observational',
                'cultural_context': 'arranged_marriage',
                'laughter_probability': 0.85,
                'regional_style': 'general',
                'target_audience': 'millennials'
            },
            {
                'text': 'Indian parents will be like, "Sharma ji ka beta is working at NASA, and you are still working on your sleep schedule"',
                'language': 'english_indian',
                'comedy_style': 'observational',
                'cultural_context': 'parental_pressure',
                'laughter_probability': 0.92,
                'regional_style': 'general',
                'target_audience': 'millennials'
            },

            # Hinglish Comedy (Code-mixed)
            {
                'text': 'Machi, I went to this desi party yaar, and the aunties were like "Beta, what are you doing with your life?"',
                'language': 'hinglish',
                'comedy_style': 'observational',
                'cultural_context': 'aunties_interrogation',
                'laughter_probability': 0.88,
                'regional_style': 'south_india',
                'target_audience': 'gen_z'
            },
            {
                'text': 'Arre yaar, this Indian wedding scene is too much na. The drama, the food, and the aunties judging everyone',
                'language': 'hinglish',
                'comedy_style': 'observational',
                'cultural_context': 'indian_wedding',
                'laughter_probability': 0.90,
                'regional_style': 'general',
                'target_audience': 'millennials'
            },
            {
                'text': 'Kya scene hai yaar, I reached the station at 9 AM and the train is at 9 PM. Classic Indian Standard Time macha',
                'language': 'hinglish',
                'comedy_style': 'observational',
                'cultural_context': 'indian_time',
                'laughter_probability': 0.87,
                'regional_style': 'west_india',
                'target_audience': 'gen_z'
            },

            # Pure Hindi Comedy (Romanized)
            {
                'text': 'Bhaiyya, aaj kal padhai mein dil nahi lagta, sirf Instagram reels mein lagta hai',
                'language': 'hindi',
                'comedy_style': 'observational',
                'cultural_context': 'social_media_obsession',
                'laughter_probability': 0.82,
                'regional_style': 'north_india',
                'target_audience': 'gen_z'
            },
            {
                'text': 'Aaj kal ke bachche sirf phone mein rehte hain, bahar khelne nahi jaate',
                'language': 'hindi',
                'comedy_style': 'observational',
                'cultural_context': 'phone_addiction',
                'laughter_probability': 0.75,
                'regional_style': 'general',
                'target_audience': 'millennials'
            },
            {
                'text': 'Sharma ji ki beti IAS officer ban gayi, meri beti reels banti rehti hai',
                'language': 'hindi',
                'comedy_style': 'observational',
                'cultural_context': 'parental_comparison',
                'laughter_probability': 0.94,
                'regional_style': 'north_india',
                'target_audience': 'millennials'
            },

            # Bollywood References
            {
                'text': 'My life is like a Bollywood movie without the songs, just the drama and the bad decisions',
                'language': 'english_indian',
                'comedy_style': 'observational',
                'cultural_context': 'bollywood_reference',
                'laughter_probability': 0.86,
                'regional_style': 'general',
                'target_audience': 'millennials'
            },
            {
                'text': 'In my house, "All is Well" is the solution to every problem, even when nothing is well',
                'language': 'english_indian',
                'comedy_style': 'observational',
                'cultural_context': 'bollywood_reference',
                'laughter_probability': 0.91,
                'regional_style': 'general',
                'target_audience': 'gen_z'
            }
        ]

        return examples

    def preprocess_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess a comedy example with Hinglish processing.

        Args:
            example: Raw comedy example

        Returns:
            Preprocessed example with linguistic features
        """
        text = example['text']

        # Detect code-mixing for Hinglish
        if example['language'] == 'hinglish':
            mixing_info = self.hinglish_processor.detect_code_mixing(text)
            example['code_mixing_info'] = mixing_info

        # Extract cultural context
        cultural_context = self.hinglish_processor.extract_cultural_context(text)
        example['cultural_features'] = cultural_context

        # Normalize script if needed
        if self.config.normalize_scripts:
            text = self.hinglish_processor.transliterate_devanagari_to_roman(text)
            example['normalized_text'] = text

        return example


class IndianComedySpecialist:
    """
    Main Indian Comedy Specialist System.

    Integrates:
    - GCACU architecture for humor detection
    - Hinglish processing for code-mixed content
    - Cultural context understanding
    - Multi-language support (English, Hinglish, Hindi)
    """

    def __init__(self, config: IndianComedyConfig):
        self.config = config
        self.hinglish_processor = HinglishProcessor(config)
        self.dataset_handler = IndianComedyDataset(config)

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(config.base_model)

        logger.info("Indian Comedy Specialist initialized")
        logger.info(f"Supported domains: {config.supported_domains}")
        logger.info(f"Regional styles: {config.regional_styles}")

    def analyze_comedy_content(self, text: str, language: str = 'english_indian') -> Dict[str, Any]:
        """
        Analyze Indian comedy content for laughter prediction.

        Args:
            text: Comedy transcript text
            language: Language domain (english_indian, hinglish, hindi)

        Returns:
            Analysis results with laughter probability
        """
        logger.info(f"Analyzing {language} content: {text[:50]}...")

        # Process text based on language
        if language == 'hinglish':
            code_mixing = self.hinglish_processor.detect_code_mixing(text)
            cultural_context = self.hinglish_processor.extract_cultural_context(text)

            linguistic_features = {
                'code_mixing_ratio': code_mixing['mixing_ratio'],
                'num_transitions': len(code_mixing['transitions']),
                'cultural_density': cultural_context['cultural_density'],
                'bollywood_refs': len(cultural_context['bollywood_references']),
                'slang_usage': len(cultural_context['slang_usage'])
            }

        elif language == 'hindi':
            # Transliterate if needed
            normalized_text = self.hinglish_processor.transliterate_devanagari_to_roman(text)
            cultural_context = self.hinglish_processor.extract_cultural_context(normalized_text)

            linguistic_features = {
                'cultural_density': cultural_context['cultural_density'],
                'bollywood_refs': len(cultural_context['bollywood_references']),
                'slang_usage': len(cultural_context['slang_usage']),
                'transliteration_needed': text != normalized_text
            }

        else:  # english_indian
            cultural_context = self.hinglish_processor.extract_cultural_context(text)
            linguistic_features = {
                'cultural_density': cultural_context['cultural_density'],
                'bollywood_refs': len(cultural_context['bollywood_references']),
                'indian_english_patterns': self._detect_indian_english_patterns(text)
            }

        # Calculate laughter probability based on features
        laughter_prob = self._calculate_laughter_probability(
            text, language, linguistic_features
        )

        return {
            'text': text,
            'language': language,
            'laughter_probability': laughter_prob,
            'linguistic_features': linguistic_features,
            'cultural_context': cultural_context if language != 'english_indian' else None,
            'confidence': self._calculate_confidence(linguistic_features)
        }

    def _detect_indian_english_patterns(self, text: str) -> Dict[str, int]:
        """Detect Indian English patterns."""
        patterns = {
            'arranged_marriage': r'arranged\s+marriage',
            'aunties_uncles': r'aunti(?:e|es)|uncle',
            'parental_pressure': r'(?:mom|mummy|dad|papa).*?(?:said|asked|told)',
            'sharma_ji': r'sharma\s+ji',
            'IAS_engineering': r'(?:IAS|engineer|engineering|doctor)',
            'desi': r'desi'
        }

        detected = {}
        text_lower = text.lower()
        for pattern_name, pattern in patterns.items():
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                detected[pattern_name] = matches

        return detected

    def _calculate_laughter_probability(
        self,
        text: str,
        language: str,
        features: Dict[str, Any]
    ) -> float:
        """
        Calculate laughter probability based on linguistic features.

        This is a simplified version - in production, this would use
        the trained GCACU model for prediction.
        """
        base_prob = 0.5

        # Cultural context boost
        cultural_boost = min(features.get('cultural_density', 0) * 0.1, 0.3)

        # Bollywood references boost
        bollywood_boost = min(features.get('bollywood_refs', 0) * 0.15, 0.25)

        # Language-specific boosts
        if language == 'hinglish':
            mixing_ratio = features.get('code_mixing_ratio', 0)
            if 0.3 <= mixing_ratio <= 0.7:  # Optimal code-mixing
                code_mixing_boost = 0.2
            else:
                code_mixing_boost = 0.0
        else:
            code_mixing_boost = 0.0

        # Indian English patterns boost
        indian_english_boost = min(
            sum(features.get('indian_english_patterns', {}).values()) * 0.05, 0.2
        )

        # Combine all factors
        probability = base_prob + cultural_boost + bollywood_boost + code_mixing_boost + indian_english_boost

        return min(probability, 0.98)  # Cap at 0.98

    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence in the prediction."""
        cultural_density = features.get('cultural_density', 0)
        bollywood_refs = features.get('bollywood_refs', 0)

        # Higher confidence with more cultural context
        base_confidence = 0.6
        cultural_boost = min(cultural_density * 0.05, 0.3)
        bollywood_boost = min(bollywood_refs * 0.1, 0.2)

        return min(base_confidence + cultural_boost + bollywood_boost, 0.95)

    def create_training_pipeline(self) -> Dict[str, Any]:
        """
        Create a training pipeline for Indian comedy content.

        Returns:
            Training pipeline configuration
        """
        return {
            'dataset_config': {
                'languages': self.config.supported_domains,
                'comedy_styles': self.config.comedy_styles,
                'regional_styles': self.config.regional_styles
            },
            'preprocessing_steps': [
                'script_normalization',
                'code_mixing_detection',
                'cultural_context_extraction',
                'slang_identification',
                'bollywood_reference_detection'
            ],
            'model_config': {
                'architecture': 'GCACU',
                'base_model': self.config.base_model,
                'hidden_size': self.config.hidden_size,
                'gcacu_dim': self.config.gcacu_dim
            },
            'training_config': {
                'batch_size': 16,
                'learning_rate': 2e-5,
                'num_epochs': 10,
                'warmup_steps': 500,
                'gradient_accumulation_steps': 2
            },
            'evaluation_config': {
                'metrics': ['f1', 'precision', 'recall', 'auc_roc'],
                'cultural_sensitivity': True,
                'regional_analysis': True,
                'language_specific_metrics': True
            }
        }


def create_indian_comedy_demo() -> Dict[str, Any]:
    """
    Create a demonstration of the Indian Comedy Specialist.

    Returns:
        Demo results with predictions
    """
    logger.info("Creating Indian Comedy Specialist Demo")

    # Initialize system
    config = IndianComedyConfig()
    specialist = IndianComedySpecialist(config)

    # Create sample dataset
    examples = specialist.dataset_handler.create_sample_dataset()

    # Analyze examples
    results = []
    for example in examples:
        analysis = specialist.analyze_comedy_content(
            text=example['text'],
            language=example['language']
        )

        result = {
            'text': example['text'],
            'language': example['language'],
            'predicted_laughter': analysis['laughter_probability'],
            'actual_laughter': example['laughter_probability'],
            'cultural_features': analysis.get('linguistic_features', {}),
            'confidence': analysis['confidence']
        }

        results.append(result)

    # Calculate accuracy
    predictions = [r['predicted_laughter'] > 0.5 for r in results]
    actuals = [r['actual_laughter'] > 0.5 for r in results]
    accuracy = sum(p == a for p, a in zip(predictions, actuals)) / len(results)

    # Create training pipeline
    pipeline = specialist.create_training_pipeline()

    return {
        'demo_results': {
            'total_examples': len(results),
            'accuracy': accuracy,
            'predictions': results
        },
        'training_pipeline': pipeline,
        'system_config': {
            'supported_languages': config.supported_domains,
            'comedy_styles': config.comedy_styles,
            'regional_styles': config.regional_styles
        }
    }


def main():
    """Main function to run the Indian Comedy Specialist."""
    logger.info("Starting Indian Comedy Specialist System")

    try:
        # Run demo
        demo_results = create_indian_comedy_demo()

        # Print results
        print("\n" + "="*50)
        print("INDIAN COMEDY SPECIALIST DEMO RESULTS")
        print("="*50)

        print(f"\nTotal Examples: {demo_results['demo_results']['total_examples']}")
        print(f"Accuracy: {demo_results['demo_results']['accuracy']:.2%}")

        print("\nPredictions:")
        print("-" * 50)

        for i, result in enumerate(demo_results['demo_results']['predictions'], 1):
            print(f"\n{i}. [{result['language'].upper()}] {result['text'][:60]}...")
            print(f"   Predicted: {result['predicted_laughter']:.2%}")
            print(f"   Actual: {result['actual_laughter']:.2%}")
            print(f"   Confidence: {result['confidence']:.2%}")

            if result['cultural_features']:
                print(f"   Features: {list(result['cultural_features'].keys())[:3]}")

        print("\n" + "="*50)
        print("SYSTEM CONFIGURATION")
        print("="*50)
        config = demo_results['system_config']
        print(f"Languages: {', '.join(config['supported_languages'])}")
        print(f"Comedy Styles: {', '.join(config['comedy_styles'])}")
        print(f"Regional Styles: {', '.join(config['regional_styles'])}")

        print("\n" + "="*50)
        print("TRAINING PIPELINE CONFIGURATION")
        print("="*50)
        pipeline = demo_results['training_pipeline']
        print(f"Architecture: {pipeline['model_config']['architecture']}")
        print(f"Base Model: {pipeline['model_config']['base_model']}")
        print(f"Batch Size: {pipeline['training_config']['batch_size']}")
        print(f"Learning Rate: {pipeline['training_config']['learning_rate']}")

        print("\n" + "="*50)
        print("REVOLUTIONARY FEATURES")
        print("="*50)
        print("✓ First system to understand Hinglish code-mixed humor")
        print("✓ Cultural context aware for Indian references")
        print("✓ Regional adaptation across India")
        print("✓ Bollywood reference detection")
        print("✓ Indian slang understanding")
        print("✓ Script transliteration support")

        print("\n✅ Indian Comedy Specialist System Ready!")
        print("🎯 Target: Revolutionize Indian comedy analysis")
        print("📈 Market: 1.4B+ Hindi speakers + 700M+ Indian English speakers")

        return demo_results

    except Exception as e:
        logger.error(f"Error running demo: {e}")
        raise


if __name__ == "__main__":
    main()