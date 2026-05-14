#!/usr/bin/env python3
"""
Convert collected YouTube comedy transcripts to word-level JSONL training format.

Input: data/audio_comedy/transcripts/{comedian}/*.json (Whisper/YouTube transcripts)
Output: data/processed/{comedian}_train.jsonl, {comedian}_val.jsonl

Requires transcripts with word-level timestamps and [laughter] markers.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import random

PROJECT_ROOT = Path(__file__).parent.parent
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Laughter markers in transcripts
LAUGHTER_MARKERS = [
    '[laughter]', '[LAUGHTER]', '[Applause]', '[APPLAUSE]',
    '[audience laughs]', '[audience laughing]', '[laughs]',
    '[crowd laughing]', '[cheering]', '[cheers]'
]

def load_transcript(transcript_path: Path) -> Optional[Dict]:
    """Load a transcript JSON file."""
    try:
        with open(transcript_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {transcript_path}: {e}")
        return None

def extract_words_with_timestamps(transcript: Dict) -> List[Dict]:
    """
    Extract word-level data from transcript.
    
    Handles two formats:
    1. YouTubeTranscriptApi format: {'words': [{'word': 'hello', 'start': 0.0, 'end': 0.5}]}
    2. Whisper segments format: {'segments': [{'text': 'hello world', 'start': 0.0, 'end': 1.0, 'words': [...]}]}
    """
    words_data = []
    
    # Try YouTube format first (word-level timestamps)
    if 'words' in transcript and transcript['words']:
        for word in transcript['words']:
            words_data.append({
                'word': word.get('word', '').strip(),
                'start': word.get('start', 0),
                'end': word.get('end', 0),
                'label': 0  # Default: no laughter
            })
        return words_data
    
    # Try Whisper segments format
    if 'segments' in transcript:
        for segment in transcript['segments']:
            segment_text = segment.get('text', '')
            segment_start = segment.get('start', 0)
            segment_end = segment.get('end', 0)
            
            # Check for laughter markers in segment
            has_laughter = any(marker in segment_text for marker in LAUGHTER_MARKERS)
            
            # Try word-level timestamps within segment
            if 'words' in segment and segment['words']:
                for word in segment['words']:
                    words_data.append({
                        'word': word.get('word', '').strip(),
                        'start': word.get('start', segment_start),
                        'end': word.get('end', segment_end),
                        'label': 1 if has_laughter else 0
                    })
            else:
                # No word-level timestamps, use segment-level
                # Split segment text into words
                text_words = segment_text.split()
                duration_per_word = (segment_end - segment_start) / max(len(text_words), 1)
                
                for i, word_text in enumerate(text_words):
                    words_data.append({
                        'word': word_text.strip(),
                        'start': segment_start + (i * duration_per_word),
                        'end': segment_start + ((i + 1) * duration_per_word),
                        'label': 1 if has_laughter else 0
                    })
        
        return words_data
    
    return []

def detect_laughter_in_words(words_data: List[Dict]) -> List[Dict]:
    """
    Detect laughter based on:
    1. Explicit [laughter] markers in text
    2. Context - words near laughter markers get label=1
    """
    # First pass: mark explicit laughter
    for entry in words_data:
        word = entry['word']
        if any(marker in word for marker in LAUGHTER_MARKERS):
            entry['label'] = 1
    
    # Second pass: context-based labeling
    # Words within 1 second before/after laughter get label=1
    laughter_indices = [i for i, e in enumerate(words_data) if e['label'] == 1]
    
    for li in laughter_indices:
        laught_start = words_data[li]['start']
        for i, entry in enumerate(words_data):
            if abs(entry['start'] - laught_start) <= 1.5:
                entry['label'] = 1
    
    return words_data

def words_to_training_example(words_data: List[Dict], comedian: str, 
                              video_id: str, source: str = "youtube") -> Dict:
    """Convert word-level data to training example."""
    words = [w['word'] for w in words_data]
    labels = [w['label'] for w in words_data]
    
    # Determine overall label (1 if any word has laughter)
    has_laughter = any(l == 1 for l in labels)
    label = 1 if has_laughter else 0
    
    return {
        'example_id': f"{comedian}_{video_id}_{random.randint(1000, 9999)}",
        'language': 'en',
        'comedian_id': comedian.lower().replace(' ', '_'),
        'show_id': video_id,
        'words': words,
        'labels': labels,
        'label': label,  # Sentence-level label
        'laughter_count': sum(labels),
        'total_words': len(words),
        'laughter_ratio': sum(labels) / max(len(words), 1),
        'metadata': {
            'source': source,
            'comedian': comedian,
            'video_id': video_id,
            'collection_type': 'youtube_transcript'
        }
    }

def process_comedian_transcripts(comedian: str, val_split: float = 0.15) -> Dict:
    """
    Process all transcripts for a comedian into train/val JSONL files.
    
    Args:
        comedian: Name of comedian (e.g., "Ali Wong")
        val_split: Fraction for validation (default 15%)
    
    Returns:
        Summary dict with counts
    """
    transcript_dir = TRANSCRIPT_DIR / comedian.lower().replace(' ', '_')
    
    if not transcript_dir.exists():
        print(f"❌ Transcript directory not found: {transcript_dir}")
        return {'error': 'directory not found'}
    
    # Find all transcript JSON files
    transcript_files = list(transcript_dir.glob("*_transcript.json"))
    
    if not transcript_files:
        print(f"❌ No transcript files found in {transcript_dir}")
        return {'error': 'no files'}
    
    print(f"📁 Processing {len(transcript_files)} transcripts for {comedian}")
    
    all_examples = []
    
    for transcript_file in transcript_files:
        print(f"   📄 {transcript_file.name}")
        
        # Load transcript
        transcript = load_transcript(transcript_file)
        if not transcript:
            continue
        
        # Extract word-level data
        words_data = extract_words_with_timestamps(transcript)
        
        if not words_data:
            print(f"   ⚠️ No words extracted from {transcript_file.name}")
            continue
        
        # Detect laughter
        words_data = detect_laughter_in_words(words_data)
        
        # Get video ID from filename
        video_id = transcript_file.name.replace('_transcript.json', '')
        
        # Convert to training example
        example = words_to_training_example(
            words_data=words_data,
            comedian=comedian,
            video_id=video_id,
            source=transcript.get('source', 'unknown')
        )
        
        all_examples.append(example)
        print(f"   ✅ {len(words_data)} words, {sum(w['label'] for w in words_data)} laughter labels")
    
    if not all_examples:
        return {'error': 'no examples created'}
    
    # Split into train/val
    random.shuffle(all_examples)
    val_count = int(len(all_examples) * val_split)
    
    train_examples = all_examples[val_count:]
    val_examples = all_examples[:val_count]
    
    # Create output directory
    output_dir = OUTPUT_DIR / comedian.lower().replace(' ', '_')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write train JSONL
    train_path = output_dir / "train.jsonl"
    with open(train_path, 'w') as f:
        for example in train_examples:
            f.write(json.dumps(example) + '\n')
    
    # Write val JSONL
    val_path = output_dir / "val.jsonl"
    with open(val_path, 'w') as f:
        for example in val_examples:
            f.write(json.dumps(example) + '\n')
    
    result = {
        'comedian': comedian,
        'total_examples': len(all_examples),
        'train_count': len(train_examples),
        'val_count': len(val_examples),
        'train_path': str(train_path),
        'val_path': str(val_path),
        'total_words': sum(len(ex['words']) for ex in all_examples),
        'total_laughter': sum(ex['laughter_count'] for ex in all_examples)
    }
    
    print(f"\n📊 {comedian} Summary:")
    print(f"   Total examples: {result['total_examples']}")
    print(f"   Train: {result['train_count']}, Val: {result['val_count']}")
    print(f"   Total words: {result['total_words']}, Laughter: {result['total_laughter']}")
    print(f"   Output: {output_dir}")
    
    return result

def merge_all_comedians(output_name: str = "combined") -> Dict:
    """
    Merge all comedian data into combined train/val/test files.
    """
    combined_train = []
    combined_val = []
    
    # Find all processed comedian directories
    if not OUTPUT_DIR.exists():
        return {'error': 'no processed data found'}
    
    for comedian_dir in OUTPUT_DIR.iterdir():
        if not comedian_dir.is_dir():
            continue
        
        # Load train
        train_file = comedian_dir / "train.jsonl"
        if train_file.exists():
            with open(train_file) as f:
                for line in f:
                    combined_train.append(json.loads(line))
        
        # Load val
        val_file = comedian_dir / "val.jsonl"
        if val_file.exists():
            with open(val_file) as f:
                for line in f:
                    combined_val.append(json.loads(line))
    
    # Write combined files
    combined_dir = OUTPUT_DIR / "combined"
    combined_dir.mkdir(exist_ok=True)
    
    train_path = combined_dir / "train.jsonl"
    val_path = combined_dir / "val.jsonl"
    
    with open(train_path, 'w') as f:
        for example in combined_train:
            f.write(json.dumps(example) + '\n')
    
    with open(val_path, 'w') as f:
        for example in combined_val:
            f.write(json.dumps(example) + '\n')
    
    result = {
        'total_train': len(combined_train),
        'total_val': len(combined_val),
        'train_path': str(train_path),
        'val_path': str(val_path)
    }
    
    print(f"\n📊 Combined Dataset:")
    print(f"   Train: {result['total_train']}, Val: {result['total_val']}")
    
    return result

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert YouTube transcripts to JSONL training format")
    parser.add_argument('--comedian', '-c', type=str, default='all',
                       help="Process specific comedian or 'all' (default: all)")
    parser.add_argument('--val_split', '-v', type=float, default=0.15,
                       help="Validation split (default: 0.15)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("YOUTUBE TRANSCRIPTS → JSONL FORMAT")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.comedian == 'all':
        # Process all comedians
        results = []
        
        for transcript_dir in TRANSCRIPT_DIR.iterdir():
            if not transcript_dir.is_dir():
                continue
            
            comedian = transcript_dir.name.replace('_', ' ').title()
            print(f"\n🎭 Processing: {comedian}")
            
            result = process_comedian_transcripts(comedian, args.val_split)
            results.append(result)
        
        # Merge all
        print("\n" + "=" * 60)
        print("MERGING ALL COMEDIANS")
        print("=" * 60)
        
        merge_result = merge_all_comedians()
        
        print("\n🎉 ALL PROCESSING COMPLETE")
        print(f"   Combined train: {merge_result['total_train']} examples")
        print(f"   Combined val: {merge_result['total_val']} examples")
        print(f"   Location: {OUTPUT_DIR / 'combined'}")
        
    else:
        # Process specific comedian
        result = process_comedian_transcripts(args.comedian, args.val_split)
        
        if 'error' not in result:
            print(f"\n🎉 {args.comedian} processing complete!")
            print(f"   Train: {result['train_path']}")
            print(f"   Val: {result['val_path']}")

if __name__ == '__main__':
    main()