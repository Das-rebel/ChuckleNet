"""
CLoST Multi-Hop Reasoning System
Advanced reasoning paths for detecting complex humor patterns

Author: GCACU Autonomous Laughter Prediction System
Date: 2026-04-03
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any, Set
import numpy as np
from dataclasses import dataclass
import networkx as nx
from collections import defaultdict

# Import CLoST components
from clost_reasoning import ComedyKnowledgeGraph, ComedyConcept, ThoughtLeap


@dataclass
class ReasoningPath:
    """
    Represents a multi-hop reasoning path for humor detection

    Attributes:
        path: List of concept IDs in the reasoning chain
        confidence: Confidence score for this path
        reasoning_steps: Individual reasoning steps
        humor_contribution: How much this path contributes to humor
        path_type: Type of reasoning (semantic, causal, pragmatic)
    """
    path: List[str]
    confidence: float
    reasoning_steps: List[str]
    humor_contribution: float
    path_type: str


@dataclass
class MultiHopAnalysis:
    """
    Results from multi-hop reasoning analysis

    Attributes:
        reasoning_paths: All discovered reasoning paths
        best_path: Highest confidence path
        path_diversity: Diversity of discovered paths
        reasoning_complexity: Complexity score of the reasoning
        humor_mechanisms: Detected humor mechanisms across paths
    """
    reasoning_paths: List[ReasoningPath]
    best_path: ReasoningPath
    path_diversity: float
    reasoning_complexity: float
    humor_mechanisms: List[str]


class MultiHopReasoningEngine(nn.Module):
    """
    Multi-hop reasoning engine for complex humor detection

    Enables the system to follow chains of reasoning that connect
    seemingly unrelated concepts through intermediate steps.
    """

    def __init__(self,
                 embedding_dim: int = 768,
                 hidden_dim: int = 256,
                 max_hops: int = 5,
                 beam_width: int = 3):
        """
        Initialize multi-hop reasoning engine

        Args:
            embedding_dim: Dimension of concept embeddings
            hidden_dim: Hidden dimension for internal layers
            max_hops: Maximum number of reasoning hops
            beam_width: Beam width for path search
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.max_hops = max_hops
        self.beam_width = beam_width

        # Path scoring network
        self.path_scorer = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Path type classifier
        self.path_classifier = nn.Sequential(
            nn.Linear(embedding_dim * 2 + hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 4)  # 4 path types
        )

        # Reasoning step encoder
        self.step_encoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2)
        )

        # Path diversity calculator
        self.diversity_network = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def find_reasoning_paths(self,
                            knowledge_graph: ComedyKnowledgeGraph,
                            source_concept: str,
                            target_concept: str,
                            max_paths: int = 10) -> List[ReasoningPath]:
        """
        Find multiple reasoning paths between concepts

        Args:
            knowledge_graph: Comedy knowledge graph
            source_concept: Starting concept ID
            target_concept: Target concept ID
            max_paths: Maximum number of paths to find

        Returns:
            List of discovered reasoning paths
        """
        if source_concept not in knowledge_graph.concepts or \
           target_concept not in knowledge_graph.concepts:
            return []

        # Find all paths up to max_hops
        all_paths = knowledge_graph.find_all_paths(
            source_concept,
            target_concept,
            max_length=self.max_hops
        )

        if not all_paths:
            return []

        # Score and rank paths
        scored_paths = []
        for path in all_paths[:max_paths]:
            path_score = self._score_path(knowledge_graph, path)
            path_type = self._classify_path_type(knowledge_graph, path)
            reasoning_steps = self._generate_reasoning_steps(knowledge_graph, path)

            reasoning_path = ReasoningPath(
                path=path,
                confidence=path_score,
                reasoning_steps=reasoning_steps,
                humor_contribution=self._compute_humor_contribution(path_score, len(path)),
                path_type=path_type
            )
            scored_paths.append(reasoning_path)

        # Sort by confidence
        scored_paths.sort(key=lambda x: x.confidence, reverse=True)

        return scored_paths[:self.beam_width]

    def _score_path(self,
                   knowledge_graph: ComedyKnowledgeGraph,
                   path: List[str]) -> float:
        """
        Score a reasoning path based on semantic coherence and relevance

        Args:
            knowledge_graph: Comedy knowledge graph
            path: List of concept IDs

        Returns:
            Path score (0-1)
        """
        if len(path) < 2:
            return 0.0

        total_score = 0.0
        edge_weights = []

        # Score each step in the path
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]

            if source_id in knowledge_graph.concepts and \
               target_id in knowledge_graph.concepts:

                # Get edge strength if available
                if knowledge_graph.graph.has_edge(source_id, target_id):
                    edge_data = knowledge_graph.graph.get_edge_data(source_id, target_id)
                    edge_strength = edge_data.get('strength', 0.5)
                else:
                    edge_strength = 0.3  # Default strength for indirect connections

                # Compute semantic similarity
                similarity = knowledge_graph.compute_semantic_similarity(source_id, target_id)

                # Combine edge strength and semantic similarity
                step_score = 0.6 * edge_strength + 0.4 * similarity
                total_score += step_score
                edge_weights.append(step_score)

        # Average over all steps
        avg_score = total_score / (len(path) - 1) if len(path) > 1 else 0.0

        # Prefer moderately long paths (not too short, not too long)
        length_bonus = 1.0 - abs(len(path) - 3) / self.max_hops

        return avg_score * length_bonus

    def _classify_path_type(self,
                           knowledge_graph: ComedyKnowledgeGraph,
                           path: List[str]) -> str:
        """
        Classify the type of reasoning path

        Args:
            knowledge_graph: Comedy knowledge graph
            path: List of concept IDs

        Returns:
            Path type (semantic, causal, pragmatic, incongruity)
        """
        # Analyze relationship types in the path
        causal_count = 0
        semantic_count = 0
        pragmatic_count = 0

        for i in range(len(path) - 1):
            if knowledge_graph.graph.has_edge(path[i], path[i + 1]):
                edge_data = knowledge_graph.graph.get_edge_data(path[i], path[i + 1])
                rel_type = edge_data.get('type', 'semantic')

                if rel_type in ['causes', 'enables', 'contradicts', 'subverts']:
                    causal_count += 1
                elif rel_type in ['references', 'cultural', 'linguistic']:
                    semantic_count += 1
                elif rel_type in ['situational', 'character']:
                    pragmatic_count += 1

        # Determine dominant type
        if causal_count >= max(semantic_count, pragmatic_count):
            return 'causal'
        elif semantic_count >= pragmatic_count:
            return 'semantic'
        else:
            return 'pragmatic'

    def _generate_reasoning_steps(self,
                                 knowledge_graph: ComedyKnowledgeGraph,
                                 path: List[str]) -> List[str]:
        """
        Generate human-readable reasoning steps

        Args:
            knowledge_graph: Comedy knowledge graph
            path: List of concept IDs

        Returns:
            List of reasoning step descriptions
        """
        steps = []

        for i in range(len(path) - 1):
            source_concept = knowledge_graph.concepts.get(path[i])
            target_concept = knowledge_graph.concepts.get(path[i + 1])

            if source_concept and target_concept:
                if knowledge_graph.graph.has_edge(path[i], path[i + 1]):
                    edge_data = knowledge_graph.graph.get_edge_data(path[i], path[i + 1])
                    rel_type = edge_data.get('type', 'related')

                    step_desc = f"{source_concept.name} → {rel_type} → {target_concept.name}"
                    steps.append(step_desc)
                else:
                    # Indirect connection
                    step_desc = f"{source_concept.name} → (related to) → {target_concept.name}"
                    steps.append(step_desc)

        return steps

    def _compute_humor_contribution(self, path_score: float, path_length: int) -> float:
        """
        Compute how much a path contributes to humor

        Args:
            path_score: Path confidence score
            path_length: Length of the path

        Returns:
            Humor contribution score (0-1)
        """
        # Longer, moderate-confidence paths tend to be more humorous
        # They represent "thought leaps" that require cognitive processing
        length_factor = min(path_length / 4.0, 1.0)  # Cap at 4 hops
        humor_score = path_score * (0.5 + 0.5 * length_factor)

        return humor_score

    def analyze_multi_hop_reasoning(self,
                                   knowledge_graph: ComedyKnowledgeGraph,
                                   setup_concepts: List[ComedyConcept],
                                   punchline_concepts: List[ComedyConcept]) -> MultiHopAnalysis:
        """
        Perform comprehensive multi-hop reasoning analysis

        Args:
            knowledge_graph: Comedy knowledge graph
            setup_concepts: Concepts from setup
            punchline_concepts: Concepts from punchline

        Returns:
            MultiHopAnalysis with complete reasoning analysis
        """
        all_paths = []
        humor_mechanisms = set()

        # Find paths between all setup-punchline concept pairs
        for setup_concept in setup_concepts[:3]:  # Limit for efficiency
            for punchline_concept in punchline_concepts[:3]:
                paths = self.find_reasoning_paths(
                    knowledge_graph,
                    setup_concept.id,
                    punchline_concept.id
                )
                all_paths.extend(paths)

        if not all_paths:
            # No paths found - this is itself a form of incongruity
            return MultiHopAnalysis(
                reasoning_paths=[],
                best_path=ReasoningPath(
                    path=[],
                    confidence=0.0,
                    reasoning_steps=["No direct reasoning path found"],
                    humor_contribution=0.5,
                    path_type="incongruity"
                ),
                path_diversity=0.0,
                reasoning_complexity=0.5,
                humor_mechanisms=["incongruity"]
            )

        # Find best path
        best_path = max(all_paths, key=lambda x: x.confidence)

        # Collect humor mechanisms
        for path in all_paths:
            humor_mechanisms.add(path.path_type)

        # Compute path diversity
        path_diversity = self._compute_path_diversity(all_paths, knowledge_graph)

        # Compute reasoning complexity
        reasoning_complexity = self._compute_reasoning_complexity(all_paths)

        return MultiHopAnalysis(
            reasoning_paths=all_paths,
            best_path=best_path,
            path_diversity=path_diversity,
            reasoning_complexity=reasoning_complexity,
            humor_mechanisms=list(humor_mechanisms)
        )

    def _compute_path_diversity(self,
                               paths: List[ReasoningPath],
                               knowledge_graph: ComedyKnowledgeGraph) -> float:
        """Compute diversity of discovered paths"""
        if len(paths) < 2:
            return 0.0

        # Compute pairwise path differences
        unique_paths = set()
        for path in paths:
            # Create path signature
            signature = tuple(path.path)
            unique_paths.add(signature)

        # Diversity based on unique paths
        diversity = len(unique_paths) / len(paths)
        return diversity

    def _compute_reasoning_complexity(self, paths: List[ReasoningPath]) -> float:
        """Compute overall reasoning complexity"""
        if not paths:
            return 0.0

        # Complexity based on average path length and diversity of types
        avg_length = np.mean([len(path.path) for path in paths])
        type_diversity = len(set(path.path_type for path in paths))

        # Normalize
        length_complexity = min(avg_length / self.max_hops, 1.0)
        type_complexity = min(type_diversity / 4.0, 1.0)  # 4 types max

        complexity = 0.6 * length_complexity + 0.4 * type_complexity
        return complexity


class MemoryEfficientMultiHopReasoning:
    """
    Memory-optimized version for 8GB Mac M2 constraints
    """

    def __init__(self,
                 embedding_dim: int = 768,
                 max_cache_size: int = 1000):
        """
        Initialize memory-efficient multi-hop reasoning

        Args:
            embedding_dim: Dimension of concept embeddings
            max_cache_size: Maximum number of cached reasoning results
        """
        self.embedding_dim = embedding_dim
        self.max_cache_size = max_cache_size

        # LRU cache for reasoning results
        self.reasoning_cache: Dict[str, List[ReasoningPath]] = {}
        self.access_order: List[str] = []

        # Simplified reasoning engine
        self.reasoning_engine = MultiHopReasoningEngine(embedding_dim)

    def find_paths_efficient(self,
                            knowledge_graph: ComedyKnowledgeGraph,
                            source_id: str,
                            target_id: str) -> List[ReasoningPath]:
        """
        Find reasoning paths with memory optimization

        Args:
            knowledge_graph: Comedy knowledge graph
            source_id: Source concept ID
            target_id: Target concept ID

        Returns:
            List of reasoning paths
        """
        # Check cache
        cache_key = f"{source_id}_{target_id}"
        if cache_key in self.reasoning_cache:
            # Update access order
            self.access_order.remove(cache_key)
            self.access_order.append(cache_key)
            return self.reasoning_cache[cache_key]

        # Compute paths (with simplified search)
        paths = self._simplified_path_search(knowledge_graph, source_id, target_id)

        # Cache result
        self._cache_result(cache_key, paths)

        return paths

    def _simplified_path_search(self,
                               knowledge_graph: ComedyKnowledgeGraph,
                               source_id: str,
                               target_id: str) -> List[ReasoningPath]:
        """
        Simplified path search for memory efficiency

        Args:
            knowledge_graph: Comedy knowledge graph
            source_id: Source concept ID
            target_id: Target concept ID

        Returns:
            List of reasoning paths
        """
        # Use BFS instead of exhaustive search
        try:
            shortest_path = nx.shortest_path(knowledge_graph.graph, source_id, target_id)

            if len(shortest_path) <= 4:  # Only use reasonably short paths
                path_score = self.reasoning_engine._score_path(knowledge_graph, shortest_path)
                path_type = self.reasoning_engine._classify_path_type(knowledge_graph, shortest_path)

                return [ReasoningPath(
                    path=shortest_path,
                    confidence=path_score,
                    reasoning_steps=self.reasoning_engine._generate_reasoning_steps(
                        knowledge_graph, shortest_path
                    ),
                    humor_contribution=self.reasoning_engine._compute_humor_contribution(
                        path_score, len(shortest_path)
                    ),
                    path_type=path_type
                )]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        return []

    def _cache_result(self, key: str, paths: List[ReasoningPath]) -> None:
        """Cache reasoning result with LRU eviction"""
        # Remove oldest if cache is full
        if len(self.reasoning_cache) >= self.max_cache_size:
            oldest_key = self.access_order.pop(0)
            del self.reasoning_cache[oldest_key]

        # Add new result
        self.reasoning_cache[key] = paths
        self.access_order.append(key)

    def clear_cache(self) -> None:
        """Clear reasoning cache"""
        self.reasoning_cache.clear()
        self.access_order.clear()


def test_multihop_reasoning():
    """Test multi-hop reasoning system"""
    print("🧪 Testing Multi-Hop Reasoning System")

    # Create sample knowledge graph
    from clost_reasoning import ComedyKnowledgeGraph, ComedyConcept
    kg = ComedyKnowledgeGraph(embedding_dim=768)

    # Add sample concepts
    concepts = [
        ComedyConcept("setup", "Setup Concept", "setup", torch.randn(768), {}, {}),
        ComedyConcept("bridge1", "Bridge Concept 1", "semantic", torch.randn(768), {}, {}),
        ComedyConcept("bridge2", "Bridge Concept 2", "causal", torch.randn(768), {}, {}),
        ComedyConcept("punchline", "Punchline Concept", "punchline", torch.randn(768), {}, {})
    ]

    for concept in concepts:
        kg.add_concept(concept)

    # Add relationships
    kg.add_relationship("setup", "bridge1", "semantic", 0.8)
    kg.add_relationship("bridge1", "bridge2", "causal", 0.7)
    kg.add_relationship("bridge2", "punchline", "subverts", 0.9)

    # Test multi-hop reasoning
    reasoning_engine = MultiHopReasoningEngine()

    print("🔍 Finding reasoning paths...")
    paths = reasoning_engine.find_reasoning_paths(kg, "setup", "punchline")

    print(f"   Found {len(paths)} paths:")
    for i, path in enumerate(paths):
        print(f"   Path {i + 1}: {path.path}")
        print(f"      Confidence: {path.confidence:.4f}")
        print(f"      Type: {path.path_type}")
        print(f"      Steps: {path.reasoning_steps}")

    # Test comprehensive analysis
    print("📊 Running comprehensive analysis...")
    analysis = reasoning_engine.analyze_multi_hop_reasoning(
        kg, [concepts[0]], [concepts[3]]
    )

    print(f"   Best path confidence: {analysis.best_path.confidence:.4f}")
    print(f"   Path diversity: {analysis.path_diversity:.4f}")
    print(f"   Reasoning complexity: {analysis.reasoning_complexity:.4f}")
    print(f"   Humor mechanisms: {analysis.humor_mechanisms}")

    # Test memory-efficient version
    print("💾 Testing memory-efficient version...")
    efficient_engine = MemoryEfficientMultiHopReasoning()

    paths_efficient = efficient_engine.find_paths_efficient(kg, "setup", "punchline")
    print(f"   Found {len(paths_efficient)} paths (memory-efficient)")

    print("✅ Multi-Hop Reasoning System Test Complete!")
    return True


if __name__ == "__main__":
    test_multihop_reasoning()