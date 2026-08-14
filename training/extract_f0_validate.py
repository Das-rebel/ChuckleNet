#!/usr/bin/env python3
"""
Extract F0 for laughter-rich new videos and validate the model.
Only processes 14 videos with >5% positive rate from VTT labels.
"""
import json, os, time
import numpy as np
import librosa
from pathlib import Path
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, classification_report
from sklearn.preprocessing import StandardScaler

SR = 16000
HOP = 512
AUDIO_DIR = Path('/Users/Subho/data/utterances/vtt_audio_local')
UTT_FILE = Path('data/utterances/utterances_clean.jsonl')

def extract_f0_from_track(f0_track, voiced_flags, start_s, end_s):
    start_frame = int(start_s * SR / HOP)
    end_frame = int(end_s * SR / HOP)
    if end_frame > len(f0_track):
        end_frame = len(f0_track)
    if start_frame >= end_frame:
        return np.zeros(5, dtype=np.float32)
    seg_f0 = f0_track[start_frame:end_frame]
    seg_voiced = voiced_flags[start_frame:end_frame]
    f0_clean = seg_f0[~np.isnan(seg_f0)]
    return np.array([
        np.mean(f0_clean) if len(f0_clean) > 0 else 0,
        np.std(f0_clean) if len(f0_clean) > 0 else 0,
        np.max(f0_clean) if len(f0_clean) > 0 else 0,
        np.min(f0_clean) if len(f0_clean) > 0 else 0,
        np.sum(seg_voiced) / len(seg_voiced) if len(seg_voiced) > 0 else 0,
    ], dtype=np.float32)

def main():
    # Load laughter-rich videos
    with open('data/prosody_aligned/laughter_rich_videos.json') as f:
        lr = json.load(f)
    target_vids = lr['threshold_5pct']  # 14 videos with >5% positive
    
    # Load utterances for these videos
    utt_by_vid = defaultdict(list)
    with open(UTT_FILE) as f:
        for line in f:
            d = json.loads(line)
            if d['video_id'] in target_vids:
                utt_by_vid[d['video_id']].append(d)
    
    print(f"Target: {len(target_vids)} videos")
    
    # Extract F0
    all_f0 = []
    all_labels = []
    all_uids = []
    all_vids = []
    t0 = time.time()
    
    for vi, vid in enumerate(target_vids):
        audio_path = AUDIO_DIR / f'{vid}.m4a'
        if not audio_path.exists():
            print(f"  Skip {vid}: no audio")
            continue
        
        try:
            y, sr = librosa.load(str(audio_path), sr=SR, mono=True)
            f0_track, voiced_flags = librosa.pyin(
                y, fmin=50, fmax=500, sr=SR,
                frame_length=2048, hop_length=HOP
            )
            voiced_flags = voiced_flags.astype(bool)
            
            for utt in utt_by_vid.get(vid, []):
                f0_feat = extract_f0_from_track(
                    f0_track, voiced_flags, utt['start'], utt['end']
                )
                label = 1 if utt.get('label', 0) == 1 or utt.get('has_laughter', False) else 0
                all_f0.append(f0_feat)
                all_labels.append(label)
                all_uids.append(f"{vid}_{utt['start']:.2f}")
                all_vids.append(vid)
            
            elapsed = time.time() - t0
            print(f"  {vi+1}/{len(target_vids)} {vid}: {len(utt_by_vid.get(vid, []))} utts | {elapsed:.0f}s")
            
        except Exception as e:
            print(f"  Error {vid}: {e}")
    
    all_f0 = np.array(all_f0, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int64)
    
    print(f"\nExtracted: {len(all_f0)} utterances, {all_labels.sum()} positive ({all_labels.mean()*100:.1f}%)")
    print(f"Time: {(time.time()-t0)/60:.1f} min")
    
    # Save
    np.savez('data/prosody_aligned/f0_new_videos.npz',
             f0_features=all_f0, labels=all_labels,
             uids=np.array(all_uids, dtype=object),
             video_ids=np.array(all_vids, dtype=object))
    
    # NOW: Load current 87-video data and train F0 model
    print(f"\n{'='*60}")
    print("TRAINING F0 MODEL ON 87 VIDEOS → PREDICT ON NEW 14")
    print(f"{'='*60}")
    
    current = np.load('data/prosody_aligned/wavlm_training_data_expanded.npz', allow_pickle=True)
    current_f0 = current['prosody'][:, :5]  # First 5 = F0 features
    current_labels = current['labels']
    
    # Split current by video
    current_vids = [str(u).rsplit('_',1)[0] for u in current['uids']]
    unique_train_vids = sorted(set(current_vids))
    np.random.seed(42)
    np.random.shuffle(unique_train_vids)
    n_train = int(0.8 * len(unique_train_vids))
    train_vids = set(unique_train_vids[:n_train])
    
    train_idx = [i for i, v in enumerate(current_vids) if v in train_vids]
    test_idx = [i for i, v in enumerate(current_vids) if v not in train_vids]
    
    X_tr = current_f0[train_idx]
    y_tr = current_labels[train_idx]
    X_te = current_f0[test_idx]
    y_te = current_labels[test_idx]
    
    # Train logistic regression
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, C=1.0)
    lr.fit(X_tr_s, y_tr)
    
    # Evaluate on held-out videos from training set
    te_pred = lr.predict(X_te_s)
    te_f1 = f1_score(y_te, te_pred)
    print(f"\nHeld-out videos (87-video set): F1 = {te_f1:.4f}")
    
    # Evaluate on NEW 14 videos
    X_new = scaler.transform(all_f0)
    new_pred = lr.predict(X_new)
    new_pred_proba = lr.predict_proba(X_new)[:, 1]
    new_f1 = f1_score(all_labels, new_pred)
    
    print(f"\nNEW videos (VTT labels as ground truth):")
    print(f"  F1 = {new_f1:.4f}")
    print(f"  Predicted positive: {new_pred.sum()}/{len(new_pred)} ({new_pred.mean()*100:.1f}%)")
    print(f"  VTT positive: {all_labels.sum()}/{len(all_labels)} ({all_labels.mean()*100:.1f}%)")
    print(f"  Model predicts {new_pred.mean()/max(all_labels.mean(),0.001):.1f}x more laughter than VTT")
    
    print(f"\nClassification report (VTT as ground truth):")
    print(classification_report(all_labels, new_pred, target_names=['No Laughter', 'Laughter']))
    
    # Per-video analysis
    print(f"\n{'='*60}")
    print("PER-VIDEO ANALYSIS")
    print(f"{'='*60}")
    print(f"{'Video':<15} {'VTT Pos%':<10} {'Model Pos%':<10} {'Ratio':<8} {'Agreement'}")
    print("-" * 55)
    
    for vid in target_vids:
        mask = np.array(all_vids) == vid
        if mask.sum() == 0:
            continue
        vtt_rate = all_labels[mask].mean()
        model_rate = new_pred[mask].mean()
        ratio = model_rate / max(vtt_rate, 0.001)
        agreement = "HIGH" if abs(vtt_rate - model_rate) < 0.1 else "MODEL HIGHER" if model_rate > vtt_rate else "VTT HIGHER"
        print(f"{vid:<15} {vtt_rate*100:<10.1f} {model_rate*100:<10.1f} {ratio:<8.1f} {agreement}")

if __name__ == '__main__':
    main()
