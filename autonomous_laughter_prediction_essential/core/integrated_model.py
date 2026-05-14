#!/usr/bin/env python3
"""
Integrated Laughter Model combining all cognitive architectures with memory optimization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional

from core.tom.theory_of_mind import TheoryOfMindLayer
from core.clost.clost import CLoSTLayer
from core.gcacu.gcacu import GCACUNetwork
from core.sevade.sevade import SEVADEEvaluator

# Import memory optimization systems
from memory.engram.engram import EngramMemorySystem, EngramConfig
from memory.mhc.mhc import ManifoldConstrainedHyperConnections, MHCConfig


class IntegratedLaughterModel(nn.Module):
    """
    Integrated model combining all cognitive architectures with memory optimization

    Features:
    - Theory of Mind for intent understanding
    - CLoST for linguistic comedy analysis
    - GCACU for humor detection
    - Engram for efficient knowledge retrieval
    - mHC for stable training
    - Memory-optimized for 8GB Mac M2
    """

    def __init__(
        self,
        embedding_dim: int = 64,
        num_heads: int = 4,
        hidden_dim: int = 64,
        turboquant_heads: int = 4,
        memory_budget_gb: float = 5.0,
        use_engram: bool = True,
        use_mhc: bool = True
    ):
        super().__init__()

        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.use_engram = use_engram
        self.use_mhc = use_mhc

        # Initialize cognitive architectures
        self.tom = TheoryOfMindLayer(embedding_dim, hidden_dim)
        self.clost = CLoSTLayer(embedding_dim, hidden_dim)
        self.gcacu = GCACUNetwork(embedding_dim, hidden_dim)
        self.sevade = SEVADEEvaluator(hidden_dim)

        # Initialize memory optimization systems
        if use_engram:
            engram_config = EngramConfig(
                max_memory_mb=50.0,  # Conservative memory usage
                embedding_dim=embedding_dim,
                top_k=5
            )
            self.engram = EngramMemorySystem(engram_config)
        else:
            self.engram = None

        if use_mhc:
            mhc_config = MHCConfig(
                num_nodes=3,  # Connect ToM, CLoST, GCACU
                use_adaptive_connections=True
            )
            self.mhc = ManifoldConstrainedHyperConnections(mhc_config)
        else:
            self.mhc = None

        # Final prediction layer
        self.final_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def initialize_knowledge_base(self, knowledge_data):
        """Initialize Engram knowledge base"""
        if self.engram and knowledge_data:
            self.engram.initialize_knowledge_base(knowledge_data)

    def forward(self, inputs: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass through integrated model

        Args:
            inputs: Dictionary with 'embeddings' and 'attention_mask' keys

        Returns:
            Dictionary with predictions and intermediate features
        """
        embeddings = inputs['embeddings']  # [batch, seq_len, embedding_dim]

        # Process through cognitive architectures
        tom_outputs = self.tom(inputs)  # Theory of Mind
        clost_outputs = self.clost(inputs)  # Comedy Language Style and Timing

        # Knowledge enhancement using Engram
        knowledge_context = None
        if self.engram and self.use_engram:
            # Create query from combined features
            query = torch.cat([tom_outputs['tom_features'], clost_outputs['clost_features']], dim=1)
            query_embedding = query.mean(dim=1, keepdim=True) if query.dim() > 2 else query

            # Retrieve relevant knowledge
            retrieved = self.engram.retrieve_knowledge(
                query_embedding.squeeze(1),
                context="",  # Could extract from inputs
                top_k=3
            )

            # Inject knowledge into features
            if retrieved['embeddings'].numel() > 0:
                knowledge_context = retrieved['embeddings'].mean(dim=0, keepdim=True)
                knowledge_context = knowledge_context.expand(tom_outputs['tom_features'].size(0), -1)

        # Combine cognitive features using mHC or simple concatenation
        if self.mhc and self.use_mhc:
            # Prepare inputs for mHC
            component_features = [
                tom_outputs['tom_features'],
                clost_outputs['clost_features'],
                torch.zeros_like(tom_outputs['tom_features'])  # Placeholder for third component
            ]

            # Apply manifold-constrained connections
            connected_features = self.mhc(component_features, update_connections=self.training)
            combined_features = connected_features[:, :self.hidden_dim]  # Take first part
        else:
            # Simple concatenation
            combined_features = torch.cat([
                tom_outputs['tom_features'],
                clost_outputs['clost_features']
            ], dim=1)

        # Process through GCACU with knowledge context
        gcacu_outputs = self.gcacu(
            tom_outputs['tom_features'],
            clost_outputs['clost_features'],
            knowledge_context
        )

        # Semantic evaluation
        sevade_outputs = self.sevade(
            gcacu_outputs['combined_features'],
            gcacu_outputs['context_features']
        )

        # Final prediction
        final_features = torch.cat([
            gcacu_outputs['combined_features'],
            sevade_outputs['combined_features']
        ], dim=1)

        predictions = self.final_predictor(final_features)

        return {
            'probabilities': predictions,
            'humor_probability': gcacu_outputs['humor_probability'],
            'laughter_probability': gcacu_outputs['laughter_probability'],
            'semantic_score': sevade_outputs['semantic_score'],
            'tom_intents': tom_outputs['intents'],
            'clost_styles': clost_outputs['style_logits'],
            'knowledge_used': knowledge_context is not None,
            'combined_features': combined_features
        }

    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        total_params = sum(p.numel() for p in self.parameters())
        total_memory = total_params * 4 / (1024 ** 2)  # MB (float32)

        stats = {
            'total_parameters': total_params,
            'model_memory_mb': total_memory
        }

        if self.engram:
            stats['engram_memory_mb'] = self.engram.calculate_memory_usage()

        return stats