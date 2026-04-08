"""
Cultural Adapter Only Model: BERT + Cultural Nuance Head

This ablation tests whether the Cultural Adapter component independently
contributes to humor recognition by adapting to cultural contexts.

Hypothesis: If Cultural-only outperforms baseline, cultural adaptation
is a key signal for humor recognition.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertModel, BertTokenizer


class CulturalOnly(nn.Module):
    """
    BERT + Cultural Adapter Head.

    Detects cultural context and adjusts humor recognition thresholds
    based on cultural norms and comedy styles.

    Architecture:
    - BERT encoder
    - Cultural embedding extraction
    - Cultural nuance head (512→256→4) for regional styles
    - Adaptive threshold adjustment
    """

    REGIONAL_STYLES = 4

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        hidden_dim: int = 512,
        dropout: float = 0.1,
        num_cultures: int = 4,
    ):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.config = self.bert.config
        self.num_cultures = num_cultures

        hidden_size = self.config.hidden_size

        self.cultural_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_cultures),
            nn.Softmax(dim=-1),
        )

        self.nuance_predictor = nn.Sequential(
            nn.Linear(hidden_size + num_cultures, hidden_dim),
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
        Forward pass with Cultural Nuance Detection.

        First predicts cultural context (Western, Eastern, etc.)
        Then uses cultural embedding to predict humor appropriateness.
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        pooled_output = outputs.pooler_output

        cultural_probs = self.cultural_head(pooled_output)

        cultural_embedding = torch.cat(
            [pooled_output, cultural_probs],
            dim=-1,
        )

        nuance_score = self.nuance_predictor(cultural_embedding)

        logits = self.classifier(nuance_score)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)

        return loss, logits, nuance_score

    def predict(
        self,
        texts: list[str],
        tokenizer: BertTokenizer,
        device: str = "cpu",
    ):
        """Predict with Cultural Nuance detection."""
        self.eval()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            _, logits, nuance_score = self.forward(**inputs)
            probs = torch.softmax(logits, dim=-1)

        return [
            {
                "text": text,
                "humor_prob": prob[1].item(),
                "nuance_score": nu.item(),
            }
            for text, prob, nu in zip(texts, probs, nuance_score)
        ]


def create_cultural_only(model_path: str | None = None, **kwargs) -> CulturalOnly:
    """Factory function for Cultural-only model."""
    model = CulturalOnly(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("CulturalOnly - BERT + Cultural Nuance Detection")
    print("=" * 50)
    print("Purpose: Test if cultural adaptation improves humor recognition")
    print()

    model = CulturalOnly()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"BERT: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"Cultural Head: {sum(p.numel() for p in model.cultural_head.parameters()):,}")
    print(f"Nuance Predictor: {sum(p.numel() for p in model.nuauce_predictor.parameters()):,}")