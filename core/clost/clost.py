"""
CLoST (Structured Thought Leaps): Knowledge graph framework for non-linear comedic narrative processing
Bridges conceptual gaps between setup and punchline using causal inference
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Set
import networkx as nx
import numpy as np
from collections import defaultdict


class ConceptNode:
    """
    Represents a concept in the knowledge graph
    """
    
    def __init__(self, 
                 concept_id: str, 
                 text: str,
                 embedding: torch.Tensor,
                 concept_type: str = "generic"):
        """
        Initialize a concept node
        
        Args:
            concept_id: Unique identifier for the concept
            text: Textual representation of the concept
            embedding: Semantic embedding of the concept
            concept_type: Type of concept (entity, action, attribute, etc.)
        """
        self.concept_id = concept_id
        self.text = text
        self.embedding = embedding
        self.concept_type = concept_type
        self.connections = set()  # Set of connected concept IDs
        self.activation = 0.0
    
    def activate(self, strength: float = 1.0):
        """Activate this concept node"""
        self.activation = max(0.0, min(1.0, strength))
    
    def propagate_activation(self, graph: 'KnowledgeGraph', decay: float = 0.8):
        """Propagate activation to connected nodes"""
        for connected_id in self.connections:
            if connected_id in graph.concepts:
                connected_node = graph.concepts[connected_id]
                edge_weight = graph.get_edge_weight(self.concept_id, connected_id)
                connected_node.activate(self.activation * edge_weight * decay)


class KnowledgeGraph:
    """
    Knowledge graph for storing and processing conceptual relationships
    """
    
    def __init__(self, embedding_dim: int = 768):
        """
        Initialize knowledge graph
        
        Args:
            embedding_dim: Dimension of concept embeddings
        """
        self.embedding_dim = embedding_dim
        self.concepts = {}  # concept_id -> ConceptNode
        self.edges = {}  # (concept_id_1, concept_id_2) -> weight
        self.nx_graph = nx.DiGraph()
        
    def add_concept(self, 
                   concept_id: str, 
                   text: str,
                   embedding: torch.Tensor,
                   concept_type: str = "generic") -> ConceptNode:
        """
        Add a concept to the knowledge graph
        
        Args:
            concept_id: Unique identifier
            text: Textual representation
            embedding: Semantic embedding
            concept_type: Type of concept
        
        Returns:
            The created ConceptNode
        """
        node = ConceptNode(concept_id, text, embedding, concept_type)
        self.concepts[concept_id] = node
        self.nx_graph.add_node(concept_id, text=text, concept_type=concept_type)
        return node
    
    def add_edge(self, 
                concept_id_1: str, 
                concept_id_2: str, 
                weight: float = 1.0,
                relation_type: str = "related"):
        """
        Add a weighted edge between two concepts
        
        Args:
            concept_id_1: First concept ID
            concept_id_2: Second concept ID
            weight: Edge weight (strength of relationship)
            relation_type: Type of relationship
        """
        if concept_id_1 not in self.concepts or concept_id_2 not in self.concepts:
            return
        
        # Update connections
        self.concepts[concept_id_1].connections.add(concept_id_2)
        
        # Store edge weight
        self.edges[(concept_id_1, concept_id_2)] = weight
        
        # Update NetworkX graph
        self.nx_graph.add_edge(concept_id_1, concept_id_2, 
                              weight=weight, relation_type=relation_type)
    
    def get_edge_weight(self, concept_id_1: str, concept_id_2: str) -> float:
        """Get weight of edge between two concepts"""
        return self.edges.get((concept_id_1, concept_id_2), 0.0)
    
    def find_path(self, start_id: str, end_id: str) -> List[str]:
        """
        Find shortest path between two concepts
        
        Args:
            start_id: Starting concept ID
            end_id: Ending concept ID
        
        Returns:
            List of concept IDs forming the path
        """
        try:
            path = nx.shortest_path(self.nx_graph, start_id, end_id)
            return path
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []
    
    def get_similar_concepts(self, 
                           concept_id: str, 
                           top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Get most similar concepts based on embedding similarity
        
        Args:
            concept_id: Concept to find similarities for
            top_k: Number of similar concepts to return
        
        Returns:
            List of (concept_id, similarity_score) tuples
        """
        if concept_id not in self.concepts:
            return []
        
        target_embedding = self.concepts[concept_id].embedding
        similarities = []
        
        for other_id, other_node in self.concepts.items():
            if other_id != concept_id:
                similarity = F.cosine_similarity(
                    target_embedding.unsqueeze(0),
                    other_node.embedding.unsqueeze(0)
                ).item()
                similarities.append((other_id, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class CausalInferenceEngine(nn.Module):
    """
    Causal inference engine for reasoning about conceptual relationships
    """
    
    def __init__(self, embedding_dim: int = 768, hidden_dim: int = 256):
        """
        Initialize causal inference engine
        
        Args:
            embedding_dim: Dimension of concept embeddings
            hidden_dim: Hidden dimension for reasoning layers
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        
        # Causal relationship encoder
        self.causal_encoder = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        # Causal strength predictor
        self.causal_strength = nn.Linear(hidden_dim // 2, 1)
        
        # Conceptual bridge detector
        self.bridge_detector = nn.Sequential(
            nn.Linear(embedding_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        
    def forward(self,
                concept_a: torch.Tensor,
                concept_b: torch.Tensor,
                bridge_concept: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Perform causal inference between concepts
        
        Args:
            concept_a: First concept embedding
            concept_b: Second concept embedding
            bridge_concept: Optional bridging concept
        
        Returns:
            Dictionary containing causal inference results
        """
        # Encode causal relationship
        combined = torch.cat([concept_a, concept_b], dim=-1)
        causal_features = self.causal_encoder(combined)
        
        # Predict causal strength
        causal_strength = torch.sigmoid(self.causal_strength(causal_features))
        
        result = {
            'causal_features': causal_features,
            'causal_strength': causal_strength
        }
        
        # Check for conceptual bridge if provided
        if bridge_concept is not None:
            bridge_input = torch.cat([concept_a, bridge_concept, concept_b], dim=-1)
            bridge_strength = torch.sigmoid(self.bridge_detector(bridge_input))
            result['bridge_strength'] = bridge_strength
        
        return result


class CLoSTLayer(nn.Module):
    """
    Main CLoST (Structured Thought Leaps) layer
    Uses knowledge graphs and causal inference to bridge conceptual gaps
    """
    
    def __init__(self, 
                 embedding_dim: int = 768,
                 hidden_dim: int = 256,
                 max_leap_distance: int = 3):
        """
        Initialize CLoST layer
        
        Args:
            embedding_dim: Dimension of input embeddings
            hidden_dim: Hidden dimension for internal layers
            max_leap_distance: Maximum conceptual leap distance
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.max_leap_distance = max_leap_distance
        
        # Knowledge graph
        self.knowledge_graph = KnowledgeGraph(embedding_dim)
        
        # Causal inference engine
        self.causal_engine = CausalInferenceEngine(embedding_dim, hidden_dim)
        
        # Concept extractor
        self.concept_extractor = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, embedding_dim)
        )
        
        # Thought leap scorer
        self.leap_scorer = nn.Sequential(
            nn.Linear(embedding_dim * 2 + hidden_dim // 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1)
        )
        
    def extract_concepts(self, 
                        embeddings: torch.Tensor,
                        attention_mask: Optional[torch.Tensor] = None) -> List[Dict[str, torch.Tensor]]:
        """
        Extract key concepts from text embeddings
        
        Args:
            embeddings: Text embeddings of shape (batch, seq_len, embedding_dim)
            attention_mask: Attention mask of shape (batch, seq_len)
        
        Returns:
            List of dictionaries containing extracted concepts
        """
        batch_size, seq_len, _ = embeddings.shape
        
        # Apply concept extraction
        concept_embeddings = self.concept_extractor(embeddings)
        
        concepts = []
        for i in range(batch_size):
            if attention_mask is not None:
                mask = attention_mask[i].bool()
                valid_embeddings = concept_embeddings[i][mask]
            else:
                valid_embeddings = concept_embeddings[i]
            
            # Simple extraction: take every 10th token as a concept
            step = max(1, len(valid_embeddings) // 10)
            for j, emb in enumerate(valid_embeddings[::step]):
                concepts.append({
                    'embedding': emb,
                    'position': j * step,
                    'text': f"concept_{i}_{j}"
                })
        
        return concepts
    
    def build_joke_graph(self, 
                        setup_concepts: List[Dict],
                        punchline_concepts: List[Dict]) -> Tuple[List[str], List[str]]:
        """
        Build knowledge graph for a joke
        
        Args:
            setup_concepts: Concepts extracted from setup
            punchline_concepts: Concepts extracted from punchline
        
        Returns:
            Tuple of (setup_concept_ids, punchline_concept_ids)
        """
        # Clear existing graph
        self.knowledge_graph = KnowledgeGraph(self.embedding_dim)
        
        setup_ids = []
        punchline_ids = []
        
        # Add setup concepts
        for i, concept in enumerate(setup_concepts):
            concept_id = f"setup_{i}"
            self.knowledge_graph.add_concept(
                concept_id,
                concept['text'],
                concept['embedding'].detach(),
                "setup"
            )
            setup_ids.append(concept_id)
        
        # Add punchline concepts
        for i, concept in enumerate(punchline_concepts):
            concept_id = f"punchline_{i}"
            self.knowledge_graph.add_concept(
                concept_id,
                concept['text'],
                concept['embedding'].detach(),
                "punchline"
            )
            punchline_ids.append(concept_id)
        
        # Connect concepts within setup
        for i, id1 in enumerate(setup_ids):
            for j, id2 in enumerate(setup_ids):
                if i != j:
                    self.knowledge_graph.add_edge(id1, id2, weight=0.8)
        
        # Connect concepts within punchline
        for i, id1 in enumerate(punchline_ids):
            for j, id2 in enumerate(punchline_ids):
                if i != j:
                    self.knowledge_graph.add_edge(id1, id2, weight=0.8)
        
        # Connect setup to punchline (these are the thought leaps)
        for setup_id in setup_ids:
            for punchline_id in punchline_ids:
                # Use causal inference to determine connection strength
                setup_emb = self.knowledge_graph.concepts[setup_id].embedding
                punchline_emb = self.knowledge_graph.concepts[punchline_id].embedding
                
                causal_result = self.causal_engine(setup_emb, punchline_emb)
                strength = causal_result['causal_strength'].item()
                
                if strength > 0.3:  # Threshold for connection
                    self.knowledge_graph.add_edge(setup_id, punchline_id, weight=strength)
        
        return setup_ids, punchline_ids
    
    def find_thought_leaps(self, 
                          setup_ids: List[str], 
                          punchline_ids: List[str]) -> List[Dict[str, any]]:
        """
        Find thought leaps (conceptual bridges) between setup and punchline
        
        Args:
            setup_ids: Setup concept IDs
            punchline_ids: Punchline concept IDs
        
        Returns:
            List of thought leap dictionaries
        """
        thought_leaps = []
        
        for setup_id in setup_ids:
            for punchline_id in punchline_ids:
                # Find path in knowledge graph
                path = self.knowledge_graph.find_path(setup_id, punchline_id)
                
                if len(path) <= self.max_leap_distance and len(path) > 1:
                    # Calculate leap strength
                    total_strength = 0.0
                    for i in range(len(path) - 1):
                        total_strength += self.knowledge_graph.get_edge_weight(path[i], path[i+1])
                    
                    avg_strength = total_strength / (len(path) - 1)
                    
                    thought_leaps.append({
                        'path': path,
                        'length': len(path),
                        'strength': avg_strength,
                        'start': setup_id,
                        'end': punchline_id
                    })
        
        # Sort by strength and return
        thought_leaps.sort(key=lambda x: x['strength'], reverse=True)
        return thought_leaps
    
    def forward(self, 
                setup_embeddings: torch.Tensor,
                punchline_embeddings: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """
        Forward pass of CLoST layer
        
        Args:
            setup_embeddings: Setup portion embeddings
            punchline_embeddings: Punchline portion embeddings
            attention_mask: Attention mask
        
        Returns:
            Dictionary containing CLoST predictions and thought leaps
        """
        # Extract concepts
        setup_concepts = self.extract_concepts(setup_embeddings.unsqueeze(0), attention_mask)
        punchline_concepts = self.extract_concepts(punchline_embeddings.unsqueeze(0), attention_mask)
        
        # Build knowledge graph
        setup_ids, punchline_ids = self.build_joke_graph(setup_concepts, punchline_concepts)
        
        # Find thought leaps
        thought_leaps = self.find_thought_leaps(setup_ids, punchline_ids)
        
        # Score thought leaps for humor prediction
        if thought_leaps:
            # Use the strongest thought leap for prediction
            best_leap = thought_leaps[0]
            
            # Get embeddings for start and end concepts
            start_emb = self.knowledge_graph.concepts[best_leap['start']].embedding
            end_emb = self.knowledge_graph.concepts[best_leap['end']].embedding
            
            # Get causal features
            causal_result = self.causal_engine(start_emb, end_emb)
            
            # Score the thought leap
            leap_features = torch.cat([
                start_emb,
                end_emb,
                causal_result['causal_features']
            ], dim=-1)
            
            humor_score = torch.sigmoid(self.leap_scorer(leap_features))
        else:
            # No thought leaps found - likely not humorous
            humor_score = torch.tensor([[0.0]])
        
        return {
            'humor_prediction': humor_score,
            'thought_leaps': thought_leaps,
            'knowledge_graph': self.knowledge_graph
        }


def test_clost():
    """Test CLoST layer"""
    print("🧪 Testing CLoST (Structured Thought Leaps)")
    
    # Create sample input
    embedding_dim = 768
    seq_len = 64
    
    setup_embeddings = torch.randn(seq_len, embedding_dim)
    punchline_embeddings = torch.randn(seq_len, embedding_dim)
    attention_mask = torch.ones(seq_len)
    
    # Initialize CLoST layer
    clost_layer = CLoSTLayer(embedding_dim=embedding_dim)
    
    # Forward pass
    outputs = clost_layer(setup_embeddings, punchline_embeddings, attention_mask)
    
    # Print results
    humor_pred = outputs['humor_prediction'].item()
    thought_leaps = outputs['thought_leaps']
    
    print(f"Humor Prediction: {humor_pred:.4f}")
    print(f"Number of Thought Leaps: {len(thought_leaps)}")
    
    if thought_leaps:
        print(f"Best Thought Leap: {thought_leaps[0]['path']} (strength: {thought_leaps[0]['strength']:.4f})")
    
    if 0.0 <= humor_pred <= 1.0:
        print("✅ CLoST test passed!")
        return True
    else:
        print("❌ CLoST test failed!")
        return False


if __name__ == "__main__":
    test_clost()