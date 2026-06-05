"""
Boundary Error Audit — ChuckleNet (Fixed audio handling)
=========================================================
Purpose: Diagnose why IoU-F1 is stuck at 0.50.

Fixed: handles stereo 48kHz audio, converts to mono 16kHz.
Uses energy spike detection for laugh onset.
"""

import json
import os
import numpy as np
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Config
AUDIO_BASE = '/Users/Subho/autonomous_laughter_prediction_essential'
ALIGNED_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl'
TARGET_SR = 16000

print_lock = threading.Lock()
def log(msg):
    with print_lock:
        print(msg, flush=True)

def load_audio_segment(audio_path, start_sec, end_sec, target_sr=TARGET_SR):
    """
    Load audio segment, convert stereo→mono, 48kHz→16kHz.
    Returns mono float32 array at target_sr.
    """
    try:
        with sf.SoundFile(audio_path) as f:
            sample_start = int(start_sec * f.samplerate)
            sample_end = int(end_sec * f.samplerate)
            f.seek(sample_start)
            segment = f.read(sample_end - sample_start)
        
        # Convert to mono if stereo
        if len(segment.shape) > 1 and segment.shape[1] > 1:
            segment = np.mean(segment, axis=1)
        
        # Convert dtype to float32
        segment = segment.astype(np.float32)
        
        # Resample if needed (simple linear interpolation)
        if f.samplerate != target_sr:
            orig_sr = f.samplerate
            num_samples = int(len(segment) * target_sr / orig_sr)
            indices = np.linspace(0, len(segment) - 1, num_samples)
            segment = np.interp(indices, np.arange(len(segment)), segment)
        
        return segment
    except Exception as e:
        return None


def detect_laugh_onset(audio, sr=TARGET_SR):
    """
    Detect audience laugh onset using RMS energy spike.
    Returns onset time in seconds from start of audio segment.
    """
    if len(audio) < sr * 0.3:  # less than 0.3s
        return None
    
    # Compute RMS in 50ms windows
    frame_length = int(0.05 * sr)
    hop_length = frame_length // 2
    
    rms_vals = []
    for i in range(0, len(audio) - frame_length, hop_length):
        frame = audio[i:i+frame_length]
        rms_vals.append(np.sqrt(np.mean(frame ** 2)))
    rms = np.array(rms_vals)
    
    if len(rms) < 10:
        return None
    
    # Threshold: median * 2.5 (audience laughter is louder than speech)
    median_rms = np.median(rms)
    threshold = median_rms * 2.5
    
    # Find sustained elevation > 100ms
    above_threshold = rms > threshold
    min_sustained_frames = int(0.1 * sr / hop_length)  # 100ms
        
    for i in range(len(above_threshold) - min_sustained_frames):
        if np.all(above_threshold[i:i+min_sustained_frames]):
            return i * hop_length / sr
    
    return None


def process_sample(args):
    """Process one positive sample."""
    idx, d = args
    
    video_id = d['video_id']
    start = d['start']
    audio_file = d.get('audio_file', '')
    
    if not audio_file:
        return {'status': 'missing_audio', 'offset_ms': None}
    
    audio_path = os.path.join(AUDIO_BASE, audio_file)
    if not os.path.exists(audio_path):
        return {'status': 'missing_audio', 'offset_ms': None}
    
    try:
        # Load segment: start - 0.5s to start + 5s
        segment = load_audio_segment(audio_path, start - 0.5, start + 5.0, TARGET_SR)
        
        if segment is None or len(segment) < TARGET_SR * 0.3:
            return {'status': 'load_error', 'offset_ms': None}
        
        # Detect laugh onset
        onset = detect_laugh_onset(segment, TARGET_SR)
        
        if onset is None:
            return {'status': 'no_onset', 'offset_ms': None}
        
        # Compute offset
        # actual_laugh_time = segment_start + onset = (start - 0.5) + onset
        actual_laugh_time = (start - 0.5) + onset
        offset_ms = (actual_laugh_time - start) * 1000
        
        return {'status': 'success', 'offset_ms': float(offset_ms)}
    
    except Exception as e:
        return {'status': 'error', 'offset_ms': None}


def audit(n_samples=50, seed=42, max_workers=4):
    log(f"Loading {ALIGNED_PATH}...")
    all_data = [json.loads(line) for line in open(ALIGNED_PATH)]
    positive_data = [d for d in all_data if d.get('label_any', 0) == 1]
    log(f"Total: {len(all_data)}, Positive: {len(positive_data)}")
    
    np.random.seed(seed)
    idxs = np.random.choice(len(positive_data), size=min(n_samples, len(positive_data)), replace=False)
    samples = [(i, positive_data[i]) for i in idxs]
    
    log(f"Processing {len(samples)} samples...")
    
    offsets = []
    status_counts = {'success': 0, 'no_onset': 0, 'missing_audio': 0, 'error': 0, 'load_error': 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(process_sample, s): s for s in samples}
        for i, f in enumerate(as_completed(futures)):
            r = f.result()
            status_counts[r['status']] += 1
            if r['status'] == 'success' and r['offset_ms'] is not None:
                offsets.append(r['offset_ms'])
            if (i + 1) % 10 == 0:
                log(f"  {i+1}/{len(samples)}...")
    
    log(f"\n{'='*60}")
    log(f"RESULTS")
    log(f"{'='*60}")
    log(f"Counts: {status_counts}")
    
    if len(offsets) == 0:
        log("❌ NO ONSETS DETECTED")
        return None
    
    offsets = np.array(offsets)
    abs_o = np.abs(offsets)
    
    log(f"\nOffset stats (ms):")
    log(f"  Mean: {np.mean(offsets):.1f}, Median: {np.median(offsets):.1f}")
    log(f"  Std: {np.std(offsets):.1f}, Range: [{np.min(offsets):.1f}, {np.max(offsets):.1f}]")
    log(f"  Mean abs: {np.mean(abs_o):.1f}ms")
    log(f"\nDistribution:")
    log(f"  <250ms: {100*np.mean(abs_o < 250):.1f}%")
    log(f"  <500ms: {100*np.mean(abs_o < 500):.1f}%")
    log(f"  <1000ms: {100*np.mean(abs_o < 1000):.1f}%")
    
    avg = np.mean(abs_o)
    
    log(f"\n{'='*60}")
    if avg < 250:
        log(f"✅ CLEAN (avg {avg:.0f}ms) → Track A (cascade)")
    elif avg < 500:
        log(f"⚠️  MODERATE (avg {avg:.0f}ms) → Track A viable, Track C adds value")
    elif avg < 1000:
        log(f"⚠️  NOISY (avg {avg:.0f}ms) → Track C first, then A")
    else:
        log(f"❌ VERY NOISY (avg {avg:.0f}ms) → Track C ESSENTIAL")
    
    return {
        'offsets': offsets.tolist(),
        'mean_offset': float(np.mean(offsets)),
        'mean_abs_offset': float(np.mean(abs_o)),
        'median_offset': float(np.median(offsets)),
        'std_offset': float(np.std(offsets)),
        'detected_count': len(offsets),
        'status_counts': status_counts,
        'pct_under_500ms': float(100 * np.mean(abs_o < 500)),
        'pct_under_1000ms': float(100 * np.mean(abs_o < 1000))
    }


if __name__ == '__main__':
    print("ChuckleNet Boundary Audit (Fixed)")
    print("=" * 60)
    results = audit(n_samples=50, seed=42, max_workers=4)
    if results:
        out = '/Users/Subho/autonomous_laughter_prediction/experiments/boundary_audit_results.json'
        with open(out, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved to {out}")