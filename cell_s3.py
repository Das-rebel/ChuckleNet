# S3: Audio Map (sdas22 account)
import glob, os

# NOTE: 'utterances' comes from S2. Mocking it for compile test.
utterances = []

BASE = '/content/gdrive/MyDrive/laughter_prediction'
audio_map = {}
for lang in ['en', 'zh', 'hi-latn', 'bn', 'fr', 'es']:
    audio_dir = f'{BASE}/audio/{lang}'
    if os.path.exists(audio_dir):
        for fname in os.listdir(audio_dir):
            if fname.endswith('.mp3'):
                vid = fname.replace('.mp3', '')
                audio_map[vid] = f'{lang}/{fname}'

covered = sum(1 for u in utterances if u['video_id'] in audio_map)
print(f'Audio files: {len(audio_map)}, Coverage: {covered}/{len(utterances)}')

items = list(audio_map.items())[:3]
for vid, path in items:
    print(f'  {vid}: {path}')
