#!/usr/bin/env python3
"""
ChuckleNet CLI - Command Line Interface for Humor Prediction

Usage:
    chucklenet predict --text "Why did the chicken cross the road?"
    chucklenet batch --file inputs.csv
    chucklenet server --port 8000

Install:
    pip install -e . && chucklenet --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


def load_model(model_path: str | None = None, device: str = "cpu"):
    """Load the trained model."""
    if not HAS_TORCH or not HAS_TRANSFORMERS:
        print("Error: PyTorch and Transformers required")
        print("Install: pip install torch transformers")
        sys.exit(1)

    if model_path is None:
        model_path = "experiments/biosemotic_humor_bert_lr2e5/best_model"

    if not Path(model_path).exists():
        print(f"Error: Model not found at {model_path}")
        print("Please provide path to trained model or run training first.")
        sys.exit(1)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    return model, tokenizer, device


def predict_text(text: str, model, tokenizer, device: str = "cpu", threshold: float = 0.5):
    """Predict humor for a single text."""
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)

    humor_prob = probs[0][1].item()
    is_humor = humor_prob >= threshold

    return {
        "text": text,
        "humor_probability": humor_prob,
        "is_humor": is_humor,
        "confidence": "high" if abs(humor_prob - 0.5) > 0.3 else "medium" if abs(humor_prob - 0.5) > 0.15 else "low",
    }


def predict_batch(texts: list[str], model, tokenizer, device: str = "cpu", threshold: float = 0.5):
    """Predict humor for a batch of texts."""
    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)

    results = []
    for i, text in enumerate(texts):
        humor_prob = probs[i][1].item()
        results.append({
            "text": text,
            "humor_probability": humor_prob,
            "is_humor": humor_prob >= threshold,
            "confidence": "high" if abs(humor_prob - 0.5) > 0.3 else "medium" if abs(humor_prob - 0.5) > 0.15 else "low",
        })

    return results


def cmd_predict(args):
    """Single text prediction."""
    model, tokenizer, device = load_model(args.model_path, args.device)

    result = predict_text(args.text, model, tokenizer, device, args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Text: {result['text']}")
        print(f"Humor: {'YES' if result['is_humor'] else 'NO'}")
        print(f"Probability: {result['humor_probability']:.4f}")
        print(f"Confidence: {result['confidence']}")


def cmd_batch(args):
    """Batch prediction from file."""
    model, tokenizer, device = load_model(args.model_path, args.device)

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    if input_path.suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(input_path)
        if "text" in df.columns:
            texts = df["text"].tolist()
        else:
            texts = df.iloc[:, 0].tolist()
    elif input_path.suffix == ".json":
        with open(input_path) as f:
            data = json.load(f)
            texts = [item["text"] if isinstance(item, dict) else item for item in data]
    else:
        with open(input_path) as f:
            texts = [line.strip() for line in f if line.strip()]

    results = predict_batch(texts, model, tokenizer, device, args.threshold)

    humorous = sum(1 for r in results if r["is_humor"])
    print(f"Processed {len(results)} texts, {humorous} humorous ({humorous/len(results)*100:.1f}%)")

    if args.output:
        import pandas as pd
        output_df = pd.DataFrame(results)
        output_df.to_csv(args.output, index=False)
        print(f"Results saved to: {args.output}")
    elif args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            marker = "[FUNNY]" if r["is_humor"] else "[  N/A  ]"
            print(f"{marker} {r['humor_probability']:.3f} - {r['text'][:60]}...")


def cmd_server(args):
    """Start FastAPI server."""
    import uvicorn
    from src.api.main import app

    print(f"Starting ChuckleNet API server on port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="ChuckleNet CLI - Biosemiotic Humor Recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "mps"])
    parser.add_argument("--model-path", default=None, help="Path to trained model")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    predict_parser = subparsers.add_parser("predict", help="Predict single text")
    predict_parser.add_argument("--text", required=True, help="Text to analyze")
    predict_parser.add_argument("--threshold", type=float, default=0.5)

    batch_parser = subparsers.add_parser("batch", help="Batch prediction from file")
    batch_parser.add_argument("--file", required=True, help="Input file (CSV, JSON, or TXT)")
    batch_parser.add_argument("--output", help="Output file (CSV)")
    batch_parser.add_argument("--threshold", type=float, default=0.5)

    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "predict":
        cmd_predict(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "server":
        cmd_server(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()