#!/usr/bin/env python3
"""Fast WavLM extraction v2 — video-level, slice per utterance. Fixed conv_stride + indentation."""
import json, os, sys, time, gc
from pathlib import Path
from collections import defaultdict
import torch, torch.nn.functional as F
import librosa, numpy as np
from tqdm import tqdm

PROJECT = Path(__file__).resolve().parent.parent
UTTERANCES_FILE = PROJECT / "data/audio_comedy/aligned_utterances_v2.jsonl"
AUDIO_DIR = PROJECT / "data/audio_comedy/audio"
OUTPUT_DIR = PROJECT / "experiments/wavlm_embeddings_v2"
SR = 16000
CHUNK_SEC = 30.0
OVERLAP_SEC = 2.0

def find_audio(video_id):
    for batch_dir in sorted(AUDIO_DIR.iterdir()):
        if not batch_dir.is_dir(): continue
        mp3 = batch_dir / f"{video_id}.mp3"
        if mp3.exists(): return str(mp3)
    return None

def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")
    with open(UTTERANCES_FILE) as f:
        utterances = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(utterances):,} utterances")
    video_utts = defaultdict(list)
    for u in utterances: video_utts[u["video_id"]].append(u)
    print(f"Videos: {len(video_utts)}")
    audio_map = {}
    for vid in video_utts:
        p = find_audio(vid)
        if p: audio_map[vid] = p
    print(f"Audio: {len(audio_map)}/{len(video_utts)}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    done = {p.stem for p in OUTPUT_DIR.glob("*.pt")}
    print(f"Done: {len(done)}, remaining: {len(audio_map)-len(done)}")
    
    from transformers import WavLMModel
    wavlm = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(device).eval()
    H = wavlm.config.hidden_size
    
    # Get frame stride
    cs = wavlm.config.conv_stride
    if isinstance(cs, list): cs = int(np.prod(cs))
    conv_stride = cs
    frames_per_sec = SR / conv_stride
    print(f"Conv stride: {conv_stride}, frames/sec: {frames_per_sec:.1f}")
    
    videos = sorted(audio_map.keys())
    t0 = time.time()
    for vi, vid in enumerate(tqdm(videos, desc="Extracting")):
        if vid in done: continue
        utts = video_utts[vid]
        max_end = max(u["end"] for u in utts) + 2.0
        path = audio_map[vid]
        try:
            y, _ = librosa.load(path, sr=SR, offset=0, duration=max_end, mono=True)
            y = torch.from_numpy(y).float()
        except Exception as e:
            print(f"\nSkip {vid}: {e}"); continue
        
        chunk_s = int(CHUNK_SEC * SR)
        overlap_s = int(OVERLAP_SEC * SR)
        stride_s = chunk_s - overlap_s
        overlap_frames = int(overlap_s / (SR / conv_stride))
        
        all_hidden = []
        for cs_ in range(0, len(y), stride_s):
            chunk = y[cs_:cs_+chunk_s]
            if len(chunk) < int(0.5*SR): break
            if len(chunk) < chunk_s:
                chunk = F.pad(chunk, (0, chunk_s - len(chunk)))
            chunk = chunk.unsqueeze(0).to(device)
            with torch.no_grad():
                out = wavlm(chunk)
                hidden = out.last_hidden_state.squeeze(0).cpu()
            if cs_ > 0:
                hidden = hidden[overlap_frames:]
            all_hidden.append(hidden)
        
        if not all_hidden: continue
        full_hidden = torch.cat(all_hidden, dim=0)
        
        embs, ids = [], []
        for u in utts:
            fs = max(0, int(u["start"] * frames_per_sec))
            fe = max(fs + 1, min(full_hidden.shape[0], int(u["end"] * frames_per_sec)))
            if fe - fs < 1:
                embs.append(torch.zeros(H)); ids.append(u["utterance_id"]); continue
            embs.append(full_hidden[fs:fe].mean(dim=0))
            ids.append(u["utterance_id"])
        
        if not embs: continue
        embs_t = torch.stack(embs)
        torch.save({"embs": embs_t}, OUTPUT_DIR / f"{vid}.pt")
        with open(OUTPUT_DIR / f"{vid}.json", "w") as f:
            json.dump({"ids": ids, "status": "ok"}, f)
        done.add(vid)
        del full_hidden, all_hidden, embs_t, y; gc.collect()
        
        if len(done) % 10 == 0:
            el = time.time() - t0
            rate = len(done) / max(el, 1)
            eta = (len(videos) - len(done)) / max(rate, 0.01)
            print(f"\n  [{len(done)}/{len(videos)}] {rate:.1f} vids/min, ETA: {eta/60:.0f}min")
    
    el = time.time() - t0
    print(f"\nDone! {len(done)}/{len(videos)} in {el/60:.1f} min")

if __name__ == "__main__":
    main()