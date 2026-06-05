"""
Track C: Pause Feature Extraction (Simplified, Single-pass)
============================================================

Extract pause_before for words in the 50 prosody videos.
Process each video in a single pass using segment seeking.
"""

import json
import os
import numpy as np
import pandas as pd
import soundfile as sf
from collections import defaultdict
import time

AUDIO_BASE = '/Users/Subho/autonomous_laughter_prediction_essential'
PROSODY_CSV = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/prosody_features_50videos.csv'
ALIGNED_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl'
OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/data/prosody_aligned'

SR = 16000
PAUSE_THRESHOLD = 0.8
CHUNK_SIZE = 60  # seconds per chunk

print("=" * 60)
print("Track C: Pause Feature Extraction")
print("=" * 60)

def find_audio_file(video_id):
    """Find the audio file for a video."""
    for batch in range(1, 30):
        path = f'{AUDIO_BASE}/data/audio_comedy/audio/batch{batch}/{video_id}.mp3'
        if os.path.exists(path):
            return path
    return None


def compute_pause_in_window(audio, sr=16000, threshold_ratio=0.05):
    """Compute total silence duration in audio window."""
    if len(audio) < sr * 0.05:
        return 0.0
    
    # 20ms frames
    frame_length = int(0.02 * sr)
    hop_length = frame_length
    
    rms_vals = []
    for i in range(0, len(audio) - frame_length, hop_length):
        frame = audio[i:i+frame_length]
        rms_vals.append(np.sqrt(np.mean(frame ** 2)))
    rms = np.array(rms_vals)
    
    if len(rms) < 3:
        return 0.0
    
    max_rms = np.max(rms)
    if max_rms < 0.001:
        return len(rms) * hop_length / sr
    
    threshold = max_rms * threshold_ratio
    silent_frames = np.sum(rms < threshold)
    
    return silent_frames * hop_length / sr


def process_video_simple(video_id, words, audio_path):
    """Process all words in a video using chunk-based loading."""
    results = []
    
    # Group words by 60-second chunks
    chunks = defaultdict(list)
    for w in words:
        chunk_start = int(w['start'] / CHUNK_SIZE) * CHUNK_SIZE
        chunks[chunk_start].append(w)
    
    # Process each chunk
    for chunk_start, chunk_words in sorted(chunks.items()):
        chunk_end = chunk_start + CHUNK_SIZE + 5  # +5s for pre-word buffer
        
        try:
            with sf.SoundFile(audio_path) as f:
                sr_native = f.samplerate
                sample_start = int(chunk_start * sr_native)
                sample_end = min(int(chunk_end * sr_native), int(f.frames))
                f.seek(sample_start)
                chunk_audio = f.read(sample_end - sample_start)
            
            # Convert to mono 16kHz
            if len(chunk_audio.shape) > 1:
                chunk_audio = np.mean(chunk_audio, axis=1)
            chunk_audio = chunk_audio.astype(np.float32)
            
            # Resample if needed
            if sr_native != SR:
                num_samples = int(len(chunk_audio) * SR / sr_native)
                indices = np.linspace(0, len(chunk_audio) - 1, num_samples)
                chunk_audio = np.interp(indices, np.arange(len(chunk_audio)), chunk_audio)
            
            # Process each word in chunk
            for w in chunk_words:
                word_start_in_chunk = w['start'] - chunk_start  # seconds from chunk start
                word_start_in_audio = word_start_in_chunk * SR
                
                # Pre-word window: 3s before word start
                pre_start = max(0, int((word_start_in_chunk - 3.0) * SR))
                pre_end = max(pre_start + 1, int(word_start_in_chunk * SR))
                
                if pre_end <= len(chunk_audio):
                    pre_audio = chunk_audio[pre_start:pre_end]
                    pause_dur = compute_pause_in_window(pre_audio, SR)
                else:
                    pause_dur = 0.0
                
                results.append({
                    'word_start': w['start'],
                    'pause_before': pause_dur,
                    'pause_before_binary': 1.0 if pause_dur > PAUSE_THRESHOLD else 0.0
                })
        
        except Exception as e:
            print(f"  Error processing chunk {chunk_start} for {video_id}: {e}")
            for w in chunk_words:
                results.append({
                    'word_start': w['start'],
                    'pause_before': 0.0,
                    'pause_before_binary': 0.0
                })
    
    return results


def main():
    # Load prosody CSV to get video list
    print("\nLoading prosody CSV...")
    prosody_df = pd.read_csv(PROSODY_CSV)
    prosody_videos = set(prosody_df['video_id'].unique())
    print(f"  {len(prosody_videos)} videos")
    
    # Load aligned utterances for prosody videos
    print("\nLoading aligned utterances...")
    video_words = defaultdict(list)
    with open(ALIGNED_PATH) as f:
        for line in f:
            d = json.loads(line)
            if d['video_id'] in prosody_videos:
                video_words[d['video_id']].append(d)
    
    print(f"  {sum(len(v) for v in video_words.values())} total words in {len(video_words)} videos")
    
    # Process each video
    print("\nProcessing videos...")
    pause_features = {}
    done = 0
    
    for video_id in sorted(prosody_videos):
        if video_id not in video_words:
            continue
        
        audio_path = find_audio_file(video_id)
        if audio_path is None:
            print(f"  Warning: no audio for {video_id}")
            continue
        
        words = video_words[video_id]
        results = process_video_simple(video_id, words, audio_path)
        
        for r in results:
            key = f"{video_id}_{r['word_start']:.2f}"
            pause_features[key] = [r['pause_before'], r['pause_before_binary']]
        
        done += 1
        if done % 10 == 0:
            print(f"  Processed {done}/{len(prosody_videos)} videos...")
    
    print(f"\nExtracted pause for {len(pause_features)} words")
    
    # Add pause features to prosody CSV
    print("\nAdding pause features to prosody...")
    
    pause_before_list = []
    pause_before_binary_list = []
    
    for _, row in prosody_df.iterrows():
        key = f"{row['video_id']}_{round(row['start'], 2)}"
        if key in pause_features:
            pause_before_list.append(pause_features[key][0])
            pause_before_binary_list.append(pause_features[key][1])
        else:
            pause_before_list.append(0.0)
            pause_before_binary_list.append(0.0)
    
    prosody_df['pause_before_extracted'] = pause_before_list
    prosody_df['pause_before_0.8s_binary'] = pause_before_binary_list
    
    non_zero = sum(1 for p in pause_before_list if p > 0)
    above_threshold = sum(1 for b in pause_before_binary_list if b > 0)
    print(f"  Non-zero pause: {non_zero} ({100*non_zero/len(pause_before_list):.1f}%)")
    print(f"  >0.8s threshold: {above_threshold} ({100*above_threshold/len(pause_before_binary_list):.1f}%)")
    
    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_csv = os.path.join(OUTPUT_DIR, 'prosody_features_enhanced_50videos.csv')
    prosody_df.to_csv(output_csv, index=False)
    print(f"\nSaved: {output_csv}")
    
    # Build joined datasets with embeddings + prosody + pause
    print("\nBuilding joined datasets with pause features...")
    emb_dir = '/Users/Subho/autonomous_laughter_prediction_essential/training/prosody_fusion_embeddings'
    
    for split_name in ['train', 'valid', 'test']:
        emb_path = f'{emb_dir}/{split_name}_embeddings.npz'
        if not os.path.exists(emb_path):
            print(f"  {split_name}: no embeddings file")
            continue
        
        data = np.load(emb_path, allow_pickle=True)
        uids = data['uids']
        labels = data['labels']
        prosody = data['prosody']  # (N, 21)
        embeddings = data['embeddings']  # (N, 384)
        
        new_prosody = []
        for i, uid in enumerate(uids):
            vid, start_str = uid.rsplit('_', 1)
            start = round(float(start_str), 2)
            key = f"{vid}_{start}"
            pause_feat = pause_features.get(key, [0.0, 0.0])
            prosody_row = list(prosody[i]) + pause_feat
            new_prosody.append(prosody_row)
        
        new_prosody = np.array(new_prosody)
        
        out_path = f'{OUTPUT_DIR}/{split_name}_with_pause.npz'
        np.savez(out_path, 
                 embeddings=embeddings, 
                 prosody=new_prosody, 
                 labels=labels, 
                 uids=uids)
        print(f"  {split_name}: {len(uids)} samples, prosody {prosody.shape}→{new_prosody.shape}")
    
    print(f"\n✅ Track C pause extraction complete!")


if __name__ == '__main__':
    main()