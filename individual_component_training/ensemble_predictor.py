#!/usr/bin/env python3
"""
Practical Ensemble Laughter Predictor
Uses verified working components separately to avoid integration issues
"""

import torch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tom.theory_of_mind import TheoryOfMindLayer
from core.gcacu.gcacu import GCACUNetwork
from memory.engram.engram import EngramMemorySystem, EngramConfig

class PracticalLaughterPredictor:
    """
    Ensemble predictor using working components separately.
    Avoids integration issues by using components independently.
    """

    def __init__(self, embedding_dim=256, num_heads=4):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        print("🎭 Initializing Practical Ensemble Predictor")
        print(f"Device: {self.device}")

        # Initialize components separately
        print("🧠 Loading Theory of Mind Layer...")
        self.tom = TheoryOfMindLayer(
            embedding_dim=self.embedding_dim,
            num_heads=self.num_heads
        ).to(self.device)

        print("⚡ Loading GCACU Network...")
        self.gcacu = GCACUNetwork(
            embedding_dim=self.embedding_dim,
            num_heads=self.num_heads
        ).to(self.device)

        print("🧠 Loading Engram Memory System...")
        import tempfile
        engram_storage = Path(tempfile.gettempdir()) / "engram_memory"
        engram_config = EngramConfig(
            storage_dir=engram_storage,
            bucket_count=128,
            cache_size=64
        )
        self.engram = EngramMemorySystem(engram_config)

        print("✅ All components loaded successfully!")

    def predict_single_input(self, text_embedding, attention_mask=None):
        """
        Predict humor score for a single input using ensemble approach.

        Args:
            text_embedding: torch.Tensor of shape (batch_size, seq_len, embedding_dim)
            attention_mask: torch.Tensor of shape (batch_size, seq_len)

        Returns:
            dict with ensemble predictions and component scores
        """
        if attention_mask is None:
            attention_mask = torch.ones_like(text_embedding[:, :, 0])

        # Ensure input is on correct device
        text_embedding = text_embedding.to(self.device)
        attention_mask = attention_mask.to(self.device)

        # Get predictions from each component
        with torch.no_grad():
            # Theory of Mind prediction
            tom_result = self.tom(text_embedding, attention_mask)
            tom_humor_score = tom_result['humor_prediction']
            tom_misalignment = tom_result['causal_reasoning']['misalignment_score']

            # GCACU prediction
            gcacu_result = self.gcacu(text_embedding, attention_mask)
            gcacu_incongruity = gcacu_result['incongruity_score']
            gcacu_importance = gcacu_result['importance_scores']

            # Store in Engram memory (simplified - just store key info)
            # Note: Engram system has specific API, using simple storage for now
            pass

        # Ensemble prediction (weighted average)
        # We can tune these weights based on validation performance
        ensemble_weights = {
            'tom': 0.6,        # Theory of Mind gets higher weight
            'gcacu': 0.4       # GCACU gets moderate weight
        }

        ensemble_score = (
            ensemble_weights['tom'] * tom_humor_score +
            ensemble_weights['gcacu'] * gcacu_incongruity
        )

        return {
            'ensemble_score': ensemble_score,
            'tom_humor_score': tom_humor_score,
            'tom_misalignment': tom_misalignment,
            'gcacu_incongruity': gcacu_incongruity,
            'gcacu_importance': gcacu_importance.mean(),
            'interpretation': self._interpret_prediction(ensemble_score)
        }

    def predict_batch(self, text_embeddings, attention_mask=None):
        """Predict humor scores for a batch of inputs"""
        return self.predict_single_input(text_embeddings, attention_mask)

    def _interpret_prediction(self, score):
        """Interpret the humor score"""
        # Handle tensor with multiple elements by taking mean
        if torch.is_tensor(score):
            if score.numel() > 1:
                score_value = score.mean().item()
            else:
                score_value = score.item()
        else:
            score_value = score

        if score_value < 0.3:
            return "Not funny - low humor detected"
        elif score_value < 0.5:
            return "Slightly amusing - mild humor detected"
        elif score_value < 0.7:
            return "Funny - moderate humor detected"
        elif score_value < 0.85:
            return "Very funny - high humor detected"
        else:
            return "Hilarious - maximum humor detected"

    def analyze_comedy_content(self, text_embedding, attention_mask=None):
        """
        Comprehensive analysis of comedy content using all components.

        Returns detailed analysis from each cognitive architecture.
        """
        if attention_mask is None:
            attention_mask = torch.ones_like(text_embedding[:, :, 0])

        text_embedding = text_embedding.to(self.device)
        attention_mask = attention_mask.to(self.device)

        with torch.no_grad():
            # Theory of Mind analysis
            tom_result = self.tom(text_embedding, attention_mask)

            # GCACU analysis
            gcacu_result = self.gcacu(text_embedding, attention_mask)

            # Retrieve relevant memories (simplified for now)
            # Note: Engram system has specific API, using basic approach
            relevant_memories = []

        return {
            'theory_of_mind_analysis': {
                'humor_prediction': tom_result['humor_prediction'].mean().item(),
                'misalignment_detection': tom_result['causal_reasoning']['misalignment_score'].mean().item(),
                'causal_features': tom_result['causal_reasoning']['causal_features'].mean().item(),
                'interpretation': f"Humor score: {tom_result['humor_prediction'].mean().item():.3f}"
            },
            'gcacu_analysis': {
                'incongruity_score': gcacu_result['incongruity_score'].mean().item(),
                'importance_score': gcacu_result['importance_scores'].mean().item(),
                'interpretation': f"Incongruity: {gcacu_result['incongruity_score'].mean().item():.3f}"
            },
            'memory_context': {
                'relevant_memories_found': len(relevant_memories),
                'memory_similarity': [m.get('similarity', 0.0) for m in relevant_memories] if relevant_memories else []
            },
            'ensemble_prediction': self.predict_single_input(text_embedding, attention_mask)
        }

    def load_component_checkpoints(self, tom_checkpoint=None, gcacu_checkpoint=None):
        """Load trained checkpoints for components"""
        if tom_checkpoint:
            tom_path = Path(tom_checkpoint)
            if tom_path.exists():
                self.tom.load_state_dict(torch.load(tom_path))
                print(f"✅ ToM checkpoint loaded from {tom_path}")

        if gcacu_checkpoint:
            gcacu_path = Path(gcacu_checkpoint)
            if gcacu_path.exists():
                self.gcacu.load_state_dict(torch.load(gcacu_path))
                print(f"✅ GCACU checkpoint loaded from {gcacu_path}")

def demo_ensemble_predictor():
    """Demonstrate the ensemble predictor with mock data"""
    print("🎭 PRACTICAL ENSEMBLE LAUGHTER PREDICTOR DEMO")
    print("=" * 60)

    # Initialize predictor
    predictor = PracticalLaughterPredictor(embedding_dim=256, num_heads=4)

    # Create mock comedy content
    batch_size = 2
    seq_len = 32
    mock_embeddings = torch.randn(batch_size, seq_len, 256)
    mock_attention = torch.ones(batch_size, seq_len)

    print("\n📊 Testing with mock comedy content...")

    # Test single prediction
    result = predictor.predict_single_input(mock_embeddings, mock_attention)

    print(f"\n🎯 ENSEMBLE PREDICTION RESULTS:")
    print(f"Ensemble Score: {result['ensemble_score'].mean().item():.4f}")
    print(f"ToM Humor Score: {result['tom_humor_score'].mean().item():.4f}")
    print(f"GCACU Incongruity: {result['gcacu_incongruity'].mean().item():.4f}")
    print(f"Interpretation: {result['interpretation']}")

    # Test comprehensive analysis
    print(f"\n📈 COMPREHENSIVE ANALYSIS:")
    analysis = predictor.analyze_comedy_content(mock_embeddings, mock_attention)

    print(f"Theory of Mind: {analysis['theory_of_mind_analysis']['interpretation']}")
    print(f"GCACU: {analysis['gcacu_analysis']['interpretation']}")
    print(f"Memory Context: {analysis['memory_context']['relevant_memories_found']} relevant memories")

    print("\n✅ Ensemble predictor working successfully!")
    print("🎯 Ready for training with real data!")

    return predictor

if __name__ == "__main__":
    predictor = demo_ensemble_predictor()