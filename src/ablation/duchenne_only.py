"""
Duchenne-Only Model: BERT + Duchenne Laughter Detection Head

This ablation variant tests whether the Duchenne marker component
(spontaneous vs volitional laughter classification) independently
contributes to humor recognition performance.

Hypothesis: If Duchenne-only outperforms baseline, it suggests that
distinguishing genuine from fake laughter is a key signal for humor.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertModel, BertTokenizer


class DuchenneOnly(nn.Module):
    """
    BERT + Duchenne Laughter Detection Head.

    This model adds a specialized head that classifies whether
    text would elicit genuine (Duchenne) laughter vs volitional laughter.

    The head uses:
    - BERT encoder output (768 dim)
    - Duchenne-specific feature extraction
    - Binary classification (genuine_humor vs not_humor)
    """

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        hidden_dim: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.config = self.bert.config

        hidden_size = self.config.hidden_size  # 768 for bert-base

        self.duchenne_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

        self.classifier = nn.Linear(1, 2)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
    ):
        """
        Forward pass with Duchenne classification.

        Args:
            input_ids: Tokenized input [batch, seq_len]
            attention_mask: Attention mask [batch, seq_len]
            labels: Binary labels for humor (optional)

        Returns:
            loss: Loss if labels provided
            logits: [batch, 2] for binary classification
            duchenne_score: [batch, 1] Duchenne probability
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        pooled_output = outputs.pooler_output  # [CLS] token representation

        duchenne_score = self.duchenne_head(pooled_output)

        logits = self.classifier(duchenne_score)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)

        return loss, logits, duchenne_score

    def predict(
        self,
        texts: list[str],
        tokenizer: BertTokenizer,
        device: str = "cpu",
    ):
        """
        Predict with Duchenne detection.

        Returns dict with:
        - text
        - humor_prob
        - duchenne_prob (genuine vs fake laughter score)
        """
        self.eval()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            _, logits, duchenne_score = self.forward(**inputs)
            probs = torch.softmax(logits, dim=-1)

        return [
            {
                "text": text,
                "humor_prob": prob[1].item(),
                "duchenne_prob": ds.item(),
            }
            for text, prob, ds in zip(texts, probs, duchenne_score)
        ]


def create_duchenne_only(model_path: str | None = None, **kwargs) -> DuchenneOnly:
    """Factory function for Duchenne-only model."""
    model = DuchenneOnly(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("DuchenneOnly - BERT + Duchenne Laughter Detection")
    print("=" * 50)
    print("Purpose: Test if Duchenne marker independently improves humor detection")
    print()

    model = DuchenneOnly()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"BERT: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"Duchenne Head: {sum(p.numel() for p in model.duchenne_head.parameters()):,}")