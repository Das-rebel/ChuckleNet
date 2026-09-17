=== Comedy Video Dataset for Nature Publication ===

DATA LOCATION:
  gdrive:subhajit-comedy-data/
    ├── all_comedy_ids.txt (634 video IDs)
    ├── comedy_videos/ (downloaded .m4a files)
    ├── features_1000.npz (extracted prosody features)
    ├── cascade_stage1.pt (trained XLM-R model)
    └── Scale_1000_Colab.ipynb (main pipeline)

PIPELINE:
  1. yt-dlp downloads audio from YouTube
  2. librosa extracts F0 + prosody features per 1-sec segment  
  3. F0 model (F1=0.98) pseudo-labels new data
  4. XLM-R cascade trains on pseudo-labeled data

CURRENT MODELS:
  - F0 Prosody: F1=0.98 (held-out comedians: Peters, Chappelle, C.K.)
  - Top200 Prosody: F1=0.9759
  - Ensemble: F1=0.941
  - WavLM Phase A: Val F1=0.756, Test F1=0.617

DOWNLOAD COMMAND (local, with deno + brave cookies):
  yt-dlp --cookies-from-browser brave --js-runtimes deno \
    -f 'bestaudio[ext=m4a]/bestaudio/best' \
    --extract-audio --audio-format m4a \
    -o '%(id)s.m4a' \
    'https://youtube.com/watch?v=VIDEO_ID'
