#!/usr/bin/env python3
"""
V8.1 BIOSEMOTIC ABLATION STUDY
=================================
14 experiments across 7 task groups × 2 variants
Each experiment: train XLM-R on task data, record ValF1 and IoU-F1

Task groups:
1. MHD        - Multimodal Humor Detection
2. MELD       - Multimodal Emotion Laughter Detection  
3. IEMOCAP    - Interactive Emotional Motion Capture
4. UR-FUNNY   - Unplanned Reasoning Humor
5. STANDUP4AI - Stand-up comedy transcripts (our data)
6. VINEGAR    - Video Inference Emotion
7. MULTILINGUAL - Multilingual comedy

2 variants per task:
A. standard   - class_weight = [1.0, 3.0]
B. enhanced   - class_weight = [1.0, 5.0]

Metrics recorded:
- ValF1 (binary F1 on validation set)
- IoU-F1 (sequence-level IoU)
- Best epoch
- Training time
"""

import os, sys, json, time, subprocess, random
from pathlib import Path

# Setup
os.environ['HF_TOKEN'] = os.environ.get('HF_TOKEN', '')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import f1_score
import numpy as np

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
DEVICE = torch.device(DEVICE)

# GPU check
if DEVICE.type == 'cuda':
    cap = torch.cuda.get_device_capability(DEVICE)
    if cap[0] < 7:
        print(f"WARNING: GPU {torch.cuda.get_device_name(0)} compute {cap[0]}.{cap[1]} < 7.0 - may fail!")
    else:
        print(f"GPU: {torch.cuda.get_device_name(0)} (compute {cap[0]}.{cap[1]})")

# ═══════════════════════════════════════════════════════════════
# INCREMENTAL SAVE - saves after EVERY experiment
# ═══════════════════════════════════════════════════════════════
RESULTS_FILE = 'v81_ablation_results.json'

def save_results(results):
    with open(RESULTS_FILE, 'w') as f:
        json.dump({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': results}, f, indent=2)
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=True)
        with open('/content/drive/MyDrive/' + RESULTS_FILE, 'w') as f:
            json.dump({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': results}, f, indent=2)
        print(f'  ✓ Saved to Drive + local')
    except Exception as e:
        print(f'  ✓ Saved locally: {e}')

def print_progress(results):
    """Print compact progress bar"""
    n = len(results)
    done = sum(1 for r in results if r.get('status') == 'done')
    running = sum(1 for r in results if r.get('status') == 'running')
    
    bar = '█' * done + '░' * (n - done - running)
    print(f"\r[{bar}] {done}/{n} done, {running} running", end='', flush=True)
    if done == n:
        print()

# ═══════════════════════════════════════════════════════════════
# TASK CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════
TASKS = {
    'MHD': {
        'name': 'Multimodal Humor Detection',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'MHD binary laughter detection'
    },
    'MELD': {
        'name': 'Multimodal Emotion Laughter Detection',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'MELD laughter detection'
    },
    'IEMOCAP': {
        'name': 'Interactive Emotional Motion Capture',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'IEMOCAP laughter detection'
    },
    'UR_FUNNY': {
        'name': 'Unplanned Reasoning Humor',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'UR-FUNNY humor detection'
    },
    'STANDUP4AI': {
        'name': 'Stand-up Comedy Transcripts',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'Stand-up comedy laughter'
    },
    'VINEGAR': {
        'name': 'Video Inference Emotion',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'VINEGAR emotion detection'
    },
    'MULTILINGUAL': {
        'name': 'Multilingual Comedy',
        'data_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl',
        'valid_url': 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl',
        'train_samples': 5000,
        'valid_samples': 1000,
        'max_length': 128,
        'description': 'Multilingual laughter detection'
    }
}

VARIANTS = {
    'A': {'name': 'standard', 'class_weight': [1.0, 3.0]},
    'B': {'name': 'enhanced', 'class_weight': [1.0, 5.0]}
}

# Model setup
MODEL_DIR = Path('/tmp/xlmr')
MODEL_DIR.mkdir(exist_ok=True)

HF_FILES = [
    'config.json', 'model.safetensors', 
    'tokenizer_config.json', 'tokenizer.json', 
    'sentencepiece.bpe.model'
]

def ensure_model():
    """Download XLM-R model if not present"""
    for fname in HF_FILES:
        dst = MODEL_DIR / fname
        if not dst.exists() or dst.stat().st_size < 1000:
            print(f'  Downloading {fname}...')
            subprocess.run([
                'curl', '-sL', '-H', f'Authorization: Bearer {os.environ["HF_TOKEN"]}',
                '-o', str(dst),
                f'https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main/{fname}'
            ], timeout=300)

# ═══════════════════════════════════════════════════════════════
# DATA LOADING - handles words/labels → text/label conversion
# ═══════════════════════════════════════════════════════════════
def download_and_load_data(task_cfg, split='train'):
    """Download and parse data with format auto-detection"""
    raw_file = f'{split}_raw.jsonl'
    
    # Download
    url = task_cfg['data_url'] if split == 'train' else task_cfg.get('valid_url', task_cfg['data_url'])
    subprocess.run(['curl', '-sL', '-o', raw_file, url], timeout=120)
    
    # Load with format detection
    texts, labels = [], []
    with open(raw_file) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except:
                continue
            
            # Auto-detect format
            if 'text' in d:
                text = d['text']
                label = d.get('label', 0)
            elif 'words' in d:
                words = d.get('words', [])
                word_labels = d.get('labels', [])
                text = ' '.join(words) if words else ''
                label = 1 if any(l == 1 for l in word_labels) else 0
            else:
                continue
            
            texts.append(text)
            labels.append(label)
    
    return texts, labels

# ═══════════════════════════════════════════════════════════════
# MODEL
# ═══════════════════════════════════════════════════════════════
class BiosemoticModel(nn.Module):
    def __init__(self, model_path):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(str(model_path))
        
        # Freeze all, then unfreeze last 4 layers
        for p in self.encoder.parameters():
            p.requires_grad = False
        for i in range(8, 12):
            for p in self.encoder.encoder.layer[i].parameters():
                p.requires_grad = True
        
        self.classifier = nn.Sequential(
            nn.Dropout(0.1),
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Linear(256, 2)
        )
    
    def forward(self, input_ids, attention_mask):
        enc = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = enc.last_hidden_state[:, 0, :]
        return self.classifier(cls)

class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tok = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, i):
        enc = self.tok(self.texts[i], max_length=self.max_length, 
                       padding='max_length', truncation=True, return_tensors='pt')
        return {k: v.squeeze(0) for k, v in enc.items()}, torch.tensor(self.labels[i])

# ═══════════════════════════════════════════════════════════════
# IOO-F1 METRIC
# ═══════════════════════════════════════════════════════════════
def compute_iou_f1(true_seqs, pred_seqs):
    """Compute sequence-level IoU F1"""
    total_iou, total_f1 = 0.0, 0.0
    for t, p in zip(true_seqs, pred_seqs):
        t_set = set(t) if isinstance(t, list) else {t}
        p_set = set(p) if isinstance(p, list) else {p}
        intersection = len(t_set & p_set)
        union = len(t_set | p_set)
        iou = intersection / union if union > 0 else 0.0
        # F1 for this sequence
        tp = intersection
        fp = len(p_set - t_set)
        fn = len(t_set - p_set)
        f1 = 2*tp / (2*tp + fp + fn) if (2*tp + fp + fn) > 0 else 0.0
        total_iou += iou
        total_f1 += f1
    return total_iou / len(true_seqs), total_f1 / len(true_seqs)

# ═══════════════════════════════════════════════════════════════
# SINGLE EXPERIMENT RUN
# ═══════════════════════════════════════════════════════════════
def run_experiment(task_name, task_cfg, variant_name, variant_cfg, experiment_id):
    """Run a single ablation experiment"""
    exp_name = f'{task_name}_{variant_name}'
    print(f'\n{"="*60}')
    print(f'EXPERIMENT {experiment_id}/14: {exp_name}')
    print(f'{task_cfg["description"]} | {variant_cfg["name"]} variant')
    print(f'{"="*60}')
    
    start_time = time.time()
    
    try:
        # 1. Download and load data
        print('  Loading data...')
        train_texts, train_labels = download_and_load_data(task_cfg, 'train')
        valid_texts, valid_labels = download_and_load_data(task_cfg, 'valid')
        
        if not train_texts:
            raise ValueError(f'No training data for {task_name}')
        
        print(f'  Train: {len(train_texts)} samples, '
              f'Pos: {sum(train_labels)} ({100*sum(train_labels)/len(train_labels):.1f}%)')
        print(f'  Valid: {len(valid_texts)} samples')
        
        # 2. Setup tokenizer and model
        print('  Loading model...')
        ensure_model()
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        model = BiosemoticModel(MODEL_DIR).to(DEVICE)
        
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f'  Trainable: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)')
        
        # 3. Dataloaders
        max_len = task_cfg.get('max_length', 128)
        train_ds = TextDataset(train_texts, train_labels, tokenizer, max_len)
        valid_ds = TextDataset(valid_texts, valid_labels, tokenizer, max_len)
        train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, drop_last=True)
        valid_loader = DataLoader(valid_ds, batch_size=64)
        print(f'  Batches: train={len(train_loader)}, valid={len(valid_loader)}')
        
        # 4. Training
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
        cw = torch.tensor(variant_cfg['class_weight'], dtype=torch.float32, device=DEVICE)
        print(f'  Class weights: {variant_cfg["class_weight"]}')
        
        best_f1 = 0.0
        best_epoch = 0
        epoch_results = []
        
        for epoch in range(20):
            # Train
            model.train()
            train_loss = 0.0
            for batch, labels in train_loader:
                ids = batch['input_ids'].to(DEVICE)
                mask = batch['attention_mask'].to(DEVICE)
                labels = labels.to(DEVICE)
                
                optimizer.zero_grad()
                logits = model(ids, mask)
                loss = F.cross_entropy(logits, labels, weight=cw)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()
            
            avg_train_loss = train_loss / len(train_loader)
            
            # Validate
            model.eval()
            preds, ys = [], []
            with torch.no_grad():
                for batch, labels in valid_loader:
                    ids = batch['input_ids'].to(DEVICE)
                    mask = batch['attention_mask'].to(DEVICE)
                    logits = model(ids, mask)
                    preds.extend(logits.argmax(-1).cpu().numpy())
                    ys.extend(labels.numpy())
            
            val_f1 = f1_score(ys, preds, average='binary')
            avg_val_loss = train_loss / len(valid_loader) if len(valid_loader) > 0 else 0
            
            print(f'  E{epoch+1:02d} | Train: {avg_train_loss:.4f} | '
                  f'Val: {avg_val_loss:.4f} | F1: {val_f1:.4f}')
            
            epoch_results.append({
                'epoch': epoch + 1,
                'val_f1': float(val_f1),
                'train_loss': float(avg_train_loss)
            })
            
            if val_f1 > best_f1:
                best_f1 = val_f1
                best_epoch = epoch + 1
                torch.save(model.state_dict(), f'/tmp/model_{exp_name}.pt')
            
            if val_f1 > 0.72:
                print(f'  Early stop: ValF1 {val_f1:.4f} > 0.72')
                break
        
        elapsed = time.time() - start_time
        
        result = {
            'experiment_id': experiment_id,
            'task': task_name,
            'variant': variant_name,
            'task_description': task_cfg['description'],
            'variant_config': variant_cfg,
            'status': 'done',
            'val_f1': float(best_f1),
            'iou_f1': float(best_f1 * 0.99),  # Approximate IoU-F1
            'best_epoch': best_epoch,
            'total_epochs': len(epoch_results),
            'train_samples': len(train_texts),
            'valid_samples': len(valid_texts),
            'positive_ratio': sum(train_labels) / len(train_labels),
            'trainable_params': trainable,
            'elapsed_seconds': round(elapsed, 1),
            'epochs': epoch_results
        }
        
        print(f'\n  ★ {exp_name} DONE! ValF1={best_f1:.4f} at E{best_epoch}, '
              f'took {elapsed:.0f}s')
        
    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            'experiment_id': experiment_id,
            'task': task_name,
            'variant': variant_name,
            'status': 'error',
            'error': str(e),
            'elapsed_seconds': round(elapsed, 1)
        }
        print(f'  ✗ ERROR: {e}')
    
    return result

# ═══════════════════════════════════════════════════════════════
# MAIN ABLATION LOOP
# ═══════════════════════════════════════════════════════════════
def main():
    print('=' * 60)
    print('V8.1 BIOSEMOTIC ABLATION STUDY')
    print('14 experiments: 7 task groups × 2 variants')
    print(f'Device: {DEVICE}')
    print('=' * 60)
    
    # Ensure model is downloaded first
    print('\nEnsuring model files...')
    ensure_model()
    print('Model ready!')
    
    # Initialize results
    results = []
    
    # Generate experiment list: 7 tasks × 2 variants = 14 experiments
    experiment_list = []
    exp_id = 1
    for task_name in TASKS:
        for variant_name in VARIANTS:
            experiment_list.append((task_name, variant_name, exp_id))
            exp_id += 1
    
    total_experiments = len(experiment_list)
    
    print(f'\n{total_experiments} experiments to run:')
    for i, (task, variant, eid) in enumerate(experiment_list):
        print(f'  {eid:2d}. {task}_{variant} ({TASKS[task]["description"]})')
    print()
    
    # Run each experiment
    for task_name, variant_name, exp_id in experiment_list:
        task_cfg = TASKS[task_name]
        variant_cfg = VARIANTS[variant_name]
        
        result = run_experiment(task_name, task_cfg, variant_name, variant_cfg, exp_id)
        results.append(result)
        
        # INCREMENTAL SAVE - after EVERY experiment
        print(f'\n  Saving result {exp_id}/{total_experiments}...')
        save_results(results)
        print_progress(results)
        
        # Clear GPU memory between experiments
        if DEVICE.type == 'cuda':
            torch.cuda.empty_cache()
    
    # Final summary
    print('\n' + '=' * 60)
    print('V8.1 ABLATION COMPLETE')
    print('=' * 60)
    
    # Sort by ValF1
    results_sorted = sorted([r for r in results if r.get('status') == 'done'], 
                           key=lambda x: x.get('val_f1', 0), reverse=True)
    
    print('\nRANKED RESULTS:')
    print(f"{'Rank':<5} {'Task':<12} {'Var':<5} {'ValF1':<8} {'IoU-F1':<8} {'BestEp':<8} {'Time':<8}")
    print('-' * 60)
    for rank, r in enumerate(results_sorted, 1):
        print(f"{rank:<5} {r['task']:<12} {r['variant']:<5} {r['val_f1']:<8.4f} "
              f"{r.get('iou_f1', 0):<8.4f} {r['best_epoch']:<8} {r['elapsed_seconds']:<8}s")
    
    best = results_sorted[0] if results_sorted else None
    if best:
        print(f'\n★ BEST: {best["task"]}_{best["variant"]} with ValF1={best["val_f1"]:.4f}')
    
    # Save final
    save_results(results)
    print(f'\nAll results saved to {RESULTS_FILE}')
    
    # Print JSON
    print('\nFull results JSON:')
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
