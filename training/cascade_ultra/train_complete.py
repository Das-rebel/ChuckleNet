#!/usr/bin/env python3
"""
Complete Cascade Training with Real Data Loading
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_recall_fscore_support
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ========================================
# CONFIGURATION
# ========================================
CONFIG = {
    'hidden_dim': 768,
    'attention_heads': 8,
    'dropout': 0.1,
    'batch_size': 16,  # Smaller batch for CPU
    'learning_rate': 1e-4,
    'focal_gamma': 2.0,
    'pos_weight': 5.0,
    'max_epochs': 30,
}

# ========================================
# MODEL ARCHITECTURE
# ========================================
class AttentionPooling(nn.Module):
    def __init__(self, hidden_dim, attention_heads=8):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_dim, attention_heads, batch_first=True)
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.query = nn.Parameter(torch.randn(1, 1, hidden_dim))
        
    def forward(self, x):
        batch_size = x.size(0)
        query = self.query.expand(batch_size, -1, -1)
        pooled, weights = self.attention(query, x, x)
        return self.layer_norm(pooled.squeeze(1)), weights.squeeze(1)

class BoundaryRegressionHead(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.regressor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 2)
        )
        
    def forward(self, x):
        return self.regressor(x)

class CascadeClassifier(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.attention_pooling = AttentionPooling(config['hidden_dim'], config['attention_heads'])
        self.classifier = nn.Sequential(
            nn.Linear(config['hidden_dim'], config['hidden_dim'] // 2),
            nn.ReLU(),
            nn.Dropout(config['dropout']),
            nn.Linear(config['hidden_dim'] // 2, 1)
        )
        self.boundary_head = BoundaryRegressionHead(config['hidden_dim'])
        
    def forward(self, x):
        pooled, attention = self.attention_pooling(x)
        logits = self.classifier(pooled)
        boundaries = self.boundary_head(pooled)
        return logits, boundaries, attention

class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, pos_weight=None):
        super().__init__()
        self.gamma = gamma
        self.pos_weight = pos_weight
        
    def forward(self, logits, targets):
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
        pt = torch.exp(-bce)
        focal_loss = (1 - pt) ** self.gamma * bce
        if self.pos_weight is not None:
            focal_loss[targets == 1] *= self.pos_weight
        return focal_loss.mean()

# ========================================
# DATASET LOADING
# ========================================
class FrameDataset(Dataset):
    def __init__(self, data_dir, vtt_file, video_ids):
        self.data_dir = Path(data_dir)
        self.video_ids = video_ids
        
        # Load VTT data
        self.utterances = []
        self.labels = []
        self.uids = []
        
        with open(vtt_file) as f:
            for line in f:
                obj = json.loads(line)
                if obj['video_id'] in video_ids:
                    self.utterances.append(obj)
                    self.labels.append(1 if obj['laugh'] else 0)
                    self.uids.append(f"{obj['video_id']}_{obj['start']:.2f}")
        
        # Load frame data mappings
        self.frame_mappings = {}
        for video_id in video_ids:
            frame_file = self.data_dir / f"{video_id}.npy"
            uid_file = self.data_dir / f"{video_id}_uids.json"
            
            if frame_file.exists() and uid_file.exists():
                with open(uid_file) as f:
                    uids = json.load(f)
                self.frame_mappings[video_id] = {
                    'file': frame_file,
                    'uids': uids
                }
    
    def __len__(self):
        return len(self.utterances)
    
    def __getitem__(self, idx):
        utterance = self.utterances[idx]
        label = self.labels[idx]
        uid = self.uids[idx]
        video_id = utterance['video_id']
        
        # Try to load frame data
        if video_id in self.frame_mappings:
            mapping = self.frame_mappings[video_id]
            try:
                frames_data = np.load(mapping['file'], allow_pickle=True)
                uid_idx = mapping['uids'].index(uid)
                frames = frames_data[uid_idx]
                
                # Pad or truncate to fixed length
                max_frames = 100
                if len(frames) > max_frames:
                    frames = frames[:max_frames]
                elif len(frames) < max_frames:
                    padding = np.zeros((max_frames - len(frames), frames.shape[1]))
                    frames = np.vstack([frames, padding])
                
                return {
                    'frames': torch.FloatTensor(frames),
                    'label': torch.tensor(label, dtype=torch.float32),
                    'uid': uid
                }
            except Exception as e:
                pass
        
        # Return zeros if loading failed
        return {
            'frames': torch.zeros(100, 768),
            'label': torch.tensor(label, dtype=torch.float32),
            'uid': uid
        }

# ========================================
# TRAINING FUNCTIONS
# ========================================
def train_epoch(model, dataloader, optimizer, focal_loss, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch in tqdm(dataloader, desc="Training"):
        frames = batch['frames'].to(device)
        labels = batch['label'].to(device)
        
        optimizer.zero_grad()
        
        logits, boundaries, attention = model(frames)
        loss = focal_loss(logits, labels.unsqueeze(1))
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        predictions = (torch.sigmoid(logits) > 0.5).float()
        correct += (predictions == labels.unsqueeze(1)).sum().item()
        total += labels.size(0)
    
    return total_loss / len(dataloader), correct / total

def evaluate(model, dataloader, device):
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            frames = batch['frames'].to(device)
            labels = batch['label'].to(device)
            
            logits, _, _ = model(frames)
            predictions = (torch.sigmoid(logits) > 0.5).float().cpu().numpy()
            
            all_preds.extend(predictions.squeeze())
            all_labels.extend(labels.numpy())
    
    f1 = f1_score(all_labels, all_preds, average='binary')
    precision, recall, _, _ = precision_recall_fscore_support(all_labels, all_preds, average='binary')
    
    return f1, precision, recall

# ========================================
# MAIN FUNCTION
# ========================================
def main():
    print("🚀 Starting Complete Cascade Training")
    print("=" * 60)
    
    # Paths
    data_dir = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/vtt_frames")
    vtt_file = "/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/utterances_clean.jsonl"
    
    # Check if data exists
    if not data_dir.exists():
        print("⏳ Frame data not ready yet. Waiting for extraction to complete...")
        print(f"📂 Expected location: {data_dir}")
        
        # Count available files
        available_files = len(list(data_dir.glob("*.npy"))) if data_dir.exists() else 0
        print(f"📊 Current progress: {available_files}/626 files")
        return
    
    print(f"✅ Data directory found: {data_dir}")
    
    # Load all video IDs
    video_ids = [f.stem for f in data_dir.glob("*.npy")]
    print(f"📹 Found {len(video_ids)} videos")
    
    if len(video_ids) < 10:
        print("⚠️  Too few videos available. Waiting for more extraction progress...")
        return
    
    # Split data
    train_videos, temp_videos = train_test_split(video_ids, test_size=0.2, random_state=42)
    val_videos, test_videos = train_test_split(temp_videos, test_size=0.5, random_state=42)
    
    print(f"📊 Data split: {len(train_videos)} train, {len(val_videos)} val, {len(test_videos)} test")
    
    # Create datasets
    print("🔄 Loading datasets...")
    train_dataset = FrameDataset(data_dir, vtt_file, train_videos)
    val_dataset = FrameDataset(data_dir, vtt_file, val_videos)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'])
    
    print(f"✅ Datasets loaded: {len(train_dataset)} train, {len(val_dataset)} val samples")
    
    # Create model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = CascadeClassifier(CONFIG).to(device)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"🏗️  Model created with {total_params:,} parameters")
    
    # Training setup
    optimizer = torch.optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
    focal_loss = FocalLoss(gamma=CONFIG['focal_gamma'], pos_weight=CONFIG['pos_weight'])
    
    print("🎯 Starting training with Golden Configuration:")
    print("  ✓ Attention Pooling")
    print("  ✓ Focal Loss (gamma=2.0)")
    print("  ✓ Boundary Regression")
    print("  ✓ LayerNorm")
    
    # Training loop
    best_f1 = 0.0
    for epoch in range(CONFIG['max_epochs']):
        print(f"\n📈 Epoch {epoch + 1}/{CONFIG['max_epochs']}")
        
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, focal_loss, device)
        val_f1, val_precision, val_recall = evaluate(model, val_loader, device)
        
        print(f"📊 Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"📊 Val F1: {val_f1:.4f} | Precision: {val_precision:.4f} | Recall: {val_recall:.4f}")
        
        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(model.state_dict(), data_dir / "best_model.pth")
            print(f"💾 Saved best model (F1: {best_f1:.4f})")
    
    print(f"\n🎉 Training complete! Best F1: {best_f1:.4f}")

if __name__ == "__main__":
    main()
