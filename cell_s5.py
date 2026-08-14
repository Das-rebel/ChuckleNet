# S5: Merge Embeddings → Save
import glob, torch, os

OUTPUT_DIR = '/content/embeddings'
all_ids, all_embs = [], []

for vf in sorted(glob.glob(f'{OUTPUT_DIR}/*.pt')):
    d = torch.load(vf, map_location='cpu')
    all_ids.extend(d['ids'])
    all_embs.append(d['embs'])
    print(f'{os.path.basename(vf)}: {d["embs"].shape[0]} embeddings')

final = torch.cat(all_embs, dim=0)
print(f'\nTotal: {final.shape}')

OUTPUT = '/content/gdrive/MyDrive/wavlm_embeddings_15k'
torch.save({
    'embeddings': final,
    'utterance_ids': all_ids,
    'model': 'microsoft/wavlm-base-plus',
    'pooling': 'mean'
}, OUTPUT)
print(f'Saved: {OUTPUT} ({os.path.getsize(OUTPUT)/1024**2:.1f} MB)')
