#!/usr/bin/env python3
"""
📊 WESR-BENCH TAXONOMY IMPLEMENTATION
Section 6.3: "Following the 2026 WESR-Bench (Word-level Event-Speech Recognition) 
protocol, the data pipeline now categorizes laughter into two distinct types: 
discrete (standalone audience laughter) and continuous (laughter mixed with the 
comedian's ongoing speech)"
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sqlite3
from dataclasses import dataclass
from enum import Enum

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LaughterCategory(Enum):
    """WESR-Bench laughter categories"""
    DISCRETE = "discrete"      # Standalone audience laughter
    CONTINUOUS = "continuous"  # Mixed with comedian speech
    NO_LAUGHTER = "no_laughter"

@dataclass
class WESRBenchAnnotation:
    """WESR-Bench annotation result"""
    word: str
    timestamp: Tuple[float, float]  # (start, end)
    category: LaughterCategory
    confidence: float
    audio_features: Dict
    
class WESRBenchClassifier:
    """
    📊 WESR-Bench Laughter Classification System
    Implements 2026 Word-level Event-Speech Recognition protocol
    """
    
    def __init__(self):
        self.discrete_indicators = [
            'laughter', 'laughs', 'audience laughter', 'laughter and applause',
            'applause', 'cheering', 'crowd laughs'
        ]
        
        self.continuous_indicators = [
            'laughs while', 'during laughter', 'amid laughter',
            'continues laughing', 'laughs through'
        ]
        
    def classify_laughter_event(self, word_data: Dict, alignment_data: Dict,
                               audio_context: Dict) -> WESRBenchAnnotation:
        """
        Categorize laughter per 2026 WESR-Bench protocol
        Two distinct types: discrete and continuous
        """
        logger.info("📊 Applying WESR-Bench taxonomy...")
        
        word = word_data.get('word', '')
        timestamp = word_data.get('timestamp', (0.0, 0.0))
        
        # Check for discrete laughter indicators
        if self.is_discrete_laughter(word_data, alignment_data, audio_context):
            logger.info(f"✅ Discrete laughter detected: '{word}'")
            return WESRBenchAnnotation(
                word=word,
                timestamp=timestamp,
                category=LaughterCategory.DISCRETE,
                confidence=self.calculate_confidence(word_data, 'discrete'),
                audio_features=self.extract_audio_features(audio_context, 'discrete')
            )
        
        # Check for continuous laughter indicators
        elif self.is_continuous_laughter(word_data, alignment_data, audio_context):
            logger.info(f"✅ Continuous laughter detected: '{word}'")
            return WESRBenchAnnotation(
                word=word,
                timestamp=timestamp,
                category=LaughterCategory.CONTINUOUS,
                confidence=self.calculate_confidence(word_data, 'continuous'),
                audio_features=self.extract_audio_features(audio_context, 'continuous')
            )
        
        # No laughter detected
        else:
            return WESRBenchAnnotation(
                word=word,
                timestamp=timestamp,
                category=LaughterCategory.NO_LAUGHTER,
                confidence=0.9,
                audio_features={}
            )
    
    def is_discrete_laughter(self, word_data: Dict, alignment_data: Dict,
                           audio_context: Dict) -> bool:
        """
        Detect discrete (standalone audience laughter) events
        "discrete (standalone audience laughter)"
        """
        word = word_data.get('word', '').lower()
        
        # Check for explicit laughter indicators
        for indicator in self.discrete_indicators:
            if indicator in word:
                return True
        
        # Check timing patterns (discrete events have clear boundaries)
        if self.has_clear_boundaries(alignment_data, audio_context):
            return True
        
        # Check audio features (isolated laughter segments)
        if self.has_isolated_laughter_audio(audio_context):
            return True
        
        return False
    
    def is_continuous_laughter(self, word_data: Dict, alignment_data: Dict,
                              audio_context: Dict) -> bool:
        """
        Detect continuous (laughter mixed with speech) events
        "continuous (laughter mixed with the comedian's ongoing speech)"
        """
        word = word_data.get('word', '').lower()
        
        # Check for continuous laughter indicators
        for indicator in self.continuous_indicators:
            if indicator in word:
                return True
        
        # Check for overlapping speech patterns
        if self.has_overlapping_speech(alignment_data, audio_context):
            return True
        
        # Check audio features (mixed speech and laughter)
        if self.has_mixed_audio_features(audio_context):
            return True
        
        return False
    
    def has_clear_boundaries(self, alignment_data: Dict, audio_context: Dict) -> bool:
        """Check for clear event boundaries (characteristic of discrete events)"""
        # Discrete laughter has clear start/end points
        timing_data = alignment_data.get('timing', {})
        
        # Check for timing gaps (indicates standalone events)
        if 'gaps_before' in timing_data and timing_data['gaps_before'] > 0.1:
            return True
        
        if 'gaps_after' in timing_data and timing_data['gaps_after'] > 0.1:
            return True
        
        return False
    
    def has_overlapping_speech(self, alignment_data: Dict, audio_context: Dict) -> bool:
        """Check for overlapping speech and laughter (characteristic of continuous)"""
        # Continuous laughter overlaps with comedian speech
        timing_data = alignment_data.get('timing', {})
        
        # Check for timing overlap
        if 'overlap_with_speech' in timing_data and timing_data['overlap_with_speech']:
            return True
        
        # Check audio features
        audio_features = audio_context.get('features', {})
        if 'simultaneous_speech_laughter' in audio_features:
            return True
        
        return False
    
    def has_isolated_laughter_audio(self, audio_context: Dict) -> bool:
        """Check for isolated laughter audio segments"""
        audio_features = audio_context.get('features', {})
        
        # Check for pure laughter segments
        if 'isolated_laughter' in audio_features and audio_features['isolated_laughter']:
            return True
        
        return False
    
    def has_mixed_audio_features(self, audio_context: Dict) -> bool:
        """Check for mixed speech and laughter audio"""
        audio_features = audio_context.get('features', {})
        
        # Check for mixed audio
        if 'mixed_speech_laughter' in audio_features and audio_features['mixed_speech_laughter']:
            return True
        
        return False
    
    def calculate_confidence(self, word_data: Dict, category: str) -> float:
        """Calculate classification confidence"""
        # Base confidence
        confidence = 0.8
        
        # Adjust based on indicators
        word = word_data.get('word', '').lower()
        
        if category == 'discrete':
            for indicator in self.discrete_indicators:
                if indicator in word:
                    confidence += 0.1
        
        elif category == 'continuous':
            for indicator in self.continuous_indicators:
                if indicator in word:
                    confidence += 0.1
        
        return min(confidence, 0.95)
    
    def extract_audio_features(self, audio_context: Dict, category: str) -> Dict:
        """Extract relevant audio features for category"""
        features = {}
        
        if category == 'discrete':
            features = {
                'clear_boundaries': audio_context.get('clear_boundaries', True),
                'isolated_segment': audio_context.get('isolated', True),
                'duration': audio_context.get('laughter_duration', 0.0)
            }
        
        elif category == 'continuous':
            features = {
                'overlap_with_speech': audio_context.get('overlap', True),
                'mixed_audio': audio_context.get('mixed', True),
                'speech_ratio': audio_context.get('speech_ratio', 0.5)
            }
        
        return features

class WESRBenchProcessor:
    """
    📊 WESR-Bench Processing Pipeline
    Applies taxonomy to all harvested comedy data
    """
    
    def __init__(self):
        self.classifier = WESRBenchClassifier()
        self.db_path = "comedy_enhanced_harvest.db"
        
    def process_harvested_data(self):
        """Process all harvested data with WESR-Bench taxonomy"""
        logger.info("📊 APPLYING WESR-BENCH TAXONOMY TO HARVESTED DATA")
        logger.info("=" * 80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all harvested items
        cursor.execute("SELECT id, raw_text, clean_text FROM enhanced_harvest WHERE processed = 1")
        items = cursor.fetchall()
        
        logger.info(f"📊 Processing {len(items)} harvested items...")
        
        for item_id, raw_text, clean_text in items:
            logger.info(f"🔍 Processing: {item_id}")
            
            # Get alignment data if available
            alignment_data = self.get_alignment_data(item_id)
            
            # Process text with WESR-Bench
            annotations = self.process_text_with_taxonomy(item_id, clean_text, alignment_data)
            
            # Save annotations
            self.save_wesr_bench_annotations(item_id, annotations)
        
        conn.close()
        
        logger.info("=" * 80)
        logger.info("✅ WESR-BENCH TAXONOMY PROCESSING COMPLETE")
        
    def get_alignment_data(self, item_id: str) -> Dict:
        """Get alignment data for item"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT word, start_time, end_time, confidence, alignment_method
                FROM alignment_details
                WHERE item_id = ?
                ORDER BY start_time
            """, (item_id,))
            
            alignments = cursor.fetchall()
            
            return {
                'alignments': [
                    {
                        'word': row[0],
                        'start_time': row[1],
                        'end_time': row[2],
                        'confidence': row[3],
                        'method': row[4]
                    }
                    for row in alignments
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting alignment data: {e}")
            return {}
        finally:
            conn.close()
    
    def process_text_with_taxonomy(self, item_id: str, text: str,
                                  alignment_data: Dict) -> List[WESRBenchAnnotation]:
        """Process text with WESR-Bench taxonomy"""
        annotations = []
        
        # Split into words
        words = text.split()
        
        for i, word in enumerate(words):
            # Get timing info if available
            timing = (0.0, 0.0)
            if alignment_data and 'alignments' in alignment_data:
                if i < len(alignment_data['alignments']):
                    align = alignment_data['alignments'][i]
                    timing = (align['start_time'], align['end_time'])
            
            # Create word data
            word_data = {
                'word': word,
                'timestamp': timing,
                'position': i
            }
            
            # Create audio context (demo)
            audio_context = {
                'features': self.demo_audio_features(word)
            }
            
            # Classify with WESR-Bench
            annotation = self.classifier.classify_laughter_event(
                word_data, alignment_data, audio_context
            )
            
            annotations.append(annotation)
        
        # Calculate statistics
        discrete_count = sum(1 for a in annotations if a.category == LaughterCategory.DISCRETE)
        continuous_count = sum(1 for a in annotations if a.category == LaughterCategory.CONTINUOUS)
        
        logger.info(f"📊 {item_id} WESR-Bench results:")
        logger.info(f"  - Discrete laughter: {discrete_count}")
        logger.info(f"  - Continuous laughter: {continuous_count}")
        logger.info(f"  - No laughter: {len(annotations) - discrete_count - continuous_count}")
        
        return annotations
    
    def demo_audio_features(self, word: str) -> Dict:
        """Generate demo audio features"""
        word_lower = word.lower()
        
        if any(indicator in word_lower for indicator in ['laughter', 'laughs', 'applause']):
            return {
                'isolated': True,
                'clear_boundaries': True,
                'laughter_duration': 0.5
            }
        
        elif any(indicator in word_lower for indicator in ['while', 'during', 'amid']):
            return {
                'overlap': True,
                'mixed': True,
                'speech_ratio': 0.6
            }
        
        else:
            return {}
    
    def save_wesr_bench_annotations(self, item_id: str, 
                                   annotations: List[WESRBenchAnnotation]):
        """Save WESR-Bench annotations to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create WESR-Bench annotations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wesr_bench_annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    word TEXT NOT NULL,
                    start_time REAL,
                    end_time REAL,
                    category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    audio_features TEXT,
                    FOREIGN KEY (item_id) REFERENCES enhanced_harvest(id)
                )
            """)
            
            # Insert annotations
            for annotation in annotations:
                cursor.execute("""
                    INSERT INTO wesr_bench_annotations 
                    (item_id, word, start_time, end_time, category, confidence, audio_features)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    annotation.word,
                    annotation.timestamp[0],
                    annotation.timestamp[1],
                    annotation.category.value,
                    annotation.confidence,
                    json.dumps(annotation.audio_features)
                ))
            
            conn.commit()
            logger.info(f"✅ Saved {len(annotations)} WESR-Bench annotations")
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
        finally:
            conn.close()

def main():
    """Execute WESR-Bench taxonomy implementation"""
    logger.info("🚀 STARTING WESR-BENCH TAXONOMY IMPLEMENTATION")
    logger.info("=" * 80)
    
    # Initialize WESR-Bench processor
    processor = WESRBenchProcessor()
    
    # Process all harvested data
    processor.process_harvested_data()
    
    logger.info("=" * 80)
    logger.info("✅ WESR-BENCH TAXONOMY IMPLEMENTATION COMPLETE")
    logger.info("🎯 All harvested data now categorized per 2026 protocol:")
    logger.info("  - Discrete: Standalone audience laughter")
    logger.info("  - Continuous: Laughter mixed with comedian speech")
    logger.info("  - No Laughter: Regular speech without laughter")
    
    return True

if __name__ == "__main__":
    main()