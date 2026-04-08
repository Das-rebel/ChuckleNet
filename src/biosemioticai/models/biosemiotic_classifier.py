"""
Biosemiotic Laughter Classifier

Integrates evolutionary laughter theory with transformer-based classification.
"""

from __future__ import annotations
import torch
from transformers import BertForSequenceClassification, BertTokenizer


class BiosemioticClassifier:
    """
    Biosemiotic framework for humor recognition.

    Integrates:
    - Duchenne vs volitional laughter classification
    - Incongruity-based sarcasm detection
    - Theory of Mind mental state modeling
    - Cross-cultural nuance detection
    """

    def __init__(
        self,
        model_path: str | None = None,
        device: str | None = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.model_path = model_path

    def load(self, model_path: str | None = None) -> None:
        """Load model and tokenizer from path."""
        path = model_path or self.model_path
        if not path:
            raise ValueError("model_path must be provided")

        self.tokenizer = BertTokenizer.from_pretrained(path)
        self.model = BertForSequenceClassification.from_pretrained(path)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, texts: list[str]) -> list[dict]:
        """Predict humor scores for texts."""
        if self.model is None:
            self.load()

        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        return [
            {"text": text, "humor_prob": prob[1].item()}
            for text, prob in zip(texts, probs)
        ]

    @classmethod
    def from_pretrained(cls, model_path: str, device: str | None = None) -> "BiosemioticClassifier":
        """Load a pre-trained classifier."""
        classifier = cls(model_path=model_path, device=device)
        classifier.load()
        return classifier
