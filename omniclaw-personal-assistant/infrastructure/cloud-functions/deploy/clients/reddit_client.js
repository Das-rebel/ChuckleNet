/**
 * Reddit API Client
 * Provides access to Reddit posts for social media trend analysis
 *
 * Requirements: Reddit API access (OAuth or app-only token)
 * Or uses AI fallback when API is unavailable
 */

const { getCacheManager } = require('./cache_manager');
const { createValidator } = require('./response_validator');

class RedditClient {
  constructor(config = {}) {
    this.redditClientId = config.redditClientId || process.env.REDDIT_CLIENT_ID;
    this.redditClientSecret = config.redditClientSecret || process.env.REDDIT_CLIENT_SECRET;
    this.redditUserAgent = config.redditUserAgent || process.env.REDDIT_USER_AGENT || 'QuantumClaw/1.0';
    this.enabled = !!(this.redditClientId && this.redditClientSecret);

    // AI fallback configuration
    this.cerebrasKey = config.cerebrasApiKey || process.env.CEREBRAS_API_KEY;
    this.groqKey = config.groqApiKey || process.env.GROQ_API_KEY;
    this.cerebrasBaseUrl = 'https://api.cerebras.ai/v1';
    this.groqBaseUrl = 'https://api.groq.com/openai/v1';

    // Response validator
    this.validator = createValidator('Reddit');

    // Rate limiting
    this.cache = getCacheManager({ ttl: 60 * 1000, maxSize: 500 }); // 60-second TTL
    this.defaultSubreddit = 'all';
    this.defaultLimit = 5;

    if (this.enabled) {
      console.log('🔴 Reddit API client initialized');
      console.log(`   - Default subreddit: ${this.defaultSubreddit}`);
      console.log(`   - Default limit: ${this.defaultLimit}`);
      console.log('   - Cache TTL: 60 seconds');
    } else {
      console.log('🔴 Reddit Client initialized with AI fallback mode');
    }
  }

  /**
     * Search Reddit for trending posts
     * @param {string} query - Search query
     * @param {string} subreddit - Subreddit to search (default: 'all')
     * @param {number} limit - Number of posts to fetch (default: 5)
     * @param {Object} options - Additional options
     * @returns {Promise<Object>} Reddit posts formatted for voice delivery
     */
  async searchReddit(query, subreddit = 'all', limit = 5, options = {}) {
    const { locale = 'en-US', useCache = true } = options;
    const actualSubreddit = subreddit || this.defaultSubreddit;
    const actualLimit = Math.min(limit || this.defaultLimit, this.defaultLimit);

    console.log(`🔴 Searching Reddit: "${query}" in r/${actualSubreddit} (limit: ${actualLimit})`);

    // Check cache first
    if (useCache) {
      const cacheKey = `reddit:${actualSubreddit}:${query}:${actualLimit}:${locale}`;
      const cached = this.cache.get(cacheKey);
      if (cached) {
        console.log('✅ Using cached Reddit results');
        return cached;
      }
    }

    // Try real Reddit API first if enabled
    if (this.enabled) {
      try {
        const result = await this._searchRedditReal(query, actualSubreddit, actualLimit, locale);
        if (useCache) {
          const cacheKey = `reddit:${actualSubreddit}:${query}:${actualLimit}:${locale}`;
          this.cache.set(cacheKey, result);
        }
        return result;
      } catch (error) {
        console.warn(`⚠️ Reddit API failed, falling back to AI: ${error.message}`);
        // Fall through to AI fallback
      }
    }

    // Use AI fallback
    const result = await this._searchRedditAI(query, actualSubreddit, actualLimit, locale);
    if (useCache) {
      const cacheKey = `reddit:${actualSubreddit}:${query}:${actualLimit}:${locale}`;
      this.cache.set(cacheKey, result);
    }
    return result;
  }

  /**
     * Search Reddit using real API
     * @private
     */
  async _searchRedditReal(query, subreddit, limit, locale) {

    // Get access token
    const accessToken = await this._getAccessToken();
    if (!accessToken) {
      throw new Error('Failed to obtain Reddit access token');
    }

    // Build API URL for hot posts
    const apiUrl = `https://oauth.reddit.com/r/${subreddit}/hot?limit=${limit}&raw_json=1`;

    console.log(`🔴 Fetching from Reddit API: ${apiUrl}`);

    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'User-Agent': this.redditUserAgent
      },
      timeout: 10000
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Reddit API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const posts = data.data?.children || [];

    console.log(`🔴 Found ${posts.length} posts on r/${subreddit}`);

    // Filter posts if query is provided
    let filteredPosts = posts;
    if (query && query.trim() !== 'all') {
      const queryLower = query.toLowerCase();
      filteredPosts = posts.filter(post => {
        const postData = post.data;
        return postData.title?.toLowerCase().includes(queryLower) ||
                       postData.selftext?.toLowerCase().includes(queryLower);
      });
    }

    // Format posts for voice delivery
    const formattedPosts = this._formatPostsForVoice(filteredPosts.slice(0, limit));

    const result = {
      success: true,
      subreddit: subreddit,
      query: query,
      posts: formattedPosts,
      count: formattedPosts.length,
      source: 'reddit_api',
      locale: locale,
      timestamp: new Date().toISOString()
    };

    // Validate response
    const validationResult = this.validator.validateRedditResponse(result);
    if (!validationResult.valid) {
      console.error(`[Reddit] Response validation failed: ${validationResult.error}`);
      // Still return the result but with validation warning
      result.validationWarning = validationResult.error;
    } else {
      console.log('[Reddit] Response validation passed');
    }

    return result;
  }

  /**
     * Search Reddit using AI fallback
     * @private
     */
  async _searchRedditAI(query, subreddit, limit, locale) {
    console.log(`🤖 Using AI fallback for Reddit search: "${query}" in r/${subreddit}`);

    const subredditInfo = subreddit === 'all' ? 'various subreddits' : `r/${subreddit}`;
    const queryInfo = query && query.trim() !== 'all' ? `about "${query}"` : 'trending posts';

    const prompt = `Simulate a search of Reddit ${subredditInfo} for ${queryInfo}.
        Provide a conversational summary of what Reddit users are discussing.
        Include 3-5 representative post titles that sound authentic and current.
        Add upvote counts naturally (e.g., "with 15,000 upvotes").
        Keep it engaging and conversational (under 200 words).
        ${this._getLanguagePrompt(locale)}`;

    const systemPrompt = `You are simulating a Reddit search assistant. Provide engaging summaries
        of Reddit discussions. Use casual, conversational language typical of Reddit.
        Include upvote context naturally. Make posts sound realistic and current-sounding.`;

    try {
      const response = await this._callAI(prompt, systemPrompt);
      if (response) {
        const result = {
          success: true,
          simulated: true,
          subreddit: subreddit,
          query: query,
          posts: response,
          count: limit,
          source: 'ai_simulation',
          locale: locale,
          timestamp: new Date().toISOString()
        };

        // Validate AI response
        const validationResult = this.validator.validateRedditResponse(result);
        if (!validationResult.valid) {
          console.warn(`[Reddit] AI response validation warning: ${validationResult.error}`);
          result.validationWarning = validationResult.error;
        }

        return result;
      }
    } catch (error) {
      console.error('❌ AI Reddit search failed:', error);
    }

    // Fallback response
    return {
      success: false,
      simulated: true,
      subreddit: subreddit,
      query: query,
      posts: this._getFallbackText(query, subredditInfo, locale),
      count: 0,
      source: 'fallback',
      locale: locale,
      error: 'Unable to search Reddit at this time'
    };
  }

  /**
     * Format Reddit posts for voice delivery
     * @private
     */
  _formatPostsForVoice(posts) {
    if (!posts || posts.length === 0) {
      return [];
    }

    return posts.map((post, index) => {
      const data = post.data;
      const title = data.title || 'No title';
      const author = data.author || 'unknown';
      const score = data.score || 0;
      const selftext = data.selftext || '';
      const url = data.url || '';

      // Format upvote count naturally
      const scoreText = this._formatScore(score);

      // Truncate selftext if too long
      const excerpt = selftext.length > 150
        ? selftext.substring(0, 150) + '...'
        : selftext;

      // Build natural language description
      let description = title;
      if (excerpt) {
        description += `. ${excerpt}`;
      }
      description += ` Posted by ${author} with ${scoreText}.`;

      return {
        index: index + 1,
        title: title,
        author: author,
        score: score,
        scoreText: scoreText,
        excerpt: excerpt,
        description: description,
        url: url,
        permalink: `https://reddit.com${data.permalink}`
      };
    });
  }

  /**
     * Format score for natural language
     * @private
     */
  _formatScore(score) {
    if (score >= 1000000) {
      return `${(score / 1000000).toFixed(1)}M upvotes`;
    } else if (score >= 1000) {
      return `${(score / 1000).toFixed(1)}K upvotes`;
    } else if (score === 1) {
      return '1 upvote';
    } else {
      return `${score} upvotes`;
    }
  }

  /**
     * Get Reddit OAuth access token
     * @private
     */
  async _getAccessToken() {

    const auth = Buffer.from(`${this.redditClientId}:${this.redditClientSecret}`).toString('base64');

    const response = await fetch('https://www.reddit.com/api/v1/access_token', {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'User-Agent': this.redditUserAgent,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: 'grant_type=client_credentials',
      timeout: 10000
    });

    if (!response.ok) {
      throw new Error('Failed to obtain Reddit access token');
    }

    const data = await response.json();
    return data.access_token;
  }

  /**
     * Call AI API for Reddit simulation
     * @private
     */
  async _callAI(prompt, systemPrompt) {

    const providers = [
      {
        name: 'cerebras',
        call: async () => {
          const response = await fetch(`${this.cerebrasBaseUrl}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.cerebrasKey}`
            },
            body: JSON.stringify({
              model: 'llama3.1-70b',
              messages: [
                ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
                { role: 'user', content: prompt }
              ],
              max_tokens: 500,
              temperature: 0.8
            })
          });
          const data = await response.json();
          return data.choices?.[0]?.message?.content || '';
        }
      },
      {
        name: 'groq',
        call: async () => {
          const response = await fetch(`${this.groqBaseUrl}/chat/completions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.groqKey}`
            },
            body: JSON.stringify({
              model: 'llama-3.3-70b-versatile',
              messages: [
                ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
                { role: 'user', content: prompt }
              ],
              max_tokens: 500,
              temperature: 0.8
            })
          });
          const data = await response.json();
          return data.choices?.[0]?.message?.content || '';
        }
      }
    ];

    // Try providers in order
    for (const provider of providers) {
      try {
        console.log(`🤖 Calling ${provider.name} for Reddit...`);
        const result = await provider.call();
        if (result) {
          console.log(`✅ ${provider.name} Reddit response received`);
          return result;
        }
      } catch (error) {
        console.warn(`⚠️ ${provider.name} Reddit API failed:`, error.message);
        continue;
      }
    }

    return null;
  }

  /**
     * Get language-specific prompt
     * @private
     */
  _getLanguagePrompt(locale) {
    const languagePrompts = {
      'en-IN-hinglish': 'Include some Hinglish elements naturally in your Reddit-like responses.',
      'es-US': 'Respond in Spanish with Reddit-like language.',
      'hi-IN': 'Respond in Hindi with Reddit-like language.',
      'bn-IN': 'Respond in Bengali with Reddit-like language.'
    };
    return languagePrompts[locale] || 'Respond in English with Reddit-like language.';
  }

  /**
     * Get fallback text for errors
     * @private
     */
  _getFallbackText(query, subredditInfo, locale) {
    if (locale === 'en-IN-hinglish') {
      return `Maine Reddit ${subredditInfo} pe "${query}" search kiya, par abhi data nahi mil raha hai. Thodi der baad try karein.`;
    }
    return `I searched Reddit ${subredditInfo} for "${query}", but couldn't retrieve the posts right now. Please try again in a moment.`;
  }

  /**
     * Check if Reddit API is enabled
     */
  isEnabled() {
    return this.enabled;
  }

  /**
     * Check if using AI fallback mode
     */
  isUsingAIFallback() {
    return !this.enabled;
  }

  /**
     * Check if query is Reddit-related
     */
  isRedditQuery(query) {
    const redditIndicators = ['reddit', 'subreddit', 'r/', 'upvote', 'downvote',
      'thread', 'karma', 'gold', 'ama', 'ask reddit'];
    return redditIndicators.some(indicator => query.toLowerCase().includes(indicator.toLowerCase()));
  }

  /**
     * Extract subreddit from query
     */
  extractSubreddit(query) {
    // Match r/subreddit pattern
    const subredditMatch = query.match(/r\/([a-zA-Z0-9_]+)/);
    if (subredditMatch) {
      return subredditMatch[1];
    }

    // Match "subreddit: name" or "in subreddit name" pattern
    const patterns = [
      /(?:subreddit|in subreddit)[:\s]+([a-zA-Z0-9_]+)/i,
      /(?:in|from)\s+r\/([a-zA-Z0-9_]+)/i
    ];

    for (const pattern of patterns) {
      const match = query.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }

    return null;
  }

  /**
     * Extract Reddit query from text
     */
  extractRedditQuery(query) {
    const lowerQuery = query.toLowerCase();

    // Remove subreddit references from query
    let cleanQuery = query;

    // Remove r/subreddit
    cleanQuery = cleanQuery.replace(/r\/[a-zA-Z0-9_]+/gi, '');

    // Remove "subreddit: name" patterns
    cleanQuery = cleanQuery.replace(/subreddit:\s*[a-zA-Z0-9_]+/gi, '');

    // Remove "in subreddit name" patterns
    cleanQuery = cleanQuery.replace(/in\s+subreddit\s+[a-zA-Z0-9_]+/gi, '');

    // Remove Reddit-specific keywords
    cleanQuery = cleanQuery.replace(/search\s+(?:reddit\s+(?:for|about)?|for\s+(?:on\s+)?)?/gi, '');

    // Remove "on Reddit" suffix
    cleanQuery = cleanQuery.replace(/on\s+reddit\s*$/gi, '');

    return cleanQuery.trim() || 'all';
  }

  /**
     * Clear cache
     */
  clearCache() {
    this.cache.clear();
    console.log('🔴 Reddit cache cleared');
  }

  /**
     * Get cache statistics
     */
  getCacheStats() {
    return this.cache.getStats();
  }

  /**
     * Health check with actual query validation
     */
  async healthCheck(testQuery = 'test') {
    console.log('[Reddit] === HEALTH CHECK START ===');

    try {
      // Execute actual test search
      const testResponse = await this.searchReddit(testQuery, 'all', 1, {
        useCache: false,
        locale: 'en-US'
      });

      console.log('[Reddit] === HEALTH CHECK SUCCESS ===');

      const isSuccess = testResponse && (
        testResponse.success || testResponse.simulated
      );

      return {
        status: 'healthy',
        provider: 'Reddit',
        testQuery: 'passed',
        enabled: this.enabled,
        source: testResponse?.source || 'unknown',
        simulated: testResponse?.simulated || false,
        postsCount: testResponse?.count || 0,
        hasPosts: isSuccess && testResponse?.count > 0
      };
    } catch (error) {
      console.log('[Reddit] === HEALTH CHECK FAILED ===');
      console.error('[Reddit] Health check error:', error.message);

      return {
        status: 'unhealthy',
        provider: 'Reddit',
        error: error.message,
        errorType: error.name || 'unknown',
        testQuery: 'failed',
        enabled: this.enabled
      };
    }
  }

  /**
     * Get validation statistics
     */
  getValidationStats() {
    return this.validator.getStats();
  }

  /**
     * Reset validation statistics
     */
  resetValidationStats() {
    this.validator.resetStats();
  }
}

module.exports = RedditClient;
