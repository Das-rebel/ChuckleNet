"""
CLoST Knowledge Base Builder
Comprehensive comedy patterns, tropes, and concept relationships

Author: GCACU Autonomous Laughter Prediction System
Date: 2026-04-03
"""

import torch
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import numpy as np
from pathlib import Path


@dataclass
class ComedyPattern:
    """
    Represents a comedy pattern or trope

    Attributes:
        id: Unique identifier
        name: Pattern name
        category: Pattern category
        description: Pattern description
        examples: Example jokes/routines
        embedding: Semantic embedding
        relationships: Related patterns
    """
    id: str
    name: str
    category: str
    description: str
    examples: List[str]
    embedding: torch.Tensor
    relationships: Dict[str, List[str]]


class ComedyKnowledgeBase:
    """
    Comprehensive knowledge base for comedy concepts, patterns, and tropes
    """

    def __init__(self, embedding_dim: int = 768):
        """
        Initialize comedy knowledge base

        Args:
            embedding_dim: Dimension of concept embeddings
        """
        self.embedding_dim = embedding_dim
        self.patterns: Dict[str, ComedyPattern] = {}
        self.semantic_clusters: Dict[str, List[str]] = {}
        self.causal_templates: Dict[str, List[str]] = {}

        # Initialize with base comedy knowledge
        self._initialize_comedy_patterns()
        self._initialize_causal_templates()
        self._initialize_semantic_clusters()

    def _initialize_comedy_patterns(self) -> None:
        """Initialize comprehensive comedy patterns and tropes"""

        # Incongruity-Based Patterns
        incongruity_patterns = [
            {
                "id": "setup_punchline_incongruity",
                "name": "Setup-Punchline Incongruity",
                "category": "incongruity",
                "description": "Traditional setup creates expectation, punchline violates it",
                "examples": [
                    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                    "I used to hate facial hair, but then it grew on me."
                ],
                "relationships": {"causes": ["expectation_violation", "surprise"]}
            },
            {
                "id": "cultural_incongruity",
                "name": "Cultural Incongruity",
                "category": "cultural",
                "description": "Conflict between cultural expectations and reality",
                "examples": [
                    "Indian parents: If you walk into a room with your shoes on, you're disrespecting the house. If you walk in barefoot, you're disrespecting their floor."
                ],
                "relationships": {"references": ["cultural_norms", "family_dynamics"]}
            },
            {
                "id": "logical_incongruity",
                "name": "Logical Incongruity",
                "category": "logical",
                "description": "Applying logic where it doesn't belong or breaking logical chains",
                "examples": [
                    "I'm on a whiskey diet. I've lost three days already.",
                    "I have an Epipen. My friend gave it to me when he was dying. It seemed very important to him that I have it."
                ],
                "relationships": {"contradicts": ["rational_thought", "common_sense"]}
            }
        ]

        # Wordplay and Linguistic Patterns
        wordplay_patterns = [
            {
                "id": "pun_double_entendre",
                "name": "Pun/Double Entendre",
                "category": "linguistic",
                "description": "Words with multiple meanings creating ambiguity",
                "examples": [
                    "I'm reading a book about anti-gravity. It's impossible to put down.",
                    "Time flies like an arrow. Fruit flies like a banana."
                ],
                "relationships": {"enables": ["ambiguity", "semantic_shift"]}
            },
            {
                "id": "malapropism",
                "name": "Malapropism",
                "category": "linguistic",
                "description": "Incorrect word usage that creates humor",
                "examples": [
                    "Dance to the beat of a different drummer (mispronounced as 'dance to the beat of a different drumer')"
                ],
                "relationships": {"subverts": ["proper_speech", "vocabulary"]}
            },
            {
                "id": "irony_situational",
                "name": "Situational Irony",
                "category": "irony",
                "description": "Outcome opposite to what was expected",
                "examples": [
                    "A fire station burning down",
                    "A marriage counselor getting divorced"
                ],
                "relationships": {"contradicts": ["expectations", "intentions"]}
            }
        ]

        # Causal Patterns
        causal_patterns = [
            {
                "id": "counterfactual_humor",
                "name": "Counterfactual Humor",
                "category": "causal",
                "description": "Exploring what would happen if impossible things were true",
                "examples": [
                    "If I had a dollar for every time I confused 'their' and 'there', I wouldn't care because I'd be rich.",
                    "What if plants were actually farming us? Giving us oxygen so we'd reproduce and spread them?"
                ],
                "relationships": {"enables": ["imagination", "absurd_reasoning"]}
            },
            {
                "id": "causal_chain_reversal",
                "name": "Causal Chain Reversal",
                "category": "causal",
                "description": "Reversing expected cause-effect relationships",
                "examples": [
                    "I don't exercise because it makes me tired. Being tired makes me eat more. Eating more makes me gain weight. So exercise makes me fat.",
                    "I didn't fail the test. The test failed me."
                ],
                "relationships": {"subverts": ["logical_causality", "rational_thought"]}
            },
            {
                "id": "exaggerated_causality",
                "name": "Exaggerated Causality",
                "category": "causal",
                "description": "Blowing cause-effect relationships out of proportion",
                "examples": [
                    "If I eat one more cookie, I'll literally explode.",
                    "My phone battery drains so fast, I can watch it go from 100% to 0% in real time."
                ],
                "relationships": {"exaggerates": ["cause_effect", "consequences"]}
            }
        ]

        # Character and Situational Patterns
        character_patterns = [
            {
                "id": "fish_out_of_water",
                "name": "Fish Out of Water",
                "category": "character",
                "description": "Character in unfamiliar environment",
                "examples": [
                    "A tech worker at a traditional factory",
                    "A city person in rural areas",
                    "An introvert at a party"
                ],
                "relationships": {"creates": ["conflict", "misunderstanding", "growth"]}
            },
            {
                "id": "straight_man_funny_man",
                "name": "Straight Man/Funny Man",
                "category": "character",
                "description": "Contrast between serious and comedic characters",
                "examples": [
                    "Dean Martin and Jerry Lewis",
                    "Abbott and Costello",
                    "Serious interviewer vs. eccentric guest"
                ],
                "relationships": {"enables": ["contrast", "timing", "reaction"]}
            },
            {
                "id": "relatable_struggle",
                "name": "Relatable Struggle",
                "category": "situational",
                "description": "Common life experiences exaggerated for humor",
                "examples": [
                    "Trying to cancel a subscription",
                    "Dealing with customer service",
                    "Social anxiety at parties",
                    "Imposter syndrome at work"
                ],
                "relationships": {"references": ["everyday_life", "universal_experiences"]}
            }
        ]

        # Cultural and Social Patterns
        cultural_patterns = [
            {
                "id": "cultural_stereotype_subversion",
                "name": "Cultural Stereotype Subversion",
                "category": "cultural",
                "description": "Playing with and subverting cultural expectations",
                "examples": [
                    "Indian comedian discussing arranged marriage expectations",
                    "Asian comedian addressing model minority myth",
                    "British comedian commenting on class system"
                ],
                "relationships": {"subverts": ["stereotypes", "cultural_expectations"]}
            },
            {
                "id": "generational_gap",
                "name": "Generational Gap",
                "category": "cultural",
                "description": "Humor from differences between generations",
                "examples": [
                    "Boomers vs. Millennials",
                    "Gen Z vs. everyone else",
                    "Technology adoption differences"
                ],
                "relationships": {"contrasts": ["generational_values", "technology_use"]}
            },
            {
                "id": "social Commentary",
                "name": "Social Commentary",
                "category": "social",
                "description": "Using humor to comment on social issues",
                "examples": [
                    "Political satire",
                    "Social inequality humor",
                    "Workplace culture critique"
                ],
                "relationships": {"critiques": ["social_norms", "politics", "institutions"]}
            }
        ]

        # Timing and Delivery Patterns
        timing_patterns = [
            {
                "id": "callback",
                "name": "Callback",
                "category": "timing",
                "description": "Referencing earlier joke later for enhanced effect",
                "examples": [
                    "Establishing a character trait early, referencing it later",
                    "Revisiting a failed setup with new context"
                ],
                "relationships": {"enhances": ["continuity", "audience_engagement"]}
            },
            {
                "id": "rule_of_three",
                "name": "Rule of Three",
                "category": "timing",
                "description": "Two similar items followed by a twist",
                "examples": [
                    "I can't believe I ate the whole thing. I can't believe I ate the whole thing. I can't believe they charged me $15.",
                    "Red, green, and... blue."
                ],
                "relationships": {"creates": ["anticipation", "pattern_breaking"]}
            },
            {
                "id": "pause_for_effect",
                "name": "Pause for Effect",
                "category": "timing",
                "description": "Strategic silence before or after punchline",
                "examples": [
                    "Setup... [pause]... punchline",
                    "Punchline... [pause]... follow-up"
                ],
                "relationships": {"enhances": ["timing", "surprise", "audience_reaction"]}
            }
        ]

        # Combine all patterns
        all_patterns = (
            incongruity_patterns +
            wordplay_patterns +
            causal_patterns +
            character_patterns +
            cultural_patterns +
            timing_patterns
        )

        # Create pattern objects
        for pattern_data in all_patterns:
            embedding = self._generate_pattern_embedding(pattern_data)
            pattern = ComedyPattern(
                id=pattern_data["id"],
                name=pattern_data["name"],
                category=pattern_data["category"],
                description=pattern_data["description"],
                examples=pattern_data["examples"],
                embedding=embedding,
                relationships=pattern_data["relationships"]
            )
            self.patterns[pattern.id] = pattern

    def _initialize_causal_templates(self) -> None:
        """Initialize causal reasoning templates for humor"""
        self.causal_templates = {
            "expectation_violation": [
                "Setup establishes X, punchline reveals not-X",
                "Audience expects A, comedian delivers B",
                "Normal outcome subverted by absurd alternative"
            ],
            "causality_reversal": [
                "Effect causes cause instead of vice versa",
                "Comedy logic reverses scientific causality",
                "Temporal causality violated for humor"
            ],
            "exaggerated_consequences": [
                "Small cause produces ridiculous effects",
                "Mild action leads to extreme outcomes",
                "Disproportionate cause-effect relationships"
            ],
            "false_premise": [
                "Joke begins with absurd proposition treated as fact",
                "Impossible scenario presented as normal",
                "Logical fallacy accepted as premise"
            ],
            "delayed_realization": [
                "Setup establishes false context",
                "Punchline provides true context",
                "Audience must mentally reconstruct causality"
            ]
        }

    def _initialize_semantic_clusters(self) -> None:
        """Initialize semantic clusters of related concepts"""
        self.semantic_clusters = {
            "wordplay": ["pun", "double_entendre", "malapropism", "irony", "satire"],
            "situational": ["fish_out_of_water", "relatable_struggle", "social_commentary"],
            "cultural": ["cultural_incongruity", "generational_gap", "stereotype_subversion"],
            "character": ["straight_man_funny_man", "eccentric_character", "everyman"],
            "timing": ["callback", "rule_of_three", "pause_for_effect", "timing_comedy"],
            "causal": ["counterfactual", "causal_reversal", "exaggerated_causality", "false_premise"]
        }

    def _generate_pattern_embedding(self, pattern_data: Dict[str, Any]) -> torch.Tensor:
        """Generate embedding for comedy pattern"""
        # Combine name, description, and examples for embedding
        text = f"{pattern_data['name']} {pattern_data['description']} {' '.join(pattern_data['examples'])}"

        # For now, use random embedding (would use actual language model in production)
        # This is a placeholder - real implementation would use BERT/similar
        torch.manual_seed(hash(text) % 1000)
        embedding = torch.randn(self.embedding_dim)
        return embedding

    def get_pattern_by_id(self, pattern_id: str) -> ComedyPattern:
        """Get pattern by ID"""
        return self.patterns.get(pattern_id)

    def get_patterns_by_category(self, category: str) -> List[ComedyPattern]:
        """Get all patterns in a category"""
        return [p for p in self.patterns.values() if p.category == category]

    def find_similar_patterns(self, pattern_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar patterns by semantic similarity"""
        if pattern_id not in self.patterns:
            return []

        target_pattern = self.patterns[pattern_id]
        target_emb = target_pattern.embedding

        similarities = []
        for other_id, other_pattern in self.patterns.items():
            if other_id != pattern_id:
                similarity = torch.cosine_similarity(
                    target_emb.unsqueeze(0),
                    other_pattern.embedding.unsqueeze(0)
                ).item()
                similarities.append((other_id, similarity))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_causal_template(self, template_type: str) -> List[str]:
        """Get causal reasoning templates"""
        return self.causal_templates.get(template_type, [])

    def export_knowledge_base(self, path: str) -> None:
        """Export knowledge base to JSON file"""
        export_data = {
            "patterns": {},
            "causal_templates": self.causal_templates,
            "semantic_clusters": self.semantic_clusters
        }

        for pattern_id, pattern in self.patterns.items():
            export_data["patterns"][pattern_id] = {
                "id": pattern.id,
                "name": pattern.name,
                "category": pattern.category,
                "description": pattern.description,
                "examples": pattern.examples,
                "embedding": pattern.embedding.tolist(),
                "relationships": pattern.relationships
            }

        with open(path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_knowledge_base(self, path: str) -> None:
        """Import knowledge base from JSON file"""
        with open(path, 'r') as f:
            import_data = json.load(f)

        self.causal_templates = import_data["causal_templates"]
        self.semantic_clusters = import_data["semantic_clusters"]

        for pattern_id, pattern_data in import_data["patterns"].items():
            pattern = ComedyPattern(
                id=pattern_data["id"],
                name=pattern_data["name"],
                category=pattern_data["category"],
                description=pattern_data["description"],
                examples=pattern_data["examples"],
                embedding=torch.tensor(pattern_data["embedding"]),
                relationships=pattern_data["relationships"]
            )
            self.patterns[pattern_id] = pattern


def create_comprehensive_knowledge_graph(knowledge_base: ComedyKnowledgeBase,
                                        embedding_dim: int = 768) -> 'ComedyKnowledgeGraph':
    """
    Create comprehensive knowledge graph from knowledge base

    Args:
        knowledge_base: ComedyKnowledgeBase instance
        embedding_dim: Embedding dimension

    Returns:
        ComedyKnowledgeGraph instance
    """
    from clost_reasoning import ComedyKnowledgeGraph, ComedyConcept

    kg = ComedyKnowledgeGraph(embedding_dim)

    # Add all patterns as concepts
    for pattern_id, pattern in knowledge_base.patterns.items():
        concept = ComedyConcept(
            id=pattern.id,
            name=pattern.name,
            category=pattern.category,
            embedding=pattern.embedding,
            properties={
                "description": pattern.description,
                "examples": pattern.examples
            },
            relationships=pattern.relationships
        )
        kg.add_concept(concept)

    # Add relationships based on semantic clusters
    for cluster_name, pattern_ids in knowledge_base.semantic_clusters.items():
        for i, pattern_id_1 in enumerate(pattern_ids):
            for pattern_id_2 in pattern_ids[i+1:]:
                if pattern_id_1 in kg.concepts and pattern_id_2 in kg.concepts:
                    kg.add_relationship(pattern_id_1, pattern_id_2, "semantic_cluster", 0.8)

    # Add relationships based on pattern relationships
    for pattern_id, pattern in knowledge_base.patterns.items():
        for rel_type, related_patterns in pattern.relationships.items():
            for related_pattern in related_patterns:
                if related_pattern in kg.concepts:
                    kg.add_relationship(pattern_id, related_pattern, rel_type, 0.7)

    return kg


def test_knowledge_base():
    """Test comedy knowledge base"""
    print("🧪 Testing Comedy Knowledge Base")

    # Create knowledge base
    kb = ComedyKnowledgeBase()

    print(f"📊 Total Patterns: {len(kb.patterns)}")
    print(f"🎯 Categories: {set(p.category for p in kb.patterns.values())}")
    print(f"🔗 Causal Templates: {len(kb.causal_templates)}")
    print(f"🎭 Semantic Clusters: {len(kb.semantic_clusters)}")

    # Test pattern retrieval
    print("\n📋 Sample Patterns:")
    for category in ["incongruity", "linguistic", "causal", "character"]:
        patterns = kb.get_patterns_by_category(category)
        print(f"   {category}: {len(patterns)} patterns")
        if patterns:
            print(f"      Example: {patterns[0].name}")

    # Test similarity search
    print("\n🔍 Testing Similarity Search:")
    target_id = "setup_punchline_incongruity"
    similar = kb.find_similar_patterns(target_id, top_k=3)
    for pattern_id, similarity in similar:
        pattern = kb.get_pattern_by_id(pattern_id)
        print(f"   {pattern.name}: {similarity:.4f}")

    # Test causal templates
    print("\n🎯 Testing Causal Templates:")
    for template_type, templates in kb.causal_templates.items():
        print(f"   {template_type}: {len(templates)} templates")

    # Create knowledge graph
    print("\n🕸️ Creating Knowledge Graph:")
    kg = create_comprehensive_knowledge_graph(kb)
    print(f"   Nodes: {len(kg.concepts)}")
    print(f"   Edges: {kg.graph.number_of_edges()}")

    # Test graph operations
    print("\n🔗 Testing Graph Operations:")
    if "setup_punchline_incongruity" in kg.concepts:
        neighbors = kg.get_neighbors("setup_punchline_incongruity")
        print(f"   Neighbors of setup_punchline_incongruity: {len(neighbors)}")

    print("✅ Comedy Knowledge Base Test Complete!")
    return True


if __name__ == "__main__":
    test_knowledge_base()