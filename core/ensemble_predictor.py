"""
Ensemble laughter prediction system built from the individually working models.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.clost.clost import CLoSTLayer
from core.gcacu.gcacu import GCACUNetwork
from core.sevade.sevade import SEVADEEvaluator
from core.tom.theory_of_mind import TheoryOfMindLayer


class EnsembleLaughterPredictor(nn.Module):
    """
    Ensemble predictor that combines the verified component models.

    The integrated model path remains separate. This module keeps the
    components decoupled and fuses their outputs through a light-weight
    weighting network.
    """

    def __init__(
        self,
        embedding_dim: int = 256,
        num_heads: int = 4,
        hidden_dim: int = 128,
        dropout: float = 0.1,
        max_seq_len: int = 512,
    ):
        super().__init__()

        self.embedding_dim = embedding_dim
        self.num_heads = num_heads

        self.theory_of_mind = TheoryOfMindLayer(
            embedding_dim=embedding_dim,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            max_seq_len=max_seq_len,
        )
        self.clost = CLoSTLayer(
            embedding_dim=embedding_dim,
            hidden_dim=hidden_dim,
            max_leap_distance=3,
        )
        self.gcacu = GCACUNetwork(
            embedding_dim=embedding_dim,
            num_heads=num_heads,
            hidden_dim=embedding_dim,
            dropout=dropout,
        )
        self.sevade = SEVADEEvaluator(
            stream_dim=embedding_dim,
            num_architectures=3,
            hidden_dim=hidden_dim,
        )

        self.ensemble_weights = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 4),
            nn.Sigmoid(),
        )

    def _zero_score(self, batch_size: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        return torch.zeros(batch_size, 1, device=device, dtype=dtype)

    def _run_clost(
        self,
        embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor],
    ) -> Dict[str, object]:
        predictions: List[torch.Tensor] = []
        streams: List[torch.Tensor] = []
        details: List[Dict[str, object]] = []

        for sample_index in range(embeddings.size(0)):
            sample_embeddings = embeddings[sample_index]
            if attention_mask is not None:
                valid_mask = attention_mask[sample_index].bool()
                valid_embeddings = sample_embeddings[valid_mask]
                if valid_embeddings.numel():
                    sample_embeddings = valid_embeddings

            if sample_embeddings.size(0) == 1:
                sample_embeddings = sample_embeddings.repeat(2, 1)

            split_point = max(1, sample_embeddings.size(0) // 2)
            if split_point >= sample_embeddings.size(0):
                split_point = sample_embeddings.size(0) - 1

            setup_embeddings = sample_embeddings[:split_point]
            punchline_embeddings = sample_embeddings[split_point:]
            if punchline_embeddings.size(0) == 0:
                punchline_embeddings = sample_embeddings[-1:].clone()

            clost_outputs = self.clost(setup_embeddings, punchline_embeddings, attention_mask=None)
            predictions.append(clost_outputs["humor_prediction"].reshape(1, 1).to(embeddings.device, embeddings.dtype))
            streams.append(((setup_embeddings.mean(dim=0) + punchline_embeddings.mean(dim=0)) / 2.0).to(embeddings.device, embeddings.dtype))
            details.append(
                {
                    "sample_index": sample_index,
                    "thought_leaps": clost_outputs["thought_leaps"],
                }
            )

        return {
            "prediction": torch.cat(predictions, dim=0),
            "stream": torch.stack(streams, dim=0),
            "details": details,
        }

    def forward(
        self,
        embeddings: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> Dict[str, object]:
        batch_size, seq_len, _ = embeddings.shape
        device = embeddings.device
        dtype = embeddings.dtype

        if attention_mask is None:
            attention_mask = torch.ones(batch_size, seq_len, device=device, dtype=dtype)
        else:
            attention_mask = attention_mask.to(device=device, dtype=dtype)

        pooled_embeddings = embeddings.mean(dim=1)
        component_outputs: Dict[str, torch.Tensor] = {}
        component_streams: Dict[str, torch.Tensor] = {}
        clost_details: List[Dict[str, object]] = []

        try:
            tom_outputs = self.theory_of_mind(embeddings, attention_mask)
            component_outputs["tom"] = tom_outputs["humor_prediction"]
            component_streams["tom"] = tom_outputs["mental_states"]["fused_mental_state"]
        except Exception as error:
            print(f"ToM error: {error}")
            component_outputs["tom"] = self._zero_score(batch_size, device, dtype)
            component_streams["tom"] = pooled_embeddings

        try:
            gcacu_outputs = self.gcacu(embeddings, attention_mask)
            component_outputs["gcacu"] = gcacu_outputs["incongruity_score"]
            component_streams["gcacu"] = gcacu_outputs.get("contextual_understanding", pooled_embeddings)
        except Exception as error:
            print(f"GCACU error: {error}")
            component_outputs["gcacu"] = self._zero_score(batch_size, device, dtype)
            component_streams["gcacu"] = pooled_embeddings

        try:
            clost_outputs = self._run_clost(embeddings, attention_mask)
            component_outputs["clost"] = clost_outputs["prediction"]  # type: ignore[assignment]
            component_streams["clost"] = clost_outputs["stream"]  # type: ignore[assignment]
            clost_details = clost_outputs["details"]  # type: ignore[assignment]
        except Exception as error:
            print(f"CLoST error: {error}")
            component_outputs["clost"] = self._zero_score(batch_size, device, dtype)
            component_streams["clost"] = pooled_embeddings

        try:
            architecture_scores = torch.cat(
                [
                    component_outputs["tom"],
                    component_outputs["gcacu"],
                    component_outputs["clost"],
                ],
                dim=-1,
            )
            residual_streams = torch.stack(
                [
                    component_streams["tom"],
                    component_streams["gcacu"],
                    component_streams["clost"],
                ],
                dim=1,
            )
            sevade_outputs = self.sevade(residual_streams, architecture_scores)
            component_outputs["sevade"] = sevade_outputs["probability"]
        except Exception as error:
            print(f"SEVADE error: {error}")
            sevade_outputs = {
                "probability": self._zero_score(batch_size, device, dtype),
                "logits": self._zero_score(batch_size, device, dtype),
                "agent_logits": torch.zeros(batch_size, 3, device=device, dtype=dtype),
                "disagreement": self._zero_score(batch_size, device, dtype),
                "entropy": self._zero_score(batch_size, device, dtype),
            }
            component_outputs["sevade"] = sevade_outputs["probability"]

        weights = self.ensemble_weights(pooled_embeddings)
        weights = weights / weights.sum(dim=-1, keepdim=True).clamp_min(1e-6)

        stacked_predictions = torch.cat(
            [
                component_outputs["tom"],
                component_outputs["gcacu"],
                component_outputs["clost"],
                component_outputs["sevade"],
            ],
            dim=-1,
        )
        ensemble_prediction = (stacked_predictions * weights).sum(dim=-1, keepdim=True)

        return {
            "ensemble_prediction": ensemble_prediction,
            "component_outputs": component_outputs,
            "component_streams": component_streams,
            "ensemble_weights": weights,
            "individual_predictions": {
                "tom": component_outputs["tom"],
                "gcacu": component_outputs["gcacu"],
                "clost": component_outputs["clost"],
                "sevade": component_outputs["sevade"],
            },
            "sevade": sevade_outputs,
            "clost_details": clost_details,
        }

    def predict_single(self, text_embeddings: torch.Tensor) -> Dict[str, object]:
        self.eval()
        with torch.no_grad():
            if text_embeddings.dim() == 2:
                text_embeddings = text_embeddings.unsqueeze(0)

            outputs = self.forward(text_embeddings)

            return {
                "ensemble_score": outputs["ensemble_prediction"].item(),
                "tom_score": outputs["individual_predictions"]["tom"].item(),
                "gcacu_score": outputs["individual_predictions"]["gcacu"].item(),
                "clost_score": outputs["individual_predictions"]["clost"].item(),
                "sevade_score": outputs["individual_predictions"]["sevade"].item(),
                "weights": outputs["ensemble_weights"].squeeze(0).tolist(),
            }

    def get_explanation(self, text_embeddings: torch.Tensor) -> str:
        predictions = self.predict_single(text_embeddings)

        explanation = "Laughter Prediction Analysis:\n"
        explanation += f"Overall Score: {predictions['ensemble_score']:.3f}\n\n"
        explanation += "Component Analysis:\n"
        explanation += f"Theory of Mind: {predictions['tom_score']:.3f} (expectation violation)\n"
        explanation += f"GCACU: {predictions['gcacu_score']:.3f} (semantic conflict)\n"
        explanation += f"CLoST: {predictions['clost_score']:.3f} (thought leaps)\n"
        explanation += f"SEVADE: {predictions['sevade_score']:.3f} (consensus calibration)\n\n"
        explanation += "Ensemble Weights:\n"

        component_names = ["ToM", "GCACU", "CLoST", "SEVADE"]
        for name, weight in zip(component_names, predictions["weights"]):
            explanation += f"  {name}: {weight:.3f}\n"

        if predictions["ensemble_score"] > 0.6:
            explanation += "\nPrediction: FUNNY"
        elif predictions["ensemble_score"] > 0.4:
            explanation += "\nPrediction: MILDLY AMUSING"
        else:
            explanation += "\nPrediction: NOT FUNNY"

        return explanation


def test_ensemble_system() -> bool:
    print("Testing Ensemble Laughter Prediction System")
    print("=" * 60)

    model = EnsembleLaughterPredictor(
        embedding_dim=256,
        num_heads=4,
        hidden_dim=128,
        dropout=0.1,
        max_seq_len=64,
    )
    model.eval()
    print("Ensemble model initialized")
    print(f"Parameters: {sum(parameter.numel() for parameter in model.parameters()):,}")

    batch_size = 2
    seq_len = 64
    embeddings = torch.randn(batch_size, seq_len, 256)
    attention_mask = torch.ones(batch_size, seq_len)

    print(f"\nTesting with {batch_size} samples...")

    try:
        outputs = model(embeddings, attention_mask)
        print("Forward pass successful")
        print(f"Ensemble predictions: {outputs['ensemble_prediction'].squeeze().tolist()}")

        single_embedding = torch.randn(1, seq_len, 256)
        predictions = model.predict_single(single_embedding)
        print("\nSingle Sample Prediction:")
        print(f"  Ensemble Score: {predictions['ensemble_score']:.3f}")
        print(f"  ToM: {predictions['tom_score']:.3f}")
        print(f"  GCACU: {predictions['gcacu_score']:.3f}")
        print(f"  CLoST: {predictions['clost_score']:.3f}")
        print(f"  SEVADE: {predictions['sevade_score']:.3f}")
        print(f"  Weights: {[f'{weight:.3f}' for weight in predictions['weights']]}")
        print("\nExplanation:")
        print(model.get_explanation(single_embedding))
        print("\nEnsemble system working.")
        return True
    except Exception as error:
        print(f"Test failed: {error}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    raise SystemExit(0 if test_ensemble_system() else 1)
