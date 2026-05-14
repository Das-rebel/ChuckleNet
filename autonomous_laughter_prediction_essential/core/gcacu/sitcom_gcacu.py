#!/usr/bin/env python3
"""
GCACU (General Comedy Analysis and Categorization Unit) - Sitcom Adaptation
Specialized version of GCACU for sitcom humor analysis with laugh track integration
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

@dataclass
class SitcomHumorFeatures:
    """Humor features specific to sitcom format"""
    dialogue_features: torch.Tensor  # Dialogue content features
    laugh_features: torch.Tensor     # Laugh track features
    character_features: torch.Tensor # Character-specific features
    timing_features: torch.Tensor    # Timing and rhythm features
    context_features: torch.Tensor   # Context and trope features

@dataclass
class GCACUSitcomOutput:
    """Output from GCACU sitcom analysis"""
    incongruity_score: float        # Semantic incongruity detection
    importance_score: float         # Importance ranking for humor
    humor_probability: float        # Overall humor likelihood
    laugh_prediction: float         # Predicted laugh response
    character_contribution: Dict[str, float]  # Character-specific contributions
    trope_confidence: Dict[str, float]        # Sitcom trope confidence scores

class SitcomGCACU(nn.Module):
    """
    GCACU Network adapted for sitcom humor analysis with laugh track integration

    Key Adaptations for Sitcom Format:
    - Multi-character dialogue processing
    - Laugh track correlation analysis
    - Ensemble cast dynamics modeling
    - Sitcom trope detection
    - Character relationship modeling
    """

    def __init__(self,
                 embedding_dim: int = 256,
                 num_heads: int = 4,
                 num_characters: int = 8,
                 num_tropes: int = 5,
                 hidden_dim: int = 128,
                 dropout: float = 0.1):
        """
        Initialize Sitcom-Adapted GCACU Network

        Args:
            embedding_dim: Dimension of input embeddings
            num_heads: Number of attention heads
            num_characters: Number of characters to track
            num_tropes: Number of sitcom tropes to detect
            hidden_dim: Hidden layer dimension
            dropout: Dropout rate for regularization
        """
        super(SitcomGCACU, self).__init__()

        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.num_characters = num_characters
        self.num_tropes = num_tropes

        # Multi-head attention for dialogue analysis
        self.dialogue_attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )

        # Laugh track integration network
        self.laugh_integration = nn.Sequential(
            nn.Linear(embedding_dim + 4, hidden_dim),  # +4 for laugh features
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embedding_dim)
        )

        # Character-specific processing
        self.character_embeddings = nn.Embedding(num_characters, embedding_dim)
        self.character_interaction = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=num_heads // 2,  # Fewer heads for character interactions
            dropout=dropout,
            batch_first=True
        )

        # Sitcom trope detection
        self.trope_detector = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_tropes),
            nn.Sigmoid()  # Multi-label classification for tropes
        )

        # Incongruity detection (adapted for sitcom dialogue)
        self.incongruity_detector = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),  # Pairwise incongruity
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Importance scoring for humor ranking
        self.importance_scorer = nn.Sequential(
            nn.Linear(embedding_dim + num_tropes, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Humor prediction combining all features
        # Input: embedding_dim (dialogue) + embedding_dim (laugh) + num_tropes + 4 (laugh_features)
        humor_input_size = embedding_dim * 2 + num_tropes + 4
        self.humor_predictor = nn.Sequential(
            nn.Linear(humor_input_size, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Laugh prediction based on all features
        # Input: embedding_dim + num_tropes
        laugh_input_size = embedding_dim + num_tropes
        self.laugh_predictor = nn.Sequential(
            nn.Linear(laugh_input_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Layer normalization for stability
        self.layer_norm = nn.LayerNorm(embedding_dim)
        self.dropout = nn.Dropout(dropout)

        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def forward(self,
                dialogue_embeddings: torch.Tensor,
                laugh_features: torch.Tensor,
                character_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> GCACUSitcomOutput:
        """
        Forward pass of Sitcom-Adapted GCACU

        Args:
            dialogue_embeddings: Dialogue text embeddings [batch, seq_len, embedding_dim]
            laugh_features: Laugh track features [batch, seq_len, 4] (intensity, duration, timing, type)
            character_ids: Character identifiers [batch, seq_len]
            attention_mask: Attention mask for padding [batch, seq_len]

        Returns:
            GCACUSitcomOutput with comprehensive humor analysis
        """
        batch_size, seq_len, _ = dialogue_embeddings.shape

        # Process dialogue with self-attention
        key_padding_mask = None
        if attention_mask is not None:
            # Convert boolean mask to float mask for attention
            key_padding_mask = (attention_mask == 0)

        dialogue_context, _ = self.dialogue_attention(
            dialogue_embeddings,
            dialogue_embeddings,
            dialogue_embeddings,
            key_padding_mask=key_padding_mask
        )
        dialogue_context = self.layer_norm(dialogue_context + dialogue_embeddings)

        # Integrate laugh track features
        laugh_enhanced = self._integrate_laugh_features(dialogue_context, laugh_features)

        # Process character-specific features
        character_embeddings = self.character_embeddings(character_ids)
        character_context, _ = self.character_interaction(
            character_embeddings,
            character_embeddings,
            character_embeddings,
            key_padding_mask=key_padding_mask
        )

        # Combine dialogue and character features
        combined_features = dialogue_context + character_context

        # Detect sitcom tropes
        trope_scores = self.trope_detector(combined_features)  # [batch, seq_len, num_tropes]

        # Calculate incongruity (dialogue vs laugh track)
        incongruity_scores = self._calculate_incongruity(dialogue_context, laugh_enhanced)

        # Score importance of each segment
        # Fix dimension mismatch by ensuring proper tensor dimensions
        trope_features = trope_scores  # [batch, seq_len, num_tropes]
        importance_input = torch.cat([combined_features, trope_features], dim=-1)
        importance_scores = self.importance_scorer(importance_input)

        # Predict humor probability
        humor_features = torch.cat([
            combined_features.mean(dim=1),  # Average dialogue [batch, embedding_dim]
            laugh_enhanced.mean(dim=1),     # Average laugh [batch, embedding_dim]
            trope_scores.mean(dim=1),       # Average tropes [batch, num_tropes]
            laugh_features.mean(dim=1)      # Average laugh features [batch, 4]
        ], dim=-1)

        # Debug: print shapes
        # print(f"Humor features shape: {humor_features.shape}")

        humor_probability = self.humor_predictor(humor_features)

        # Predict laugh response
        laugh_prediction_features = torch.cat([
            combined_features.mean(dim=1),  # [batch, embedding_dim]
            trope_scores.mean(dim=1)        # [batch, num_tropes]
        ], dim=-1)  # [batch, embedding_dim + num_tropes]

        # Debug: print shapes
        # print(f"Laugh prediction features shape: {laugh_prediction_features.shape}")

        laugh_prediction = self.laugh_predictor(laugh_prediction_features)

        # Calculate character contributions
        character_contributions = self._calculate_character_contributions(
            character_context, importance_scores
        )

        # Format trope confidence scores
        trope_confidence = self._format_trope_confidence(trope_scores)

        # Debug shapes
        # print(f"Humor probability shape: {humor_probability.shape}")
        # print(f"Laugh prediction shape: {laugh_prediction.shape}")

        return GCACUSitcomOutput(
            incongruity_score=incongruity_scores.mean().item() if incongruity_scores.nelement() > 0 else 0.0,
            importance_score=importance_scores.mean().item() if importance_scores.nelement() > 0 else 0.0,
            humor_probability=humor_probability.flatten()[0].item() if humor_probability.nelement() > 0 else 0.0,
            laugh_prediction=laugh_prediction.flatten()[0].item() if laugh_prediction.nelement() > 0 else 0.0,
            character_contribution=character_contributions,
            trope_confidence=trope_confidence
        )

    def _integrate_laugh_features(self, dialogue_context: torch.Tensor,
                                 laugh_features: torch.Tensor) -> torch.Tensor:
        """Integrate laugh track features with dialogue context"""
        # Concatenate dialogue and laugh features
        combined = torch.cat([dialogue_context, laugh_features], dim=-1)

        # Process through integration network
        laugh_enhanced = self.laugh_integration(combined)

        return self.layer_norm(laugh_enhanced + dialogue_context)

    def _calculate_incongruity(self, dialogue_context: torch.Tensor,
                             laugh_enhanced: torch.Tensor) -> torch.Tensor:
        """Calculate incongruity between dialogue and laugh track"""
        # Pairwise comparison between dialogue and laugh-enhanced features
        combined = torch.cat([dialogue_context, laugh_enhanced], dim=-1)

        # Reshape for pairwise calculation
        batch_size, seq_len, embedding_dim = dialogue_context.shape
        combined_flat = combined.view(batch_size * seq_len, -1)

        # Calculate incongruity scores
        incongruity = self.incongruity_detector(combined_flat)
        incongruity = incongruity.view(batch_size, seq_len, 1)

        return incongruity.squeeze(-1)

    def _calculate_character_contributions(self,
                                         character_context: torch.Tensor,
                                         importance_scores: torch.Tensor) -> Dict[str, float]:
        """Calculate each character's contribution to humor"""
        contributions = {}

        # Average importance per character
        for char_id in range(self.num_characters):
            char_mask = (character_context.argmax(dim=-1) == char_id).float()
            if char_mask.sum() > 0:
                char_importance = (importance_scores.squeeze(-1) * char_mask).sum() / char_mask.sum()
                contributions[f'character_{char_id}'] = char_importance.item()

        return contributions

    def _format_trope_confidence(self, trope_scores: torch.Tensor) -> Dict[str, float]:
        """Format trope confidence scores"""
        trope_names = [
            'nerd_culture',
            'social_awkwardness',
            'intellectual_humor',
            'relationship_comedy',
            'roommate_conflicts'
        ]

        confidence = {}
        avg_scores = trope_scores.mean(dim=0).mean(dim=0)  # Average over batch and sequence

        for i, trope_name in enumerate(trope_names):
            if i < avg_scores.shape[0]:
                confidence[trope_name] = avg_scores[i].item()

        return confidence

    def train_with_sitcom_data(self,
                              dialogues: List[str],
                              laugh_tracks: List[Dict[str, float]],
                              character_ids: List[int],
                              humor_scores: List[float],
                              optimizer: torch.optim.Optimizer,
                              criterion: nn.Module) -> Dict[str, float]:
        """
        Train the network with sitcom data

        Args:
            dialogues: List of dialogue texts
            laugh_tracks: List of laugh track features
            character_ids: List of character IDs
            humor_scores: Ground truth humor scores
            optimizer: Optimizer for training
            criterion: Loss function

        Returns:
            Training metrics dictionary
        """
        self.train()

        # Convert inputs to tensors (simplified - would use proper tokenization)
        dialogue_embeddings = torch.randn(len(dialogues), 32, self.embedding_dim)
        laugh_features = self._prepare_laugh_features(laugh_tracks)
        character_tensor = torch.tensor(character_ids).unsqueeze(1).expand(-1, 32)
        attention_mask = torch.ones(len(dialogues), 32)

        # Forward pass
        outputs = self.forward(dialogue_embeddings, laugh_features, character_tensor, attention_mask)

        # Calculate loss
        predicted_scores = outputs.humor_probability
        target_scores = torch.tensor(humor_scores, dtype=torch.float32)

        # Combine multiple losses
        humor_loss = criterion(predicted_scores, target_scores)
        laugh_loss = criterion(torch.tensor(outputs.laugh_prediction), target_scores.mean())

        total_loss = humor_loss + 0.3 * laugh_loss

        # Backward pass
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return {
            'total_loss': total_loss.item(),
            'humor_loss': humor_loss.item(),
            'laugh_loss': laugh_loss.item(),
            'predicted_humor': predicted_scores.item(),
            'target_humor': target_scores.mean().item()
        }

    def _prepare_laugh_features(self, laugh_tracks: List[Dict[str, float]]) -> torch.Tensor:
        """Prepare laugh features tensor from laugh track data"""
        batch_size = len(laugh_tracks)
        seq_len = 32  # Fixed sequence length
        feature_dim = 4  # intensity, duration, timing, type

        laugh_features = torch.zeros(batch_size, seq_len, feature_dim)

        for i, laugh_data in enumerate(laugh_tracks):
            if laugh_data:
                laugh_features[i, 0, 0] = laugh_data.get('intensity', 0.5)
                laugh_features[i, 0, 1] = laugh_data.get('duration', 1.0)
                laugh_features[i, 0, 2] = laugh_data.get('timing', 1.0)
                laugh_features[i, 0, 3] = laugh_data.get('type', 0.5)

        return laugh_features

    def analyze_sitcom_scene(self,
                            scene_dialogues: List[Dict[str, Any]],
                            scene_laughs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a complete sitcom scene

        Args:
            scene_dialogues: List of dialogue dictionaries
            scene_laughs: List of laugh track data

        Returns:
            Comprehensive scene analysis
        """
        self.eval()

        with torch.no_grad():
            # Prepare inputs
            dialogue_embeddings = torch.randn(1, len(scene_dialogues), self.embedding_dim)
            laugh_features = self._prepare_scene_laugh_features(scene_laughs, len(scene_dialogues))
            character_ids = self._prepare_character_ids(scene_dialogues)
            attention_mask = torch.ones(1, len(scene_dialogues))

            # Forward pass
            outputs = self.forward(dialogue_embeddings, laugh_features, character_ids, attention_mask)

            # Format analysis results
            analysis = {
                'scene_humor_score': outputs.humor_probability,
                'predicted_laugh_response': outputs.laugh_prediction,
                'incongruity_detected': outputs.incongruity_score > 0.5,
                'importance_ranking': outputs.importance_score,
                'character_contributions': outputs.character_contribution,
                'detected_tropes': outputs.trope_confidence,
                'scene_quality': self._assess_scene_quality(outputs)
            }

            return analysis

    def _prepare_scene_laugh_features(self, scene_laughs: List[Dict[str, Any]],
                                    num_dialogues: int) -> torch.Tensor:
        """Prepare laugh features for a scene"""
        laugh_features = torch.zeros(1, num_dialogues, 4)

        for i, laugh in enumerate(scene_laughs[:num_dialogues]):
            if i < num_dialogues and laugh:
                laugh_features[0, i, 0] = laugh.get('intensity', 0.5)
                laugh_features[0, i, 1] = laugh.get('duration', 1.0)
                laugh_features[0, i, 2] = laugh.get('response_time', 1.0)
                laugh_features[0, i, 3] = hash(laugh.get('type', 'laughter')) % 10 / 10.0

        return laugh_features

    def _prepare_character_ids(self, scene_dialogues: List[Dict[str, Any]]) -> torch.Tensor:
        """Prepare character IDs for a scene"""
        character_map = {
            'sheldon_cooper': 0,
            'leonard_hofstadter': 1,
            'penny': 2,
            'howard_wolowitz': 3,
            'raj_koothrappali': 4,
            'amy_fowler': 5,
            'bernadette_rostenkowski': 6,
            'stuart_bloom': 7
        }

        character_ids = []
        for dialogue in scene_dialogues:
            character = dialogue.get('character', 'unknown')
            char_id = character_map.get(character, 0)
            character_ids.append(char_id)

        # Pad to fixed length if needed
        while len(character_ids) < 32:
            character_ids.append(0)

        character_tensor = torch.tensor(character_ids)[:32].unsqueeze(0)
        return character_tensor

    def _assess_scene_quality(self, outputs: GCACUSitcomOutput) -> str:
        """Assess overall scene quality based on outputs"""
        humor_score = outputs.humor_probability
        laugh_pred = outputs.laugh_prediction
        incongruity = outputs.incongruity_score

        if humor_score > 0.7 and laugh_pred > 0.6:
            return "excellent"
        elif humor_score > 0.5 and laugh_pred > 0.4:
            return "good"
        elif humor_score > 0.3:
            return "moderate"
        else:
            return "weak"

def main():
    """Main function for testing the Sitcom GCACU"""
    print("🎭 GCACU Sitcom Adaptation")
    print("=" * 50)

    # Initialize network
    network = SitcomGCACU(
        embedding_dim=256,
        num_heads=4,
        num_characters=8,
        num_tropes=5
    )

    print("✅ Sitcom-Adapted GCACU Network initialized")
    print(f"📊 Parameters: {sum(p.numel() for p in network.parameters()):,}")

    # Test with sample data
    batch_size = 2
    seq_len = 32
    dialogue_embeddings = torch.randn(batch_size, seq_len, 256)
    laugh_features = torch.randn(batch_size, seq_len, 4)
    character_ids = torch.randint(0, 8, (batch_size, seq_len))
    attention_mask = torch.ones(batch_size, seq_len)

    print("\n🔬 Testing forward pass...")
    outputs = network(dialogue_embeddings, laugh_features, character_ids, attention_mask)

    print(f"✅ Forward pass successful!")
    print(f"📈 Results:")
    print(f"   - Incongruity Score: {outputs.incongruity_score:.3f}")
    print(f"   - Importance Score: {outputs.importance_score:.3f}")
    print(f"   - Humor Probability: {outputs.humor_probability:.3f}")
    print(f"   - Laugh Prediction: {outputs.laugh_prediction:.3f}")
    print(f"   - Character Contributions: {len(outputs.character_contribution)} characters")
    print(f"   - Trope Confidence: {len(outputs.trope_confidence)} tropes")

    print("\n🎯 Key capabilities:")
    print("   - Multi-character dialogue processing")
    print("   - Laugh track correlation analysis")
    print("   - Ensemble cast dynamics modeling")
    print("   - Sitcom trope detection")
    print("   - Character relationship modeling")

if __name__ == "__main__":
    main()