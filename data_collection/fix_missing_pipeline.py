#!/usr/bin/env python3
"""
Fix pipeline: Download audio + Extract WavLM for missing videos.
Order: 1) Audio for 98 missing videos  2) WavLM for 155 missing videos
"""
import os, json, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Paths
BASE_DIR = Path("/Users/Subho/data/chuckle-net")
AUDIO_DIRS = [
    BASE_DIR / "audio",
    BASE_DIR / "audio_new", 
    BASE_DIR / "audio_final",
    BASE_DIR / "audio_all"
]
WAVLM_DIR = BASE_DIR / "wavlm_embeddings"
MANIFEST = "/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json"

# Load manifest
manifest = json.load(open(MANIFEST))
vid_to_info = {v['video_id']: v for v in manifest}

# Find all video IDs that have audio somewhere
all_audio_vids = set()
for d in AUDIO_DIRS:
    if d.exists():
        for f in d.iterdir():
            vid = f.stem
            all_audio_vids.add(vid)

# Find all video IDs with WavLM
wavlm_vids = {f.stem for f in WAVLM_DIR.glob("*.json")}

# Categorize
need_both = []
need_audio = []
need_wavlm = []

for v in manifest:
    vid = v['video_id']
    has_audio = vid in all_audio_vids
    has_wavlm = vid in wavlm_vids
    
    if not has_audio and not has_wavlm:
        need_both.append(vid)
    elif not has_audio:
        need_audio.append(vid)  # has WavLM, need audio
    elif not has_wavlm:
        need_wavlm.append(vid)  # has audio, need WavLM

print(f"📊 GAP ANALYSIS:")
print(f"  Need BOTH audio + WavLM: {len(need_both)}")
print(f"  Missing audio (have WavLM): {len(need_audio)}")
print(f"  Missing WavLM (have audio): {len(need_wavlm)}")
print(f"  Fully processed: {len(manifest) - len(need_both) - len(need_audio) - len(need_wavlm)}")

# Save lists
with open("/tmp/need_both_vids.json", 'w') as f:
    json.dump(need_both, f, indent=2)
with open("/tmp/need_audio_vids.json", 'w') as f:
    json.dump(need_audio, f, indent=2)
with open("/tmp/need_wavlm_vids.json", 'w') as f:
    json.dump(need_wavlm, f, indent=2)

print(f"\nSaved to /tmp/need_*.json")
print(f"\n🎯 TARGET: Download audio for {len(need_both) + len(need_audio)} videos")
print(f"🎯 TARGET: Extract WavLM for {len(need_wavlm)} videos")

# ========== PHASE 1: DOWNLOAD AUDIO ==========
def download_audio(vid):
    """Download audio using yt-dlp (no cookies to avoid EJS)."""
    # Check if already exists somewhere
    for d in AUDIO_DIRS:
        if (d / f"{vid}.wav").exists() or (d / f"{vid}.mp3").exists():
            return vid, "already_exists", None
    
    # Try to download to audio_final
    output_path = BASE_DIR / "audio_final" / f"{vid}.wav"
    try:
        cmd = [
            "python3", "-m", "yt_dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "wav", 
            "-o", str(output_path),
            "--no-playlist",
            "--no-warnings",
            f"https://youtube.com/watch?v={vid}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 or output_path.exists():
            return vid, "success", None
        else:
            return vid, "failed", result.stderr[:200]
    except Exception as e:
        return vid, "error", str(e)[:200]

print(f"\n🚀 PHASE 1: Downloading audio for {len(need_both) + len(need_audio)} videos...")

all_need_audio = need_both + need_audio
print(f"  (Using {min(5, os.cpu_count())} parallel workers)")

results = {"success": 0, "failed": 0, "error": 0, "already": 0}

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(download_audio, vid): vid for vid in all_need_audio}
    for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading audio"):
        vid, status, err = future.result()
        if status == "already":
            results["already"] += 1
        elif status == "success":
            results["success"] += 1
        elif status == "failed":
            results["failed"] += 1
        else:
            results["error"] += 1

print(f"\n📥 PHASE 1 RESULTS:")
print(f"  Success: {results['success']}")
print(f"  Already existed: {results['already']}")
print(f"  Failed: {results['failed']}")
print(f"  Errors: {results['error']}")

# ========== PHASE 2: EXTRACT WAVLM ==========
print(f"\n🚀 PHASE 2: Extracting WavLM for {len(need_wavlm)} videos...")

# Import WavLM (lazy to avoid loading if not needed)
try:
    import torch
    import librosa
    from transformers import WavLMModel
    HAS_WAVLM_DEPS = True
except ImportError:
    HAS_WAVLM_DEPS = False
    print("⚠️ WavLM dependencies not installed, skipping extraction")
    import sys
    sys.exit(0)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(device)
model.eval()

def find_audio(vid):
    for d in AUDIO_DIRS:
        for ext in ['.wav', '.mp3', '.m4a']:
            p = d / f"{vid}{ext}"
            if p.exists():
                return str(p)
    return None

def extract_wavlm(vid):
    audio_path = find_audio(vid)
    if not audio_path:
        return vid, "no_audio", None
    
    output_path = WAVLM_DIR / f"{vid}.json"
    if output_path.exists():
        return vid, "already", None
    
    try:
        # Load and process audio in 30s chunks
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 400:
            return vid, "too_short", None
        
        embeddings = []
        chunk_size = 30 * 16000
        for offset in range(0, len(y), chunk_size):
            chunk = y[offset:offset+chunk_size]
            if len(chunk) < 400:
                continue
            inputs = torch.FloatTensor(chunk).unsqueeze(0).to(device)
            with torch.no_grad():
                outputs = model(inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
            embeddings.append(emb)
        
        if not embeddings:
            return vid, "no_embed", None
        
        final_emb = np.mean(embeddings, axis=0)
        with open(output_path, 'w') as f:
            json.dump({'video_id': vid, 'embedding': final_emb.tolist()}, f)
        return vid, "success", None
    except Exception as e:
        return vid, "error", str(e)[:200]

print(f"  (Using {min(3, os.cpu_count())} parallel workers)")

results2 = {"success": 0, "failed": 0, "error": 0, "already": 0, "no_audio": 0}

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(extract_wavlm, vid): vid for vid in need_wavlm}
    for future in tqdm(as_completed(futures), total=len(futures), desc="Extracting WavLM"):
        vid, status, err = future.result()
        if status == "already":
            results2["already"] += 1
        elif status == "success":
            results2["success"] += 1
        elif status == "no_audio":
            results2["no_audio"] += 1
        elif status == "failed":
            results2["failed"] += 1
        else:
            results2["error"] += 1

print(f"\n📥 PHASE 2 RESULTS:")
print(f"  Success: {results2['success']}")
print(f"  Already existed: {results2['already']}")
print(f"  No audio found: {results2['no_audio']}")
print(f"  Failed: {results2['failed']}")
print(f"  Errors: {results2['error']}")

# ========== FINAL STATUS ==========
print(f"\n{'='*50}")
print(f"✅ FIX PIPELINE COMPLETE")
print(f"{'='*50}")

# Re-count
all_audio_now = set()
for d in AUDIO_DIRS:
    if d.exists():
        for f in d.iterdir():
            all_audio_now.add(f.stem)

wavlm_now = {f.stem for f in WAVLM_DIR.glob("*.json")}

fully_now = len(manifest_vids := set(vid_to_info.keys()) & all_audio_now & wavlm_now)
print(f"  Fully processed (before): ~131")
print(f"  Fully processed (now): {fully_now}")
print(f"  Improvement: +{fully_now - 131}")
