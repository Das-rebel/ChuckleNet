#!/usr/bin/env python3
"""
Pre-extract WavLM-Base+ embeddings for all utterances.

Loads each video's audio once, segments utterances by timestamp,
runs through microsoft/wavlm-base-plus, mean-pools to 768-dim,
and saves as a dict mapping utterance_id → tensor(768).

Handles missing audio gracefully (zero vector).
Supports resuming (skips already-extracted videos).
Runs on CPU, CUDA, or MPS (M1 Mac).

Usage:
    python training/extract_wavlm_embeddings.py
    python training/extract_wavlm_embeddings.py --device cuda --batch-size 8
    python training/extract_wavlm_embeddings.py --resume  # skip already-extracted videos
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import torchaudio
import numpy as np
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------

def get_device(device_flag: str = "auto") -> torch.device:
    """Select device: auto-detect CUDA > MPS > CPU, or use flag."""
    if device_flag != "auto":
        return torch.device(device_flag)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

# ---------------------------------------------------------------------------
# Audio loading (with LRU cache so each file is loaded once)
# ---------------------------------------------------------------------------

_audio_cache: Dict[str, Tuple[torch.Tensor, int]] = {}

def load_audio(audio_path: str, target_sr: int = 16000) -> Optional[Tuple[torch.Tensor, int]]:
    """Load audio file, resample to target_sr. Returns (waveform, sample_rate) or None."""
    if audio_path in _audio_cache:
        return _audio_cache[audio_path]
    
    # Try multiple path variations
    candidates = _resolve_audio_path(audio_path)
    
    for path in candidates:
        try:
            waveform, sr = torchaudio.load(path)
            # Resample if needed
            if sr != target_sr:
                waveform = torchaudio.functional.resample(waveform, sr, target_sr)
            # Convert to mono
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            _audio_cache[audio_path] = (waveform, target_sr)
            return (waveform, target_sr)
        except Exception as e:
            continue
    
    return None


def _resolve_audio_path(audio_path: str) -> List[str]:
    """Resolve audio path to actual file location. Tries multiple strategies."""
    candidates = []
    
    # 1. Try as-is
    candidates.append(audio_path)
    
    # 2. Try under autonomous_laughter_prediction_essential/
    base = os.path.basename(audio_path)
    parent = os.path.basename(os.path.dirname(audio_path))
    vid_id = base.replace(".mp3", "")
    
    # Search in all known batch dirs
    search_roots = [
        "data/audio_comedy/audio",
        "autonomous_laughter_prediction_essential/data/audio_comedy/audio",
    ]
    
    for root in search_roots:
        if os.path.isdir(root):
            # Direct file in batch dir
            for batch_dir in sorted(os.listdir(root)):
                batch_path = os.path.join(root, batch_dir)
                if os.path.isdir(batch_path):
                    candidate = os.path.join(batch_path, vid_id + ".mp3")
                    candidates.append(candidate)
                # Handle split dirs (e.g., KkA-HLICnwc subdir)
                if os.path.isdir(batch_path):
                    for sub in os.listdir(batch_path):
                        sub_path = os.path.join(batch_path, sub)
                        if os.path.isdir(sub_path) and sub == vid_id:
                            # Split audio: look for individual segments
                            for f in sorted(os.listdir(sub_path)):
                                if f.endswith(".mp3"):
                                    candidates.append(os.path.join(sub_path, f))
    
    return candidates


def extract_segment(
    waveform: torch.Tensor,
    sr: int,
    start: float,
    end: float,
    context_pad: float = 0.2,
) -> torch.Tensor:
    """Extract audio segment with context padding."""
    pad_samples = int(context_pad * sr)
    start_sample = max(0, int(start * sr) - pad_samples)
    end_sample = min(waveform.shape[-1], int(end * sr) + pad_samples)
    return waveform[:, start_sample:end_sample]


# ---------------------------------------------------------------------------
# WavLM model
# ---------------------------------------------------------------------------

def load_wavlm_model(device: torch.device):
    """Load WavLM-Base+ model from HuggingFace."""
    from transformers import WavLMModel
    
    model_name = "microsoft/wavlm-base-plus"
    print(f"Loading {model_name}...")
    model = WavLMModel.from_pretrained(model_name)
    model = model.to(device)
    model.eval()
    return model


@torch.no_grad()
def extract_wavlm_embedding(
    model,
    audio_segment: torch.Tensor,
    device: torch.device,
    max_duration: float = 30.0,
    sr: int = 16000,
) -> torch.Tensor:
    """
    Extract WavLM embedding for an audio segment.
    Returns 768-dim mean-pooled tensor.
    
    If segment exceeds max_duration, we still process it but
    truncate to max_duration seconds to avoid OOM.
    """
    # Truncate if too long
    max_samples = int(max_duration * sr)
    if audio_segment.shape[-1] > max_samples:
        # Take the middle portion for very long segments
        mid = audio_segment.shape[-1] // 2
        half = max_samples // 2
        audio_segment = audio_segment[:, mid - half : mid + half]
    
    # Minimum length: 0.4s (WavLM needs at least ~400 samples at 16kHz)
    min_samples = int(0.4 * sr)
    if audio_segment.shape[-1] < min_samples:
        # Pad with zeros
        pad = min_samples - audio_segment.shape[-1]
        audio_segment = torch.nn.functional.pad(audio_segment, (0, pad))
    
    audio_segment = audio_segment.to(device)
    
    # WavLM expects shape (batch, sequence_length)
    if audio_segment.dim() == 2:
        audio_segment = audio_segment.squeeze(0)
    
    outputs = model(audio_segment.unsqueeze(0))
    # outputs.last_hidden_state: (1, T, 768)
    embedding = outputs.last_hidden_state.squeeze(0).mean(dim=0)  # (768,)
    
    return embedding.cpu()


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract WavLM utterance embeddings")
    parser.add_argument("--utterances", type=str,
                        default="autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl",
                        help="Path to aligned_utterances.jsonl")
    parser.add_argument("--output", type=str,
                        default="data/audio_comedy/wavlm_utterance_embeddings.pt",
                        help="Output .pt file")
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cuda", "mps", "cpu"],
                        help="Device to use")
    parser.add_argument("--batch-size", type=int, default=1,
                        help="Processing batch size (currently 1, kept for future)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-extracted videos")
    parser.add_argument("--max-videos", type=int, default=0,
                        help="Max videos to process (0 = all)")
    parser.add_argument("--context-pad", type=float, default=0.2,
                        help="Context padding in seconds around each utterance")
    parser.add_argument("--max-audio-duration", type=float, default=30.0,
                        help="Max audio duration in seconds (truncate longer)")
    args = parser.parse_args()
    
    device = get_device(args.device)
    print(f"Using device: {device}")
    
    # Load utterances
    print(f"Loading utterances from {args.utterances}...")
    utterances_by_video: Dict[str, List[dict]] = defaultdict(list)
    all_utterances: List[dict] = []
    
    with open(args.utterances) as f:
        for line in f:
            d = json.loads(line.strip())
            utterances_by_video[d["video_id"]].append(d)
            all_utterances.append(d)
    
    print(f"Loaded {len(all_utterances)} utterances across {len(utterances_by_video)} videos")
    
    # Load or initialize embeddings dict
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    
    embeddings: Dict[str, torch.Tensor] = {}
    already_extracted_videos: set = set()
    
    if args.resume and os.path.exists(args.output):
        print(f"Resuming from existing embeddings at {args.output}")
        saved = torch.load(args.output, map_location="cpu", weights_only=False)
        embeddings.update(saved)
        # Find which videos are already done
        existing_uids = set(embeddings.keys())
        for vid, utts in utterances_by_video.items():
            if all(u["utterance_id"] in existing_uids for u in utts):
                already_extracted_videos.add(vid)
        print(f"Already extracted {len(already_extracted_videos)} videos, "
              f"{len(embeddings)} utterances")
    
    # Count positive rate
    pos = sum(1 for u in all_utterances if u.get("label_any", 0) == 1)
    print(f"Label distribution: {pos}/{len(all_utterances)} positive "
          f"({100*pos/len(all_utterances):.1f}%)")
    
    # Load WavLM model
    model = load_wavlm_model(device)
    dim = model.config.hidden_size  # Should be 768
    print(f"WavLM hidden size: {dim}")
    
    # Process by video
    video_ids = sorted(utterances_by_video.keys())
    if args.max_videos > 0:
        video_ids = video_ids[:args.max_videos]
    
    stats = {"extracted": 0, "missing_audio": 0, "total": 0}
    
    for video_id in tqdm(video_ids, desc="Videos"):
        if video_id in already_extracted_videos:
            continue
        
        utts = utterances_by_video[video_id]
        if not utts:
            continue
        
        # Load audio for this video (once per video)
        audio_path = utts[0]["audio_file"]
        audio_data = load_audio(audio_path, target_sr=16000)
        
        if audio_data is None:
            print(f"\n  [WARN] No audio for video {video_id}, using zero vectors")
            for utt in utts:
                embeddings[utt["utterance_id"]] = torch.zeros(dim)
                stats["missing_audio"] += 1
                stats["total"] += 1
            # Save checkpoint
            if stats["total"] % 500 == 0:
                torch.save(embeddings, args.output)
                print(f"\n  Checkpoint saved: {len(embeddings)} embeddings")
            continue
        
        waveform, sr = audio_data
        
        for utt in tqdm(utts, desc=f"  {video_id}", leave=False):
            uid = utt["utterance_id"]
            start = utt["start"]
            end = utt["end"]
            
            # Extract segment
            segment = extract_segment(
                waveform, sr, start, end,
                context_pad=args.context_pad,
            )
            
            # Get WavLM embedding
            try:
                emb = extract_wavlm_embedding(
                    model, segment, device,
                    max_duration=args.max_audio_duration,
                    sr=sr,
                )
                embeddings[uid] = emb
                stats["extracted"] += 1
            except Exception as e:
                print(f"\n  [ERROR] Failed to extract {uid}: {e}")
                embeddings[uid] = torch.zeros(dim)
                stats["missing_audio"] += 1
            
            stats["total"] += 1
        
        # Clear audio cache to free memory
        if audio_path in _audio_cache:
            del _audio_cache[audio_path]
        
        # Periodic save
        if stats["total"] % 500 == 0 and stats["total"] > 0:
            torch.save(embeddings, args.output)
            print(f"\n  Checkpoint: {stats}")
    
    # Final save
    print(f"\nFinal save: {len(embeddings)} embeddings to {args.output}")
    torch.save(embeddings, args.output)
    
    # Summary statistics
    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"  Total utterances: {stats['total']}")
    print(f"  Successfully extracted: {stats['extracted']}")
    print(f"  Missing audio (zero vectors): {stats['missing_audio']}")
    print(f"  Embedding dimension: {dim}")
    print(f"  Output: {args.output}")
    print(f"  File size: {os.path.getsize(args.output) / 1e6:.1f} MB")
    print(f"{'='*60}")
    
    # Validate: check embedding quality
    non_zero = sum(1 for v in embeddings.values() if v.abs().sum() > 0)
    print(f"  Non-zero embeddings: {non_zero}/{len(embeddings)}")
    if non_zero > 0:
        norms = [v.norm().item() for v in embeddings.values() if v.abs().sum() > 0]
        print(f"  Embedding norms: mean={np.mean(norms):.3f}, "
              f"std={np.std(norms):.3f}, "
              f"min={np.min(norms):.3f}, max={np.max(norms):.3f}")


if __name__ == "__main__":
    main()