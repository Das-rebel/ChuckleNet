#!/usr/bin/env python3
"""
Utterance-Level Frame Extraction for WavLM.
Extracts full frame sequences (not mean embeddings) for Attention Pooling.
"""

import os
import json
import numpy as np
import torch
import librosa
import soundfile as sf
from pathlib import Path
from tqdm import tqdm
from transformers import WavLMModel
import warnings
warnings.filterwarnings('ignore')

# Config
DATA_DIR = Path("/Users/Subho/data/utterances")
AUDIO_DIR = DATA_DIR / "vtt_audio_local"
OUTPUT_DIR = DATA_DIR / "vtt_frames"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Load WavLM model
print("Loading WavLM model...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(device).eval()
print(f"Using device: {device}")

# Load VTT utterance data
vtt_data = {}
with open(DATA_DIR / "utterances_clean.jsonl") as f:
    for line in f:
        obj = json.loads(line)
        vid = obj['video_id']
        if vid not in vtt_data:
            vtt_data[vid] = []
        vtt_data[vid].append(obj)

print(f"Loaded {len(vtt_data)} videos with {sum(len(v) for v in vtt_data.values())} utterances")

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

# Process each video
print("\n=== PROCESSING VIDEOS ===")
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
    
    # Save video frames if we got any
    if video_frames:
        try:
            # Save as numpy array
            output_path = OUTPUT_DIR / f"{video_id}.npy"
            np.save(output_path, np.array(video_frames, dtype=object))  # object dtype for variable length
            # Save mapping
            with open(OUTPUT_DIR / f"{video_id}_uids.json", 'w') as f:
                json.dump(video_uids, f)
        except Exception as e:
            print(f"Error saving {video_id}: {e}")

print(f"\n=== EXTRACTION COMPLETE ===")
print(f"Frames saved to: {OUTPUT_DIR}")

# Create summary
total_utterances = sum(len(v) for v in vtt_data.values())
processed_utterances = sum(len([f for f in OUTPUT_DIR.glob("*.npy")]))
print(f"Processed {processed_utterances}/{total_utterances} utterances")
