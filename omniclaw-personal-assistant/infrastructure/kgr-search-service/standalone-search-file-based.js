#!/usr/bin/env node

/**
 * ⚡ Ultra-Fast Intelligent Search Server (File-Based)
 * Works with your existing knowledge graph - no cloud setup needed!
 */

const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;

// Middleware
app.use(express.json());
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// Load knowledge graph from file
let knowledgeGraph = null;
const KG_PATH = process.env.KG_PATH || '/app/data/unified_knowledge_graph.json';

async function loadKnowledgeGraph() {
  if (knowledgeGraph) return knowledgeGraph;

  try {
    const data = await fs.readFile(KG_PATH, 'utf8');
    knowledgeGraph = JSON.parse(data);

    // Normalize structure - support both {nodes: []} and {graph: {nodes: []}}
    if (knowledgeGraph.graph) {
      knowledgeGraph.nodes = knowledgeGraph.graph.nodes || [];
      knowledgeGraph.relationships = knowledgeGraph.graph.relationships || [];
    } else if (!knowledgeGraph.nodes) {
      knowledgeGraph.nodes = [];
      knowledgeGraph.relationships = [];
    }

    // Rebuild search index
    searchEngine = new SearchEngine(knowledgeGraph.nodes);

    console.log('✅ Knowledge graph loaded');
    console.log(`   Nodes: ${knowledgeGraph.nodes.length}`);
    console.log(`   Relationships: ${knowledgeGraph.relationships?.length || 0}`);
    console.log(`   Search index: ${searchEngine.index.index.size} terms indexed`);

    return knowledgeGraph;
  } catch (error) {
    console.error('Failed to load knowledge graph:', error);
    throw error;
  }
}

// TF-IDF based search engine
class SearchEngine {
  constructor(nodes) {
    this.nodes = nodes;
    this.index = this.buildIndex(nodes);
    this.docCount = nodes.length;
    this.idfCache = new Map();
  }

  // Tokenize and normalize text
  tokenize(text) {
    if (!text) return [];
    return text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(t => t.length > 1);
  }

  // Build inverted index for fast lookup
  buildIndex(nodes) {
    const index = new Map();
    const docFreq = new Map();

    // First pass: count document frequencies
    for (const node of nodes) {
      const terms = new Set([
        ...this.tokenize(node.name),
        ...this.tokenize(node.content),
        ...this.tokenize(node.type)
      ]);

      for (const term of terms) {
        docFreq.set(term, (docFreq.get(term) || 0) + 1);
      }
    }

    // Second pass: build posting lists
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      const terms = [
        ...this.tokenize(node.name),
        ...this.tokenize(node.content),
        ...this.tokenize(node.type)
      ];

      for (const term of new Set(terms)) {
        if (!index.has(term)) {
          index.set(term, []);
        }
        index.get(term).push({ nodeIndex: i, count: terms.filter(t => t === term).length });
      }
    }

    return { index, docFreq };
  }

  // Calculate IDF for a term
  idf(term) {
    if (this.idfCache.has(term)) {
      return this.idfCache.get(term);
    }

    const df = this.index.docFreq.get(term) || 0;
    // Smoothed IDF formula
    const value = Math.log((this.docCount + 1) / (df + 1)) + 1;
    this.idfCache.set(term, value);
    return value;
  }

  // Calculate TF-IDF score for a node against query
  scoreNode(nodeIndex, queryTerms) {
    const node = this.nodes[nodeIndex];
    const nameTerms = this.tokenize(node.name);
    const contentTerms = this.tokenize(node.content);

    let score = 0;

    for (const queryTerm of queryTerms) {
      // Name matches (highest weight - 0.5)
      const nameTf = nameTerms.filter(t => t === queryTerm || t.includes(queryTerm) || queryTerm.includes(t)).length;
      if (nameTf > 0) {
        const tf = 1 + Math.log(nameTf);
        score += tf * this.idf(queryTerm) * 0.5;
      }

      // Content matches (medium weight - 0.35)
      const contentTf = contentTerms.filter(t => t === queryTerm || t.includes(queryTerm) || queryTerm.includes(t)).length;
      if (contentTf > 0) {
        const tf = 1 + Math.log(contentTf);
        score += tf * this.idf(queryTerm) * 0.35;
      }

      // Subword matching for partial matches
      const subwordMatches = [...nameTerms, ...contentTerms].filter(t =>
        t.includes(queryTerm) || queryTerm.includes(t)
      ).length;
      if (subwordMatches > 0 && nameTf === 0) {
        score += subwordMatches * 0.1 * this.idf(queryTerm);
      }
    }

    // Boost for exact phrase matches
    const nameLower = (node.name || '').toLowerCase();
    const contentLower = (node.content || '').toLowerCase();
    const queryLower = queryTerms.join(' ');

    if (nameLower.includes(queryLower)) score += 0.5;
    if (contentLower.includes(queryLower)) score += 0.3;

    return score;
  }

  // Multi-field search with field boosting
  search(query, options = {}) {
    const maxResults = options.maxResults || 20;
    const queryTerms = this.tokenize(query);
    const queryLower = query.toLowerCase();

    const scored = [];

    // Get candidate nodes from index
    const candidateSet = new Set();
    for (const term of queryTerms) {
      const postings = this.index.index.get(term) || [];
      for (const posting of postings) {
        candidateSet.add(posting.nodeIndex);
      }
      // Also add partial matches
      for (const [indexTerm] of this.index.index) {
        if (indexTerm.includes(term) || term.includes(indexTerm)) {
          const partialPostings = this.index.index.get(indexTerm) || [];
          for (const posting of partialPostings) {
            candidateSet.add(posting.nodeIndex);
          }
        }
      }
    }

    // Score all candidates
    for (const nodeIndex of candidateSet) {
      const node = this.nodes[nodeIndex];
      let relevance = this.scoreNode(nodeIndex, queryTerms);

      // Additional field-based boosts
      const nameLower = (node.name || '').toLowerCase();
      const typeLower = (node.type || '').toLowerCase();

      // Exact type match boost
      if (typeLower.includes(queryLower) || queryLower.includes(typeLower)) {
        relevance += 0.2;
      }

      // URL/domain relevance
      if (node.url && queryTerms.some(t => node.url.toLowerCase().includes(t))) {
        relevance += 0.1;
      }

      if (relevance > 0) {
        scored.push({ ...node, relevance: Math.min(relevance, 1.0) });
      }
    }

    // Sort by relevance
    scored.sort((a, b) => b.relevance - a.relevance);

    return scored.slice(0, maxResults);
  }
}

// Global search engine instance
let searchEngine = null;

function getSearchEngine() {
  if (!searchEngine && knowledgeGraph?.nodes) {
    searchEngine = new SearchEngine(knowledgeGraph.nodes);
  }
  return searchEngine;
}

function searchNodes(query, options = {}) {
  const engine = getSearchEngine();
  if (!engine) return [];

  const results = engine.search(query, options);

  // Normalize relevance scores to 0-1 range
  const maxRelevance = results.length > 0 ? results[0].relevance : 1;
  return results.map(r => ({
    ...r,
    relevance: maxRelevance > 0 ? r.relevance / maxRelevance : 0
  }));
}

function findRelatedNodes(nodeId, maxDepth = 2) {
  const relationships = knowledgeGraph?.relationships || [];
  const related = new Set();

  for (const rel of relationships) {
    if (rel.from_id === nodeId) {
      related.add(rel.to_id);
    }
    if (rel.to_id === nodeId && maxDepth > 1) {
      related.add(rel.from_id);
    }
  }

  return Array.from(related).slice(0, 10);
}

function generateAnswer(query, results) {
  if (results.length === 0) {
    return {
      answer: `I couldn't find any information about "${query}" in your knowledge graph of ${knowledgeGraph?.nodes?.length || 0} items.`,
      confidence: 0,
      sources: []
    };
  }

  const topResults = results.slice(0, 5);
  const topics = [...new Set(topResults.map(r => r.type).filter(t => t))];
  const sources = topResults.map(r => ({
    id: r.id,
    name: r.name,
    type: r.type,
    url: r.url
  }));

  // Detect intent and generate contextual answer
  const queryLower = query.toLowerCase();

  let answer = '';

  if (queryLower.includes('how to') || queryLower.includes('how do')) {
    const tutorials = topResults.filter(r =>
      r.content?.toLowerCase().includes('tutorial') ||
            r.content?.toLowerCase().includes('guide') ||
            r.content?.toLowerCase().includes('how to')
    );

    if (tutorials.length > 0) {
      answer = `Based on your ${results.length} bookmarks about "${query}", here's what I found:\n\n` +
                   `You have ${tutorials.length} relevant tutorials and guides. ` +
                   `The top result discusses: ${tutorials[0].content?.substring(0, 150)}...`;
    } else {
      answer = `I found ${results.length} relevant items in your knowledge graph about "${query}".\n\n` +
                   `Top result: "${topResults[0].name?.substring(0, 50)}..." (${topResults[0].type})\n` +
                   `${topResults[0].content ? `Content: ${topResults[0].content.substring(0, 200)}...` : ''}`;
    }
  } else if (queryLower.includes('what is') || queryLower.includes('what are')) {
    const entity = topResults.find(r => r.type === 'entity');
    const topic = topResults.find(r => r.type === 'topic');

    if (entity) {
      const connections = findRelatedNodes(entity.id);
      answer = `"${entity.name}" appears in your knowledge graph with ${results.length} related items. ` +
                   `It's connected to ${connections.length} other concepts. ` +
                   'You\'ve saved significant content about this entity.';
    } else if (topic) {
      answer = `"${topic.name}" is one of your main topics with ${results.length} related bookmarks. ` +
                   'You\'ve curated extensive content about this subject across your collection.';
    } else {
      answer = `I found ${results.length} items about "${query}" in your knowledge graph.\n\n` +
                   `The most relevant is: "${topResults[0].name?.substring(0, 50)}..."\n` +
                   `${topResults[0].content ? `It mentions: ${topResults[0].content.substring(0, 150)}...` : ''}`;
    }
  } else {
    answer = `I found ${results.length} relevant items about "${query}" in your knowledge graph of ${knowledgeGraph?.nodes?.length || 0} items.\n\n` +
               'Top results include:\n' +
               topResults.slice(0, 3).map((r, i) =>
                 `${i + 1}. "${r.name?.substring(0, 50)}..." (${r.type})`
               ).join('\n') +
               `\n\n${topResults[0].content ? `Key content: ${topResults[0].content.substring(0, 200)}...` : ''}`;
  }

  return {
    answer,
    confidence: results.length >= 5 ? 0.9 : results.length >= 3 ? 0.7 : 0.5,
    sources
  };
}

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'intelligent-search',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Main search endpoint
app.post('/api/search', async (req, res) => {
  try {
    const { query, options = {} } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: 'Missing query parameter'
      });
    }

    await loadKnowledgeGraph();
    const startTime = Date.now();

    // Search nodes
    const results = searchNodes(query, options);

    // Generate intelligent answer
    const { answer, confidence, sources } = generateAnswer(query, results);

    res.status(200).json({
      success: true,
      query,
      answer,
      sources,
      confidence,
      resultCount: results.length,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      query: req.body?.query
    });
  }
});

// Simple ask endpoint
app.post('/api/ask', async (req, res) => {
  try {
    const { question } = req.body;

    if (!question) {
      return res.status(400).json({
        success: false,
        error: 'Missing question parameter'
      });
    }

    await loadKnowledgeGraph();
    const startTime = Date.now();

    // Search with content enabled
    const results = searchNodes(question, { searchContent: true });
    const { answer, confidence, sources } = generateAnswer(question, results);

    res.status(200).json({
      success: true,
      question,
      answer,
      sources,
      confidence,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Ask error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      question: req.body?.question
    });
  }
});

// Search health check with stats
app.get('/api/search/health', async (req, res) => {
  try {
    await loadKnowledgeGraph();

    const nodes = knowledgeGraph?.nodes || [];
    const relationships = knowledgeGraph?.relationships || [];

    const nodeTypes = {};
    for (const node of nodes) {
      if (node.type) {
        nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
      }
    }

    res.status(200).json({
      status: 'healthy',
      service: 'intelligent-search',
      version: '1.0.0',
      statistics: {
        nodes: {
          total: nodes.length,
          byType: nodeTypes
        },
        relationships: {
          total: relationships.length
        }
      },
      source: 'file-based',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Intelligent Knowledge Graph Search',
    version: '1.0.0',
    status: 'running',
    description: 'Fast intelligent search across your 5,862 Twitter bookmarks',
    endpoints: {
      'POST /api/search': 'Search with intelligent answers',
      'POST /api/ask': 'Simple question answering',
      'GET /api/search/health': 'Service health and statistics'
    },
    examples: [
      { query: 'React performance', description: 'Find React optimization tips' },
      { query: 'Claude AI', description: 'Find Claude-related content' },
      { query: 'how to optimize API', description: 'Get actionable advice' }
    ]
  });
});

// Start server
if (require.main === module) {
  app.listen(Number(PORT), '0.0.0.0', () => {
    console.log('\n🔍 Intelligent Search Server (File-Based)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`✅ Server running on http://0.0.0.0:${PORT}`);
    console.log(`📚 Knowledge Graph: ${KG_PATH}`);
    console.log('📚 Endpoints:');
    console.log('   POST /api/search - Search with intelligent answers');
    console.log('   POST /api/ask - Simple Q&A');
    console.log('   GET /api/search/health - Health & stats');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  });
}

module.exports = app;
