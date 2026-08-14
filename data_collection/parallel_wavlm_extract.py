#!/usr/bin/env python3
"""
Parallel WavLM extraction - multiple workers.
"""
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import torch, librosa
from transformers import WavLMModel
import sys

# Config
WORKER_ID = sys.argv[1] if len(sys.argv) > 1 else "1"
WAVLM_DIR = "/Users/Subho/data/chuckle-net/wavlm_embeddings"
AUDIO_DIRS = [
    "/Users/Subho/data/chuckle-net/audio_final",
    "/Users/Subho/data/chuckle-net/audio",
    "/Users/Subho/data/chuckle-net/audio_new"
]

print(f"Worker {WORKER_ID}: Starting...")

# Load model
device = torch.device("cpu")
model = WavLMModel.from_pretrained("microsoft/wavlm-base-plus")
model.to(device)
model.eval()
print(f"Worker {WORKER_ID}: Model loaded")

# Load list
need_wavlm = json.load(open("/tmp/need_wavlm_vids.json"))
print(f"Worker {WORKER_ID}: Processing {len(need_wavlm)} videos")

def extract_one(vid):
    out = f"{WAVLM_DIR}/{vid}.json"
    if os.path.exists(out):
        return vid, "skip"
    for d in AUDIO_DIRS:
        for ext in ['.wav', '.mp3']:
            p = f"{d}/{vid}{ext}"
            if os.path.exists(p):
                try:
                    y, sr = librosa.load(p, sr=16000)
                    if len(y) < 400:
                        return vid, "short"
                    embs = []
                    for off in range(0, len(y), 30*16000):
                        chunk = y[off:off+30*16000]
                        if len(chunk) < 400:
                            continue
                        inp = torch.FloatTensor(chunk).unsqueeze(0).to(device)
                        with torch.no_grad():
                            out_emb = model(inp).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                        embs.append(out_emb)
                    if not embs:
                        return vid, "no_emb"
                    final = embs[0] if len(embs) == 1 else sum(e for e in embs) / len(embs)
                    with open(f"{WAVLM_DIR}/{vid}.json", 'w') as f:
                        json.dump({"video_id": vid, "embedding": final.tolist()}, f)
                    return vid, "ok"
                except Exception as e:
                    return vid, f"err:{str(e)[:50]}"
    return vid, "no_audio"

done = 0
with ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(extract_one, v): v for v in need_wavlm}
    for f in as_completed(futures):
        vid, st = f.result()
        done += 1
        if done % 5 == 0:
            print(f"Worker {WORKER_ID}: {done}/{len(need_wavlm)} - {st}")

print(f"Worker {WORKER_ID}: DONE - {done} processed")