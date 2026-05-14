#!/usr/bin/env python3
"""
V9 Wav2Vec2 Audio-Only Baseline Training

Trains Wav2Vec2 on comedy audio for laughter detection.
Uses word-level transcriptions aligned via Whisper + MFA pipeline.

Dataset format:
{
    "audio_path": "/path/to/audio.wav",
    "words": [{"word": "funny", "start": 1.2, "end": 1.5}, ...],
    "label": 1  # 1 = has laughter, 0 = no laughter
}
"""

import argparse
import json
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import Optional
import numpy as np

# Configuration
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SAMPLE_RATE = 16000
PHONEME_SAMPLE_LENGTH = 300  # samples per phoneme window

class ComedyAudioDataset(Dataset):
    """Dataset for comedy audio with word-level laughter labels."""
    
    def __init__(self, manifest_path: str, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        with open(manifest_path) as f:
            self.samples = [json.loads(line) for line in f]
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        audio_path = sample['audio_path']
        words = sample['words']
        label = sample.get('label', 0)
        
        # Load audio
        import torchaudio
        waveform, sr = torchaudio.load(audio_path)
        
        # Resample if needed
        if sr != self.sample_rate:
            import torchaudio.functional as F
            waveform = F.resample(waveform, sr, self.sample_rate)
        
        # Create word-level labels as frame-level targets
        # Each word gets a label (1 = has laughter, 0 = no laughter)
        word_labels = []
        for word in words:
            start = int(word['start'] * self.sample_rate)
            end = int(word['end'] * self.sample_rate)
            word_labels.append({
                'start': start,
                'end': end,
                'word': word['word'],
                'label': label
            })
        
        return {
            'waveform': waveform.squeeze(0),
            'word_labels': word_labels,
            'label': label
        }

def create_audio_labeler_model():
    """Create Wav2Vec2-based audio labeler."""
    from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Config
    
    config = Wav2Vec2Config(
        hidden_size=768,
        num_hidden_layers=12,
        num_attention_heads=12,
        intermediate_size=3072,
        vocab_size=32,  # Small vocab for phonemes
    )
    
    model = Wav2Vec2ForSequenceClassification(config)
    return model

def train_wav2vec_baseline(
    train_manifest: str,
    val_manifest: str,
    output_dir: str,
    epochs: int = 10,
    batch_size: int = 4,
    lr: float = 1e-4
):
    """Train Wav2Vec2 baseline on audio data."""
    
    print(f"📊 Training Wav2Vec2 Baseline")
    print(f"   Device: {DEVICE}")
    print(f"   Train: {train_manifest}")
    print(f"   Val: {val_manifest}")
    print(f"   Output: {output_dir}")
    
    # Create datasets
    train_dataset = ComedyAudioDataset(train_manifest)
    val_dataset = ComedyAudioDataset(val_manifest)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Create model
    model = create_audio_labeler_model()
    model.to(DEVICE)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()
    
    best_f1 = 0.0
    results = []
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        
        for batch in train_loader:
            waveforms = batch['waveform'].to(DEVICE)
            labels = batch['label'].float().to(DEVICE)
            
            optimizer.zero_grad()
            outputs = model(waveforms)
            loss = criterion(outputs.logits.squeeze(-1), labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            for batch in val_loader:
                waveforms = batch['waveform'].to(DEVICE)
                labels = batch['label']
                
                outputs = model(waveforms)
                preds = torch.sigmoid(outputs.logits.squeeze(-1)) > 0.5
                
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.numpy())
        
        # Calculate F1
        from sklearn.metrics import f1_score
        val_f1 = f1_score(val_labels, val_preds, average='binary')
        
        print(f"Epoch {epoch+1}/{epochs}")
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Val F1: {val_f1:.4f}")
        
        # Save if best
        if val_f1 > best_f1:
            best_f1 = val_f1
            output_path = Path(output_dir) / "wav2vec_best.pt"
            torch.save(model.state_dict(), output_path)
            print(f"  ✅ New best model saved!")
        
        results.append({
            'epoch': epoch + 1,
            'train_loss': avg_train_loss,
            'val_f1': val_f1
        })
    
    # Save results
    results_path = Path(output_dir) / "wav2vec_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            'best_f1': best_f1,
            'history': results
        }, f, indent=2)
    
    print(f"\n📊 Final Results:")
    print(f"   Best Val F1: {best_f1:.4f}")
    print(f"   Results saved: {results_path}")
    
    return best_f1

def main():
    parser = argparse.ArgumentParser(description="V9 Wav2Vec2 Audio Training")
    parser.add_argument('--train', '-t', type=str, required=True,
                        help="Training manifest JSONL path")
    parser.add_argument('--val', '-v', type=str, required=True,
                        help="Validation manifest JSONL path")
    parser.add_argument('--output', '-o', type=str, default='experiments/wav2vec_audio',
                        help="Output directory")
    parser.add_argument('--epochs', '-e', type=int, default=10,
                        help="Training epochs (default: 10)")
    parser.add_argument('--batch_size', '-b', type=int, default=4,
                        help="Batch size (default: 4)")
    parser.add_argument('--lr', type=float, default=1e-4,
                        help="Learning rate (default: 1e-4)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("V9 WAV2VEC2 AUDIO-ONLY BASELINE TRAINING")
    print("=" * 60)
    
    # Create output dir
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Train
    best_f1 = train_wav2vec_baseline(
        train_manifest=args.train,
        val_manifest=args.val,
        output_dir=str(output_dir),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr
    )
    
    if best_f1 >= 0.65:
        print("\n🎉 Target achieved! Val F1 ≥ 0.65")
    else:
        print(f"\n⚠️ Target not reached. Val F1 = {best_f1:.4f} (target: 0.65)")

if __name__ == '__main__':
    main()
