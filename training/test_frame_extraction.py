#!/usr/bin/env python3
"""
Debug frame extraction - processes just one video
"""

import os
import sys
import json
import numpy as np
import torch
import librosa
import soundfile as sf
from pathlib import Path
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
OUTPUT_DIR = DATA_DIR / "vtt_frames_test"
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
    
    # Resample if needed
    if sample_rate != 16000:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=16000)
    
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
        print(f"Error extracting frames: {e}")
        return None

def load_audio_segment(video_id, start, end, audio_dir):
    """Load audio segment for a specific utterance."""
    # Try m4a first, then mp3
    for ext in ['.m4a', '.mp3']:
        audio_path = audio_dir / f"{video_id}{ext}"
        if audio_path.exists():
            try:
                # Load full audio file
                waveform, sample_rate = sf.read(str(audio_path))
                
                # Convert to mono if needed
                if len(waveform.shape) > 1:
                    waveform = waveform.mean(axis=1)
                
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
            except Exception as e:
                print(f"Error loading {audio_path}: {e}")
                continue
    
    return None, None

# Process just ONE video for debugging
print("\n=== DEBUGGING: PROCESSING ONE VIDEO ===")

# Get the first video ID
first_video_id = list(vtt_data.keys())[0]
print(f"Processing video: {first_video_id}")

utterances = vtt_data[first_video_id]
print(f"Video has {len(utterances)} utterances")

video_frames = []
video_uids = []

# Process just first 3 utterances for debugging
for i, utter in enumerate(utterances[:3]):
    uid = f"{first_video_id}_{utter['start']:.2f}"
    print(f"\nProcessing utterance {i+1}: {uid}")
    print(f"  Start: {utter['start']:.2f}, End: {utter['end']:.2f}")
    
    # Load audio segment
    waveform, sample_rate = load_audio_segment(
        first_video_id, utter['start'], utter['end'], AUDIO_DIR
    )
    
    if waveform is not None:
        print(f"  ✓ Loaded audio segment: {len(waveform)} samples at {sample_rate}Hz")
        # Extract frames
        frames = extract_frames(waveform, sample_rate)
        if frames is not None:
            print(f"  ✓ Extracted frames: shape {frames.shape}")
            video_frames.append(frames)
            video_uids.append(uid)
        else:
            print(f"  ✗ Frame extraction failed")
    else:
        print(f"  ✗ Failed to load audio segment")

# Save results if we got any
if video_frames:
    try:
        print(f"\nSaving {len(video_frames)} frame sequences...")
        output_path = OUTPUT_DIR / f"{first_video_id}.npy"
        np.save(output_path, np.array(video_frames, dtype=object))
        print(f"✓ Saved to {output_path}")
        
        # Save mapping
        with open(OUTPUT_DIR / f"{first_video_id}_uids.json", 'w') as f:
            json.dump(video_uids, f)
        print(f"✓ Saved UID mapping")
        
        print(f"\n=== TEST SUCCESSFUL ===")
        print(f"Processed {len(video_frames)}/{len(utterances[:3])} test utterances")
    except Exception as e:
        print(f"✗ Error saving: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n=== TEST FAILED ===")
    print("No frames were extracted")
