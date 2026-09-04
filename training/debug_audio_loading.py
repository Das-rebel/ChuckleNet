"""
Debug audio loading for boundary audit
"""
import json
import os
import soundfile as sf
import numpy as np

AUDIO_BASE = '/Users/Subho/autonomous_laughter_prediction_essential'
ALIGNED_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl'

# Load first positive sample
all_data = [json.loads(line) for line in open(ALIGNED_PATH)]
positive_data = [d for d in all_data if d.get('label_any', 0) == 1]

d = positive_data[0]
print("Sample data:")
print(f"  video_id: {d['video_id']}")
print(f"  start: {d['start']}, end: {d['end']}")
print(f"  audio_file: {d['audio_file']}")

audio_path = os.path.join(AUDIO_BASE, d['audio_file'])
print(f"\nFull path: {audio_path}")
print(f"Exists: {os.path.exists(audio_path)}")

if os.path.exists(audio_path):
    try:
        with sf.SoundFile(audio_path) as f:
            print(f"Sample rate: {f.samplerate}")
            print(f"Channels: {f.channels}")
            print(f"Frames: {len(f)}")
            print(f"Duration: {len(f)/f.samplerate:.1f}s")
            
            # Try reading the segment we need
            target_start = max(0, d['start'] - 0.5)
            target_end = d['start'] + 5.0
            sample_start = int(target_start * f.samplerate)
            sample_end = int(target_end * f.samplerate)
            
            f.seek(sample_start)
            segment = f.read(sample_end - sample_start)
            print(f"\nSegment: {target_start:.2f}s to {target_end:.2f}s")
            print(f"Segment frames: {len(segment)}, shape: {segment.shape}")
            print(f"Segment dtype: {segment.dtype}")
            print(f"Segment RMS: {np.sqrt(np.mean(segment.astype(np.float32)**2)):.4f}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()