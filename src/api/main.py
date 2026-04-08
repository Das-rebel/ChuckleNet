"""
FastAPI Inference Service for ChuckleNet

Provides REST API endpoints for humor prediction using trained biosemiotic models.

Usage:
    uvicorn src.api.main:app --reload --port 8000

Endpoints:
- GET /health - Health check
- POST /predict - Single text prediction
- POST /batch_predict - Batch predictions
- GET /components/{component} - Individual component scores
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..ablation.full_model import FullBiosemiotic
from ..ablation.baseline_model import BaselineBERT


app = FastAPI(
    title="ChuckleNet API",
    description="Biosemiotic AI for Computational Humor Recognition",
    version="1.0.0",
)


class PredictRequest(BaseModel):
    text: str | list[str] = Field(..., description="Text or list of texts to analyze")
    model_type: str = Field(default="full", description="Model type: 'full' or 'baseline'")
    return_components: bool = Field(default=False, description="Return individual component scores")


class PredictResponse(BaseModel):
    humor_prob: float = Field(..., description="Probability of being humorous (0-1)")
    is_humor: bool = Field(..., description="Binary prediction")
    model_type: str
    components: dict | None = None


class BatchPredictRequest(BaseModel):
    texts: list[str] = Field(..., description="List of texts to analyze")
    model_type: str = Field(default="full")


class BatchPredictResponse(BaseModel):
    predictions: list[PredictResponse]
    total: int
    humorous_count: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    model_type: str | None


MODEL_REGISTRY = {
    "full": FullBiosemiotic,
    "baseline": BaselineBERT,
}


def get_device() -> str:
    """Detect available device."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(model_type: str = "full", model_path: str | None = None):
    """Load model from path or use default architecture."""
    model_class = MODEL_REGISTRY.get(model_type)
    if not model_class:
        raise ValueError(f"Unknown model type: {model_type}")

    model = model_class()

    if model_path and Path(model_path).exists():
        state_dict = torch.load(model_path, map_location=get_device())
        model.load_state_dict(state_dict)

    device = get_device()
    model.to(device)
    model.eval()

    return model, device


_model_cache: dict[str, tuple[FullBiosemiotic | BaselineBERT, str]] = {}


def get_cached_model(model_type: str = "full", model_path: str | None = None):
    """Get or load model with caching."""
    cache_key = f"{model_type}:{model_path}"

    if cache_key not in _model_cache:
        model, device = load_model(model_type, model_path)
        _model_cache[cache_key] = (model, device)

    return _model_cache[cache_key]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        model, device = get_cached_model()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            device=device,
            model_type="full",
        )
    except Exception as e:
        return HealthResponse(
            status=f"error: {str(e)}",
            model_loaded=False,
            device=get_device(),
            model_type=None,
        )


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Predict humor for a single text or list of texts.

    Returns probability and binary prediction.
    Optionally returns individual biosemiotic component scores.
    """
    try:
        model, device = get_cached_model(request.model_type)

        texts = [request.text] if isinstance(request.text, str) else request.text

        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            if request.model_type == "full":
                _, logits, head_scores = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )
                probs = torch.softmax(logits, dim=-1)

                result = PredictResponse(
                    humor_prob=probs[0][1].item(),
                    is_humor=bool(probs[0][1].item() > 0.5),
                    model_type=request.model_type,
                    components={
                        "duchenne": head_scores["duchenne"][0].item(),
                        "incongruity": head_scores["gcacu"][0].item(),
                        "audience": head_scores["tom"][0].item(),
                        "cultural": head_scores["cultural"][0].item(),
                    } if request.return_components else None,
                )
            else:
                _, logits = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )
                probs = torch.softmax(logits, dim=-1)

                result = PredictResponse(
                    humor_prob=probs[0][1].item(),
                    is_humor=bool(probs[0][1].item() > 0.5),
                    model_type=request.model_type,
                    components=None,
                )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_predict", response_model=BatchPredictResponse)
async def batch_predict(request: BatchPredictRequest):
    """Predict humor for a batch of texts."""
    try:
        model, device = get_cached_model(request.model_type)

        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

        inputs = tokenizer(
            request.texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            if request.model_type == "full":
                _, logits, head_scores = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )
            else:
                _, logits = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                )

            probs = torch.softmax(logits, dim=-1)

        predictions = []
        for i, text in enumerate(request.texts):
            predictions.append(PredictResponse(
                humor_prob=probs[i][1].item(),
                is_humor=bool(probs[i][1].item() > 0.5),
                model_type=request.model_type,
                components=None,
            ))

        return BatchPredictResponse(
            predictions=predictions,
            total=len(predictions),
            humorous_count=sum(1 for p in predictions if p.is_humor),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ChuckleNet API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "predict": "POST /predict",
            "batch_predict": "POST /batch_predict",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)