#!/usr/bin/env python3
"""
Theory of Mind (ToM) Layer for Intent Recognition
Models mental states and intentions of speakers in comedy contexts
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional


class TheoryOfMindLayer(nn.Module):
    """
    Theory of Mind Layer for understanding speaker intentions and beliefs

    Features:
    - Intent recognition from speech patterns
    - Belief state modeling
    - Social context understanding
    - Emotional state inference
    """

    def __init__(self, embedding_dim: int = 64, hidden_dim: int = 64):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Intent recognition network
        self.intent_network = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 8)  # 8 intent categories
        )

        # Belief state modeling
        self.belief_network = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

        # Emotional state inference
        self.emotion_network = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 6)  # 6 basic emotions
        )

    def forward(self, inputs: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass for ToM processing

        Args:
            inputs: Dictionary with 'embeddings' key [batch, seq_len, embedding_dim]

        Returns:
            Dictionary with intent, belief, and emotion predictions
        """
        embeddings = inputs['embeddings']

        # Pool embeddings across sequence
        pooled = embeddings.mean(dim=1)  # [batch, embedding_dim]

        # Intent recognition
        intents = self.intent_network(pooled)  # [batch, 8]

        # Belief state
        beliefs = self.belief_network(pooled)  # [batch, hidden_dim]

        # Emotional state
        emotions = self.emotion_network(pooled)  # [batch, 6]

        return {
            'intents': intents,
            'beliefs': beliefs,
            'emotions': emotions,
            'tom_features': pooled
        }