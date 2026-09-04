#!/usr/bin/env python3
"""
Extract eGeMAPS from YouTube Audio
=================================
Uses openSMILE to extract eGeMAPS features compatible with original dataset.
"""

import opensmile
import numpy as np
import json
import glob
import os
from datetime import datetime
import time

AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-youtube/egemaps'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_egemaps(audio_path, video_id):
    """Extract eGeMAPS features from audio file."""
    try:
        smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.Functionals,
        )
        
        result = smile.process_file(audio_path)
        
        # Get column names and values
        columns = list(result.columns)
        values = result.iloc[0].values
        
        # Create dict with column name as key
        features = {col: float(val) for col, val in zip(columns, values)}
        
        return {
            'video_id': video_id,
            'features': features,
            'n_features': len(columns),
            'duration': float(result.index[-1] - result.index[0]) if len(result) > 1 else 0,
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("="*70)
    print("EXTRACTING eGeMAPS FROM YOUTUBE AUDIO")
    print("="*70)
    
    audio_files = glob.glob(f'{AUDIO_DIR}/*.wav')
    print(f"Audio files: {len(audio_files)}")
    
    # Check already done
    done_files = set(os.path.basename(f)[:-5] for f in glob.glob(f'{OUTPUT_DIR}/*.json'))
    to_process = [f for f in audio_files if os.path.basename(f)[:-4] not in done_files]
    print(f"Already done: {len(done_files)}")
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Process first 30
    success = 0
    for i, audio_path in enumerate(to_process[:30]):
        vid = os.path.basename(audio_path)[:-4]
        print(f"[{i+1}/{min(30, len(to_process))}] {vid}...", end=" ", flush=True)
        
        result = extract_egemaps(audio_path, vid)
        
        if result:
            out_file = f'{OUTPUT_DIR}/{vid}.json'
            with open(out_file, 'w') as f:
                json.dump(result, f)
            print(f"✓ {result['n_features']} features")
            success += 1
        
        time.sleep(0.1)
    
    print(f"\nSuccess: {success}/30")
    print(f"Total eGeMAPS files: {len(glob.glob(f'{OUTPUT_DIR}/*.json'))}")

if __name__ == '__main__':
    main()
