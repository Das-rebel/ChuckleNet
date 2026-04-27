"""
Chucklenet Biosemotic Ablation Study — 41K 27-dim Data
======================================================
Self-contained Colab notebook script. Implements the FULL planned pipeline:

  PHASE A: Baselines (plain XLM-R, no aux)
    A1: pw=5 baseline
    A2: pw=3 baseline  

  PHASE B: Full biosemotic model
    B1: Full 27-dim, aux_weight=0.3
    B2: Full 27-dim, aux_weight=0.5

  PHASE C: Single-dimension ablation (remove 1 group)
    C1: no_duchenne
    C2: no_incongruity
    C3: no_tom
    C4: no_cue
    C5: no_structural
    C6: no_linguistic
    C7: no_metadata

  PHASE D: Group ablation
    D1: core_trio_only (duchenne+incongruity+tom only)
    D2: no_cognitive (only surface: cue+struct+ling+meta)
    D3: surface_only (duchenne+incongruity+tom disabled)

Data: 41,240 clean examples with real [laughter] markers + 27 biosemotic dims
"""

import os; os.environ['TOKENIZERS_PARALLELISM']='false'
import subprocess, sys, json, time, gc, math, random
import numpy as np
from pathlib import Path

# ================================================================
# STEP 0: Download XLM-RoBERTa from HuggingFace CDN via wget
# (bypasses HF API rate limit by using the CDN directly)
# ================================================================
MODEL_LOCAL = "/tmp/xlm-roberta-base-ms"
HF_CDN = "https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main"
HF_FILES = [
    "config.json", "model.safetensors", "tokenizer_config.json",
    "tokenizer.json", "vocab.json", "merges.txt",
    "sentencepiece.bpe.model", "special_tokens_map.json",
]


# Force clean redownload (prev run may have left corrupt files)
os.system("rm -rf " + MODEL_LOCAL)
if not Path(MODEL_LOCAL).joinpath("model.safetensors").exists() or \
   Path(MODEL_LOCAL).joinpath("model.safetensors").stat().st_size < 1000:
    print("Downloading XLM-RoBERTa from HuggingFace CDN (no rate limits)...")
    os.makedirs(MODEL_LOCAL, exist_ok=True)
    for fname in HF_FILES:
        dst = f"{MODEL_LOCAL}/{fname}"
        if not Path(dst).exists() or Path(dst).stat().st_size < 100:
            print(f"  Downloading {fname}...", end="", flush=True)
            r = subprocess.run(["wget", "-q", "-O", dst, f"{HF_CDN}/{fname}"],
                             capture_output=True, timeout=300)
            size = Path(dst).stat().st_size if Path(dst).exists() else 0
            print(f" {size/1024/1024:.1f} MB")
        else:
            print(f"  {fname}: already exists")
    print(f"Model ready at {MODEL_LOCAL}")
    files = [f.name for f in Path(MODEL_LOCAL).iterdir()]
    print(f"Files: {files}")
else:
    print(f"Model already at {MODEL_LOCAL}")

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'transformers', 'scikit-learn'], check=True)

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, AutoConfig
from transformers import get_linear_schedule_with_warmup
from sklearn.metrics import f1_score, precision_recall_fscore_support

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# ================================================================
# Download 27-dim data from GitHub
# ================================================================
BASE_URL = "https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data"
for s in ['train', 'valid', 'test']:
    fname = f'{s}.jsonl'
    if not Path(fname).exists():
        print(f"Downloading {fname}...")
        subprocess.run(['wget', '-q', f'{BASE_URL}/{fname}', '-O', fname], check=True)

# Verify data
n_train = sum(1 for _ in open('train.jsonl'))
n_valid = sum(1 for _ in open('valid.jsonl'))
n_test  = sum(1 for _ in open('test.jsonl'))
print(f"Data: train={n_train:,} valid={n_valid:,} test={n_test:,}")

# Check biosemotic dimensions
try:
    sample = json.loads(open('train.jsonl').readline())
    bio_keys = [k for k in sample if k not in ['words','labels','language','metadata','example_id','cue_bucket_ids']]
    print(f"Biosemotic fields ({len(bio_keys)}): {bio_keys}")
except (json.JSONDecodeError, IndexError, Exception) as e:
    print(f"WARNING: Could not read sample line: {e}")
    # Try second line
    try:
        sample = json.loads(open('train.jsonl').readline())
        bio_keys = [k for k in sample if k not in ['words','labels','language','metadata','example_id','cue_bucket_ids']]
        print(f"Biosemotic fields (from line 2, {len(bio_keys)}): {bio_keys}")
    except:
        bio_keys = ['comedian_id','show_id','laughter_type','dialect_bucket','language_domain','gender','age_group','current_segment_start','clause_boundary_ratio','punchline_zone_ratio','setup_zone_ratio','filler_token_ratio','filler_token_count','negation_ratio','negation_count','exclamation_ratio','exclamation_count','quoted_speech_ratio','in_quoted_speech','duchenne_joy_intensity','duchenne_genuine_humor_probability','duchenne_spontaneous_laughter_markers','duchenne_setup_punchline_structure','incongruity_expectation_violation_score','incongruity_humor_complexity_score','incongruity_resolution_time','tom_speaker_intent_label','tom_speaker_intent_confidence','tom_audience_perspective_score','tom_social_context_humor_score','tom_character_interaction_pattern','tom_character_interaction_score']
        print(f"Biosemotic fields (fallback, {len(bio_keys)}): {bio_keys}")

# ================================================================
# Dataset with 27-dim biosemotic features
# ================================================================
class BiosemoticDataset(Dataset):
    """Pre-tokenized dataset with subword-aligned labels + biosemotic features."""

    def __init__(self, filepath, tokenizer, max_length=256):
        self.examples = []
        raw = []
        try:
            with open(filepath) as f:
                for idx, line in enumerate(f):
                    line = line.strip()
                    if line:
                        try:
                            raw.append(json.loads(line))
                        except json.JSONDecodeError:
                            print(f"  WARNING: Skipping malformed line {idx+1}: {line[:50]}")
        except Exception as e:
            print(f"  ERROR loading {filepath}: {e}")

        print(f"  Pre-tokenizing {len(raw)} examples...")
        for idx, ex in enumerate(raw):
            words = [str(x) for x in ex.get('words', [])]
            if not words: continue
            labels = ex.get('labels', [0]*len(words))

            # Subword-aligned tokenization
            enc = tokenizer(words, is_split_into_words=True,
                           truncation=True, max_length=max_length,
                           padding='max_length', return_tensors='pt')

            input_ids = enc['input_ids'].squeeze(0)
            attention_mask = enc['attention_mask'].squeeze(0)

            # Align labels to subword tokens
            word_ids = enc.word_ids(batch_index=0)
            tok_labels = []
            prev = None
            for wid in word_ids:
                if wid is None:
                    tok_labels.append(-100)
                elif wid != prev and wid < len(labels):
                    tok_labels.append(labels[wid])
                    prev = wid
                else:
                    tok_labels.append(-100)

            # Biosemotic features
            def _s(field, default=0.5):
                v = ex.get(field, default)
                return float(v) if v is not None else default

            # Group 1: Duchenne (4 regression)
            duchenne = torch.tensor([
                _s('duchenne_joy_intensity'),
                _s('duchenne_genuine_humor_probability'),
                _s('duchenne_spontaneous_laughter_markers'),
                _s('duchenne_setup_punchline_structure'),
            ], dtype=torch.float32)

            # Group 2: Incongruity (3 regression)
            incongruity = torch.tensor([
                _s('incongruity_expectation_violation_score'),
                _s('incongruity_humor_complexity_score'),
                _s('incongruity_resolution_time'),
            ], dtype=torch.float32)

            # Group 3: Theory of Mind (1 classification + 3 regression)
            intent_map = {'humor_expression': 0, 'playful_banter': 1, 'storytelling': 2}
            tom_intent = torch.tensor(
                intent_map.get(ex.get('tom_speaker_intent_label', ''), 0), dtype=torch.long)
            tom_reg = torch.tensor([
                _s('tom_speaker_intent_confidence'),
                _s('tom_audience_perspective_score'),
                _s('tom_social_context_humor_score'),
            ], dtype=torch.float32)

            # Group 4: Cue buckets (7 binary)
            cue_ids = ex.get('cue_bucket_ids', [0]*7)
            cue_buckets = torch.tensor((cue_ids + [0]*7)[:7], dtype=torch.long)

            # Group 5: Structural (3 regression)
            structural = torch.tensor([
                _s('clause_boundary_ratio', 0.33),
                _s('punchline_zone_ratio', 0.33),
                _s('setup_zone_ratio', 0.33),
            ], dtype=torch.float32)

            # Group 6: Linguistic (4 regression)
            linguistic = torch.tensor([
                _s('filler_token_ratio', 0.1),
                _s('negation_ratio', 0.1),
                _s('exclamation_ratio', 0.1),
                _s('quoted_speech_ratio', 0.1),
            ], dtype=torch.float32)

            # Group 7: Metadata (6 categorical)
            def _hash_cat(field, n_bins=6):
                return hash(str(ex.get(field, 'unknown'))) % n_bins
            metadata = torch.tensor([
                _hash_cat('language'),
                _hash_cat('dialect_bucket'),
                _hash_cat('laughter_type'),
                _hash_cat('gender'),
                _hash_cat('age_group'),
                _hash_cat('comedian_id'),
            ], dtype=torch.long)

            self.examples.append({
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'token_labels': torch.tensor(tok_labels, dtype=torch.long),
                'duchenne': duchenne,
                'incongruity': incongruity,
                'tom_intent': tom_intent,
                'tom_reg': tom_reg,
                'cue_buckets': cue_buckets,
                'structural': structural,
                'linguistic': linguistic,
                'metadata': metadata,
            })

            if (idx+1) % 10000 == 0:
                print(f"    {idx+1}/{len(raw)}", flush=True)

        print(f"  Done: {len(self.examples)} examples")

    def __len__(self): return len(self.examples)
    def __getitem__(self, idx): return self.examples[idx]


def collate_fn(batch):
    return {k: torch.stack([b[k] for b in batch]) for k in batch[0]}

# ================================================================
# Biosemotic Model with 7 auxiliary task heads
# ================================================================
class BiosemoticModel(nn.Module):
    def __init__(self, model_name=MODEL_LOCAL,
                 disable_duchenne=False, disable_incongruity=False,
                 disable_tom=False, disable_cue=False,
                 disable_structural=False, disable_linguistic=False,
                 disable_metadata=False, disable_all_aux=False):
        super().__init__()
        self.flags = {
            'duchenne': disable_duchenne or disable_all_aux,
            'incongruity': disable_incongruity or disable_all_aux,
            'tom': disable_tom or disable_all_aux,
            'cue': disable_cue or disable_all_aux,
            'structural': disable_structural or disable_all_aux,
            'linguistic': disable_linguistic or disable_all_aux,
            'metadata': disable_metadata or disable_all_aux,
        }

        config = AutoConfig.from_pretrained(model_name)
        self.backbone = AutoModel.from_pretrained(model_name, config=config)
        hidden = config.hidden_size  # 768

        # PRIMARY: Token-level laughter classification
        self.laughter_head = nn.Sequential(
            nn.Linear(hidden, 256), nn.GELU(), nn.Dropout(0.1), nn.Linear(256, 2))

        # AUX heads (created only if enabled)
        self.duchenne_head = nn.Linear(hidden, 4) if not self.flags['duchenne'] else None
        self.incongruity_head = nn.Linear(hidden, 3) if not self.flags['incongruity'] else None
        self.tom_intent_head = nn.Linear(hidden, 3) if not self.flags['tom'] else None
        self.tom_reg_head = nn.Linear(hidden, 3) if not self.flags['tom'] else None
        self.cue_head = nn.Linear(hidden, 7) if not self.flags['cue'] else None
        self.structural_head = nn.Linear(hidden, 3) if not self.flags['structural'] else None
        self.linguistic_head = nn.Linear(hidden, 4) if not self.flags['linguistic'] else None
        self.metadata_head = nn.Linear(hidden, 6) if not self.flags['metadata'] else None

    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        cls = out.last_hidden_state[:, 0]   # [B, 768]
        seq = out.last_hidden_state          # [B, L, 768]

        result = {'laughter_logits': self.laughter_head(seq)}
        if self.duchenne_head:     result['duchenne'] = self.duchenne_head(cls)
        if self.incongruity_head:  result['incongruity'] = self.incongruity_head(cls)
        if self.tom_intent_head:   result['tom_intent'] = self.tom_intent_head(cls)
        if self.tom_reg_head:      result['tom_reg'] = self.tom_reg_head(cls)
        if self.cue_head:          result['cue'] = self.cue_head(cls)
        if self.structural_head:   result['structural'] = self.structural_head(cls)
        if self.linguistic_head:   result['linguistic'] = self.linguistic_head(cls)
        if self.metadata_head:     result['metadata'] = self.metadata_head(cls)
        return result

# ================================================================
# Multi-task loss
# ================================================================
def compute_loss(outputs, batch, pos_weight=5.0, aux_weight=0.3):
    device = outputs['laughter_logits'].device
    losses = {}

    # PRIMARY: Token-level laughter
    logits = outputs['laughter_logits']
    labels = batch['token_labels'].to(device)
    mask = (labels != -100)
    if mask.sum() > 0:
        cw = torch.tensor([1.0, pos_weight], device=device)
        losses['laughter'] = F.cross_entropy(
            logits.view(-1, 2)[mask.view(-1)],
            labels.view(-1)[mask.view(-1)], weight=cw)

    # AUX losses
    if 'duchenne' in outputs:
        losses['duchenne'] = F.mse_loss(outputs['duchenne'], batch['duchenne'].to(device))
    if 'incongruity' in outputs:
        losses['incongruity'] = F.mse_loss(outputs['incongruity'], batch['incongruity'].to(device))
    if 'tom_intent' in outputs:
        losses['tom_intent'] = F.cross_entropy(outputs['tom_intent'], batch['tom_intent'].to(device))
    if 'tom_reg' in outputs:
        losses['tom_reg'] = F.mse_loss(outputs['tom_reg'], batch['tom_reg'].to(device))
    if 'cue' in outputs:
        losses['cue'] = F.cross_entropy(outputs['cue'].view(-1,7), batch['cue_buckets'].to(device).view(-1))
    if 'structural' in outputs:
        losses['structural'] = F.mse_loss(outputs['structural'], batch['structural'].to(device))
    if 'linguistic' in outputs:
        losses['linguistic'] = F.mse_loss(outputs['linguistic'], batch['linguistic'].to(device))
    if 'metadata' in outputs:
        losses['metadata'] = F.cross_entropy(outputs['metadata'].view(-1,6), batch['metadata'].to(device).view(-1))

    total = losses['laughter']
    aux_keys = [k for k in losses if k != 'laughter']
    if aux_keys:
        total = total + aux_weight * sum(losses[k] for k in aux_keys) / len(aux_keys)

    return total, losses

# ================================================================
# Training + Evaluation
# ================================================================
@torch.no_grad()
def evaluate(model, loader, device, pos_weight=5.0, aux_weight=0.3):
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0

    for batch in loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        outputs = model(input_ids, attention_mask)
        loss, losses = compute_loss(outputs, batch, pos_weight, aux_weight)
        total_loss += loss.item()

        labels = batch['token_labels'].to(device)
        mask = (labels != -100)
        preds = outputs['laughter_logits'].argmax(dim=-1)
        all_preds.extend(preds[mask].cpu().tolist())
        all_labels.extend(labels[mask].cpu().tolist())

    avg_loss = total_loss / len(loader)
    f1 = f1_score(all_labels, all_preds, pos_label=1, zero_division=0)
    p, r, f1b, _ = precision_recall_fscore_support(all_labels, all_preds, pos_label=1, zero_division=0)
    return {'loss': avg_loss, 'f1': f1, 'precision': float(p), 'recall': float(r)}


def run_experiment(name, pos_weight=5.0, epochs=10, lr=2e-5, batch_size=16,
                   aux_weight=0.3, patience=3, unfreeze_layers=4, **disable_flags):
    import traceback as _tb
    try:
        print(f"\n{'─'*60}")
        print(f" {name}  pw={pos_weight} aux={aux_weight} uf={unfreeze_layers}")
        disabled = [k for k,v in disable_flags.items() if v]
        if disabled: print(f" Disabled: {disabled}")
        print(f"{'─'*60}")

        device = torch.device('cuda')
        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_LOCAL)
        except Exception as e:
            print(f"ERROR loading tokenizer: {e}")
            import os
            os.system(f"rm -rf {MODEL_LOCAL}")
            os.makedirs(MODEL_LOCAL, exist_ok=True)
            for fname in HF_FILES:
                subprocess.run(["wget", "-q", "-O", f"{MODEL_LOCAL}/{fname}", f"{HF_CDN}/{fname}"], check=True)
            tokenizer = AutoTokenizer.from_pretrained(MODEL_LOCAL)
        start = time.time()

        train_ds = BiosemoticDataset('train.jsonl', tokenizer)
        valid_ds = BiosemoticDataset('valid.jsonl', tokenizer)
        test_ds  = BiosemoticDataset('test.jsonl', tokenizer)

        train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              collate_fn=collate_fn, num_workers=0, pin_memory=True)
        valid_dl = DataLoader(valid_ds, batch_size=batch_size*2, shuffle=False,
                              collate_fn=collate_fn, num_workers=0, pin_memory=True)
        test_dl  = DataLoader(test_ds,  batch_size=batch_size*2, shuffle=False,
                              collate_fn=collate_fn, num_workers=0, pin_memory=True)

        model = BiosemoticModel(**disable_flags).to(device)
        optimizer = torch.optim.AdamW([
            {'params': model.backbone.parameters(), 'lr': lr},
            {'params': model.laughter_head.parameters(), 'lr': lr*5},
        ], weight_decay=0.01)

        total_steps = len(train_dl) * epochs
        scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1*total_steps), total_steps)

        best_f1 = 0.0
        best_state = None
        wait = 0

        for epoch in range(epochs):
            # Freeze/unfreeze
            if epoch == 0:
                for p in model.backbone.parameters(): p.requires_grad = False
            else:
                for p in model.backbone.parameters(): p.requires_grad = False
                if 0 < unfreeze_layers < 12:
                    for layer in model.backbone.encoder.layer[-unfreeze_layers:]:
                        for p in layer.parameters(): p.requires_grad = True
                elif unfreeze_layers >= 12:
                    for p in model.backbone.parameters(): p.requires_grad = True
            for p in model.laughter_head.parameters(): p.requires_grad = True

            # Train
            model.train()
            epoch_loss = 0
            optimizer.zero_grad()
            for step, batch in enumerate(train_dl):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                outputs = model(input_ids, attention_mask)
                loss, losses = compute_loss(outputs, batch, pos_weight, aux_weight)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                epoch_loss += loss.item()

            # Validate
            val = evaluate(model, valid_dl, device, pos_weight, aux_weight)
            improved = val['f1'] > best_f1
            if improved:
                best_f1 = val['f1']
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                wait = 0
            else:
                wait += 1

            elapsed = (time.time() - start) / 60
            print(f"  E{epoch+1:2d}/{epochs} loss={epoch_loss/len(train_dl):.4f} "
                  f"VaF1={val['f1']:.4f} best={best_f1:.4f} "
                  f"{'★' if improved else ''} [{elapsed:.1f}m]", flush=True)

            if wait >= patience:
                print(f"  Early stop at epoch {epoch+1}")
                break

        # Test with best model
        if best_state:
            model.load_state_dict(best_state)
        test = evaluate(model, test_dl, device, pos_weight, aux_weight)

        print(f"  TEST: F1={test['f1']:.4f} P={test['precision']:.4f} R={test['recall']:.4f}")

        # Cleanup
        del model, best_state, train_ds, valid_ds, test_ds
        gc.collect(); torch.cuda.empty_cache()

        return {
            'name': name,
            'val_f1': best_f1,
            'test_f1': test['f1'],
            'test_precision': test['precision'],
            'test_recall': test['recall'],
            'time_min': round((time.time() - start)/60),
            'disabled': disabled,
        }

    except Exception as e:
        print(f"\n*** ERROR in {name}: {e}")
        _tb.print_exc()
        return {
            'name': name,
            'val_f1': 0.0,
            'test_f1': 0.0,
            'test_precision': 0.0,
            'test_recall': 0.0,
            'time_min': round((time.time() - start)/60),
            'disabled': disabled if 'disabled' in dir() else [],
            'error': str(e),
        }


