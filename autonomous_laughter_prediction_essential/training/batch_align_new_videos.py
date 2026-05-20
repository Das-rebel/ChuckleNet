#!/usr/bin/env python3
"""
Batch align new videos: Whisper transcription → VTT laughter markers → utterance segments.

Processes videos that have audio + VTT but aren't yet in aligned_utterances.jsonl.
Output: Appends to aligned_segments.jsonl and regenerates aligned_utterances.jsonl.
"""

import json
import os
import sys
import re
import glob
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training"))

from faster_whisper import WhisperModel

# === CONFIG ===
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "audio"
VTT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "vtt_subtitles"
SEGMENTS_FILE = PROJECT_ROOT / "data" / "audio_comedy" / "aligned_segments.jsonl"
UTTERANCES_FILE = PROJECT_ROOT / "data" / "audio_comedy" / "aligned_utterances.jsonl"

LAUGHTER_MARKERS = [
    "[laughter]", "[laugh]", "[Laugh]", "[LAUGHTER]",
    "[applause]", "[Applause]", "[APPLAUSE]",
    "[praise]", "[प्रशंसा]",
    "[Audience laughter]", "[audience laughter]",
    "(laughter)", "(laugh)", "(applause)",
    "(audience laughs)", "(audience applause)",
    "(audience laughter)", "(audience laughing)",
    "(audience clapping)",
]

UTTERANCE_WINDOW = 10  # words per utterance
UTTERANCE_OVERLAP = 2   # overlap between utterances


def find_audio(video_id):
    """Find audio file for a video ID."""
    for ext in ['*.mp3', '*.wav', '*.m4a', '*.opus']:
        for path in glob.glob(f"{AUDIO_DIR}/**/{video_id}.{ext.lstrip('*')}", recursive=True):
            return str(path)
    return None


def find_vtt(video_id):
    """Find VTT subtitle file for a video ID."""
    # Try multiple paths
    for pattern in [f"{VTT_DIR}/{video_id}.en.vtt", f"{VTT_DIR}/{video_id}.vtt"]:
        if os.path.exists(pattern):
            return pattern
    # Search recursive
    for path in glob.glob(f"{VTT_DIR}/**/{video_id}*.vtt", recursive=True):
        return str(path)
    return None


def parse_vtt(vtt_path):
    """Parse VTT file to extract segments with timestamps and laughter markers."""
    with open(vtt_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    segments = []
    # VTT format: timestamp range, then text
    pattern = r'(\d{2}:\d{2}[:.]\d{3})\s*-->\s*(\d{2}:\d{2}[:.]\d{3})\s*\n(.+?)(?=\n\n|\Z)'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        start_str, end_str, text = match.groups()
        
        # Parse timestamps
        start = parse_timestamp(start_str)
        end = parse_timestamp(end_str)
        
        # Check for laughter markers
        text_lower = text.strip().lower()
        has_laughter = any(m.lower() in text_lower for m in LAUGHTER_MARKERS)
        
        # Clean text (remove markers)
        clean_text = text.strip()
        for marker in LAUGHTER_MARKERS:
            clean_text = clean_text.replace(marker, '')
        clean_text = clean_text.strip()
        
        if start is not None and end is not None:
            segments.append({
                'start': start,
                'end': end,
                'text': clean_text,
                'has_laughter': has_laughter,
            })
    
    return segments


def parse_timestamp(ts):
    """Parse VTT timestamp to seconds."""
    try:
        # HH:MM:SS.mmm or HH:MM:SS,mmm or MM:SS.mmm
        ts = ts.replace(',', '.')
        parts = ts.split(':')
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    except:
        pass
    return None


def transcribe_with_whisper(audio_path, video_id):
    """Transcribe audio using faster-whisper."""
    print(f"  Transcribing {video_id}...")
    model = WhisperModel("base", compute_type="int8", device="cpu")
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language=None,  # Auto-detect for multilingual
    )
    
    words = []
    for seg in segments:
        for word_info in seg.words:
            words.append({
                'word': word_info.word.strip(),
                'start': round(word_info.start, 3),
                'end': round(word_info.end, 3),
            })
    
    return words, info.language


def align_words_with_laughter(words, vtt_segments):
    """Align Whisper words with VTT laughter markers."""
    if not vtt_segments or not words:
        return words
    
    # For each word, check if any VTT laughter segment overlaps
    for word in words:
        word_center = (word['start'] + word['end']) / 2
        word['label'] = 0  # default: no laughter
        
        for vtt_seg in vtt_segments:
            if vtt_seg['has_laughter']:
                # Check if word falls within or near a laughter segment
                # Use a small buffer (0.5s) to account for timing differences
                if (vtt_seg['start'] - 0.5) <= word_center <= (vtt_seg['end'] + 0.5):
                    word['label'] = 1
                    break
    
    return words


def create_utterances(words, video_id, audio_file):
    """Create utterance-level data from word-level segments."""
    utterances = []
    
    if not words:
        return utterances
    
    i = 0
    utt_idx = 0
    while i < len(words):
        # Get window of words
        end_i = min(i + UTTERANCE_WINDOW, len(words))
        window_words = words[i:end_i]
        
        # If we have enough words for the next window, advance by (window - overlap)
        if end_i < len(words):
            i += UTTERANCE_WINDOW - UTTERANCE_OVERLAP
        else:
            i = len(words)  # Done
        
        # Create utterance
        text = ' '.join(w['word'] for w in window_words)
        start = window_words[0]['start']
        end = window_words[-1]['end']
        labels = [w.get('label', 0) for w in window_words]
        n_positive = sum(labels)
        positive_ratio = n_positive / len(labels) if labels else 0
        
        utterances.append({
            'utterance_id': f'{video_id}_{utt_idx:04d}',
            'video_id': video_id,
            'text': text,
            'start': start,
            'end': end,
            'duration': round(end - start, 3),
            'n_words': len(window_words),
            'n_positive_words': n_positive,
            'positive_ratio': round(positive_ratio, 3),
            'label_any': 1 if n_positive > 0 else 0,
            'label_majority': 1 if positive_ratio > 0.5 else 0,
            'audio_file': audio_file,
        })
        utt_idx += 1
    
    return utterances


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-videos', type=int, default=26, help='Max videos to process')
    parser.add_argument('--skip-whisper', action='store_true', help='Skip transcription if transcripts exist')
    args = parser.parse_args()
    
    # Load new videos for alignment
    new_videos_path = PROJECT_ROOT / "data" / "audio_comedy" / "new_videos_for_alignment.json"
    if not new_videos_path.exists():
        print("No new_videos_for_alignment.json found. Run discovery first.")
        return
    
    with open(new_videos_path) as f:
        new_videos = json.load(f)
    
    print(f"Found {len(new_videos)} new videos ready for alignment")
    
    # Load existing segments
    existing_segments = []
    existing_utterances = []
    existing_vids = set()
    
    if SEGMENTS_FILE.exists():
        with open(SEGMENTS_FILE) as f:
            for line in f:
                seg = json.loads(line)
                existing_segments.append(seg)
                existing_vids.add(seg.get('video_id', ''))
    
    if UTTERANCES_FILE.exists():
        with open(UTTERANCES_FILE) as f:
            for line in f:
                existing_utterances.append(json.loads(line))
    
    print(f"Existing: {len(existing_segments)} segments, {len(existing_utterances)} utterances from {len(existing_vids)} videos")
    
    # Process new videos
    all_new_segments = []
    all_new_utterances = []
    processed = 0
    
    for video_info in new_videos[:args.max_videos]:
        video_id = video_info['video_id']
        audio_path = video_info['audio_path']
        vtt_path = video_info['vtt_path']
        
        if video_id in existing_vids:
            print(f"  Skipping {video_id}: already aligned")
            continue
        
        if not os.path.exists(audio_path):
            print(f"  Skipping {video_id}: audio not found at {audio_path}")
            continue
        
        print(f"\nProcessing {video_id}...")
        
        # Step 1: Parse VTT
        vtt_segments = parse_vtt(vtt_path)
        print(f"  VTT: {len(vtt_segments)} segments, {sum(1 for s in vtt_segments if s['has_laughter'])} with laughter")
        
        # Step 2: Transcribe with Whisper
        try:
            words, language = transcribe_with_whisper(audio_path, video_id)
            print(f"  Whisper: {len(words)} words (language: {language})")
        except Exception as e:
            print(f"  ❌ Whisper failed: {e}")
            continue
        
        if not words:
            print(f"  ❌ No words transcribed")
            continue
        
        # Step 3: Align with laughter markers
        words = align_words_with_laughter(words, vtt_segments)
        n_positive = sum(1 for w in words if w.get('label', 0) == 1)
        print(f"  Aligned: {n_positive}/{len(words)} words labeled positive")
        
        # Step 4: Create word-level segments
        # Find audio batch directory
        batch_dir = os.path.basename(os.path.dirname(audio_path))
        audio_file = f"data/audio_comedy/audio/{batch_dir}/{os.path.basename(audio_path)}"
        
        for w in words:
            # Add context words
            idx = words.index(w)
            context_start = max(0, idx - 3)
            context = [{'word': words[j]['word'], 'label': words[j].get('label', 0)} 
                       for j in range(context_start, idx)]
            
            all_new_segments.append({
                'video_id': video_id,
                'comedian': batch_dir,
                'audio_file': audio_file,
                'word': w['word'],
                'start': w['start'],
                'end': w['end'],
                'label': w.get('label', 0),
                'context_words': [c['word'] for c in context[-3:]],
                'context_labels': [c['label'] for c in context[-3:]],
            })
        
        # Step 5: Create utterances
        utterances = create_utterances(words, video_id, audio_file)
        all_new_utterances.extend(utterances)
        
        processed += 1
        print(f"  ✅ Created {len(utterances)} utterances")
    
    print(f"\n{'='*60}")
    print(f"Processed {processed}/{len(new_videos[:args.max_videos])} videos")
    print(f"New segments: {len(all_new_segments)}")
    print(f"New utterances: {len(all_new_utterances)}")
    
    if all_new_segments:
        # Append new segments
        with open(SEGMENTS_FILE, 'a') as f:
            for seg in all_new_segments:
                f.write(json.dumps(seg) + '\n')
        print(f"✅ Appended {len(all_new_segments)} segments to {SEGMENTS_FILE}")
        
        # Rewrite utterances (need to regenerate since they overlap)
        # Combine existing + new
        combined = existing_utterances + all_new_utterances
        with open(UTTERANCES_FILE, 'w') as f:
            for utt in combined:
                f.write(json.dumps(utt) + '\n')
        print(f"✅ Wrote {len(combined)} utterances to {UTTERANCES_FILE}")
        
        # Stats
        total_segs = len(existing_segments) + len(all_new_segments)
        total_utts = len(combined)
        print(f"\nTotal segments: {total_segs:,}")
        print(f"Total utterances: {total_utts:,}")


if __name__ == "__main__":
    main()