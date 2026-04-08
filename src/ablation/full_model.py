"""
Full Biosemiotic Model: Complete Integration of All Heads

This is the full model with all biosemiotic components:
- Duchenne Laughter Detection
- GCACU Incongruity Detection
- Theory of Mind Audience Modeling
- Cultural Adapter

This represents the complete ChuckleNet architecture.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertModel, BertTokenizer


class FullBiosemiotic(nn.Module):
    """
    Full Biosemiotic Humor Recognition Model.

    Integrates all four biosemiotic components with attention-based
    fusion for comprehensive humor detection.

    Architecture:
    - BERT encoder (768 dim)
    - Duchenne head (768→512→1)
    - GCACU head (768→512→256→1)
    - ToM head (768→512→256→64→1)
    - Cultural head (768→512→256→4 cultures)
    - Attention fusion layer (4→1)
    """

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
        self.hidden_dim = hidden_dim
        self.num_cultures = num_cultures

        hidden_size = self.config.hidden_size  # 768

        self.duchenne_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

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

        self.attention_fusion = nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

        self.classifier = nn.Sequential(
            nn.Linear(1, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 2),
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
    ):
        """
        Full forward pass with all biosemiotic heads.

        Returns:
            loss: Cross-entropy loss if labels provided
            logits: [batch, 2] for binary classification
            head_scores: dict with scores from each head
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        pooled_output = outputs.pooler_output

        duchenne_score = self.duchenne_head(pooled_output)
        gcacu_score = self.gcacu_head(pooled_output)
        tom_score = self.tom_head(pooled_output)

        cultural_probs = self.cultural_head(pooled_output)
        cultural_embedding = torch.cat([pooled_output, cultural_probs], dim=-1)
        nuance_score = self.nuance_predictor(cultural_embedding)

        head_scores = torch.cat(
            [duchenne_score, gcacu_score, tom_score, nuance_score],
            dim=-1,
        )

        fused_score = self.attention_fusion(head_scores)

        logits = self.classifier(fused_score)

        loss = None
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            loss = loss_fn(logits, labels)

        return loss, logits, {
            "duchenne": duchenne_score,
            "gcacu": gcacu_score,
            "tom": tom_score,
            "cultural": nuance_score,
            "fused": fused_score,
        }

    def predict(
        self,
        texts: list[str],
        tokenizer: BertTokenizer,
        device: str = "cpu",
    ):
        """Predict with full biosemiotic model."""
        self.eval()
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            _, logits, head_scores = self.forward(**inputs)
            probs = torch.softmax(logits, dim=-1)

        return [
            {
                "text": text,
                "humor_prob": prob[1].item(),
                "duchenne_prob": hs["duchenne"].item(),
                "incongruity_prob": hs["gcacu"].item(),
                "audience_prob": hs["tom"].item(),
                "cultural_prob": hs["cultural"].item(),
            }
            for text, prob, hs in zip(texts, probs, head_scores["fused"])
        ]


def create_full_model(model_path: str | None = None, **kwargs) -> FullBiosemiotic:
    """Factory function for full biosemiotic model."""
    model = FullBiosemiotic(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("FullBiosemiotic - Complete ChuckleNet Architecture")
    print("=" * 50)
    print("Components:")
    print("  - Duchenne Laughter Detection")
    print("  - GCACU Incongruity Detection")
    print("  - Theory of Mind Audience Modeling")
    print("  - Cultural Adapter")
    print()

    model = FullBiosemiotic()
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"BERT: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"Trainable heads: {sum(p.numel() for p in [model.duchenne_head, model.gcacu_head, model.tom_head, model.cultural_head, model.attention_fusion])}")