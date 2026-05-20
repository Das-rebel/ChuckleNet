#!/usr/bin/env python3
"""
Phase 0: Utterance-Level Realignment for Audio-First Laughter Detection.

Converts word-level aligned segments (733K, broken 5s window) to 
utterance-level segments using VTT subtitle structure.

Output: aligned_utterances.jsonl with ~50K utterances, proper labels.

Based on PRD v5.0 and Hypothesis Validation Report V2.
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import timedelta

import numpy as np


def parse_vtt_timestamp(ts_str: str) -> float:
    """Parse VTT timestamp to seconds."""
    ts_str = ts_str.strip()
    # Handle HH:MM:SS.mmm and MM:SS.mmm
    parts = ts_str.replace(',', '.').split(':')
    if len(parts) == 3:
        h, m, s = parts
        return float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return float(m) * 60 + float(s)
    return float(ts_str)


def parse_vtt(vtt_path: str) -> list[dict]:
    """Parse VTT file into utterance segments with timestamps."""
    utterances = []
    
    with open(vtt_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT.*\n', '', content)
    
    # Split into blocks
    blocks = re.split(r'\n\n+', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
        
        # Find timestamp line
        ts_match = re.search(
            r'(\d{1,2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[.,]\d{3})',
            block
        )
        if not ts_match:
            # Try MM:SS.mmm format
            ts_match = re.search(
                r'(\d{1,2}:\d{2}[.,]\d{3})\s*-->\s*(\d{1,2}:\d{2}[.,]\d{3})',
                block
            )
        
        if not ts_match:
            continue
        
        start = parse_vtt_timestamp(ts_match.group(1))
        end = parse_vtt_timestamp(ts_match.group(2))
        
        # Get text lines (after timestamp)
        ts_line_idx = None
        for i, line in enumerate(lines):
            if '-->' in line:
                ts_line_idx = i
                break
        
        if ts_line_idx is None:
            continue
        
        text_lines = lines[ts_line_idx + 1:]
        # Clean up: remove alignment/position attributes, take the plain text line
        text = ' '.join(text_lines).strip()
        # Remove HTML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        
        if not text:
            continue
        
        # Check for [laughter], [applause], [Music] markers
        has_laughter = bool(re.search(r'\[laughter\]', text, re.IGNORECASE))
        has_applause = bool(re.search(r'\[applause\]', text, re.IGNORECASE))
        has_music = bool(re.search(r'\[music\]', text, re.IGNORECASE))
        
        utterances.append({
            'start': start,
            'end': end,
            'text': text,
            'has_laughter_marker': has_laughter,
            'has_applause_marker': has_applause,
            'has_music_marker': has_music,
            'duration': end - start,
        })
    
    return utterances


def assign_utterance_labels(utterances: list[dict], context_window: float = 0.0) -> list[dict]:
    """
    Assign laughter labels to utterances.
    
    Strategy:
    - If utterance contains [laughter] marker → label=1
    - If utterance is within context_window seconds of a [laughter] marker → label=1
    - Otherwise → label=0
    
    context_window=0 means only direct [laughter] markers get label=1
    """
    # Find all laughter marker timestamps
    laughter_times = []
    for u in utterances:
        if u['has_laughter_marker']:
            laughter_times.append((u['start'] + u['end']) / 2)  # midpoint
    
    for u in utterances:
        # Direct marker
        if u['has_laughter_marker']:
            u['label'] = 1
            u['label_source'] = 'direct_marker'
            continue
        
        # Context window
        u_mid = (u['start'] + u['end']) / 2
        near_laugh = False
        for lt in laughter_times:
            if abs(u_mid - lt) <= context_window:
                near_laugh = True
                break
        
        if near_laugh:
            u['label'] = 1
            u['label_source'] = f'within_{context_window}s'
        else:
            u['label'] = 0
            u['label_source'] = 'no_marker'
    
    return utterances


def merge_short_utterances(utterances: list[dict], min_duration: float = 1.0) -> list[dict]:
    """Merge very short utterances (< min_duration) with adjacent ones."""
    if not utterances:
        return []
    
    merged = [utterances[0].copy()]
    
    for u in utterances[1:]:
        prev = merged[-1]
        
        # Merge if previous is too short AND same label
        if prev['duration'] < min_duration and prev['label'] == u['label']:
            prev['text'] += ' ' + u['text']
            prev['end'] = u['end']
            prev['duration'] = prev['end'] - prev['start']
            prev['has_laughter_marker'] = prev['has_laughter_marker'] or u['has_laughter_marker']
            prev['has_applause_marker'] = prev['has_applause_marker'] or u['has_applause_marker']
        else:
            merged.append(u.copy())
    
    return merged


def filter_utterances(utterances: list[dict], 
                      min_duration: float = 0.5,
                      max_duration: float = 30.0,
                      remove_music_only: bool = True) -> list[dict]:
    """Filter out unwanted utterances."""
    filtered = []
    for u in utterances:
        # Skip very short or very long
        if u['duration'] < min_duration or u['duration'] > max_duration:
            continue
        
        # Skip music-only utterances
        if remove_music_only and u['has_music_marker'] and not u['text'].replace('[Music]', '').strip():
            continue
        
        # Skip empty text
        text_clean = re.sub(r'\[(laughter|applause|music|__|​)\]', '', u['text'], flags=re.IGNORECASE).strip()
        if not text_clean and not u['has_laughter_marker']:
            continue
        
        filtered.append(u)
    
    return filtered


def find_audio_file(video_id: str, audio_dirs: list[Path]) -> str | None:
    """Find the audio file for a video ID."""
    for d in audio_dirs:
        for ext in ['mp3', 'wav', 'm4a']:
            candidate = d / f"{video_id}.{ext}"
            if candidate.exists():
                return str(candidate)
            # Check batch subdirectories
            for subdir in d.iterdir():
                if subdir.is_dir():
                    candidate = subdir / f"{video_id}.{ext}"
                    if candidate.exists():
                        return str(candidate)
    return None


def main():
    parser = argparse.ArgumentParser(description='Phase 0: Utterance-Level Realignment')
    parser.add_argument('--vtt-dir', default='data/audio_comedy/vtt_subtitles',
                        help='Directory containing VTT files')
    parser.add_argument('--output', default='data/audio_comedy/aligned_utterances.jsonl',
                        help='Output JSONL file')
    parser.add_argument('--context-window', type=float, default=0.0,
                        help='Seconds around [laughter] marker to label positive (0=exact only)')
    parser.add_argument('--min-duration', type=float, default=0.5,
                        help='Minimum utterance duration in seconds')
    parser.add_argument('--max-duration', type=float, default=30.0,
                        help='Maximum utterance duration in seconds')
    parser.add_argument('--merge-short', type=float, default=1.0,
                        help='Merge utterances shorter than this (seconds)')
    args = parser.parse_args()
    
    vtt_dir = Path(args.vtt_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Find audio directories
    audio_base = Path('data/audio_comedy/audio')
    audio_dirs = [audio_base]
    if audio_base.exists():
        audio_dirs.extend([d for d in audio_base.iterdir() if d.is_dir()])
    
    # Find all VTT files
    vtt_files = list(vtt_dir.glob('*.vtt')) + list(vtt_dir.glob('**/*.vtt'))
    vtt_files = [f for f in vtt_files if f.is_file()]
    
    print(f"Found {len(vtt_files)} VTT files")
    print(f"Context window: {args.context_window}s")
    print(f"Duration filter: {args.min_duration}s - {args.max_duration}s")
    print()
    
    all_utterances = []
    stats = defaultdict(int)
    
    for vtt_path in sorted(vtt_files):
        # Extract video ID from filename
        video_id = vtt_path.stem.split('.')[0]
        
        # Detect language from path
        rel_path = vtt_path.relative_to(vtt_dir)
        parts = rel_path.parts
        lang = 'en'
        if len(parts) > 1:
            if 'zh' in parts[0]:
                lang = 'zh'
            elif 'hi' in parts[0]:
                lang = 'hi-latn'
        
        try:
            utterances = parse_vtt(str(vtt_path))
        except Exception as e:
            print(f"  ERROR parsing {vtt_path.name}: {e}")
            continue
        
        if not utterances:
            continue
        
        # Assign labels
        utterances = assign_utterance_labels(utterances, args.context_window)
        
        # Merge short utterances
        if args.merge_short > 0:
            utterances = merge_short_utterances(utterances, args.merge_short)
        
        # Filter
        utterances = filter_utterances(
            utterances,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
        )
        
        # Find audio file
        audio_file = find_audio_file(video_id, audio_dirs)
        
        # Write utterances
        for i, u in enumerate(utterances):
            # Clean text for output
            text_clean = re.sub(r'\[(laughter|applause|music)\]', '', u['text'], flags=re.IGNORECASE).strip()
            
            record = {
                'utterance_id': f"{video_id}_{i:04d}",
                'video_id': video_id,
                'language': lang,
                'text': text_clean,
                'text_raw': u['text'],
                'start': round(u['start'], 3),
                'end': round(u['end'], 3),
                'duration': round(u['duration'], 3),
                'label': u['label'],
                'label_source': u['label_source'],
                'has_laughter_marker': u['has_laughter_marker'],
                'has_applause_marker': u['has_applause_marker'],
                'audio_file': audio_file or '',
            }
            all_utterances.append(record)
            stats['total'] += 1
            if u['label'] == 1:
                stats['positive'] += 1
            else:
                stats['negative'] += 1
            if audio_file:
                stats['has_audio'] += 1
    
    # Write output
    with open(output_path, 'w') as f:
        for record in all_utterances:
            f.write(json.dumps(record) + '\n')
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"UTTERANCE-LEVEL REALIGNMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Total utterances: {stats['total']:,}")
    print(f"Positive (laughter): {stats['positive']:,} ({stats['positive']/stats['total']*100:.1f}%)")
    print(f"Negative (no laughter): {stats['negative']:,} ({stats['negative']/stats['total']*100:.1f}%)")
    print(f"Has audio file: {stats['has_audio']:,} ({stats['has_audio']/stats['total']*100:.1f}%)")
    print(f"\nOutput: {output_path}")
    
    # Language breakdown
    lang_counts = defaultdict(lambda: {'total': 0, 'positive': 0})
    for r in all_utterances:
        lang_counts[r['language']]['total'] += 1
        if r['label'] == 1:
            lang_counts[r['language']]['positive'] += 1
    
    print(f"\nBy Language:")
    for lang, counts in sorted(lang_counts.items()):
        pct = counts['positive'] / counts['total'] * 100 if counts['total'] > 0 else 0
        print(f"  {lang}: {counts['total']:,} utterances, {counts['positive']:,} positive ({pct:.1f}%)")
    
    # Duration statistics
    durations = [r['duration'] for r in all_utterances]
    print(f"\nDuration Statistics:")
    print(f"  Mean: {np.mean(durations):.2f}s")
    print(f"  Median: {np.median(durations):.2f}s")
    print(f"  P95: {np.percentile(durations, 95):.2f}s")
    print(f"  Max: {np.max(durations):.2f}s")


if __name__ == '__main__':
    main()
