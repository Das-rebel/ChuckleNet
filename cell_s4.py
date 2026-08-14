# S4: Stream Extract: One Video at a Time → Embeddings
import torch, librosa, gc, os
from collections import defaultdict
from tqdm.auto import tqdm

# Mock utterances from S2
utterances = []

device = torch.device('cuda')
from transformers import WavLMModel
wavlm = WavLMModel.from_pretrained('microsoft/wavlm-base-plus').to(device).eval()
SR = 16000
PAD = 0.2
OUTPUT_DIR = '/content/embeddings'
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE = '/content/gdrive/MyDrive/laughter_prediction'
audio_map = {}
for lang in ['en', 'zh', 'hi-latn', 'bn', 'fr', 'es']:
    audio_dir = f'{BASE}/audio/{lang}'
    if os.path.exists(audio_dir):
        for fname in os.listdir(audio_dir):
            if fname.endswith('.mp3'):
                vid = fname.replace('.mp3', '')
                audio_map[vid] = f'{lang}/{fname}'

print(f'Audio map: {len(audio_map)} files')

video_utts = defaultdict(list)
for u in utterances:
    if u['video_id'] in audio_map:
        video_utts[u['video_id']].append(u)

videos = sorted(video_utts.keys())
print(f'Videos to process: {len(videos)}')

done = sorted([f.replace('.pt','') for f in os.listdir(OUTPUT_DIR) if f.endswith('.pt')])
start_idx = len(done)
if start_idx > 0:
    print(f'Resuming from video {start_idx}/{len(videos)}')

for vi, vid in enumerate(tqdm(videos[start_idx:], desc='Videos')):
    utts = video_utts[vid]
    try:
        full_path = f'{BASE}/audio/{audio_map[vid]}'
        y, sr = librosa.load(full_path, sr=SR, mono=True)
    except:
        torch.save({'ids': [u['utterance_id'] for u in utts], 'embs': torch.zeros(len(utts), 768)}, 
                    f'{OUTPUT_DIR}/{vid}.pt')
        continue
    
    embs, ids = [], []
    for u in utts:
        t0 = max(0, u['start'] - PAD)
        t1 = min(len(y)/SR, u['end'] + PAD)
        clip = y[int(t0*SR):int(t1*SR)]
        
        if len(clip) < int(0.1*SR):
            clip = torch.zeros(int(0.1*SR))
        else:
            clip = torch.from_numpy(clip.astype('float32'))
        
        with torch.no_grad():
            out = wavlm(clip.unsqueeze(0).to(device))
            emb = out.last_hidden_state.mean(1).squeeze(0).float().cpu()
        
        embs.append(emb)
        ids.append(u['utterance_id'])
    
    torch.save({'ids': ids, 'embs': torch.stack(embs)}, f'{OUTPUT_DIR}/{vid}.pt')
    
    del y, embs, clip, out, emb
    torch.cuda.empty_cache()
    gc.collect()

print(f'\nDone! {len(videos)} videos extracted')
