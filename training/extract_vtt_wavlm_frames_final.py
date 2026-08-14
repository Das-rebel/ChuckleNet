#!/usr/bin/env python3
"""
Utterance-Level Frame Extraction for WavLM - Fixed Audio Loading.
Uses librosa instead of soundfile for better format support.
"""

import os
import sys
import json
import numpy as np
import torch
import librosa
from pathlib import Path
from tqdm import tqdm
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

# Count audio files
audio_files = list(AUDIO_DIR.glob("*.m4a")) + list(AUDIO_DIR.glob("*.mp3"))
print(f"Found {len(audio_files)} audio files")

if len(audio_files) == 0:
    print("✗ No audio files found!")
    sys.exit(1)

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
if not vtt_file.exists():
    print(f"✗ VTT data file not found: {vtt_file}")
    sys.exit(1)

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
        print(f"Error extracting frames: {e}")
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
            except Exception as e:
                print(f"Error loading {audio_path}: {e}")
                continue
    
    return None, None

# Process each video
print("\n=== PROCESSING VIDEOS ===")
processed_videos = 0
total_frames_extracted = 0
errors = []

for video_id in tqdm(vtt_data.keys(), desc="Extracting frames"):
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
            print(error_msg)
            errors.append(error_msg)

print(f"\n=== EXTRACTION COMPLETE ===")
print(f"Processed videos: {processed_videos}/{len(vtt_data)}")
print(f"Total utterances processed: {total_frames_extracted}/{utterance_count}")
print(f"Frames saved to: {OUTPUT_DIR}")
if errors:
    print(f"\nErrors encountered: {len(errors)}")
    for error in errors[:5]:  # Show first 5 errors
        print(f"  - {error}")
