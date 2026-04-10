#!/usr/bin/env python3
"""
Simple API Server for Knowledge Graph Queries
Run with: python3 api_server.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import re

app = Flask(__name__)
CORS(app)

# Load graph data
with open('knowledge_graph_comprehensive.json', 'r') as f:
    graph_data = json.load(f)

with open('concept_sample_posts.json', 'r') as f:
    sample_posts = json.load(f)

@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get full graph data"""
    return jsonify(graph_data)

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes"""
    return jsonify(graph_data['nodes'])

@app.route('/api/node/<node_id>', methods=['GET'])
def get_node(node_id):
    """Get specific node details"""
    node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
    if node:
        # Add sample posts
        if node_id in sample_posts:
            node['sample_posts'] = sample_posts[node_id]
        return jsonify(node)
    return jsonify({'error': 'Node not found'}), 404

@app.route('/api/query', methods=['POST'])
def query():
    """Natural language query"""
    data = request.json
    query_text = data.get('query', '').lower()
    
    results = {
        'matched_nodes': [],
        'matched_links': [],
        'suggestions': []
    }
    
    # Simple keyword matching
    keywords = {
        'growth': ['Growth Marketing'],
        'cac': ['Customer Acquisition Cost'],
        'brand': ['Brand Strategy'],
        'campaign': ['Campaign Management'],
        'ai': ['AI/Technology'],
        'funnel': ['Marketing Funnel'],
        'roas': ['ROAS']
    }
    
    matched_concepts = []
    for key, concepts in keywords.items():
        if key in query_text:
            matched_concepts.extend(concepts)
    
    for concept in matched_concepts:
        node = next((n for n in graph_data['nodes'] if n['id'] == concept), None)
        if node:
            results['matched_nodes'].append(node)
    
    # Find related links
    for link in graph_data['links']:
        if any(c in str(link.get('source', '')) + str(link.get('target', '')) for c in matched_concepts):
            results['matched_links'].append(link)
    
    return jsonify(results)

@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    """Get timeline data"""
    return jsonify(graph_data.get('timeline', {}))

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Get discovered topics"""
    return jsonify(graph_data.get('topics', []))

@app.route('/api/insights', methods=['GET'])
def get_insights():
    """Get insights summary"""
    return jsonify({
        'metadata': graph_data.get('metadata', {}),
        'sentiment': graph_data.get('sentiment_summary', {}),
        'top_concepts': sorted(
            [n for n in graph_data['nodes'] if n['type'] == 'concept'],
            key=lambda x: x.get('count', 0),
            reverse=True
        )[:5]
    })

if __name__ == '__main__':
    print("🚀 Starting Knowledge Graph API Server...")
    print("📡 API available at: http://localhost:5000")
    print("📚 Endpoints:")
    print("  GET  /api/graph - Full graph data")
    print("  GET  /api/nodes - All nodes")
    print("  GET  /api/node/<id> - Node details")
    print("  POST /api/query - Natural language query")
    print("  GET  /api/timeline - Timeline data")
    print("  GET  /api/topics - Discovered topics")
    print("  GET  /api/insights - Insights summary")
    app.run(debug=True, port=5000)
