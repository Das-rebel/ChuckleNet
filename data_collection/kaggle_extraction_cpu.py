#!/usr/bin/env python3
"""
CPU-based WavLM feature extraction for local machines.
Extracts WavLM-Base-Plus embeddings with prosody features.

Usage:
    python kaggle_extraction_cpu.py                    # Full run
    python kaggle_extraction_cpu.py --resume           # Resume from checkpoint
    python kaggle_extraction_cpu.py --limit 50         # Limit to 50 videos
    python kaggle_extraction_cpu.py --video-id XYZ     # Single video
"""

import os
import sys
import json
import time
import argparse
import subprocess
import numpy as np
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import torch
import librosa
from transformers import WavLMModel, Wav2Vec2FeatureExtractor

# ============================================================================
# PATHS
# ============================================================================

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
PROSODY_FILE = PROJECT_ROOT / "data/prosody_aligned/prosody_aligned_features.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "wavlm_embeddings_cpu"
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"

# Audio search paths
AUDIO_SEARCH_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "data_collection",
    PROJECT_ROOT / "data/youtube_scraped",
    PROJECT_ROOT / "data/audio_comedy",
]

# ============================================================================
# ARGS
# ============================================================================

parser = argparse.ArgumentParser(description="CPU WavLM feature extraction")
parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
parser.add_argument("--limit", type=int, default=0, help="Limit number of videos (0=all)")
parser.add_argument("--video-id", type=str, default=None, help="Process single video")
parser.add_argument("--batch-size", type=int, default=8, help="Batch size for extraction")
parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="Device")
args = parser.parse_args()

# ============================================================================
# SETUP
# ============================================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

SR = 16000
DEVICE = torch.device(args.device if args.device == "cuda" and torch.cuda.is_available() else "cpu")

print("=" * 60)
print("WavLM CPU Feature Extraction")
print("=" * 60)
print(f"Device: {DEVICE}")
print(f"Resume: {args.resume}")
print(f"Limit: {args.limit or 'all'}")
print(f"Prosody file: {PROSODY_FILE}")
print(f"Output dir: {OUTPUT_DIR}")
print()

# ============================================================================
# LOAD PROSODY DATA
# ============================================================================

print("Loading prosody features...")
utterances = []
with open(PROSODY_FILE) as f:
    for line in f:
        d = json.loads(line)
        if d.get("prosody_matched") or d.get("video_id"):
            utterances.append(d)

print(f"Loaded {len(utterances):,} utterances")

# Group by video
video_utts: Dict[str, List[Dict]] = defaultdict(list)
for utt in utterances:
    uid = utt.get("uid", "")
    # uid format: video_id_start
    parts = uid.rsplit("_", 2)
    if len(parts) >= 2:
        vid = parts[0]
    else:
        vid = utt.get("video_id", "")
    if vid:
        video_utts[vid].append(utt)

print(f"Videos: {len(video_utts)}")

# ============================================================================
# CHECKPOINT
# ============================================================================

done_videos: set = set()
failed_videos: set = set()

if args.resume and CHECKPOINT_FILE.exists():
    with open(CHECKPOINT_FILE) as f:
        ckpt = json.load(f)
    done_videos = set(ckpt.get("done", []))
    failed_videos = set(ckpt.get("failed", []))
    print(f"Resuming: {len(done_videos)} done, {len(failed_videos)} failed")

videos_to_process = [v for v in video_utts if v not in done_videos and v not in failed_videos]
if args.video_id:
    videos_to_process = [v for v in videos_to_process if v == args.video_id]
if args.limit > 0:
    videos_to_process = videos_to_process[: args.limit]

print(f"Videos to process: {len(videos_to_process)}")

# ============================================================================
# AUDIO LOADING
# ============================================================================

AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".wma"]


def find_audio_file(video_id: str) -> Optional[str]:
    """Find audio file for a video."""
    for search_dir in AUDIO_SEARCH_DIRS:
        if not search_dir.exists():
            continue
        for root, dirs, files in os.walk(search_dir):
            for f in files:
                if video_id in f:
                    for ext in AUDIO_EXTENSIONS:
                        if f.endswith(ext):
                            return os.path.join(root, f)
    return None


@lru_cache(maxsize=8)
def load_audio_cached(audio_path: str) -> Optional[np.ndarray]:
    """Load audio file, resample to 16kHz mono."""
    if not audio_path or not os.path.exists(audio_path):
        return None
    try:
        y, _ = librosa.load(audio_path, sr=SR, mono=True)
        return y
    except Exception as e:
        print(f"Audio load error {audio_path}: {e}")
        return None


def extract_segment(
    audio_path: str, start: float, end: float, pad_ms: float = 200
) -> np.ndarray:
    """Extract audio segment with padding."""
    y = load_audio_cached(audio_path)
    if y is None:
        return np.zeros(int(0.5 * SR), dtype=np.float32)

    s = max(0, start - pad_ms / 1000)
    e = min(len(y) / SR, end + pad_ms / 1000)
    s_samp = int(s * SR)
    e_samp = int(e * SR)

    if s_samp >= len(y) or e_samp <= s_samp:
        return np.zeros(int(0.5 * SR), dtype=np.float32)

    seg = y[s_samp:e_samp].astype(np.float32)

    min_len = int(0.1 * SR)
    if len(seg) < min_len:
        seg = np.pad(seg, (0, min_len - len(seg)))

    return seg


# ============================================================================
# WAVLM MODEL
# ============================================================================

print("\nLoading WavLM-Base-Plus...")
wavlm_model = WavLMModel.from_pretrained("facebook/wavlm-base-plus")
wavlm_model.to(DEVICE)
wavlm_model.eval()
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/wavlm-base-plus")
print(f"WavLM loaded. Params: {sum(p.numel() for p in wavlm_model.parameters())/1e6:.1f}M")


def get_wavlm_embedding(audio_segment: np.ndarray) -> np.ndarray:
    """Get WavLM embedding for a single audio segment."""
    if len(audio_segment) < 400:
        return np.zeros(768, dtype=np.float32)

    inputs = feature_extractor(audio_segment, sampling_rate=SR, return_tensors="pt")
    input_values = inputs.input_values.to(DEVICE)

    with torch.no_grad():
        outputs = wavlm_model(input_values)

    hidden = outputs.last_hidden_state[0].cpu().numpy()
    return hidden.mean(axis=0).astype(np.float32)


def get_wavlm_embedding_batch(audio_segments: List[np.ndarray]) -> List[np.ndarray]:
    """Get WavLM embeddings for a batch of audio segments."""
    # Filter too-short segments
    valid_mask = [len(s) >= 400 for s in audio_segments]
    valid_segs = [s if m else np.zeros(int(0.5 * SR), dtype=np.float32) for s, m in zip(audio_segments, valid_mask)]

    # Pad to max length
    max_len = max(len(s) for s in valid_segs)
    padded = np.zeros((len(valid_segs), max_len), dtype=np.float32)
    for i, s in enumerate(valid_segs):
        padded[i, : len(s)] = s

    inputs = feature_extractor(padded, sampling_rate=SR, return_tensors="pt", padding=True)
    input_values = inputs.input_values.to(DEVICE)

    with torch.no_grad():
        outputs = wavlm_model(input_values)

    hidden = outputs.last_hidden_state.cpu().numpy()
    embeddings = []
    for i in range(len(audio_segments)):
        if valid_mask[i]:
            emb = hidden[i].mean(axis=0)
        else:
            emb = np.zeros(768, dtype=np.float32)
        embeddings.append(emb.astype(np.float32))

    return embeddings


# ============================================================================
# MAIN EXTRACTION LOOP
# ============================================================================

CHECKPOINT_EVERY = 10  # videos
BATCH_SIZE = args.batch_size

total_embeddings = 0
t0 = time.time()
current_audio_path = None
current_audio_cache_key = None


def save_checkpoint():
    ckpt = {
        "done": sorted(list(done_videos)),
        "failed": sorted(list(failed_videos)),
        "total_embeddings": total_embeddings,
        "timestamp": time.time(),
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(ckpt, f, indent=2)


for vi, video_id in enumerate(videos_to_process):
    t_vid = time.time()
    utts = video_utts[video_id]

    # Find audio
    audio_path = find_audio_file(video_id)
    if not audio_path:
        print(f"[{vi+1}/{len(videos_to_process)}] {video_id}: audio not found, skipping")
        failed_videos.add(video_id)
        continue

    # Clear cache when audio file changes
    if audio_path != current_audio_path:
        load_audio_cached.cache_clear()
        current_audio_path = audio_path

    # Extract embeddings in batches
    embeddings: Dict[str, List[float]] = {}
    prosody_features: Dict[str, List[float]] = {}

    for batch_start in range(0, len(utts), BATCH_SIZE):
        batch_utts = utts[batch_start : batch_start + BATCH_SIZE]
        audio_segs = []

        for utt in batch_utts:
            uid = utt.get("uid")
            if not uid:
                continue
            start = utt.get("start")
            end = utt.get("end")
            if start is None or end is None:
                continue
            audio_segs.append(extract_segment(audio_path, start, end))

        # Batch WavLM extraction
        embs = get_wavlm_embedding_batch(audio_segs)

        for j, utt in enumerate(batch_utts):
            uid = utt.get("uid")
            if not uid:
                continue
            embeddings[uid] = embs[j].tolist()
            prosody_features[uid] = utt.get("prosody_10dim", [0.0] * 10)

    if not embeddings:
        print(f"[{vi+1}/{len(videos_to_process)}] {video_id}: no embeddings extracted")
        failed_videos.add(video_id)
        continue

    # Save this video's embeddings
    out_path = OUTPUT_DIR / f"{video_id}_wavlm_prosody.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "video_id": video_id,
                "wavlm_embeddings": embeddings,
                "prosody_features": prosody_features,
                "n_embeddings": len(embeddings),
            },
            f,
        )

    done_videos.add(video_id)
    total_embeddings += len(embeddings)

    elapsed = time.time() - t_vid
    print(f"[{vi+1}/{len(videos_to_process)}] {video_id}: {len(embeddings)} emb, {elapsed:.1f}s")

    # Checkpoint every CHECKPOINT_EVERY videos
    if (vi + 1) % CHECKPOINT_EVERY == 0:
        save_checkpoint()
        elapsed_total = time.time() - t0
        rate = (vi + 1) / elapsed_total
        eta = (len(videos_to_process) - vi - 1) / rate / 60
        print(f"\n  === CHECKPOINT {vi+1}/{len(videos_to_process)} | {total_embeddings:,} emb | ETA: {eta:.0f} min ===\n")

# Final checkpoint
save_checkpoint()

total_time = time.time() - t0
print(f"\n{'='*60}")
print(f"EXTRACTION COMPLETE")
print(f"{'='*60}")
print(f"Videos done: {len(done_videos)}")
print(f"Videos failed: {len(failed_videos)}")
print(f"Total embeddings: {total_embeddings:,}")
print(f"Time: {total_time/60:.1f} min")
print(f"Output: {OUTPUT_DIR}")
print(f"Checkpoint: {CHECKPOINT_FILE}")

# ============================================================================
# VERIFY OUTPUT
# ============================================================================

output_files = list(OUTPUT_DIR.glob("*.json"))
print(f"\nOutput files: {len(output_files)}")

if output_files:
    sample = output_files[0]
    with open(sample) as f:
        data = json.load(f)
    sample_uid = list(data["wavlm_embeddings"].keys())[0]
    emb = data["wavlm_embeddings"][sample_uid]
    pros = data["prosody_features"][sample_uid]
    print(f"Sample: {sample.name}")
    print(f"  WavLM dim: {len(emb)}")
    print(f"  Prosody dim: {len(pros)}")
    print(f"  UIDs: {data['n_embeddings']}")