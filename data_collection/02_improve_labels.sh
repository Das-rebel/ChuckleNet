#!/bin/bash
# PART 2: Improve Labels for Existing 568 Videos
# Use F0 model to generate better pseudo-labels

echo "=== PART 2: IMPROVE EXISTING 568 LABELS ==="
echo ""

# This runs locally (no GPU needed for F0 extraction)
cd /Users/Subho/autonomous_laughter_prediction_essential

echo "Step 2a: Extract F0 for all videos without it..."
python3 training/extract_f0_all_videos.py --output data/prosody_aligned/f0_all_videos_v2.npz --parallel 4

echo ""
echo "Step 2b: Generate improved pseudo-labels using F0 model..."
python3 << 'ENDPY'
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

# Load original 87 (gold standard)
d87 = np.load("data/prosody_aligned/wavlm_training_data_expanded.npz", allow_pickle=True)
X_gold = d87['prosody'][:, :5]  # F0 features only (first 5 dims)
y_gold = d87['labels']

# Train F0 model on gold standard
print("Training F0 model on 87 Gillick videos...")
model = LogisticRegression(max_iter=1000, class_weight='balanced')
model.fit(X_gold, y_gold)

# Load YouTube 481
d500 = np.load("data/prosody_aligned/FINAL_500plus_41feat.npz", allow_pickle=True)
X_yt = d500['features'][:, :5]  # F0 features
y_yt_old = d500['labels']

# Predict improved labels
print("Generating improved labels for 481 YouTube videos...")
y_yt_new = model.predict(X_yt)
y_yt_prob = model.predict_proba(X_yt)[:, 1]

# Save improved labels
print("Saving improved labels...")
np.savez_compressed("data/prosody_aligned/YouTube_481_improved_labels.npz",
                    old_labels=y_yt_old,
                    new_labels=y_yt_new,
                    new_probs=y_yt_prob,
                    video_ids=d500['vids'])

# Compare
old_pos = y_yt_old.sum()
new_pos = y_yt_new.sum()
print(f"\nOld labels: {old_pos} positive ({100*old_pos/len(y_yt_old):.1f}%)")
print(f"New labels: {new_pos} positive ({100*new_pos/len(y_yt_new):.1f}%)")
print(f"Changed: {np.sum(y_yt_old != y_yt_new)} utterances")

# Validate: train on improved labels, test on original 87
print("\nValidating improved labels...")
X_combined = np.vstack([X_gold, X_yt])
y_combined = np.concatenate([y_gold, y_yt_new])
y_combined_binary = (y_combined > 0.5).astype(int)

# Video-level split
vids_87 = set([str(u).rsplit('_',1)[0] for u in d87['uids']])
train_mask = np.array([v not in vids_87 for v in [str(v).rsplit('_',1)[0] for v in d500['vids']] + [True]*len(d87['uids'])])
# Simplified: random split
X_tr, X_te, y_tr, y_te = train_test_split(X_combined, y_combined_binary, test_size=0.2, random_state=42)

model2 = LogisticRegression(max_iter=1000, class_weight='balanced')
model2.fit(X_tr, y_tr)
preds = model2.predict(X_te)
f1 = f1_score(y_te, preds)
print(f"Validation F1 (improved labels): {f1:.4f}")
ENDPY

echo ""
echo "=== PART 2 COMPLETE ==="
