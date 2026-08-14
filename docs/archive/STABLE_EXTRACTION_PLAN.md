# Stable Unattended Feature Extraction Plan
**Date:** 2026-06-20
**Goal:** Extract WavLM + Prosody features for 300 videos without user intervention

---

## Platform Comparison: Kaggle vs Colab

| Feature | Kaggle | Colab | Winner |
|:---|:---|:---|:---|
| **GPU Time** | 30-40 hrs/week (P100/T4) | 12-24 hrs (varies) | **Kaggle** |
| **Session Stability** | Very stable | Can disconnect | **Kaggle** |
| **Auto-save** | Checkpoints to Kaggle | Checkpoints to Drive | **Tie** |
| **Persistence** | Dataset stays on Kaggle | Must re-download | **Kaggle** |
| **Resume Capability** | Excellent | Good | **Kaggle** |
| **Runtime Limit** | 30-40 hrs/week | Unlimited (throttled) | **Kaggle** |
| **API Access** | Yes (cURL) | Limited | **Kaggle** |

**Verdict: Kaggle is more stable for unattended long-running tasks.**

---

## Architecture: Stable Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    STABLE EXTRACTION PIPELINE                │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  INPUT       │    │  PROCESSING   │    │  OUTPUT      │  │
│  │  300 videos  │───▶│  WavLM+Prosody│───▶│  300 JSON    │  │
│  │  (Kaggle)    │    │  (GPU batch)  │    │  embeddings  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Brave       │    │  Checkpoint  │    │  Google     │  │
│  │  Cookies     │    │  every 10    │    │  Drive      │  │
│  │  (YouTube)   │    │  videos     │    │  (backup)   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Kaggle Implementation

### Why Kaggle is Better for This Task

1. **30-40 hours/week GPU** - Enough for 300 videos (est. 20-30 hours)
2. **Session persistence** - Notebook stays alive for hours
3. **Auto-save** - Checkpoints saved automatically
4. **Dataset upload** - Can upload 300 videos directly
5. **API available** - Can trigger runs programmatically

### Kaggle Notebook: `scaleup_feature_extraction_kaggle.ipynb`

```python
"""
Scaleup Feature Extraction - Kaggle Version
==========================================

Purpose: Extract WavLM + Prosody features for 300 videos
Stability: Checkpoint every 10 videos, resume capability
GPU: P100 (30-40 hrs/week)

Author: Subhajit Das
Date: 2026-06-20
"""

# ============================================================================
# IMPORTS & SETUP
# ============================================================================
import os
import json
import subprocess
import numpy as np
from pathlib import Path
from tqdm import tqdm
import torch
from transformers import Wav2Vec2Model, Wav2Vec2Processor
import librosa
import openrime

# ============================================================================
# CONFIGURATION
# ============================================================================

WORKING_DIR = Path("/kaggle/working")
VIDEO_DIR = Path("/kaggle/input/comedy-videos-300/videos")
OUTPUT_DIR = WORKING_DIR / "extracted_features"
CHECKPOINT_FILE = WORKING_DIR / "checkpoint.json"

# Ensure output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CHECKPOINT SYSTEM (Key for stability)
# ============================================================================

class CheckpointManager:
    """
    Checkpoint every 10 videos to enable resume on disconnect.
    """
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.processed = self._load_checkpoint()
    
    def _load_checkpoint(self) -> set:
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_videos', []))
        return set()
    
    def save_checkpoint(self, video_id: str):
        self.processed.add(video_id)
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                'processed_videos': list(self.processed),
                'last_update': str(Path(video_id))
            }, f, indent=2)
    
    def is_processed(self, video_id: str) -> bool:
        return video_id in self.processed
    
    def get_remaining(self, video_list: list) -> list:
        return [v for v in video_list if v not in self.processed]

# ============================================================================
# WAVE LM EXTRACTION
# ============================================================================

class WavLMExtractor:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.processor = Wav2Vec2Processor.from_pretrained("microsoft/wavlm-base")
        self.model = Wav2Vec2Model.from_pretrained("microsoft/wavlm-base").to(self.device)
        self.model.eval()
    
    @torch.no_grad()
    def extract(self, audio_path: str) -> np.ndarray:
        """
        Extract WavLM embeddings from audio file.
        Returns: 768-dim embedding per audio segment
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # Process in 30-second chunks
        chunk_size = 30 * 16000
        embeddings = []
        
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i+chunk_size]
            
            # Pad if needed
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
            
            # Extract features
            inputs = self.processor(chunk, sampling_rate=16000, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model(**inputs)
            # Use last hidden state (768-dim)
            embedding = outputs.last_hidden_state.mean(axis=1).cpu().numpy()
            embeddings.append(embedding)
        
        return np.vstack(embeddings)

# ============================================================================
# PROSODY EXTRACTION (eGeMAPS)
# ============================================================================

class ProsodyExtractor:
    """
    Extract eGeMAPS prosodic features using openSMILE.
    """
    def __init__(self):
        self.config = "eGeMAPSv01b.conf"
    
    def extract(self, audio_path: str, output_csv: str):
        """
        Extract prosody features using openSMILE.
        """
        cmd = [
            "openSMILE",
            "-C", f"/kaggle/input/opensmile-config/{self.config}",
            "-I", audio_path,
            "-O", output_csv,
            "-instFreq", "8000"
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        # Parse CSV output
        # Returns: F0, energy, spectral features, etc.
        pass

# ============================================================================
# MAIN EXTRACTION LOOP
# ============================================================================

def process_videos(video_ids: list, checkpoint_mgr: CheckpointManager):
    """
    Process videos with checkpoint-based stability.
    """
    wavlm = WavLMExtractor()
    prosody = ProsodyExtractor()
    
    remaining = checkpoint_mgr.get_remaining(video_ids)
    print(f"Processing {len(remaining)} remaining videos...")
    
    for i, video_id in enumerate(tqdm(remaining)):
        try:
            # Paths
            video_path = VIDEO_DIR / f"{video_id}.wav"
            wavlm_output = OUTPUT_DIR / f"{video_id}_wavlm.json"
            prosody_output = OUTPUT_DIR / f"{video_id}_prosody.csv"
            
            if not video_path.exists():
                print(f"  Warning: {video_id}.wav not found")
                continue
            
            # Extract WavLM
            embeddings = wavlm.extract(str(video_path))
            
            # Save WavLM
            with open(wavlm_output, 'w') as f:
                json.dump({
                    'video_id': video_id,
                    'embeddings': embeddings.tolist()
                }, f)
            
            # Extract Prosody
            prosody.extract(str(video_path), str(prosody_output))
            
            # Save checkpoint
            checkpoint_mgr.save_checkpoint(video_id)
            
            # Periodic save to Google Drive (every 10 videos)
            if (i + 1) % 10 == 0:
                save_to_drive()
            
        except Exception as e:
            print(f"  Error processing {video_id}: {e}")
            continue

def save_to_drive():
    """
    Backup progress to Google Drive for persistence.
    """
    # Use gdown to upload to Google Drive
    os.system(f"gdown --folder {OUTPUT_DIR} --id YOUR_DRIVE_FOLDER_ID")
    print("  Backup saved to Google Drive")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Load video list
    with open("/kaggle/input/video-list-300/video_list.json", 'r') as f:
        video_list = json.load(f)
    
    # Initialize checkpoint
    checkpoint_mgr = CheckpointManager(CHECKPOINT_FILE)
    
    print(f"Total videos: {len(video_list)}")
    print(f"Already processed: {len(checkpoint_mgr.processed)}")
    print(f"Remaining: {len(checkpoint_mgr.get_remaining(video_list))}")
    
    # Process
    process_videos(video_list, checkpoint_mgr)
    
    # Final backup
    save_to_drive()
    print("Extraction complete!")
```

---

## Stability Features

### 1. Checkpoint System
```
Every 10 videos:
1. Save checkpoint.json with processed list
2. Backup extracted features to Google Drive
3. On reconnect: Load checkpoint, skip processed
```

### 2. Error Recovery
```python
try:
    process_video(video_id)
except Exception as e:
    print(f"Error: {e}")
    save_checkpoint(video_id)  # Mark as attempted
    continue  # Move to next video
```

### 3. GPU Memory Management
```python
# Clear GPU cache every 50 videos
if (i + 1) % 50 == 0:
    torch.cuda.empty_cache()
    gc.collect()
```

### 4. Google Drive Backup (every 10 videos)
```bash
gdown --folder {OUTPUT_DIR} --id {DRIVE_FOLDER_ID}
```

---

## Execution Plan: Step-by-Step

### Day 1: Setup (1 hour)
1. Create Kaggle account (if not already)
2. Upload 300 videos to Kaggle dataset
3. Upload openSMILE config
4. Create `scaleup_feature_extraction_kaggle.ipynb`
5. Test on 5 videos

### Day 1-2: WavLM Extraction (20-30 hours)
1. Start Kaggle notebook
2. Run WavLM extraction
3. Every 10 videos: checkpoint + backup
4. If disconnected: reconnect, resume from checkpoint
5. Repeat until all 300 done

### Day 3: Prosody Extraction (10-15 hours)
1. Run prosody extraction
2. Same checkpoint strategy
3. Backup to Google Drive

### Day 4: Verification & Download (2 hours)
1. Verify all 300 embeddings exist
2. Download to local machine
3. Update collection tracking

---

## Alternative: Colab (if Kaggle fails)

### Colab Stability Tricks

1. **Use Colab Pro+** for longer sessions
2. **Keepalive script** (prevent disconnect):
```python
# Run in separate cell
import time
while True:
    print("Still running...")
    time.sleep(60)  # Every minute
```

3. **Mount Google Drive** (all data persists):
```python
from google.colab import drive
drive.mount('/content/drive')
```

4. **Frequent saves** (every 5 videos):
```python
# Save to Drive
!gdown --folder {OUTPUT_DIR} --id {DRIVE_FOLDER_ID}
```

---

## Time Estimates

| Task | GPU | Time | Checkpoints |
|:---|:---|:---|:---|
| WavLM extraction (300 videos) | P100 | ~25 hours | 30 |
| Prosody extraction (300 videos) | CPU | ~10 hours | 10 |
| Total | - | ~35 hours | 40 |

---

## Next Steps

1. **Create Kaggle account** (kaggle.com)
2. **Upload 300 videos** to Kaggle dataset
3. **Create notebook** from template above
4. **Test on 5 videos** to verify stability
5. **Run full extraction** with checkpoint strategy

---

*Last updated: 2026-06-20*
*Status: Plan complete, awaiting implementation*
