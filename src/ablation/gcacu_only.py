"""
GCACU-Only Model: BERT + Incongruity Detection Head

This ablation tests whether the GCACU (Generalized Cognitive Architecture
for Conceptual Understanding) incongruity detection component independently
contributes to humor recognition.

Hypothesis: If GCACU-only outperforms baseline, semantic incongruity
detection is a key signal for humor recognition.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertModel, BertTokenizer


class GCACUOnly(nn.Module):
    """
    BERT + GCACU Incongruity Detection Head.

    Detects semantic conflicts and incongruity patterns that underlie humor.
    Uses attention weights to identify conceptual mismatches.

    Architecture:
    - BERT encoder
    - Attention pooling over all tokens (not just [CLS])
    - GCACU incongruity head (512→256→1)
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

        self.attention_pool = nn.Linear(hidden_size, 1)

        self.gcacu_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
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
        Forward pass with GCACU incongruity detection.

        Uses attention pooling to capture incongruity across entire sequence,
        not just the [CLS] token representation.
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        sequence_output = outputs.last_hidden_state  # [batch, seq_len, hidden]

        attention_weights = self.attention_pool(sequence_output)
        attention_weights = attention_weights.squeeze(-1)

        attention_mask_expanded = attention_mask.unsqueeze(-1).float()
        attention_weights = attention_weights.masked_fill(
            attention_mask_expanded.squeeze(-1) == 0, float("-inf")
        )
        attention_weights = torch.softmax(attention_weights, dim=-1)

        weighted_output = torch.sum(sequence_output * attention_weights.unsqueeze(-1), dim=1)

        incongruity_score = self.gcacu_head(weighted_output)

        logits = self.classifier(incongruity_score)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)

        return loss, logits, incongruity_score

    def predict(
        self,
        texts: list[str],
        tokenizer: BertTokenizer,
        device: str = "cpu",
    ):
        """Predict with GCACU incongruity detection."""
        self.eval()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            _, logits, incongruity_score = self.forward(**inputs)
            probs = torch.softmax(logits, dim=-1)

        return [
            {
                "text": text,
                "humor_prob": prob[1].item(),
                "incongruity_score": inc.item(),
            }
            for text, prob, inc in zip(texts, probs, incongruity_score)
        ]


def create_gcacu_only(model_path: str | None = None, **kwargs) -> GCACUOnly:
    """Factory function for GCACU-only model."""
    model = GCACUOnly(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("GCACUOnly - BERT + Incongruity Detection")
    print("=" * 50)
    print("Purpose: Test if GCACU incongruity detection improves humor recognition")
    print()

    model = GCACUOnly()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"BERT: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"GCACU Head: {sum(p.numel() for p in model.gcacu_head.parameters()):,}")