# Step 1: Install and use ModelScope to download XLM-RoBERTa (no rate limits)
import subprocess, sys, os

print("Installing ModelScope...")
subprocess.run([sys.executable, "-m", "pip", "install", "modelscope", "-q"], check=True)

from modelscope.hub.snapshot_download import snapshot_download

print("Downloading XLM-RoBERTa from ModelScope (no rate limits)...")
MODEL_DIR = "/tmp/xlm-roberta-base"
if not os.path.exists(f"{MODEL_DIR}/model.safetensors"):
    cache_dir = snapshot_download(
        'iic/xlm-roberta-base',
        cache_dir='/tmp/modelscope_cache'
    )
    print(f"Model cached at: {cache_dir}")
else:
    print(f"Model already exists at {MODEL_DIR}")

# Move to expected location
import shutil
model_path = f"/tmp/modelscope_cache/iic/xlm-roberta-base"
if os.path.exists(model_path) and not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR, exist_ok=True)
    for f in os.listdir(model_path):
        shutil.copy(f"{model_path}/{f}", f"{MODEL_DIR}/{f}")
    print(f"Moved model to {MODEL_DIR}")

print(f"Model files in {MODEL_DIR}:")
for f in os.listdir(MODEL_DIR):
    size = os.path.getsize(f"{MODEL_DIR}/{f}")
    print(f"  {f}: {size/1024/1024:.1f} MB")

print("\nModel download complete! Now running V8...")
# Step 2: Now download and run V8
subprocess.run(["wget", "-q", "https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data/colab_biosemotic_ablation_v8.py", "-O", "v8.py"], check=True)
exec(open("v8.py").read())
