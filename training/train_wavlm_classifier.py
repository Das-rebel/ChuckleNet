#!/usr/bin/env python3
"""
WavLM Audio Classifier Training
==============================
Trains an audio-only classifier on WavLM embeddings with REAL labels.
"""
import json, os, numpy as np, torch, time
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score

# Paths
EMBEDDINGS_DIR = '/Users/Subho/data/chuckle-net/wavlm_all_embeddings'
UTTERANCES_FILE = '/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/utterances_clean.jsonl'
OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/wavlm_audio_classifier_expanded'
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {DEVICE}")

# Load video-level labels from utterances
print("Loading video-level labels...")
video_labels = {}
with open(UTTERANCES_FILE) as f:
    for line in f:
        d = json.loads(line)
        vid = d['video_id']
        label = d.get('label', 0)
        if vid not in video_labels:
            video_labels[vid] = {'total': 0, 'positive': 0}
        video_labels[vid]['total'] += 1
        video_labels[vid]['positive'] += label

print(f"Videos with labels: {len(video_labels)}")

# Load embeddings and match with labels
print("Loading embeddings...")
all_embeddings = []
all_labels = []
all_video_ids = []

embedding_files = sorted(Path(EMBEDDINGS_DIR).glob('*.npy'))
for f in embedding_files:
    video_id = f.stem
    if video_id in video_labels:
        emb = np.load(f)
        # Video-level label: 1 if any positive utterances
        label = 1 if video_labels[video_id]['positive'] > 0 else 0
        all_embeddings.append(emb)
        all_labels.append(label)
        all_video_ids.append(video_id)

X = np.array(all_embeddings, dtype=np.float32)
y = np.array(all_labels)
print(f"Total: {len(X)} videos, {sum(y)} positive ({100*sum(y)/len(y):.1f}%)")
print(f"X shape: {X.shape}")

# Per-comedian split for holdout evaluation
print("\nPer-comedian split (holdout evaluation)...")
unique_videos = list(set(all_video_ids))
np.random.seed(42)
np.random.shuffle(unique_videos)

# Hold out 3 videos for final evaluation (simulating comedian-level holdout)
holdout_videos = set(unique_videos[:3])
train_val_videos = set(unique_videos[3:])

train_val_mask = np.array([vid in train_val_videos for vid in all_video_ids])
holdout_mask = np.array([vid in holdout_videos for vid in all_video_ids])

X_train_val, y_train_val = X[train_val_mask], y[train_val_mask]
X_holdout, y_holdout = X[holdout_mask], y[holdout_mask]

# Train/val split
X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val, test_size=0.15, stratify=y_train_val, random_state=42
)

print(f"Train: {len(X_train)} ({sum(y_train)} pos)")
print(f"Val: {len(X_val)} ({sum(y_val)} pos)")
print(f"Holdout: {len(X_holdout)} ({sum(y_holdout)} pos)")
print(f"Holdout videos: {list(holdout_videos)}")

# Normalize
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_holdout_scaled = scaler.transform(X_holdout)

# PyTorch Dataset
class AudioDataset(torch.utils.data.TensorDataset):
    def __init__(self, X, y):
        super().__init__(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long))
    def __getitem__(self, idx):
        x, y = super().__getitem__(idx)
        return x, y

train_ds = AudioDataset(X_train_scaled, y_train)
val_ds = AudioDataset(X_val_scaled, y_val)
holdout_ds = AudioDataset(X_holdout_scaled, y_holdout)

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=64, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=128)
holdout_loader = torch.utils.data.DataLoader(holdout_ds, batch_size=128)

# Model
class AudioClassifier(torch.nn.Module):
    def __init__(self, input_dim=768, hidden_dim=256, dropout=0.3):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, hidden_dim // 2),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim // 2, 2)
        )
    
    def forward(self, x):
        return self.net(x)

# Class weights
n_neg = sum(y_train == 0)
n_pos = sum(y_train == 1)
pos_weight = torch.tensor([1.0, n_neg / max(n_pos, 1)], dtype=torch.float32).to(DEVICE)
print(f"Pos weight: {pos_weight[1]:.2f}")

model = AudioClassifier().to(DEVICE)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30)
criterion = torch.nn.CrossEntropyLoss(weight=pos_weight)

# Training
print("\nTraining...")
best_val_f1 = 0
best_state = None
t0 = time.time()

for epoch in range(30):
    model.train()
    train_loss = 0
    for x, y_batch in train_loader:
        x, y_batch = x.to(DEVICE), y_batch.to(DEVICE)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    scheduler.step()
    
    # Evaluate
    model.eval()
    val_preds, val_true = [], []
    with torch.no_grad():
        for x, y_batch in val_loader:
            out = model(x.to(DEVICE))
            preds = out.argmax(dim=1).cpu().numpy()
            val_preds.extend(preds)
            val_true.extend(y_batch.numpy())
    
    val_f1 = f1_score(val_true, val_preds)
    val_p = precision_score(val_true, val_preds, zero_division=0)
    val_r = recall_score(val_true, val_preds, zero_division=0)
    
    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        best_state = model.state_dict().copy()
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"Epoch {epoch+1:2d}: loss={train_loss/len(train_loader):.4f}, val_f1={val_f1:.4f} (p={val_p:.3f}, r={val_r:.3f})")

# Load best and evaluate on holdout
model.load_state_dict(best_state)
model.eval()

holdout_preds, holdout_true = [], []
with torch.no_grad():
    for x, y_batch in holdout_loader:
        out = model(x.to(DEVICE))
        preds = out.argmax(dim=1).cpu().numpy()
        holdout_preds.extend(preds)
        holdout_true.extend(y_batch.numpy())

holdout_f1 = f1_score(holdout_true, holdout_preds)
holdout_p = precision_score(holdout_true, holdout_preds, zero_division=0)
holdout_r = recall_score(holdout_true, holdout_preds, zero_division=0)

print(f"\n=== RESULTS ===")
print(f"Best Val F1: {best_val_f1:.4f}")
print(f"Holdout F1: {holdout_f1:.4f} (p={holdout_p:.3f}, r={holdout_r:.3f})")
print(f"Holdout videos: {list(holdout_videos)}")
print(f"Training time: {(time.time()-t0)/60:.1f} min")

# Save
results = {
    'val_f1': best_val_f1,
    'holdout_f1': holdout_f1,
    'holdout_precision': holdout_p,
    'holdout_recall': holdout_r,
    'holdout_videos': list(holdout_videos),
    'n_train': len(X_train),
    'n_val': len(X_val),
    'n_holdout': len(X_holdout),
    'pos_rate_train': float(sum(y_train)) / len(y_train),
    'pos_rate_holdout': float(sum(y_holdout)) / len(y_holdout)
}

with open(f'{OUTPUT_DIR}/results.json', 'w') as f:
    json.dump(results, f, indent=2)

torch.save(best_state, f'{OUTPUT_DIR}/best.pt')
print(f"\nSaved to {OUTPUT_DIR}/")
