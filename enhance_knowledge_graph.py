#!/usr/bin/env python3
"""
Enhanced Knowledge Graph Builder
Implements improvements: search, filtering, node details, co-occurrence, etc.
"""

import json
from collections import defaultdict, Counter
import re

class EnhancedKnowledgeGraph:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.posts = []
        self.concept_cooccurrence = defaultdict(int)
        self.concept_engagement = defaultdict(list)
        
    def load_data(self):
        """Load posts and analyze"""
        print("📂 Loading and analyzing data...")
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        # Extract all posts
        for cat, post_list in data.get('posts_by_category', {}).items():
            for post in post_list:
                post['category'] = cat
                self.posts.append(post)
        
        print(f"✅ Loaded {len(self.posts)} posts")
    
    def analyze_cooccurrence(self):
        """Analyze which concepts appear together"""
        print("🔗 Analyzing concept co-occurrence...")
        
        key_concepts = [
            'Customer Acquisition Cost', 'CAC', 'LTV', 'Lifetime Value',
            'ROAS', 'ROI', 'Marketing Funnel', 'Brand Strategy',
            'Growth Marketing', 'Campaign Management', 'AI/Technology',
            'Analytics & Data', 'Funnel', 'Conversion'
        ]
        
        for post in self.posts:
            text = post.get('text', '').lower()
            concepts_in_post = []
            
            for concept in key_concepts:
                if concept.lower() in text or concept.split()[0].lower() in text:
                    concepts_in_post.append(concept)
            
            # Count co-occurrences
            for i, concept1 in enumerate(concepts_in_post):
                for concept2 in concepts_in_post[i+1:]:
                    pair = tuple(sorted([concept1, concept2]))
                    self.concept_cooccurrence[pair] += 1
                    
                    # Track engagement for each concept
                    reactions = post.get('reactions', 0)
                    if isinstance(reactions, list):
                        reactions = len(reactions)
                    comments = post.get('comments', 0)
                    if isinstance(comments, list):
                        comments = len(comments)
                    engagement = reactions + comments
                    self.concept_engagement[concept1].append(engagement)
                    self.concept_engagement[concept2].append(engagement)
        
        # Calculate average engagement per concept
        self.concept_avg_engagement = {
            k: sum(v)/len(v) if v else 0
            for k, v in self.concept_engagement.items()
        }
        
        print(f"✅ Found {len(self.concept_cooccurrence)} concept pairs")
        print(f"✅ Top pairs: {sorted(self.concept_cooccurrence.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    def calculate_centrality(self):
        """Calculate node centrality metrics"""
        print("📊 Calculating centrality metrics...")
        
        # Build adjacency from co-occurrence
        concept_connections = defaultdict(int)
        
        for (c1, c2), count in self.concept_cooccurrence.items():
            concept_connections[c1] += count
            concept_connections[c2] += count
        
        self.centrality_scores = dict(sorted(concept_connections.items(), 
                                            key=lambda x: x[1], reverse=True))
        
        print(f"✅ Centrality calculated for {len(self.centrality_scores)} concepts")
    
    def generate_enhanced_graph_data(self):
        """Generate enhanced graph data with all improvements"""
        print("🎨 Generating enhanced graph data...")
        
        # Core nodes
        nodes = [
            {"id": "All Posts", "type": "hub", "count": len(self.posts), "centrality": 100}
        ]
        
        # Category nodes
        categories = Counter([p.get('category') for p in self.posts])
        for cat, count in categories.items():
            nodes.append({
                "id": cat,
                "type": "category",
                "count": count,
                "centrality": count * 2
            })
        
        # Key concept nodes
        key_concepts = {
            'AI/Technology': 303,
            'Brand Strategy': 276,
            'Growth Marketing': 234,
            'Campaign Management': 193,
            'Analytics & Data': 93,
            'Customer Acquisition Cost': 53,
            'ROAS': 29,
            'Marketing Funnel': 27,
            'Lifetime Value': 19
        }
        
        for concept, count in key_concepts.items():
            avg_engagement = self.concept_avg_engagement.get(concept, 0)
            centrality = self.centrality_scores.get(concept, count)
            
            nodes.append({
                "id": concept,
                "type": "concept",
                "count": count,
                "centrality": centrality,
                "avg_engagement": round(avg_engagement, 1)
            })
        
        # Links with weights based on co-occurrence
        links = []
        
        # Hub to categories
        for cat in categories.keys():
            links.append({
                "source": "All Posts",
                "target": cat,
                "weight": categories[cat],
                "type": "category_connection"
            })
        
        # Hub to concepts (based on mention count)
        for concept, count in key_concepts.items():
            links.append({
                "source": "All Posts",
                "target": concept,
                "weight": count,
                "type": "concept_connection"
            })
        
        # Co-occurrence links
        for (c1, c2), count in self.concept_cooccurrence.items():
            if count >= 2:  # Only show significant co-occurrences
                links.append({
                    "source": c1,
                    "target": c2,
                    "weight": count,
                    "type": "cooccurrence",
                    "strength": "strong" if count >= 5 else "medium" if count >= 3 else "weak"
                })
        
        # Category to concept links
        concept_to_category = defaultdict(set)
        for post in self.posts:
            cat = post.get('category')
            text = post.get('text', '').lower()
            for concept in key_concepts.keys():
                if concept.lower() in text:
                    concept_to_category[concept].add(cat)
        
        for concept, cats in concept_to_category.items():
            for cat in cats:
                links.append({
                    "source": cat,
                    "target": concept,
                    "weight": len([p for p in self.posts 
                                  if p.get('category') == cat and concept.lower() in p.get('text', '').lower()]),
                    "type": "category_concept"
                })
        
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "total_posts": len(self.posts),
                "total_concepts": len(key_concepts),
                "total_connections": len(links),
                "cooccurrence_pairs": len(self.concept_cooccurrence)
            }
        }
    
    def generate_insights(self):
        """Generate AI-style insights"""
        insights = []
        
        # Top concepts
        top_concepts = sorted(self.concept_avg_engagement.items(), 
                            key=lambda x: x[1], reverse=True)[:5]
        
        insights.append({
            "type": "top_engagement",
            "title": "Most Engaging Topics",
            "description": "Topics that generate the most engagement per post",
            "data": [{"concept": k, "avg_engagement": round(v, 1)} for k, v in top_concepts]
        })
        
        # Strongest relationships
        top_pairs = sorted(self.concept_cooccurrence.items(), 
                          key=lambda x: x[1], reverse=True)[:5]
        
        insights.append({
            "type": "strong_relationships",
            "title": "Strongest Concept Relationships",
            "description": "Concepts that appear together most frequently",
            "data": [{"pair": f"{k[0]} ↔ {k[1]}", "count": v} for k, v in top_pairs]
        })
        
        # Most central concepts
        top_central = sorted(self.centrality_scores.items(), 
                           key=lambda x: x[1], reverse=True)[:5]
        
        insights.append({
            "type": "centrality",
            "title": "Most Central Concepts",
            "description": "Concepts that connect to the most other concepts",
            "data": [{"concept": k, "connections": v} for k, v in top_central]
        })
        
        return insights


def main():
    kg = EnhancedKnowledgeGraph('linkedin_jagadeesh_posts_database_enhanced.json')
    
    # Load and analyze
    kg.load_data()
    kg.analyze_cooccurrence()
    kg.calculate_centrality()
    
    # Generate enhanced graph
    graph_data = kg.generate_enhanced_graph_data()
    
    # Save enhanced data
    with open('knowledge_graph_enhanced_data.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"\n✅ Enhanced graph data saved!")
    print(f"   Nodes: {len(graph_data['nodes'])}")
    print(f"   Links: {len(graph_data['links'])}")
    
    # Generate insights
    insights = kg.generate_insights()
    
    with open('knowledge_graph_insights_enhanced.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    print(f"✅ Enhanced insights saved!")
    
    return graph_data, insights


if __name__ == "__main__":
    main()
