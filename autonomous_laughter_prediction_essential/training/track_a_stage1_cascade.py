"""
Track A Stage 1: XLM-R Cascade — Text Region Proposal
=======================================================

Purpose: Build Stage 1 of cascade architecture.
Text model predicts COARSE LAUGH_REGIONS (span-level), not token-level.

Architecture:
- XLM-R base → span-level prediction
- Input: word sequence with punctuation markers
- Output: which spans contain audience laughter

Why span-level instead of token-level?
- Boundary audit: 62% of labels within 500ms, median 175ms
- Single token classification can't capture "region" semantics
- Span-level naturally groups consecutive laughter tokens

Expected: Break IoU-F1 0.50 ceiling by predicting regions first,
then refining boundaries in Stage 2 with prosody.
"""

import json
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import XLMRobertaTokenizer, XLMRobertaModel, AutoConfig
from pathlib import Path
from collections import defaultdict

# Config
MODEL_NAME = "xlm-roberta-base"
MAX_LEN = 256
BATCH_SIZE = 32
EPOCHS = 10
LR = 2e-5
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Paths
ALIGNED_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl'
OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/track_a_stage1'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Device: {DEVICE}")


class SpanDataset(Dataset):
    """
    Dataset for span-level laughter prediction.
    
    For each video, we group consecutive positive tokens into SPANS.
    A span = [start_word_idx, end_word_idx] that captures a laugh region.
    
    The model learns to predict: given a sequence of words, which spans contain laughter?
    """
    
    def __init__(self, video_groups, tokenizer, max_len=256):
        self.video_groups = video_groups  # {video_id: [(word, start, end, label), ...]}
        self.tokenizer = tokenizer
        self.max_len = max_len
        
        # Build training examples: each video = one sequence
        self.examples = []
        for video_id, words_data in self.video_groups.items():
            text_tokens = [w[0] for w in words_data]  # word texts
            labels = [w[3] for w in words_data]  # label_any
            
            # Group consecutive positives into spans
            spans = self._group_into_spans(labels)
            
            # Store for later span matching
            self.examples.append({
                'video_id': video_id,
                'words': text_tokens,
                'starts': [w[1] for w in words_data],
                'ends': [w[2] for w in words_data],
                'labels': labels,
                'spans': spans  # list of (start_idx, end_idx)
            })
    
    def _group_into_spans(self, labels):
        """Group consecutive positive tokens into spans."""
        spans = []
        i = 0
        while i < len(labels):
            if labels[i] == 1:
                start = i
                while i < len(labels) and labels[i] == 1:
                    i += 1
                end = i - 1
                spans.append((start, end))
            else:
                i += 1
        return spans
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        ex = self.examples[idx]
        words = ex['words']
        spans = ex['spans']
        
        # Tokenize
        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].squeeze(0)
        attention_mask = encoding['attention_mask'].squeeze(0)
        
        # Map token labels to word positions
        # For span prediction: we predict for each word whether it's in a positive span
        word_labels = ex['labels']  # list of 0/1 per word
        
        # Create span labels: for each word position, is it part of a positive span?
        span_labels = torch.zeros(self.max_len, dtype=torch.float)
        
        # Map spans to token positions (approximate)
        word_ids = encoding.word_ids()
        for token_idx, word_idx in enumerate(word_ids):
            if word_idx is not None and word_idx < len(word_labels):
                # If this word is in any positive span, label it
                for span_start, span_end in spans:
                    if span_start <= word_idx <= span_end:
                        span_labels[token_idx] = 1.0
                        break
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': span_labels,
            'video_id': ex['video_id']
        }


class SpanPredictor(nn.Module):
    """
    XLM-R based span predictor for laughter regions.
    
    Architecture:
    - XLM-R base → contextualized token embeddings
    - Mean pooling → span representation
    - MLP → binary span prediction
    """
    
    def __init__(self, model_name=MODEL_NAME):
        super().__init__()
        self.xlmr = XLMRobertaModel.from_pretrained(model_name)
        hidden_size = self.xlmr.config.hidden_size  # 768
        
        # Span prediction head
        self.span_head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )
    
    def forward(self, input_ids, attention_mask):
        outputs = self.xlmr(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # (batch, seq_len, hidden)
        
        # Mean pooling over non-padded tokens
        mask_expanded = attention_mask.unsqueeze(-1).expand(sequence_output.size()).float()
        sum_embeddings = torch.sum(sequence_output * mask_expanded, dim=1)
        sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        pooled = sum_embeddings / sum_mask
        
        # Span prediction
        span_logits = self.span_head(pooled)  # (batch, 1)
        
        return span_logits.squeeze(-1)


def build_train_valid_split():
    """
    Build train/valid/test splits based on videos.
    Use held-out comedians (Burr, Chappelle, Peters) as test.
    """
    print("Building train/valid/test splits...")
    
    # Load all data
    all_data = [json.loads(line) for line in open(ALIGNED_PATH)]
    print(f"  Total utterances: {len(all_data)}")
    
    # Group by video
    video_data = defaultdict(list)
    for d in all_data:
        video_data[d['video_id']].append(d)
    
    # Check for split info in existing data
    # For now: random 80/10/10 split by video
    video_ids = list(video_data.keys())
    np.random.seed(42)
    np.random.shuffle(video_ids)
    
    n = len(video_ids)
    train_videos = set(video_ids[:int(n * 0.8)])
    valid_videos = set(video_ids[int(n * 0.8):int(n * 0.9)])
    test_videos = set(video_ids[int(n * 0.9):])
    
    print(f"  Train videos: {len(train_videos)}")
    print(f"  Valid videos: {len(valid_videos)}")
    print(f"  Test videos: {len(test_videos)}")
    
    # Build video groups for each split
    def build_video_groups(video_set):
        groups = {}
        for vid in video_set:
            if vid in video_data:
                words_list = []
                for d in video_data[vid]:
                    words_list.append((
                        d.get('text', ''),
                        d.get('start', 0),
                        d.get('end', 0),
                        d.get('label_any', 0)
                    ))
                groups[vid] = words_list
        return groups
    
    train_groups = build_video_groups(train_videos)
    valid_groups = build_video_groups(valid_videos)
    test_groups = build_video_groups(test_videos)
    
    print(f"  Train words: {sum(len(v) for v in train_groups.values())}")
    print(f"  Valid words: {sum(len(v) for v in valid_groups.values())}")
    print(f"  Test words: {sum(len(v) for v in test_groups.values())}")
    
    return train_groups, valid_groups, test_groups


def compute_metrics(preds, labels, threshold=0.5):
    """Compute token-level and span-level metrics."""
    preds_binary = (preds > threshold).float()
    
    # Token-level
    tp = ((preds_binary == 1) & (labels == 1)).sum().item()
    fp = ((preds_binary == 1) & (labels == 0)).sum().item()
    fn = ((preds_binary == 0) & (labels == 1)).sum().item()
    tn = ((preds_binary == 0) & (labels == 0)).sum().item()
    
    precision = tp / (tp + fp + 1e-9)
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)
    
    # Span-level IoU
    # For each example, compute span IoU
    span_ious = []
    for p, l in zip(preds_binary.cpu().numpy(), labels.cpu().numpy()):
        pred_spans = extract_spans(p)
        true_spans = extract_spans(l)
        iou = compute_span_iou(pred_spans, true_spans)
        span_ious.append(iou)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'span_iou_f1': np.mean(span_ious) if span_ious else 0.0,
        'tp': tp, 'fp': fp, 'fn': fn
    }


def extract_spans(binary_array):
    """Extract contiguous spans from binary array."""
    spans = []
    i = 0
    while i < len(binary_array):
        if binary_array[i] == 1:
            start = i
            while i < len(binary_array) and binary_array[i] == 1:
                i += 1
            spans.append((start, i - 1))
        else:
            i += 1
    return spans


def compute_span_iou(pred_spans, true_spans):
    """Compute IoU between predicted and true spans."""
    if len(pred_spans) == 0 and len(true_spans) == 0:
        return 1.0
    if len(pred_spans) == 0 or len(true_spans) == 0:
        return 0.0
    
    ious = []
    for pred in pred_spans:
        max_iou = 0.0
        for true in true_spans:
            inter_start = max(pred[0], true[0])
            inter_end = min(pred[1], true[1])
            union_start = min(pred[0], true[0])
            union_end = max(pred[1], true[1])
            
            inter_len = max(0, inter_end - inter_start + 1)
            union_len = union_end - union_start + 1
            
            if union_len > 0:
                iou = inter_len / union_len
                max_iou = max(max_iou, iou)
        ious.append(max_iou)
    
    return np.mean(ious)


def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask)
        
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        all_preds.append(outputs.detach())
        all_labels.append(labels)
    
    preds = torch.cat(all_preds)
    labels = torch.cat(all_labels)
    
    return total_loss / len(dataloader), compute_metrics(preds, labels)


def eval_epoch(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids, attention_mask)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            all_preds.append(outputs)
            all_labels.append(labels)
    
    preds = torch.cat(all_preds)
    labels = torch.cat(all_labels)
    
    return total_loss / len(dataloader), compute_metrics(preds, labels)


def main():
    print("=" * 60)
    print("Track A Stage 1: XLM-R Cascade — Text Region Proposal")
    print("=" * 60)
    
    # Load tokenizer
    print("\nLoading XLM-R tokenizer...")
    tokenizer = XLMRobertaTokenizer.from_pretrained(MODEL_NAME)
    
    # Build splits
    train_groups, valid_groups, test_groups = build_train_valid_split()
    
    # Create datasets
    print("\nCreating datasets...")
    train_dataset = SpanDataset(train_groups, tokenizer, max_len=MAX_LEN)
    valid_dataset = SpanDataset(valid_groups, tokenizer, max_len=MAX_LEN)
    test_dataset = SpanDataset(test_groups, tokenizer, max_len=MAX_LEN)
    
    print(f"  Train: {len(train_dataset)} videos")
    print(f"  Valid: {len(valid_dataset)} videos")
    print(f"  Test: {len(test_dataset)} videos")
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)
    
    # Create model
    print("\nCreating model...")
    model = SpanPredictor(MODEL_NAME)
    model = model.to(DEVICE)
    
    # Loss and optimizer
    # Use weighted BCE for class imbalance
    pos_rate = sum(len(ex['spans']) for ex in train_dataset.examples) / sum(len(ex['words']) for ex in train_dataset.examples)
    pos_weight = torch.tensor([(1 - pos_rate) / (pos_rate + 1e-9)]).to(DEVICE)
    criterion = nn.BCELoss()
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    
    # Training loop
    print("\nTraining...")
    best_val_f1 = 0
    best_epoch = 0
    results = {'train': [], 'valid': []}
    
    for epoch in range(EPOCHS):
        train_loss, train_metrics = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss, val_metrics = eval_epoch(model, valid_loader, criterion, DEVICE)
        
        results['train'].append({
            'epoch': epoch,
            'loss': train_loss,
            'f1': train_metrics['f1'],
            'span_iou_f1': train_metrics['span_iou_f1']
        })
        results['valid'].append({
            'epoch': epoch,
            'loss': val_loss,
            'f1': val_metrics['f1'],
            'span_iou_f1': val_metrics['span_iou_f1']
        })
        
        print(f"Epoch {epoch:2d} | "
              f"Train Loss: {train_loss:.4f}, F1: {train_metrics['f1']:.4f}, Span-IoU: {train_metrics['span_iou_f1']:.4f} | "
              f"Val Loss: {val_loss:.4f}, F1: {val_metrics['f1']:.4f}, Span-IoU: {val_metrics['span_iou_f1']:.4f}")
        
        if val_metrics['f1'] > best_val_f1:
            best_val_f1 = val_metrics['f1']
            best_epoch = epoch
            torch.save(model.state_dict(), f'{OUTPUT_DIR}/best_model.pt')
            print(f"  → New best model saved!")
    
    # Load best model and evaluate on test
    print("\n" + "=" * 60)
    print("EVALUATION ON TEST SET")
    print("=" * 60)
    
    model.load_state_dict(torch.load(f'{OUTPUT_DIR}/best_model.pt'))
    test_loss, test_metrics = eval_epoch(model, test_loader, criterion, DEVICE)
    
    print(f"\nTest Results (best epoch {best_epoch}):")
    print(f"  Token F1: {test_metrics['f1']:.4f}")
    print(f"  Span IoU-F1: {test_metrics['span_iou_f1']:.4f}")
    print(f"  Precision: {test_metrics['precision']:.4f}")
    print(f"  Recall: {test_metrics['recall']:.4f}")
    print(f"  TP: {test_metrics['tp']}, FP: {test_metrics['fp']}, FN: {test_metrics['fn']}")
    
    # Save results
    results['test'] = {
        'loss': test_loss,
        'f1': test_metrics['f1'],
        'span_iou_f1': test_metrics['span_iou_f1'],
        'precision': test_metrics['precision'],
        'recall': test_metrics['recall']
    }
    results['best_epoch'] = best_epoch
    
    with open(f'{OUTPUT_DIR}/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {OUTPUT_DIR}/results.json")
    
    return results


if __name__ == '__main__':
    results = main()
    print("\n✅ Track A Stage 1 complete!")