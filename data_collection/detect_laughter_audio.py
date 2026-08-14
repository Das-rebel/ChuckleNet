#!/usr/bin/env python3
"""
Audio-based laughter detection for Hindi/Chinese videos.

Uses energy-based heuristics to detect laughter segments:
1. Low speech energy (voicing < 30% of segment)
2. Repeated burst patterns (rhythmic energy spikes)
3. Spectral characteristics of laughter (formant-like structure)

This is NOT as accurate as labeled data, but gives weak labels for non-English content.
"""

import numpy as np
import librosa
import json
from pathlib import Path
from typing import List, Dict, Optional
import os

def detect_laughter_segments(audio_path: str, sr: int = 16000) -> List[Dict]:
    """
    Detect laughter segments using audio energy analysis.
    
    Returns segments with laughter probability scores.
    """
    
    # Load audio
    y, sr = librosa.load(audio_path, sr=sr)
    
    # Parameters
    frame_length = 1024
    hop_length = 512
    n_mels = 128
    
    # Compute energy
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Compute spectral contrast (laughter has distinctive spectral structure)
    spectral_contrast = librosa.feature.spectral_contrast(
        y=y, sr=sr, n_fft=frame_length, hop_length=hop_length
    )
    
    # Compute zero crossing rate (laughter has higher ZCR during bursts)
    zcr = librosa.feature.zero_crossing_rate(
        y=y, frame_length=frame_length, hop_length=hop_length
    )[0]
    
    # Compute onset strength (repeated patterns)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    
    # Frame times
    frames = np.arange(len(rms))
    times = librosa.frames_to_time(frames, sr=sr, hop_length=hop_length)
    
    # Segment into 2-second windows with 1-second overlap
    window_size = int(2 * sr / hop_length)  # 2 seconds in frames
    hop = int(1 * sr / hop_length)  # 1 second hop
    
    laughter_segments = []
    
    for i in range(0, len(rms) - window_size, hop):
        # Window
        rms_window = rms[i:i+window_size]
        zcr_window = zcr[i:i+window_size]
        sc_window = spectral_contrast[:, i:i+window_size]
        onset_window = onset_env[i:i+window_size]
        
        # Features
        mean_rms = np.mean(rms_window)
        max_rms = np.max(rms_window)
        std_rms = np.std(rms_window)
        mean_zcr = np.mean(zcr_window)
        
        # Spectral contrast features (laughter has specific pattern)
        mean_sc = np.mean(sc_window, axis=0)
        
        # Onset regularity (laughter is rhythmic/repetitive)
        onset_diff = np.diff(onset_window)
        onset_regularity = np.std(onset_diff) / (np.mean(onset_diff) + 1e-8)
        
        # Laughter heuristic scoring
        # High energy variability + rhythmic onset pattern + moderate ZCR
        energy_ratio = std_rms / (mean_rms + 1e-8)
        
        # Score based on heuristics
        score = 0.0
        
        # 1. Energy variability (laughter has bursts)
        if energy_ratio > 0.5:
            score += 0.3 * min(energy_ratio, 2.0) / 2.0
        
        # 2. Rhythmic pattern (repeated bursts)
        if onset_regularity < 1.5:  # Regular/periodic
            score += 0.3
        
        # 3. Not too high energy (laughter isn't screamed)
        if mean_rms < 0.3:  # Moderate energy
            score += 0.2
        
        # 4. Not too low energy (silence)
        if mean_rms > 0.05:  # Some energy
            score += 0.2
        
        # Convert to segment
        start_time = times[i]
        end_time = times[i + window_size]
        
        if score > 0.3:  # Threshold
            laughter_segments.append({
                'start': float(start_time),
                'end': float(end_time),
                'score': float(score),
                'energy_ratio': float(energy_ratio),
                'onset_regularity': float(onset_regularity),
                'mean_rms': float(mean_rms),
                'mean_zcr': float(mean_zcr),
            })
    
    # Merge overlapping segments
    merged = merge_segments(laughter_segments)
    
    return merged

def merge_segments(segments: List[Dict], gap_threshold: float = 0.5) -> List[Dict]:
    """Merge segments that are close together."""
    if not segments:
        return []
    
    # Sort by start time
    segments = sorted(segments, key=lambda x: x['start'])
    
    merged = [segments[0]]
    
    for seg in segments[1:]:
        if seg['start'] <= merged[-1]['end'] + gap_threshold:
            # Merge
            merged[-1]['end'] = max(merged[-1]['end'], seg['end'])
            merged[-1]['score'] = max(merged[-1]['score'], seg['score'])
        else:
            merged.append(seg)
    
    return merged

def extract_text_segments(audio_path: str, transcript: List[Dict]) -> List[Dict]:
    """
    Map transcript words to audio segments.
    """
    if not transcript:
        return []
    
    utterances = []
    current_utt = None
    
    for word_data in transcript:
        word = word_data['word']
        start = word_data['start_time']
        end = word_data['end_time']
        
        # End of sentence
        if word.endswith(('.', '!', '?', '।')) or current_utt is None:
            if current_utt:
                utterances.append(current_utt)
            current_utt = {
                'start': start,
                'end': end,
                'text': word,
                'words': [word_data]
            }
        else:
            current_utt['end'] = end
            current_utt['text'] += ' ' + word
            current_utt['words'].append(word_data)
    
    if current_utt:
        utterances.append(current_utt)
    
    return utterances

def combine_signals(audio_segments: List[Dict], transcript_segments: List[Dict]) -> Dict:
    """
    Combine audio-based laughter detection with text-based signals.
    """
    laughter_markers = []
    
    # Check each audio segment
    for audio_seg in audio_segments:
        # Check if there's overlapping speech
        overlapping_text = None
        for text_seg in transcript_segments:
            if (audio_seg['start'] < text_seg['end'] and 
                audio_seg['end'] > text_seg['start']):
                overlapping_text = text_seg
                break
        
        # Laughter keywords in overlapping text
        laugh_text = False
        if overlapping_text:
            text_lower = overlapping_text['text'].lower()
            laugh_text = any(lt in text_lower for lt in 
                ['haha', 'hehe', 'hoho', 'lol', 'हाहा', 'हीही', '哈哈', '呵呵'])
        
        # Combined score
        if audio_seg['score'] > 0.5 or laugh_text:
            laughter_markers.append({
                'start': audio_seg['start'],
                'end': audio_seg['end'],
                'text': overlapping_text['text'] if overlapping_text else '',
                'has_laughter': True,
                'score': audio_seg['score']
            })
    
    return {
        'laughter_count': len(laughter_markers),
        'laughter_markers': laughter_markers,
        'total_utterances': len(transcript_segments),
        'utterances': transcript_segments[:500] if transcript_segments else [],
        'status': 'success'
    }

def process_video_with_audio(video_id: str, audio_path: str, transcript: List[Dict], lang: str) -> Dict:
    """Process a video: audio-based laughter + transcript."""
    
    print(f"    Detecting laughter in audio...")
    audio_segments = detect_laughter_segments(audio_path)
    print(f"    Found {len(audio_segments)} audio segments with laughter-like patterns")
    
    print(f"    Mapping transcript...")
    text_segments = extract_text_segments(audio_path, transcript)
    print(f"    Found {len(text_segments)} text segments")
    
    result = combine_signals(audio_segments, text_segments)
    result['id'] = video_id
    result['lang'] = lang
    
    return result

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('audio_path')
    parser.add_argument('--lang', default='hi')
    args = parser.parse_args()
    
    print(f"Processing: {args.audio_path}")
    
    # Load transcript if exists
    transcript_path = args.audio_path.replace('.wav', '_transcript.json')
    transcript = []
    if os.path.exists(transcript_path):
        with open(transcript_path) as f:
            transcript = json.load(f)
    
    result = process_video_with_audio('test', args.audio_path, transcript, args.lang)
    
    print(f"\n=== Results ===")
    print(f"Laughter count: {result['laughter_count']}")
    print(f"Total utterances: {result['total_utterances']}")
