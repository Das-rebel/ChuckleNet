#!/usr/bin/env python3
"""
Build a Knowledge Graph from LinkedIn Posts
Extracts entities, relationships, and key themes to visualize insights
"""

import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from datetime import datetime

class LinkedInKnowledgeGraph:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.posts = []
        self.G = nx.Graph()
        self.entities = defaultdict(int)
        self.relationships = defaultdict(int)
        self.themes = []
        
    def load_posts(self):
        """Load posts from JSON file"""
        print("📂 Loading posts from database...")
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        # Extract all posts
        for cat, post_list in data.get('posts_by_category', {}).items():
            self.posts.extend(post_list)
        
        print(f"✅ Loaded {len(self.posts)} posts")
    
    def extract_entities(self, text: str) -> Set[str]:
        """Extract entities (concepts, terms) from text"""
        entities = set()
        
        # Extract capitalized phrases (potential concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        entities.update([c.strip() for c in capitalized if len(c.split()) <= 4])
        
        # Extract common business/marketing terms
        business_terms = [
            'CAC', 'LTV', 'ROAS', 'ROI', 'CPA', 'CPC', 'CPM',
            'Growth', 'Marketing', 'Advertising', 'Campaign',
            'Funnel', 'Conversion', 'Retention', 'Acquisition',
            'Brand', 'Customer', 'User', 'Product', 'Revenue',
            'AI', 'Technology', 'Analytics', 'Data', 'Metrics',
            'Strategy', 'Planning', 'Execution', 'Optimization'
        ]
        
        text_upper = text.upper()
        for term in business_terms:
            if term.upper() in text_upper:
                entities.add(term)
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        entities.update(hashtags)
        
        return entities
    
    def extract_key_concepts(self):
        """Extract key concepts and relationships from all posts"""
        print("🔍 Extracting entities and relationships...")
        
        concept_counter = Counter()
        category_posts = defaultdict(list)
        
        for post in self.posts:
            text = post.get('text', '').lower()
            category = None
            
            # Determine category from post content
            for cat, post_list in self.posts_by_category.items():
                if post in post_list:
                    category = cat
                    break
            
            # Extract domain-specific concepts
            if 'cac' in text or 'customer acquisition' in text:
                concept_counter['Customer Acquisition Cost'] += 1
                self.G.add_node('Customer Acquisition Cost', type='concept', count=concept_counter['Customer Acquisition Cost'])
                self.G.add_edge('All Posts', 'Customer Acquisition Cost', weight=1)
            
            if 'ltv' in text or 'lifetime value' in text:
                concept_counter['Lifetime Value'] += 1
                self.G.add_node('Lifetime Value', type='concept', count=concept_counter['Lifetime Value'])
                self.G.add_edge('All Posts', 'Lifetime Value', weight=1)
            
            if 'roas' in text or 'return on ad spend' in text:
                concept_counter['ROAS'] += 1
                self.G.add_node('ROAS', type='concept', count=concept_counter['ROAS'])
                self.G.add_edge('All Posts', 'ROAS', weight=1)
            
            if 'funnel' in text:
                concept_counter['Marketing Funnel'] += 1
                self.G.add_node('Marketing Funnel', type='concept', count=concept_counter['Marketing Funnel'])
                self.G.add_edge('All Posts', 'Marketing Funnel', weight=1)
            
            if 'campaign' in text:
                concept_counter['Campaign Management'] += 1
                self.G.add_node('Campaign Management', type='concept', count=concept_counter['Campaign Management'])
                self.G.add_edge('All Posts', 'Campaign Management', weight=1)
            
            if 'brand' in text or 'branding' in text:
                concept_counter['Brand Strategy'] += 1
                self.G.add_node('Brand Strategy', type='concept', count=concept_counter['Brand Strategy'])
                self.G.add_edge('All Posts', 'Brand Strategy', weight=1)
            
            if 'growth' in text:
                concept_counter['Growth Marketing'] += 1
                self.G.add_node('Growth Marketing', type='concept', count=concept_counter['Growth Marketing'])
                self.G.add_edge('All Posts', 'Growth Marketing', weight=1)
            
            if 'ai' in text or 'artificial intelligence' in text:
                concept_counter['AI/Technology'] += 1
                self.G.add_node('AI/Technology', type='concept', count=concept_counter['AI/Technology'])
                self.G.add_edge('All Posts', 'AI/Technology', weight=1)
            
            if 'analytics' in text or 'data' in text:
                concept_counter['Analytics & Data'] += 1
                self.G.add_node('Analytics & Data', type='concept', count=concept_counter['Analytics & Data'])
                self.G.add_edge('All Posts', 'Analytics & Data', weight=1)
            
            # Extract entities from text
            entities = self.extract_entities(post.get('text', ''))
            for entity in entities:
                self.entities[entity] += 1
                self.G.add_node(entity, type='concept', count=self.entities[entity])
                self.G.add_edge('All Posts', entity, weight=1)
        
            # Add category nodes
        categories = Counter()
        for post in self.posts:
            # Find which category this post belongs to
            for cat_name, post_list in self.posts_by_category.items():
                if post in post_list:
                    categories[cat_name] += 1
                    self.G.add_node(cat_name, type='category', count=categories[cat_name])
                    # Handle comments being either int or list
                    comments = post.get('comments', 0)
                    if isinstance(comments, list):
                        comments = len(comments)
                    reactions = post.get('reactions', 0)
                    if isinstance(reactions, list):
                        reactions = len(reactions)
                    self.G.add_edge('All Posts', cat_name, weight=reactions + comments)
        
        print(f"✅ Extracted {len(self.entities)} unique entities")
        print(f"✅ Top concepts: {dict(concept_counter.most_common(10))}")
        
        self.top_concepts = concept_counter
    
    def analyze_themes(self):
        """Analyze main themes and extract crux insights"""
        print("📊 Analyzing themes and extracting crux...")
        
        # Count topics by category
        category_topics = defaultdict(Counter)
        
        for post in self.posts:
            text = post.get('text', '').lower()
            category = None
            
            # Find category
            for cat_name, post_list in self.posts_by_category.items():
                if post in post_list:
                    category = cat_name
                    break
            
            if category:
                # Extract topic keywords
                if 'cac' in text or 'acquisition cost' in text:
                    category_topics[category]['Customer Acquisition'] += 1
                if 'funnel' in text or 'conversion' in text:
                    category_topics[category]['Conversion Optimization'] += 1
                if 'brand' in text:
                    category_topics[category]['Branding'] += 1
                if 'campaign' in text:
                    category_topics[category]['Campaign Strategy'] += 1
                if 'growth' in text:
                    category_topics[category]['Growth Hacking'] += 1
        
        # Extract crux (main insights)
        self.themes = []
        
        # Marketing & Advertising insights
        marketing_posts = [p for cat, pl in self.posts_by_category.items() if 'Marketing' in cat for p in pl]
        if marketing_posts:
            self.themes.append({
                'theme': 'Marketing Expertise',
                'count': len(marketing_posts),
                'insights': [
                    'Focus on CAC optimization and growth strategies',
                    'Emphasis on campaign management and ROI',
                    'Understanding of marketing funnel dynamics',
                    'Brand positioning and customer acquisition'
                ]
            })
        
        # Technology & AI insights
        tech_posts = [p for cat, pl in self.posts_by_category.items() if 'Technology' in cat or 'AI' in cat for p in pl]
        if tech_posts:
            self.themes.append({
                'theme': 'Technology Integration',
                'count': len(tech_posts),
                'insights': [
                    'Integration of AI in marketing strategies',
                    'Data-driven decision making',
                    'Analytics and measurement focus'
                ]
            })
        
        print(f"✅ Identified {len(self.themes)} main themes")
    
    def build_graph(self):
        """Build the complete knowledge graph"""
        print("🕸️  Building knowledge graph...")
        
        # Load posts
        self.load_posts()
        
        # Organize posts by category
        self.posts_by_category = defaultdict(list)
        with open(self.json_file, 'r') as f:
            data = json.load(f)
            for cat, post_list in data.get('posts_by_category', {}).items():
                self.posts_by_category[cat] = post_list
        
        # Central hub: All Posts
        self.G.add_node('All Posts', type='hub', count=len(self.posts), size=500)
        
        # Extract concepts
        self.extract_key_concepts()
        
        # Analyze themes
        self.analyze_themes()
        
        # Add relationships between concepts
        self.add_concept_relationships()
        
        print(f"✅ Graph built with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges")
    
    def add_concept_relationships(self):
        """Add relationships between related concepts"""
        # Core marketing concepts
        marketing_core = ['Customer Acquisition Cost', 'Lifetime Value', 'ROAS', 'Marketing Funnel']
        for i, concept1 in enumerate(marketing_core):
            for concept2 in marketing_core[i+1:]:
                if concept1 in self.G and concept2 in self.G:
                    self.G.add_edge(concept1, concept2, type='related', weight=5)
        
        # Strategy concepts
        strategy_concepts = ['Brand Strategy', 'Growth Marketing', 'Campaign Management']
        for i, concept1 in enumerate(strategy_concepts):
            for concept2 in strategy_concepts[i+1:]:
                if concept1 in self.G and concept2 in self.G:
                    self.G.add_edge(concept1, concept2, type='related', weight=3)
    
    def visualize(self, output_file: str = 'knowledge_graph.png'):
        """Create visualization of the knowledge graph"""
        print("🎨 Creating visualization...")
        
        plt.figure(figsize=(24, 18))
        
        # Use spring layout for better visualization
        pos = nx.spring_layout(self.G, k=3, iterations=50, seed=42)
        
        # Color nodes by type
        node_colors = []
        node_sizes = []
        
        for node in self.G.nodes():
            node_type = self.G.nodes[node].get('type', 'other')
            if node_type == 'hub':
                node_colors.append('#FF6B6B')  # Red for hub
                node_sizes.append(3000)
            elif node_type == 'category':
                node_colors.append('#4ECDC4')  # Teal for categories
                node_sizes.append(1500)
            elif node_type == 'concept':
                node_colors.append('#95E1D3')  # Light teal for concepts
                count = self.G.nodes[node].get('count', 1)
                node_sizes.append(300 + count * 20)
            else:
                node_colors.append('#F7DC6F')  # Yellow for others
                node_sizes.append(500)
        
        # Draw edges with weights
        edges = self.G.edges()
        weights = [self.G[u][v].get('weight', 1) for u, v in edges]
        
        # Normalize weights for visualization
        if weights:
            max_weight = max(weights)
            edge_widths = [w / max_weight * 5 for w in weights]
        else:
            edge_widths = [1] * len(edges)
        
        nx.draw_networkx_edges(self.G, pos, alpha=0.3, width=edge_widths, edge_color='gray')
        
        # Draw nodes
        nx.draw_networkx_nodes(self.G, pos, node_color=node_colors, 
                              node_size=node_sizes, alpha=0.9)
        
        # Add labels for important nodes
        important_nodes = ['All Posts'] + list(self.top_concepts.keys())[:15]
        labels = {}
        for node in self.G.nodes():
            if node in important_nodes or self.G.nodes[node].get('type') == 'category':
                labels[node] = node
            elif len(node) < 15:
                labels[node] = node
        
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, font_weight='bold')
        
        plt.title('LinkedIn Posts Knowledge Graph\nKey Concepts, Categories, and Relationships', 
                 fontsize=20, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"✅ Visualization saved: {output_file}")
        
        return output_file
    
    def generate_insights_report(self, output_file: str = 'knowledge_graph_insights.md'):
        """Generate a markdown report with insights"""
        print("📝 Generating insights report...")
        
        report = []
        report.append("# LinkedIn Posts Knowledge Graph - Key Insights\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Total Posts Analyzed:** {len(self.posts)}\n")
        report.append("---\n\n")
        
        # Crux Insights
        report.append("## 🎯 The Crux - Main Insights\n\n")
        
        report.append("### Core Expertise Areas\n\n")
        
        # Top concepts
        report.append("#### Most Discussed Concepts:\n\n")
        for concept, count in self.top_concepts.most_common(10):
            pct = (count / len(self.posts)) * 100
            report.append(f"1. **{concept}**: Mentioned in {count} posts ({pct:.1f}%)\n")
        
        report.append("\n")
        
        # Theme insights
        report.append("### Main Themes & Insights\n\n")
        for theme in self.themes:
            report.append(f"#### {theme['theme']} ({theme['count']} posts)\n\n")
            for insight in theme['insights']:
                report.append(f"- {insight}\n")
            report.append("\n")
        
        # Category distribution
        report.append("### Category Distribution\n\n")
        total_posts = len(self.posts)
        for cat, posts_list in sorted(self.posts_by_category.items(), 
                                     key=lambda x: len(x[1]), reverse=True):
            pct = (len(posts_list) / total_posts) * 100
            report.append(f"- **{cat}**: {len(posts_list)} posts ({pct:.1f}%)\n")
        
        report.append("\n")
        
        # Graph statistics
        report.append("### Knowledge Graph Statistics\n\n")
        report.append(f"- **Total Nodes**: {self.G.number_of_nodes()}\n")
        report.append(f"- **Total Edges**: {self.G.number_of_edges()}\n")
        report.append(f"- **Unique Concepts**: {len(self.entities)}\n")
        report.append(f"- **Categories**: {len(self.posts_by_category)}\n")
        
        report.append("\n")
        
        # Key Relationships
        report.append("### Key Relationships Identified\n\n")
        
        # Find strongly connected concepts
        marketing_core = ['Customer Acquisition Cost', 'Marketing Funnel', 'Growth Marketing']
        for node in marketing_core:
            if node in self.G:
                neighbors = list(self.G.neighbors(node))
                if neighbors:
                    report.append(f"**{node}** connects to: {', '.join(neighbors[:5])}\n\n")
        
        # Write report
        with open(output_file, 'w') as f:
            f.write(''.join(report))
        
        print(f"✅ Insights report saved: {output_file}")
        return output_file
    
    def export_graph_json(self, output_file: str = 'knowledge_graph.json'):
        """Export graph data as JSON for interactive visualization"""
        print("💾 Exporting graph data...")
        
        graph_data = {
            'nodes': [],
            'links': []
        }
        
        # Export nodes
        for node in self.G.nodes():
            node_data = {
                'id': node,
                'type': self.G.nodes[node].get('type', 'other'),
                'count': self.G.nodes[node].get('count', 1)
            }
            graph_data['nodes'].append(node_data)
        
        # Export edges
        for source, target in self.G.edges():
            edge_data = {
                'source': source,
                'target': target,
                'weight': self.G[source][target].get('weight', 1),
                'type': self.G[source][target].get('type', 'connection')
            }
            graph_data['links'].append(edge_data)
        
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"✅ Graph JSON exported: {output_file}")
        return output_file


def main():
    kg = LinkedInKnowledgeGraph('linkedin_jagadeesh_posts_database_enhanced.json')
    
    # Build graph
    kg.build_graph()
    
    # Create visualization
    kg.visualize('linkedin_knowledge_graph.png')
    
    # Generate insights
    kg.generate_insights_report('knowledge_graph_insights.md')
    
    # Export for interactive tools
    kg.export_graph_json('knowledge_graph_data.json')
    
    print("\n" + "="*70)
    print("🎉 Knowledge Graph Created Successfully!")
    print("="*70)
    print("\n📁 Generated Files:")
    print("  - linkedin_knowledge_graph.png (Visualization)")
    print("  - knowledge_graph_insights.md (Insights Report)")
    print("  - knowledge_graph_data.json (Graph Data)")
    print("\n✨ The crux: See knowledge_graph_insights.md for key insights")


if __name__ == "__main__":
    main()
