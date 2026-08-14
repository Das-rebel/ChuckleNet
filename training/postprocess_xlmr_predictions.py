"""
Post-Process XLM-R Predictions - Corrected
===========================================
"""

import json
import numpy as np
from collections import defaultdict
import torch
from transformers import XLMRobertaModel, XLMRobertaTokenizerFast
import time
import os

DATA_PATH = '/Users/Subho/aligned_segments.jsonl'
CHECKPOINT_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/experiments/xlmr_baseline_retrained/best.pt'
OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/track_a_postprocess'
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_trained_model():
    """Load the trained XLM-R checkpoint."""
    print("Loading trained model...")
    
    base_model = XLMRobertaModel.from_pretrained('xlm-roberta-base')
    
    class TrainedClassifier(torch.nn.Module):
        def __init__(self, base):
            super().__init__()
            self.base = base
            self.classifier = torch.nn.Sequential(
                torch.nn.Linear(768, 256),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.1),
                torch.nn.Linear(256, 2)
            )
        
        def forward(self, input_ids, attention_mask):
            outputs = self.base(input_ids=input_ids, attention_mask=attention_mask)
            cls = outputs.last_hidden_state[:, 0, :]
            return self.classifier(cls)
    
    model = TrainedClassifier(base_model)
    
    checkpoint = torch.load(CHECKPOINT_PATH, map_location='cpu')
    model.load_state_dict(checkpoint['model_state'], strict=False)
    model = model.to(DEVICE)
    model.eval()
    
    print(f"  Loaded epoch {checkpoint.get('epoch')}, val_f1={checkpoint.get('val_f1')}")
    return model


def load_word_data():
    print("Loading word data...")
    video_data = defaultdict(list)
    skipped = 0
    for line in open(DATA_PATH):
        d = json.loads(line)
        # Skip entries without 'word' field (mixed format in file)
        if 'word' not in d:
            skipped += 1
            continue
        video_data[d['video_id']].append({
            'word': d['word'], 'start': d['start'], 'end': d['end'],
            'label': d['label'], 'context_words': d['context_words']
        })
    if skipped:
        print(f"  Skipped {skipped} entries without 'word' field")
    print(f"  {len(video_data)} videos, {sum(len(v) for v in video_data.values())} words")
    return video_data


def compute_iou(s1, s2):
    inter_start = max(s1['start'], s2['start'])
    inter_end = min(s1['end'], s2['end'])
    if inter_end <= inter_start:
        return 0.0
    return (inter_end - inter_start) / (max(s1['end'], s2['end']) - min(s1['start'], s2['start']))


def extract_spans(words_info, preds, threshold):
    spans = []
    i = 0
    while i < len(preds):
        if preds[i] > threshold:
            start = words_info[i]['start']
            end = words_info[i]['end']
            max_prob = preds[i]
            while i < len(preds) and preds[i] > threshold:
                max_prob = max(max_prob, preds[i])
                end = words_info[i]['end']
                i += 1
            spans.append({'start': start, 'end': end, 'conf': max_prob})
        else:
            i += 1
    return spans


def nms(spans, iou_thresh=0.5):
    if not spans:
        return []
    sorted_spans = sorted(enumerate(spans), key=lambda x: x[1]['conf'], reverse=True)
    keep = []
    while sorted_spans:
        idx, span = sorted_spans.pop(0)
        keep.append(span)
        sorted_spans = [(i, s) for i, s in sorted_spans if compute_iou(span, s) < iou_thresh]
    return keep


def filter_duration(spans, min_d=0.2, max_d=3.0):
    return [s for s in spans if min_d <= (s['end'] - s['start']) <= max_d]


def evaluate(pred_spans, true_spans, iou_thresh=0.5):
    tp = fp = fn = 0
    matched_true = set()
    for pi, pred in enumerate(pred_spans):
        for ti, true in enumerate(true_spans):
            if ti not in matched_true and compute_iou(pred, true) > iou_thresh:
                tp += 1
                matched_true.add(ti)
                break
    fn = len(true_spans) - len(matched_true)
    fp = len(pred_spans) - tp
    return tp, fp, fn


def main():
    print("=" * 60)
    print("Post-Process XLM-R Predictions")
    print("=" * 60)
    
    t0 = time.time()
    model = load_trained_model()
    video_data = load_word_data()
    
    print("\nPredicting...")
    tokenizer = XLMRobertaTokenizerFast.from_pretrained('xlm-roberta-base')
    
    all_preds = {}
    for vi, (vid, words) in enumerate(video_data.items()):
        contexts = [w['context_words'] for w in words]
        enc = tokenizer(contexts, is_split_into_words=True, max_length=32,
                        padding='max_length', truncation=True, return_tensors='pt')
        
        with torch.no_grad():
            logits = model(enc['input_ids'].to(DEVICE), enc['attention_mask'].to(DEVICE))
            probs = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
        
        all_preds[vid] = {'words': words, 'probs': probs}
        
        if (vi + 1) % 10 == 0:
            print(f"  {vi+1}/{len(video_data)} ({time.time()-t0:.0f}s)")
    
    print(f"\nPrediction done in {time.time()-t0:.0f}s")
    
    print("\nPost-processing...")
    results = []
    
    for thresh in [0.3, 0.4, 0.5, 0.6, 0.7]:
        all_tp = all_fp = all_fn = 0
        
        for vid, data in all_preds.items():
            pred_spans = extract_spans(data['words'], data['probs'], thresh)
            true_spans = extract_spans(data['words'], [w['label'] for w in data['words']], 0.5)
            pred_spans = nms(pred_spans)
            pred_spans = filter_duration(pred_spans)
            
            tp, fp, fn = evaluate(pred_spans, true_spans)
            all_tp += tp
            all_fp += fp
            all_fn += fn
        
        p = all_tp / (all_tp + all_fp + 1e-9)
        r = all_tp / (all_tp + all_fn + 1e-9)
        f1 = 2 * p * r / (p + r + 1e-9)
        
        print(f"thresh={thresh}: IoU-F1={f1:.4f} (P={p:.4f}, R={r:.4f})")
        results.append({'threshold': thresh, 'f1': f1, 'precision': p, 'recall': r})
    
    best = max(results, key=lambda x: x['f1'])
    print(f"\nBest: thresh={best['threshold']}, IoU-F1={best['f1']:.4f}")
    
    with open(f'{OUTPUT_DIR}/postprocess_results.json', 'w') as f:
        json.dump({'best': best, 'results': results}, f, indent=2)
    
    print(f"\nTotal time: {time.time()-t0:.0f}s")
    return best


if __name__ == '__main__':
    main()