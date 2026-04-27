import subprocess, os

MODEL_DIR = "/tmp/xlm-roberta-base-ms"
os.makedirs(MODEL_DIR, exist_ok=True)

BASE = "https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main"
FILES = [
    "config.json",
    "model.safetensors",  # 1.12 GB
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.json",
    "merges.txt",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "flax_model.msgpack",
    "rust_model.ot",
    "tf_model.h5",
]

print(f"Downloading XLM-RoBERTa to {MODEL_DIR}...")
for f in FILES:
    dst = f"{MODEL_DIR}/{f}"
    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
        print(f"  Downloading {f}...", end="", flush=True)
        r = subprocess.run(
            ["wget", "-q", "--show-progress", "-O", dst, f"{BASE}/{f}"],
            capture_output=True, text=True, timeout=300
        )
        if r.returncode != 0:
            print(f" FAILED: {r.stderr[:100]}")
            # Try without --show-progress
            r = subprocess.run(
                ["wget", "-q", "-O", dst, f"{BASE}/{f}"],
                capture_output=True, text=True, timeout=300
            )
        size = os.path.getsize(dst) if os.path.exists(dst) else 0
        print(f" {size/1024/1024:.1f} MB")
    else:
        size = os.path.getsize(dst)
        print(f"  {f}: already exists ({size/1024/1024:.1f} MB)")

print(f"\nAll files in {MODEL_DIR}:")
for f in sorted(os.listdir(MODEL_DIR)):
    size = os.path.getsize(f"{MODEL_DIR}/{f}")
    print(f"  {f}: {size/1024/1024:.1f} MB")

print("\nModel ready!")
