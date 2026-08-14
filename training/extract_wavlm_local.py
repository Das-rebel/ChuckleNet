#!/usr/bin/env python3
"""
Extract WavLM embeddings locally on Mac CPU.
Frame-level loading (librosa offset+duration) — no full-file loads, no OOM.
Resume: skips already-saved videos.
Per-video output: experiments/wavlm_embeddings/{video_id}.pt + .json

Runtime: ~30-60 min for 68 videos on Mac CPU.
"""

import json, os, sys, time, gc
from pathlib import Path
from collections import defaultdict

import torch
import numpy as np
import librosa
from tqdm import tqdm

# ─── Config ───
PROJECT = Path(__file__).resolve().parent.parent
UTTERANCES = PROJECT / "data" / "audio_comedy" / "aligned_utterances.jsonl"
AUDIO_DIR = PROJECT / "data" / "audio_comedy" / "audio"
OUTPUT_DIR = PROJECT / "experiments" / "wavlm_embeddings"

SR = 16000
PAD = 0.2
MAX_CLIP_SEC = 7.8


def find_audio(video_id, audio_dir):
    """Find MP3 file for a video_id by scanning batch directories."""
    if not audio_dir.exists():
        return None
    # Search in batch*/ subdirs
    for batch_dir in sorted(audio_dir.iterdir()):
        if not batch_dir.is_dir():
            continue
        mp3 = batch_dir / f"{video_id}.mp3"
        if mp3.exists():
            return str(mp3)
    return None


def load_segment(path, t0, t1, sr=SR):
    """Load audio segment [t0, t1] using librosa offset+duration (no full-file load)."""
    dur = t1 - t0
    if dur < 0.1:
        t0 = max(0.0, t1 - 0.1)
        dur = 0.1
    try:
        y, _ = librosa.load(path, sr=sr, offset=t0, duration=dur, mono=True)
        y = torch.from_numpy(y).float()
    except Exception:
        return None
    target = int(sr * dur)
    if len(y) < target:
        y = torch.nn.functional.pad(y, (0, target - len(y)))
    else:
        y = y[:target]
    return y.unsqueeze(0)  # (1, T)


def main():
    print(f"{'='*60}")
    print("WavLM Embedding Extraction (local CPU)")
    print(f"{'='*60}")

    # Device
    device = torch.device("cpu")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    print(f"Device: {device}")

    # Load utterances
    print(f"Loading utterances from {UTTERANCES}...")
    with open(UTTERANCES) as f:
        utterances = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(utterances)} utterances")

    # Group by video
    video_utts = defaultdict(list)
    for u in utterances:
        video_utts[u["video_id"]].append(u)
    print(f"Videos: {len(video_utts)}")

    # Find audio files
    print(f"Scanning {AUDIO_DIR}...")
    audio_map = {}
    for vid in sorted(video_utts.keys()):
        path = find_audio(vid, AUDIO_DIR)
        if path:
            audio_map[vid] = path
    print(f"Found audio for {len(audio_map)}/{len(video_utts)} videos")

    # Resume
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    done = set()
    for pf in OUTPUT_DIR.glob("*.pt"):
        done.add(pf.stem)
    if done:
        remaining = len(audio_map) - len(done)
        print(f"Resume: {len(done)} done, {remaining} remaining")

    # Load WavLM
    print("Loading WavLM...")
    from transformers import WavLMModel
    wavlm = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(device).eval()
    print("WavLM loaded")

    videos = sorted(audio_map.keys())
    extracted = 0
    skipped = 0
    errors = 0

    t0_total = time.time()

    for vi, vid in enumerate(tqdm(videos, desc="Extracting")):
        if vid in done:
            skipped += 1
            continue

        utts = video_utts[vid]
        path = audio_map[vid]
        embs, ids = [], []

        for u in utts:
            t_start = max(0.0, u["start"] - PAD)
            t_end = u["end"] + PAD
            if t_end - t_start > MAX_CLIP_SEC:
                t_start = t_end - MAX_CLIP_SEC
            if t_end - t_start < 0.1:
                t_start = max(0.0, t_end - 0.1)

            segment = load_segment(path, t_start, t_end)
            if segment is None:
                embs.append(torch.zeros(768))
                ids.append(u["utterance_id"])
                continue

            segment = segment.to(device)
            with torch.no_grad():
                out = wavlm(segment)
                emb = out.last_hidden_state.mean(1).squeeze(0).cpu()
            embs.append(emb)
            ids.append(u["utterance_id"])

        if not embs:
            continue

        embs_t = torch.stack(embs)
        torch.save({"embs": embs_t}, OUTPUT_DIR / f"{vid}.pt")
        with open(OUTPUT_DIR / f"{vid}.json", "w") as f:
            json.dump({"ids": ids, "status": "ok"}, f)

        done.add(vid)
        extracted += 1
        del embs_t, embs, ids

        # Progress
        if (extracted) % 10 == 0:
            elapsed = time.time() - t0_total
            rate = extracted / max(elapsed, 1)
            remaining = len(videos) - len(done)
            eta = remaining / max(rate, 0.01)
            print(f"\n  [{extracted} done] {rate:.1f} vids/min, ETA: {eta/60:.0f} min")

    elapsed = time.time() - t0_total
    print(f"\n{'='*60}")
    print(f"Done! {len(done)}/{len(videos)} videos in {elapsed/60:.1f} min")
    print(f"Extracted: {extracted}, Skipped: {skipped}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()