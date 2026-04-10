#!/usr/bin/env python3
"""
Comprehensive Knowledge Graph Improvements Implementation
Implements all features from the roadmap
"""

import json
import re
from collections import defaultdict, Counter
from datetime import datetime
import math

# For advanced features
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from textblob import TextBlob
    ADVANCED_LIBS = True
except ImportError:
    ADVANCED_LIBS = False
    print("⚠️ Some advanced libraries not available. Install with: pip install scikit-learn textblob")

class ComprehensiveKnowledgeGraph:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.posts = []
        self.concept_cooccurrence = defaultdict(int)
        self.concept_engagement = defaultdict(list)
        self.post_dates = []
        self.topic_model = None
        self.sentiment_scores = {}
        
    def load_data(self):
        """Load posts and extract dates"""
        print("📂 Loading and analyzing data...")
        with open(self.json_file, 'r') as f:
            data = json.load(f)
        
        for cat, post_list in data.get('posts_by_category', {}).items():
            for post in post_list:
                post['category'] = cat
                # Extract date if available
                date_str = post.get('date') or post.get('timestamp')
                if date_str and date_str != 'Unknown':
                    try:
                        post['parsed_date'] = self.parse_date(date_str)
                    except:
                        post['parsed_date'] = None
                else:
                    # Try to extract from text
                    post['parsed_date'] = self.extract_date_from_text(post.get('text', ''))
                
                self.posts.append(post)
                if post['parsed_date']:
                    self.post_dates.append(post['parsed_date'])
        
        print(f"✅ Loaded {len(self.posts)} posts")
        print(f"✅ Extracted {len([d for d in self.post_dates if d])} dates")
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return None
        
        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass
        
        # Try relative dates from text
        if 'ago' in date_str.lower() or 'month' in date_str.lower() or 'year' in date_str.lower():
            return None  # Will handle in extract_date_from_text
        
        return None
    
    def extract_date_from_text(self, text):
        """Extract date from post text"""
        # Look for patterns like "1 year ago", "5 months ago"
        patterns = [
            (r'(\d+)\s*year[s]?\s*ago', -365),
            (r'(\d+)\s*yr\s*ago', -365),
            (r'(\d+)\s*month[s]?\s*ago', -30),
            (r'(\d+)\s*mo\s*ago', -30),
            (r'(\d+)\s*week[s]?\s*ago', -7),
            (r'(\d+)\s*w\s*ago', -7),
            (r'(\d+)\s*day[s]?\s*ago', -1),
        ]
        
        from datetime import timedelta
        today = datetime.now()
        
        for pattern, days_per_unit in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    value = int(match.group(1))
                    days = value * abs(days_per_unit)
                    return today - timedelta(days=days)
                except:
                    pass
        
        return None
    
    def analyze_cooccurrence(self):
        """Analyze concept co-occurrence"""
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
            
            for i, concept1 in enumerate(concepts_in_post):
                for concept2 in concepts_in_post[i+1:]:
                    pair = tuple(sorted([concept1, concept2]))
                    self.concept_cooccurrence[pair] += 1
                    
                    reactions = post.get('reactions', 0)
                    if isinstance(reactions, list):
                        reactions = len(reactions)
                    comments = post.get('comments', 0)
                    if isinstance(comments, list):
                        comments = len(comments)
                    engagement = reactions + comments
                    self.concept_engagement[concept1].append(engagement)
                    self.concept_engagement[concept2].append(engagement)
        
        self.concept_avg_engagement = {
            k: sum(v)/len(v) if v else 0
            for k, v in self.concept_engagement.items()
        }
        
        print(f"✅ Found {len(self.concept_cooccurrence)} concept pairs")
    
    def calculate_centrality(self):
        """Calculate node centrality"""
        print("📊 Calculating centrality metrics...")
        
        concept_connections = defaultdict(int)
        for (c1, c2), count in self.concept_cooccurrence.items():
            concept_connections[c1] += count
            concept_connections[c2] += count
        
        self.centrality_scores = dict(sorted(concept_connections.items(), 
                                            key=lambda x: x[1], reverse=True))
    
    def perform_topic_modeling(self):
        """LDA Topic Modeling to discover hidden topics"""
        if not ADVANCED_LIBS:
            print("⚠️ Skipping topic modeling (libraries not available)")
            return
        
        print("🔍 Performing LDA Topic Modeling...")
        
        # Prepare texts
        texts = [post.get('text', '')[:500] for post in self.posts if post.get('text')]
        
        if len(texts) < 10:
            print("⚠️ Not enough posts for topic modeling")
            return
        
        # Vectorize
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
        try:
            X = vectorizer.fit_transform(texts)
            
            # LDA
            n_topics = min(7, len(texts) // 10)  # Adaptive number of topics
            lda = LatentDirichletAllocation(n_components=n_topics, random_state=42, max_iter=10)
            lda.fit(X)
            
            # Extract topics
            feature_names = vectorizer.get_feature_names_out()
            self.topics = []
            
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                self.topics.append({
                    'id': f'topic_{topic_idx}',
                    'name': f'Topic {topic_idx + 1}',
                    'keywords': top_words[:5],
                    'weight': float(topic.sum())
                })
            
            self.topic_model = lda
            self.vectorizer = vectorizer
            print(f"✅ Discovered {len(self.topics)} topics")
        except Exception as e:
            print(f"⚠️ Topic modeling error: {e}")
            self.topics = []
    
    def analyze_sentiment(self):
        """Analyze sentiment of posts"""
        if not ADVANCED_LIBS:
            print("⚠️ Skipping sentiment analysis (libraries not available)")
            return
        
        print("😊 Analyzing sentiment...")
        
        for i, post in enumerate(self.posts):
            text = post.get('text', '')[:500]  # Limit text length
            if text:
                try:
                    blob = TextBlob(text)
                    sentiment = blob.sentiment.polarity  # -1 to 1
                    self.sentiment_scores[i] = {
                        'polarity': sentiment,
                        'subjectivity': blob.sentiment.subjectivity,
                        'label': 'positive' if sentiment > 0.1 else 'negative' if sentiment < -0.1 else 'neutral'
                    }
                except:
                    self.sentiment_scores[i] = {'polarity': 0, 'subjectivity': 0.5, 'label': 'neutral'}
        
        # Aggregate by concept
        self.concept_sentiment = defaultdict(list)
        key_concepts = ['Customer Acquisition Cost', 'Brand Strategy', 'Growth Marketing', 
                       'Campaign Management', 'AI/Technology']
        
        for i, post in enumerate(self.posts):
            text = post.get('text', '').lower()
            sentiment = self.sentiment_scores.get(i, {}).get('polarity', 0)
            
            for concept in key_concepts:
                if concept.lower() in text:
                    self.concept_sentiment[concept].append(sentiment)
        
        self.concept_avg_sentiment = {
            k: sum(v)/len(v) if v else 0
            for k, v in self.concept_sentiment.items()
        }
        
        print(f"✅ Analyzed sentiment for {len(self.sentiment_scores)} posts")
    
    def generate_timeline_data(self):
        """Generate timeline data for visualization"""
        print("📅 Generating timeline data...")
        
        # Group posts by year/month
        timeline = defaultdict(lambda: defaultdict(int))
        timeline_concepts = defaultdict(lambda: defaultdict(int))
        
        key_concepts = ['Customer Acquisition Cost', 'Brand Strategy', 'Growth Marketing', 
                       'Campaign Management', 'AI/Technology']
        
        for post in self.posts:
            if post.get('parsed_date'):
                date = post['parsed_date']
                year = date.year
                month = date.month
                key = f"{year}-{month:02d}"
                timeline[key]['total'] += 1
                
                text = post.get('text', '').lower()
                for concept in key_concepts:
                    if concept.lower() in text:
                        timeline_concepts[key][concept] += 1
        
        self.timeline_data = {
            'by_period': dict(timeline),
            'concepts_by_period': {k: dict(v) for k, v in timeline_concepts.items()}
        }
        
        print(f"✅ Generated timeline for {len(timeline)} time periods")
    
    def generate_comprehensive_data(self):
        """Generate all comprehensive data"""
        print("\n🎨 Generating comprehensive graph data...")
        
        # Core nodes
        nodes = [
            {"id": "All Posts", "type": "hub", "count": len(self.posts), 
             "centrality": 100, "sentiment": 0.5}
        ]
        
        # Categories
        categories = Counter([p.get('category') for p in self.posts])
        for cat, count in categories.items():
            nodes.append({
                "id": cat,
                "type": "category",
                "count": count,
                "centrality": count * 2,
                "sentiment": 0.5
            })
        
        # Key concepts with sentiment
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
            sentiment = self.concept_avg_sentiment.get(concept, 0.5)
            
            nodes.append({
                "id": concept,
                "type": "concept",
                "count": count,
                "centrality": centrality,
                "avg_engagement": round(avg_engagement, 1),
                "sentiment": round(sentiment, 2),
                "sentiment_label": 'positive' if sentiment > 0.1 else 'negative' if sentiment < -0.1 else 'neutral'
            })
        
        # Add discovered topics as nodes
        if hasattr(self, 'topics') and self.topics:
            for topic in self.topics:
                nodes.append({
                    "id": topic['name'],
                    "type": "topic",
                    "keywords": topic['keywords'],
                    "count": 0,
                    "centrality": topic['weight']
                })
        
        # Links
        links = []
        
        # Hub to categories
        for cat in categories.keys():
            links.append({
                "source": "All Posts",
                "target": cat,
                "weight": categories[cat],
                "type": "category_connection"
            })
        
        # Hub to concepts
        for concept, count in key_concepts.items():
            links.append({
                "source": "All Posts",
                "target": concept,
                "weight": count,
                "type": "concept_connection"
            })
        
        # Co-occurrence links
        for (c1, c2), count in self.concept_cooccurrence.items():
            if count >= 2:
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
            "timeline": self.timeline_data if hasattr(self, 'timeline_data') else {},
            "topics": self.topics if hasattr(self, 'topics') else [],
            "sentiment_summary": {
                "avg_polarity": sum([s.get('polarity', 0) for s in self.sentiment_scores.values()]) / len(self.sentiment_scores) if self.sentiment_scores else 0,
                "positive": len([s for s in self.sentiment_scores.values() if s.get('label') == 'positive']),
                "neutral": len([s for s in self.sentiment_scores.values() if s.get('label') == 'neutral']),
                "negative": len([s for s in self.sentiment_scores.values() if s.get('label') == 'negative'])
            },
            "metadata": {
                "total_posts": len(self.posts),
                "total_concepts": len(key_concepts),
                "total_connections": len(links),
                "cooccurrence_pairs": len(self.concept_cooccurrence),
                "posts_with_dates": len([d for d in self.post_dates if d]),
                "topics_discovered": len(self.topics) if hasattr(self, 'topics') else 0
            }
        }
    
    def generate_neo4j_export(self, graph_data):
        """Generate Neo4j Cypher import script"""
        print("💾 Generating Neo4j export...")
        
        cypher = ["// Neo4j Import Script for LinkedIn Knowledge Graph", 
                  "// Generated automatically", ""]
        
        # Create nodes
        cypher.append("// Create Nodes")
        for node in graph_data['nodes']:
            props = {k: v for k, v in node.items() if k != 'id' and k != 'type'}
            props_str = ', '.join([f"{k}: {json.dumps(v)}" for k, v in props.items()])
            cypher.append(f"CREATE (n:{node['type'].upper()} {{id: '{node['id']}', {props_str}}});")
        
        cypher.append("")
        cypher.append("// Create Relationships")
        for link in graph_data['links']:
            source = link['source']
            target = link['target']
            weight = link.get('weight', 1)
            link_type = link.get('type', 'CONNECTED_TO').upper().replace(' ', '_')
            cypher.append(f"MATCH (a), (b) WHERE a.id = '{source}' AND b.id = '{target}'")
            cypher.append(f"CREATE (a)-[r:{link_type} {{weight: {weight}}}]->(b);")
        
        return '\n'.join(cypher)
    
    def generate_sample_posts(self, concept, limit=3):
        """Get sample posts for a concept"""
        sample_posts = []
        for post in self.posts:
            text = post.get('text', '').lower()
            if concept.lower() in text:
                sample_posts.append({
                    "text": post.get('text', '')[:200] + "...",
                    "category": post.get('category'),
                    "reactions": post.get('reactions', 0),
                    "comments": post.get('comments', 0),
                    "date": post.get('date') or 'Unknown'
                })
                if len(sample_posts) >= limit:
                    break
        return sample_posts


def main():
    print("="*70)
    print("🚀 COMPREHENSIVE KNOWLEDGE GRAPH IMPROVEMENTS")
    print("="*70)
    print()
    
    kg = ComprehensiveKnowledgeGraph('linkedin_jagadeesh_posts_database_enhanced.json')
    
    # Step 1: Load and basic analysis
    kg.load_data()
    kg.analyze_cooccurrence()
    kg.calculate_centrality()
    
    # Step 2: Advanced analysis
    kg.perform_topic_modeling()
    kg.analyze_sentiment()
    kg.generate_timeline_data()
    
    # Step 3: Generate comprehensive data
    graph_data = kg.generate_comprehensive_data()
    
    # Save enhanced data
    with open('knowledge_graph_comprehensive.json', 'w') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"\n✅ Comprehensive graph data saved!")
    print(f"   Nodes: {len(graph_data['nodes'])}")
    print(f"   Links: {len(graph_data['links'])}")
    print(f"   Topics: {len(graph_data.get('topics', []))}")
    print(f"   Timeline periods: {len(graph_data.get('timeline', {}).get('by_period', {}))}")
    
    # Generate Neo4j export
    neo4j_script = kg.generate_neo4j_export(graph_data)
    with open('neo4j_import.cypher', 'w') as f:
        f.write(neo4j_script)
    print(f"✅ Neo4j export saved: neo4j_import.cypher")
    
    # Generate sample posts for each concept
    sample_posts = {}
    for node in graph_data['nodes']:
        if node['type'] == 'concept':
            sample_posts[node['id']] = kg.generate_sample_posts(node['id'])
    
    with open('concept_sample_posts.json', 'w') as f:
        json.dump(sample_posts, f, indent=2)
    print(f"✅ Sample posts saved: concept_sample_posts.json")
    
    print("\n" + "="*70)
    print("🎉 ALL IMPROVEMENTS IMPLEMENTED!")
    print("="*70)
    
    return graph_data


if __name__ == "__main__":
    main()
