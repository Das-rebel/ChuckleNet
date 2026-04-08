"""
Baseline Model: Pure BERT without any biosemiotic heads

This is the control experiment - standard BERT fine-tuning
for binary humor classification without any specialized heads.

Purpose: Establish baseline to measure if biosemiotic components
actually add value beyond standard BERT fine-tuning.
"""

from __future__ import annotations

import torch
from torch import nn
from transformers import BertForSequenceClassification, BertTokenizer


class BaselineBERT(nn.Module):
    """
    Standard BERT fine-tuning baseline.

    Architecture: BERT → [CLS] token → Classification Head → Binary output

    This represents the "traditional" approach that most NLP systems use.
    No specialized humor theory components - just pattern matching.
    """

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        num_labels: int = 2,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.bert = BertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
        )
        self.config = self.bert.config
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
    ):
        """
        Forward pass.

        Args:
            input_ids: Tokenized input text [batch, seq_len]
            attention_mask: Attention mask [batch, seq_len]
            labels: Ground truth labels [batch] (optional)

        Returns:
            loss: Cross-entropy loss if labels provided
            logits: Raw model outputs [batch, num_labels]
        """
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )
        return outputs.loss, outputs.logits

    def predict(self, texts: list[str], tokenizer: BertTokenizer, device: str = "cpu"):
        """
        Predict humor probability for texts.

        Args:
            texts: List of input texts
            tokenizer: BERT tokenizer
            device: Computation device

        Returns:
            List of dicts with text and humor probability
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
            outputs = self.bert(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        return [
            {"text": text, "humor_prob": prob[1].item()}
            for text, prob in zip(texts, probs)
        ]


def create_baseline(model_path: str | None = None, **kwargs) -> BaselineBERT:
    """
    Factory function to create baseline model.

    Args:
        model_path: Optional path to load saved weights
        **kwargs: Additional arguments for BaselineBERT

    Returns:
        Initialized baseline model
    """
    model = BaselineBERT(**kwargs)
    if model_path:
        state_dict = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state_dict)
    return model


if __name__ == "__main__":
    print("BaselineBERT - Pure BERT fine-tuning")
    print("=" * 50)
    print("Purpose: Control experiment for ablation study")
    print("Hypothesis: Biosemiotic heads should outperform this baseline")
    print()

    model = BaselineBERT()
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"BERT parameters: {sum(p.numel() for p in model.bert.parameters()):,}")
    print(f"Trainable (classification head): {sum(p.numel() for p in model.bert.classifier.parameters()):,}")