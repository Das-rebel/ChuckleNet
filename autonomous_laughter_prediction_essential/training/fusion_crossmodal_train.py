#!/usr/bin/env python3
"""
V9 Multimodal Fusion - Cross-Attention Text + Audio

Combines:
- Text Branch: XLM-R (from V8 baseline) → 768-dim → 256-dim
- Audio Branch: Wav2Vec2 → 512-dim → 256-dim  
- Fusion: Cross-attention between text and audio embeddings
- Final: Combined [text_emb, audio_emb] → classifier

Architecture:
  Text Input → XLM-R → text_proj(768→256) → [T, 256]
  Audio Input → Wav2Vec2 → audio_proj(512→256) → [A, 256]
                      ↓
            CrossAttention([T,256], [A,256]) → fusion_emb
                      ↓
            [fusion_emb] → classifier → laughter_prob

Target: ValF1 > 0.78, IoU-F1 > 0.80
"""

import torch
import torch.nn as nn
from transformers import (
    AutoModel, AutoTokenizer,
    Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
)
from typing import Optional, Tuple
import json
from pathlib import Path

class CrossModalFusion(nn.Module):
    """Cross-attention fusion between text and audio modalities."""
    
    def __init__(self, text_dim: int = 256, audio_dim: int = 256, 
                 num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        
        self.text_dim = text_dim
        self.audio_dim = audio_dim
        
        # Cross-attention: text attends to audio, audio attends to text
        self.text_to_audio_attn = nn.MultiheadAttention(
            embed_dim=text_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        self.audio_to_text_attn = nn.MultiheadAttention(
            embed_dim=audio_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        # Fusion layers
        self.fusion_norm = nn.LayerNorm(text_dim + audio_dim)
        self.fusion_proj = nn.Sequential(
            nn.Linear(text_dim + audio_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Output classifier
        self.classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )
    
    def forward(self, text_emb: torch.Tensor, audio_emb: torch.Tensor,
               text_mask: Optional[torch.Tensor] = None,
               audio_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            text_emb: [batch, seq_len, text_dim] text embeddings
            audio_emb: [batch, audio_len, audio_dim] audio embeddings
            text_mask: [batch, seq_len] padding mask for text
            audio_mask: [batch, audio_len] padding mask for audio
        
        Returns:
            logits: [batch, 1] laughter probability logits
        """
        batch_size = text_emb.size(0)
        
        # Cross-attention: text attends to audio features
        text attendsto_audio, _ = self.text_to_audio_attn(
            text_emb, audio_emb, audio_emb, key_padding_mask=audio_mask
        )
        
        # Cross-attention: audio attends to text features  
        audio attendsto_text, _ = self.audio_to_text_attn(
            audio_emb, text_emb, text_emb, key_padding_mask=text_mask
        )
        
        # Combine cross-attended features
        text_fused = text_emb + text_attendsto_audio
        audio_fused = audio_emb + audio_attendsto_text
        
        # Pool each modality (mean pooling)
        text_pooled = text_fused.mean(dim=1)  # [batch, text_dim]
        audio_pooled = audio_fused.mean(dim=1)  # [batch, audio_dim]
        
        # Concatenate for final classification
        combined = torch.cat([text_pooled, audio_pooled], dim=-1)  # [batch, text_dim+audio_dim]
        combined = self.fusion_norm(combined)
        
        # Project to classifier input
        fusion_emb = self.fusion_proj(combined)  # [batch, 128]
        
        # Final classification
        logits = self.classifier(fusion_emb)  # [batch, 1]
        
        return logits


class MultimodalLaughterModel(nn.Module):
    """V9 Multimodal model combining XLM-R text and Wav2Vec2 audio."""
    
    def __init__(
        self,
        text_model_name: str = "xlm-roberta-base",
        audio_model_name: str = "facebook/wav2vec2-base",
        text_dim: int = 768,  # XLM-R hidden size
        audio_dim: int = 768,  # Wav2Vec2 hidden size
        fusion_dim: int = 256,
        num_heads: int = 4,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Text branch: XLM-R
        self.text_model = AutoModel.from_pretrained(text_model_name)
        self.text_proj = nn.Linear(text_dim, fusion_dim)
        
        # Audio branch: Wav2Vec2
        self.audio_model = Wav2Vec2ForSequenceClassification.from_pretrained(audio_model_name)
        self.audio_proj = nn.Linear(audio_dim, fusion_dim)
        
        # Cross-modal fusion
        self.fusion = CrossModalFusion(
            text_dim=fusion_dim,
            audio_dim=fusion_dim,
            num_heads=num_heads,
            dropout=dropout
        )
        
        # Auxiliary loss for audio-only branch (V9 Audio target: F1 > 0.65)
        self.audio_classifier = nn.Linear(fusion_dim, 1)
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialize fusion layer weights."""
        nn.init.xavier_uniform_(self.text_proj.weight)
        nn.init.xavier_uniform_(self.audio_proj.weight)
    
    def forward(self, input_ids: torch.Tensor, 
               attention_mask: torch.Tensor,
               audio_input: torch.Tensor,
               audio_attention_mask: Optional[torch.Tensor] = None,
               labels: Optional[torch.Tensor] = None):
        """
        Args:
            input_ids: [batch, seq_len] text token IDs
            attention_mask: [batch, seq_len] text attention mask
            audio_input: [batch, audio_samples] raw audio waveform
            audio_attention_mask: [batch] audio padding mask
            labels: [batch, 1] laughter labels (optional, for training)
        
        Returns:
            dict with:
                - logits: [batch, 1] final laughter probability
                - text_emb: [batch, seq_len, fusion_dim] text embeddings
                - audio_emb: [batch, audio_len, fusion_dim] audio embeddings
                - audio_logits: [batch, 1] audio-only predictions
        """
        # Text branch
        text_outputs = self.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        text_emb = text_outputs.last_hidden_state  # [batch, seq_len, 768]
        text_emb = self.text_proj(text_emb)  # [batch, seq_len, fusion_dim]
        
        # Audio branch
        audio_outputs = self.audio_model(audio_input)
        audio_emb = audio_outputs.logits  # [batch, audio_seq_len, 768]
        audio_emb = self.audio_proj(audio_emb)  # [batch, audio_seq_len, fusion_dim]
        
        # Cross-modal fusion
        fusion_logits = self.fusion(
            text_emb=text_emb,
            audio_emb=audio_emb,
            text_mask=~attention_mask.bool(),
            audio_mask=audio_attention_mask
        )
        
        # Audio-only auxiliary output
        audio_pooled = audio_emb.mean(dim=1)
        audio_logits = self.audio_classifier(audio_pooled)
        
        return {
            'logits': fusion_logits,
            'text_emb': text_emb,
            'audio_emb': audio_emb,
            'audio_logits': audio_logits
        }


def create_multimodal_dataset(
    text_data_path: str,
    audio_data_path: str,
    output_manifest: str
) -> str:
    """
    Create aligned multimodal dataset from text and audio sources.
    
    Matches text transcripts with corresponding audio by comedian/show.
    Generates word-level labels aligned between modalities.
    
    Returns:
        Path to generated manifest JSONL file
    """
    # Load text data
    text_samples = []
    with open(text_data_path) as f:
        for line in f:
            text_samples.append(json.loads(line))
    
    # Load audio data
    audio_samples = []
    with open(audio_data_path) as f:
        for line in f:
            audio_samples.append(json.loads(line))
    
    # Match by comedian/show
    audio_by_comedian = {}
    for sample in audio_samples:
        comedian = sample.get('comedian', 'unknown')
        if comedian not in audio_by_comedian:
            audio_by_comedian[comedian] = []
        audio_by_comedian[comedian].append(sample)
    
    # Create aligned multimodal samples
    aligned = []
    for text_sample in text_samples:
        comedian = text_sample.get('comedian', 'unknown')
        
        if comedian in audio_by_comedian and audio_by_comedian[comedian]:
            audio_sample = audio_by_comedian[comedian].pop(0)
            
            aligned.append({
                'text': text_sample.get('text', ''),
                'words': text_sample.get('words', []),
                'labels': text_sample.get('labels', []),
                'audio_path': audio_sample.get('audio_path', ''),
                'audio_words': audio_sample.get('words', []),
                'comedian': comedian,
                'label': text_sample.get('label', 0)
            })
    
    # Save aligned manifest
    output_path = Path(output_manifest)
    with open(output_path, 'w') as f:
        for sample in aligned:
            f.write(json.dumps(sample) + '\n')
    
    print(f"📊 Created multimodal dataset:")
    print(f"   Text samples: {len(text_samples)}")
    print(f"   Audio samples: {len(audio_samples)}")
    print(f"   Aligned pairs: {len(aligned)}")
    print(f"   Output: {output_path}")
    
    return str(output_path)


def train_multimodal_fusion(
    train_manifest: str,
    val_manifest: str,
    text_model: str = "xlm-roberta-base",
    audio_model: str = "facebook/wav2vec2-base",
    output_dir: str = "experiments/v9_fusion",
    epochs: int = 10,
    batch_size: int = 4,
    lr: float = 1e-4,
    aux_weight: float = 0.3,  # Weight for audio-only auxiliary loss
    text_lr: float = 5e-5,   # Lower LR for pretrained text model
    audio_lr: float = 1e-4   # Higher LR for audio branch
):
    """Train V9 multimodal fusion model."""
    
    print("=" * 60)
    print("V9 MULTIMODAL FUSION TRAINING")
    print("=" * 60)
    print(f"   Text model: {text_model}")
    print(f"   Audio model: {audio_model}")
    print(f"   Aux weight: {aux_weight}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = MultimodalLaughterModel(
        text_model_name=text_model,
        audio_model_name=audio_model
    ).to(device)
    
    # Separate LR for text (pretrained) vs audio/fusion (random init)
    text_params = list(model.text_model.parameters())
    audio_params = list(model.audio_model.parameters()) + \
                   list(model.text_proj.parameters()) + \
                   list(model.audio_proj.parameters()) + \
                   list(model.fusion.parameters()) + \
                   list(model.audio_classifier.parameters())
    
    optimizer = torch.optim.AdamW([
        {'params': text_params, 'lr': text_lr},
        {'params': audio_params, 'lr': audio_lr}
    ])
    
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([5.0]).to(device))
    
    best_f1 = 0.0
    results = []
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_text_loss = 0.0
        train_audio_loss = 0.0
        
        # Load and train batch
        # (In real implementation, use proper DataLoader)
        # Simplified here for structure
        
        # Validation
        model.eval()
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            # Validation loop would go here
            pass
        
        # Calculate F1
        from sklearn.metrics import f1_score
        # Placeholder - actual implementation needs proper val loader
        val_f1 = 0.0  # Replace with actual calculation
        
        print(f"Epoch {epoch+1}/{epochs}")
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val F1: {val_f1:.4f}")
        
        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(model.state_dict(), output_path / "v9_fusion_best.pt")
            print(f"  ✅ Best model saved!")
        
        results.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_f1': val_f1
        })
    
    # Save results
    with open(output_path / "v9_fusion_results.json", 'w') as f:
        json.dump({'best_f1': best_f1, 'history': results}, f, indent=2)
    
    print(f"\n📊 Final Results:")
    print(f"   Best Val F1: {best_f1:.4f}")
    print(f"   Target: 0.78")
    
    return best_f1


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V9 Multimodal Fusion Training")
    parser.add_argument('--train', '-t', type=str, required=True,
                       help="Training manifest JSONL")
    parser.add_argument('--val', '-v', type=str, required=True,
                       help="Validation manifest JSONL")
    parser.add_argument('--output', '-o', type=str, default='experiments/v9_fusion',
                       help="Output directory")
    parser.add_argument('--epochs', '-e', type=int, default=10)
    parser.add_argument('--batch_size', '-b', type=int, default=4)
    parser.add_argument('--aux_weight', '-w', type=float, default=0.3,
                       help="Audio auxiliary loss weight")
    
    args = parser.parse_args()
    
    train_multimodal_fusion(
        train_manifest=args.train,
        val_manifest=args.val,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        aux_weight=args.aux_weight
    )

if __name__ == '__main__':
    main()
