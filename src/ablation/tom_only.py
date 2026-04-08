"""
Theory of Mind (ToM) Only Model: BERT + Audience Modeling Head

This ablation tests whether the Theory of Mind component independently
contributes to humor recognition by modeling audience mental states.

Hypothesis: If ToM-only outperforms baseline, predicting audience
response is a key signal for humor recognition.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertModel, BertTokenizer


class TOMOnly(nn.Module):
    """
    BERT + Theory of Mind Audience Modeling Head.

    Models mental states and audience expectations to predict
    whether a given audience will appreciate the humor.

    Architecture:
    - BERT encoder
    - ToM trajectory modeling (512→256→128→1)
    - Predicts audience engagement score
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

        hidden_size = self.config.hidden_size

        self.tom_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
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
        Forward pass with ToM audience modeling.

        Predicts how likely the target audience is to find the content funny
        based on mental state trajectory modeling.
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        pooled_output = outputs.pooler_output

        audience_score = self.tom_head(pooled_output)

        logits = self.classifier(audience_score)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)

        return loss, logits, audience_score

    def predict(
        self,
        texts: list[str],
        tokenizer: BertTokenizer,
        device: str = "cpu",
    ):
        """Predict with ToM audience modeling."""
        self.eval()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            _, logits, audience_score = self.forward(**inputs)
            probs = torch.softmax(logits, dim=-1)

        return [
            {
                "text": text,
                "humor_prob": prob[1].item(),
                "audience_score": aud.item(),
            }
            for text, prob, aud in zip(texts, probs, audience_score)
        ]


def create_tom_only(model_path: str | None = None, **kwargs) -> TOMOnly:
    """Factory function for ToM-only model."""
    model = TOMOnly(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("TOMOnly - BERT + Theory of Mind Audience Modeling")
    print("=" * 50)
    print("Purpose: Test if ToM audience modeling improves humor recognition")
    print()

    model = TOMOnly()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"BERT: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"ToM Head: {sum(p.numel() for p in model.tom_head.parameters()):,}")