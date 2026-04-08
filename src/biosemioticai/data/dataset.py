"""
Humor Dataset Loader

Handles loading and preprocessing of humor datasets.
"""

from __future__ import annotations
import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import BertTokenizer


class HumorDataset(Dataset):
    """
    Dataset for humor recognition training and evaluation.
    """

    def __init__(
        self,
        data_path: str,
        tokenizer: BertTokenizer,
        max_length: int = 128,
    ):
        self.data = pd.read_csv(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length

        required_cols = ["text", "label"]
        if not all(col in self.data.columns for col in required_cols):
            raise ValueError(f"Data must contain: {required_cols}")

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> dict:
        row = self.data.iloc[idx]
        text = str(row["text"])
        label = int(row["label"])

        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "label": torch.tensor(label, dtype=torch.long),
        }
