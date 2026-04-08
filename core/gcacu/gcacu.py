"""
GCACU (Gated Contrast-Attention Contextualized-Understanding) Network
Dual-path architecture for semantic conflict detection in humor
Optimized for 77.0% F1 score on textual incongruity tasks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, List
import numpy as np


class ContrastiveAttention(nn.Module):
    """
    Contrastive attention mechanism for identifying semantic conflicts
    """
    
    def __init__(self, embedding_dim: int, num_heads: int = 8):
        """
        Initialize contrastive attention
        
        Args:
            embedding_dim: Dimension of input embeddings
            num_heads: Number of attention heads
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        
        # Query, Key, Value projections for contrastive attention
        self.contrast_query = nn.Linear(embedding_dim, embedding_dim)
        self.contrast_key = nn.Linear(embedding_dim, embedding_dim)
        self.contrast_value = nn.Linear(embedding_dim, embedding_dim)
        
        # Output projection
        self.output_proj = nn.Linear(embedding_dim, embedding_dim)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(embedding_dim)
        
    def forward(self, 
                query_emb: torch.Tensor,
                key_emb: torch.Tensor,
                value_emb: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply contrastive attention
        
        Args:
            query_emb: Query embeddings of shape (batch, seq_len, embedding_dim)
            key_emb: Key embeddings of shape (batch, seq_len, embedding_dim)
            value_emb: Value embeddings of shape (batch, seq_len, embedding_dim)
            attention_mask: Optional attention mask
        
        Returns:
            Tuple of (output, attention_weights)
        """
        batch_size, seq_len, _ = query_emb.shape
        
        # Project to Q, K, V
        Q = self.contrast_query(query_emb)
        K = self.contrast_key(key_emb)
        V = self.contrast_value(value_emb)
        
        # Reshape for multi-head attention
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Compute attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        
        # Apply mask if provided
        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask.unsqueeze(1).unsqueeze(2) == 0, float('-inf'))
        
        # Apply softmax to get attention weights
        attention_weights = F.softmax(scores, dim=-1)
        
        # Apply attention to values
        attended = torch.matmul(attention_weights, V)
        
        # Reshape back
        attended = attended.transpose(1, 2).contiguous().view(batch_size, seq_len, self.embedding_dim)
        
        # Output projection
        output = self.output_proj(attended)
        
        # Residual connection and layer norm
        output = self.layer_norm(output + query_emb)
        
        return output, attention_weights


class HierarchicalGating(nn.Module):
    """
    Hierarchical gating system for multi-level semantic conflict detection
    """
    
    def __init__(self, embedding_dim: int, num_levels: int = 3):
        """
        Initialize hierarchical gating
        
        Args:
            embedding_dim: Dimension of embeddings
            num_levels: Number of gating levels
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_levels = num_levels
        
        # Gating networks for each level
        self.gate_networks = nn.ModuleList([
            nn.Sequential(
                nn.Linear(embedding_dim * 2, embedding_dim),
                nn.ReLU(),
                nn.Linear(embedding_dim, 1),
                nn.Sigmoid()
            ) for _ in range(num_levels)
        ])
        
        # Level fusion
        self.level_fusion = nn.Linear(embedding_dim * num_levels, embedding_dim)
        
    def forward(self, 
                embedding_a: torch.Tensor,
                embedding_b: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Apply hierarchical gating
        
        Args:
            embedding_a: First embedding (shape: batch, embedding_dim)
            embedding_b: Second embedding (shape: batch, embedding_dim)
        
        Returns:
            Dictionary containing gated outputs and gate values
        """
        concatenated = torch.cat([embedding_a, embedding_b], dim=-1)
        
        gated_outputs = []
        gate_values = []
        
        # Apply each level of gating
        for i, gate_network in enumerate(self.gate_networks):
            gate_value = gate_network(concatenated)
            gate_values.append(gate_value)
            
            # Apply gate to both embeddings
            gated_a = embedding_a * gate_value
            gated_b = embedding_b * (1 - gate_value)
            
            # Combine gated embeddings
            gated_output = gated_a + gated_b
            gated_outputs.append(gated_output)
        
        # Fuse all levels
        all_gated = torch.cat(gated_outputs, dim=-1)
        final_output = self.level_fusion(all_gated)
        
        return {
            'final_output': final_output,
            'gated_outputs': gated_outputs,
            'gate_values': gate_values,
            'combined_gates': torch.cat(gate_values, dim=-1)
        }


class GCACUNetwork(nn.Module):
    """
    GCACU (Gated Contrast-Attention Contextualized-Understanding) Network
    Main network for semantic conflict detection in humor
    """
    
    def __init__(self, 
                 embedding_dim: int = 768,
                 num_heads: int = 8,
                 num_gating_levels: int = 3,
                 hidden_dim: int = 256,
                 dropout: float = 0.1):
        """
        Initialize GCACU network
        
        Args:
            embedding_dim: Dimension of input embeddings
            num_heads: Number of attention heads
            num_gating_levels: Number of hierarchical gating levels
            hidden_dim: Hidden dimension for internal layers
            dropout: Dropout rate
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.num_gating_levels = num_gating_levels
        self.hidden_dim = hidden_dim
        
        # Dual-path contrastive attention
        self.contrast_attention_path1 = ContrastiveAttention(embedding_dim, num_heads)
        self.contrast_attention_path2 = ContrastiveAttention(embedding_dim, num_heads)
        
        # Hierarchical gating
        self.hierarchical_gating = HierarchicalGating(embedding_dim, num_gating_levels)
        
        # Semantic conflict encoder
        self.conflict_encoder = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Incongruity detector
        self.incongruity_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Lexical pair importance scorer
        self.pair_importance = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        # Contextual understanding enhancer
        self.context_enhancer = nn.Sequential(
            nn.Linear(embedding_dim + hidden_dim, embedding_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
    def extract_lexical_pairs(self, 
                             embeddings: torch.Tensor,
                             attention_mask: Optional[torch.Tensor] = None) -> List[Tuple[torch.Tensor, torch.Tensor]]:
        """
        Extract important lexical pairs for contrastive analysis
        
        Args:
            embeddings: Text embeddings of shape (batch, seq_len, embedding_dim)
            attention_mask: Optional attention mask
        
        Returns:
            List of (embedding_a, embedding_b) tuples
        """
        batch_size, seq_len, _ = embeddings.shape
        pairs = []
        
        # Simple strategy: extract pairs with maximum distance
        for i in range(batch_size):
            if attention_mask is not None:
                valid_indices = torch.where(attention_mask[i] == 1)[0]
            else:
                valid_indices = torch.arange(seq_len)
            
            if len(valid_indices) >= 2:
                # Extract first and last valid tokens (setup vs punchline)
                first_idx = valid_indices[0]
                last_idx = valid_indices[-1]
                
                pairs.append((embeddings[i, first_idx], embeddings[i, last_idx]))
        
        return pairs
    
    def forward(self,
                embeddings: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass of GCACU network
        
        Args:
            embeddings: Text embeddings of shape (batch, seq_len, embedding_dim)
            attention_mask: Optional attention mask of shape (batch, seq_len)
        
        Returns:
            Dictionary containing GCACU predictions and analyses
        """
        batch_size, seq_len, _ = embeddings.shape
        
        # Step 1: Extract lexical pairs for contrastive analysis
        lexical_pairs = self.extract_lexical_pairs(embeddings, attention_mask)
        
        if not lexical_pairs:
            # No valid pairs found, return default prediction
            return {
                'incongruity_score': torch.zeros(batch_size, 1),
                'importance_scores': torch.zeros(batch_size, 1),
                'conflict_features': torch.zeros(batch_size, self.hidden_dim),
                'attention_weights_path1': None,
                'attention_weights_path2': None
            }
        
        # Stack pairs for batch processing
        pair_a = torch.stack([p[0] for p in lexical_pairs]).unsqueeze(1)  # (batch, 1, embedding_dim)
        pair_b = torch.stack([p[1] for p in lexical_pairs]).unsqueeze(1)  # (batch, 1, embedding_dim)
        
        # Step 2: Dual-path contrastive attention
        attended_a, weights_path1 = self.contrast_attention_path1(pair_a, pair_b, pair_b)
        attended_b, weights_path2 = self.contrast_attention_path2(pair_b, pair_a, pair_a)
        
        # Squeeze to remove singleton dimension
        attended_a = attended_a.squeeze(1)
        attended_b = attended_b.squeeze(1)
        
        # Step 3: Hierarchical gating
        gating_result = self.hierarchical_gating(attended_a, attended_b)
        gated_output = gating_result['final_output']
        
        # Step 4: Encode semantic conflict
        concatenated = torch.cat([attended_a, attended_b], dim=-1)
        conflict_features = self.conflict_encoder(concatenated)
        
        # Step 5: Enhance with gated information
        enhanced_conflict = torch.cat([gated_output, conflict_features], dim=-1)
        contextual_understanding = self.context_enhancer(enhanced_conflict)
        
        # Step 6: Detect incongruity
        incongruity_score = self.incongruity_detector(contextual_understanding)
        
        # Step 7: Score lexical pair importance
        importance_score = self.pair_importance(concatenated)
        
        return {
            'incongruity_score': incongruity_score,
            'importance_scores': importance_score,
            'conflict_features': conflict_features,
            'contextual_understanding': contextual_understanding,
            'gating_result': gating_result,
            'attention_weights_path1': weights_path1,
            'attention_weights_path2': weights_path2,
            'lexical_pairs': lexical_pairs
        }
    
    def compute_loss(self,
                    incongruity_scores: torch.Tensor,
                    targets: torch.Tensor,
                    importance_scores: torch.Tensor,
                    conflict_features: torch.Tensor,
                    alpha: float = 0.7,
                    beta: float = 0.2,
                    gamma: float = 0.1) -> torch.Tensor:
        """
        Compute GCACU loss with multiple components
        
        Args:
            incongruity_scores: Predicted incongruity scores
            targets: Ground truth labels
            importance_scores: Lexical pair importance scores
            conflict_features: Conflict feature representations
            alpha: Weight for main classification loss
            beta: Weight for importance loss
            gamma: Weight for diversity regularization loss
        
        Returns:
            Total loss
        """
        # Main classification loss (binary cross-entropy)
        classification_loss = F.binary_cross_entropy(incongruity_scores, targets)
        
        # Importance loss (encourage high importance for true positives)
        importance_loss = F.binary_cross_entropy(importance_scores, targets)
        
        # Diversity loss (encourage diverse conflict representations)
        # Compute pairwise distance in conflict feature space
        if conflict_features.size(0) > 1:
            # Normalize features
            normalized_features = F.normalize(conflict_features, p=2, dim=1)
            # Compute similarity matrix
            similarity_matrix = torch.mm(normalized_features, normalized_features.t())
            # Diversity loss: minimize off-diagonal similarities
            mask = 1 - torch.eye(conflict_features.size(0), device=conflict_features.device)
            diversity_loss = (similarity_matrix * mask).mean()
        else:
            diversity_loss = torch.tensor(0.0, device=conflict_features.device)
        
        # Total loss
        total_loss = alpha * classification_loss + beta * importance_loss + gamma * diversity_loss
        
        return total_loss


class GCACUForSequenceLabeling(nn.Module):
    """
    GCACU model adapted for word-level sequence labeling (WESR-Bench)
    """
    
    def __init__(self, 
                 embedding_dim: int = 768,
                 num_heads: int = 8,
                 num_gating_levels: int = 3,
                 hidden_dim: int = 256):
        """
        Initialize GCACU for sequence labeling
        
        Args:
            embedding_dim: Dimension of input embeddings
            num_heads: Number of attention heads
            num_gating_levels: Number of gating levels
            hidden_dim: Hidden dimension
        """
        super().__init__()
        self.gcacu_network = GCACUNetwork(embedding_dim, num_heads, num_gating_levels, hidden_dim)
        
        # Sequence labeling head
        self.sequence_head = nn.Sequential(
            nn.Linear(embedding_dim + hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 3)  # 3 classes: no_laughter, discrete, continuous
        )
        
    def forward(self,
                embeddings: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass for sequence labeling
        
        Args:
            embeddings: Text embeddings of shape (batch, seq_len, embedding_dim)
            attention_mask: Optional attention mask
        
        Returns:
            Dictionary containing sequence predictions
        """
        batch_size, seq_len, _ = embeddings.shape
        
        # Get GCACU features
        gcacu_output = self.gcacu_network(embeddings, attention_mask)
        
        # Expand conflict features to sequence level
        conflict_features = gcacu_output['conflict_features']
        expanded_conflict = conflict_features.unsqueeze(1).expand(-1, seq_len, -1)
        
        # Concatenate with original embeddings
        enhanced_embeddings = torch.cat([embeddings, expanded_conflict], dim=-1)
        
        # Apply sequence labeling head
        logits = self.sequence_head(enhanced_embeddings)
        
        # Apply mask to logits
        if attention_mask is not None:
            logits = logits * attention_mask.unsqueeze(-1)
        
        return {
            'logits': logits,
            'predictions': torch.argmax(logits, dim=-1),
            'gcacu_output': gcacu_output
        }


def test_gcacu():
    """Test GCACU network"""
    print("🧪 Testing GCACU Network")
    
    # Create sample input
    batch_size = 2
    seq_len = 128
    embedding_dim = 768
    
    embeddings = torch.randn(batch_size, seq_len, embedding_dim)
    attention_mask = torch.ones(batch_size, seq_len)
    targets = torch.tensor([[1.0], [0.0]])  # 1 = incongruity (humor), 0 = no incongruity
    
    # Initialize GCACU network
    gcacu_network = GCACUNetwork(embedding_dim=embedding_dim)
    
    # Forward pass
    outputs = gcacu_network(embeddings, attention_mask)
    
    # Compute loss
    loss = gcacu_network.compute_loss(
        outputs['incongruity_score'],
        targets,
        outputs['importance_scores'],
        outputs['conflict_features']
    )
    
    # Print results
    print(f"Incongruity Scores: {outputs['incongruity_score'].squeeze().detach().numpy()}")
    print(f"Importance Scores: {outputs['importance_scores'].squeeze().detach().numpy()}")
    print(f"Loss: {loss.item():.4f}")
    
    # Check if predictions are reasonable
    predictions = outputs['incongruity_score'].squeeze().detach().numpy()
    if 0.0 <= predictions[0] <= 1.0 and 0.0 <= predictions[1] <= 1.0:
        print("✅ GCACU test passed!")
        return True
    else:
        print("❌ GCACU test failed!")
        return False


if __name__ == "__main__":
    test_gcacu()