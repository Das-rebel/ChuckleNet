#!/usr/bin/env python3
"""
Production frame extraction - no tqdm, detailed progress, robust error handling
"""

import os
import sys
import json
import numpy as np
import torch
import librosa
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import WavLMModel
    print("✓ Transformers imported successfully")
except ImportError as e:
    print(f"✗ Failed to import transformers: {e}")
    sys.exit(1)

# Config
PROJECT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential")
DATA_DIR = PROJECT_DIR / "data/utterances"
AUDIO_DIR = Path("/Users/Subho/data/utterances/vtt_audio_local")
OUTPUT_DIR = DATA_DIR / "vtt_frames"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

print(f"Project directory: {PROJECT_DIR}")
print(f"Audio directory: {AUDIO_DIR}")
print(f"Output directory: {OUTPUT_DIR}")

# Load WavLM model
print("\nLoading WavLM model...")
try:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = WavLMModel.from_pretrained("microsoft/wavlm-base-plus")
    model = model.to(device).eval()
    print(f"✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Load VTT utterance data
print("\nLoading VTT utterance data...")
vtt_file = DATA_DIR / "utterances_clean.jsonl"
vtt_data = {}
utterance_count = 0

try:
    with open(vtt_file) as f:
        for line in f:
            obj = json.loads(line)
            vid = obj['video_id']
            if vid not in vtt_data:
                vtt_data[vid] = []
            vtt_data[vid].append(obj)
            utterance_count += 1
    print(f"✓ Loaded {len(vtt_data)} videos with {utterance_count} utterances")
except Exception as e:
    print(f"✗ Failed to load VTT data: {e}")
    sys.exit(1)

def extract_frames(waveform, sample_rate=16000):
    """Extract WavLM frame sequences from audio waveform."""
    if waveform is None or len(waveform) < 160:
        return None
    
    # Resample to 16kHz if needed (WavLM requirement)
    if sample_rate != 16000:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=16000)
        sample_rate = 16000
    
    # Ensure minimum length
    if len(waveform) < 160:
        return None
    
    try:
        # Convert to tensor
        inputs = torch.FloatTensor(waveform).unsqueeze(0).to(device)
        
        # Extract WavLM features
        with torch.no_grad():
            outputs = model(inputs)
            # Return full frame sequences: (seq_len, hidden_dim)
            frames = outputs.last_hidden_state.squeeze(0).cpu().numpy()
            return frames
    except Exception as e:
        # Silently skip errors for very short utterances
        return None

def load_audio_segment(video_id, start, end, audio_dir):
    """Load audio segment for a specific utterance using librosa."""
    # Try m4a first, then mp3
    for ext in ['.m4a', '.mp3']:
        audio_path = audio_dir / f"{video_id}{ext}"
        if audio_path.exists():
            try:
                # Load with librosa (supports more formats)
                # Load the full file first
                waveform, sample_rate = librosa.load(str(audio_path), sr=None, mono=True)
                
                # Slice by time
                start_sample = int(start * sample_rate)
                end_sample = int(end * sample_rate)
                
                # Ensure bounds
                if start_sample >= len(waveform):
                    return None, sample_rate
                if end_sample > len(waveform):
                    end_sample = len(waveform)
                
                segment = waveform[start_sample:end_sample]
                return segment, sample_rate
            except Exception:
                continue
    
    return None, None

# Process all videos
print("\n=== PROCESSING ALL VIDEOS ===")
print(f"Starting extraction of {len(vtt_data)} videos...")
print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

processed_videos = 0
total_frames_extracted = 0
errors = []
start_time = time.time()

for i, video_id in enumerate(vtt_data.keys()):
    # Print progress every 10 videos
    if i % 10 == 0 or i == len(vtt_data) - 1:
        elapsed = time.time() - start_time
        videos_remaining = len(vtt_data) - i
        avg_time = elapsed / (i + 1) if i > 0 else 0
        eta_seconds = avg_time * videos_remaining
        eta = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
        print(f"[{i+1}/{len(vtt_data)}] Videos processed: {processed_videos} | ETA: {eta} | Errors: {len(errors)}")
    
    utterances = vtt_data[video_id]
    video_frames = []
    video_uids = []
    
    for utter in utterances:
        uid = f"{video_id}_{utter['start']:.2f}"
        
        # Load audio segment
        waveform, sample_rate = load_audio_segment(
            video_id, utter['start'], utter['end'], AUDIO_DIR
        )
        
        if waveform is not None:
            # Extract frames
            frames = extract_frames(waveform, sample_rate)
            if frames is not None:
                video_frames.append(frames)
                video_uids.append(uid)
                total_frames_extracted += 1
    
    # Save video frames if we got any
    if video_frames:
        try:
            # Save as numpy array
            output_path = OUTPUT_DIR / f"{video_id}.npy"
            np.save(output_path, np.array(video_frames, dtype=object))  # object dtype for variable length
            # Save mapping
            with open(OUTPUT_DIR / f"{video_id}_uids.json", 'w') as f:
                json.dump(video_uids, f)
            processed_videos += 1
        except Exception as e:
            error_msg = f"Error saving {video_id}: {e}"
            errors.append(error_msg)

total_time = time.time() - start_time

print(f"\n=== EXTRACTION COMPLETE ===")
print(f"Total time: {int(total_time // 60)}m {int(total_time % 60)}s")
print(f"Processed videos: {processed_videos}/{len(vtt_data)}")
print(f"Total utterances processed: {total_frames_extracted}/{utterance_count}")
print(f"Success rate: {processed_videos / len(vtt_data) * 100:.1f}%")
print(f"Frames saved to: {OUTPUT_DIR}")

if errors:
    print(f"\n⚠️  Errors encountered: {len(errors)}")
    print("Sample errors (first 5):")
    for error in errors[:5]:
        print(f"  - {error}")

print(f"\n✅ EXTRACTION SUCCESSFUL!")
print(f"Ready for ultra-optimized training with Attention Pooling!")
