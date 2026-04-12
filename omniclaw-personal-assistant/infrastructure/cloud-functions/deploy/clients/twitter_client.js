/**
 * Twitter/X API v2 Client
 * Provides optimized access to Twitter data for Alexa
 *
 * Requirements: Twitter Developer Account with Bearer Token
 * Get access: https://developer.twitter.com/en/portal/dashboard
 */

const https = require('https');
const { createValidator } = require('./response_validator');

class TwitterClient {
  constructor(bearerToken, aiConfig = {}) {
    this.bearerToken = bearerToken;
    this.baseUrl = 'api.twitter.com';
    this.enabled = !!bearerToken;

    // AI fallback configuration
    this.aiFallbackEnabled = true;
    this.cerebrasKey = aiConfig.cerebrasApiKey || process.env.CEREBRAS_API_KEY;
    this.groqKey = aiConfig.groqApiKey || process.env.GROQ_API_KEY;
    this.cerebrasBaseUrl = 'https://api.cerebras.ai/v1';
    this.groqBaseUrl = 'https://api.groq.com/openai/v1';

    // Response validator
    this.validator = createValidator('Twitter');

    this.rateLimit = {
      remaining: 500,
      reset: null,
      limit: 500
    };

    if (this.enabled) {
      console.log('🐦 Twitter/X API client initialized');
      console.log(`   - Rate limit: ${this.rateLimit.limit} requests/15min`);
    } else if (this.aiFallbackEnabled) {
      console.log('🐦 Twitter Client initialized with AI fallback mode');
    } else {
      console.warn('⚠️ Twitter API disabled (no bearer token or AI fallback)');
    }
  }

  /**
     * Search tweets by query
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Array>} Array of tweets
     */
  async searchTweets(query, options = {}) {
    if (!this.enabled) {
      throw new Error('Twitter API is not enabled (missing bearer token)');
    }

    const {
      maxResults = 10,
      searchType = 'recent'
    } = options;

    await this.waitForRateLimitReset();

    return new Promise((resolve, reject) => {
      const path = `/2/search/2/tweets?query=${encodeURIComponent(query)}&max_results=${maxResults}&tweet.fields=created_at,public_metrics,text,author_id,lang`;

      this._makeRequest('GET', path)
        .then(data => {
          const tweets = data.data || [];
          this._updateRateLimit(data.headers);
          console.log(`🐦 Found ${tweets.length} tweets for "${query}"`);
          resolve(tweets);
        })
        .catch(reject);
    });
  }

  /**
     * Get recent tweets from a specific user
     * @param {string} username - Username without @
     * @param {number} count - Number of tweets to fetch
     * @returns {Promise<Array>} Array of tweets
     */
  async getUserTweets(username, count = 5) {
    if (!this.enabled) {
      throw new Error('Twitter API is not enabled (missing bearer token)');
    }

    await this.waitForRateLimitReset();

    return new Promise((resolve, reject) => {
      const path = `/2/users/by/username/${username}?user.fields=id,username,name,public_metrics`;

      // First get user ID
      this._makeRequest('GET', path)
        .then(userData => {
          const userId = userData.data.id;
          console.log(`🐦 Found user: @${username} (ID: ${userId})`);

          // Then get tweets
          const tweetsPath = `/2/users/${userId}/tweets?max_results=${count}&tweet.fields=created_at,text,public_metrics&exclude=retweets,replies`;
          return this._makeRequest('GET', tweetsPath);
        })
        .then(data => {
          const tweets = data.data || [];
          this._updateRateLimit(data.headers);
          console.log(`🐦 Fetched ${tweets.length} tweets from @${username}`);
          resolve(tweets);
        })
        .catch(reject);
    });
  }

  /**
     * Get trending topics
     * @param {number} woeid - Where On Earth ID (1 = worldwide)
     * @returns {Promise<Array>} Array of trending topics
     */
  async getTrendingTopics(woeid = 1) {
    if (!this.enabled) {
      throw new Error('Twitter API is not enabled (missing bearer token)');
    }

    await this.waitForRateLimitReset();

    return new Promise((resolve, reject) => {
      const path = `/1.1/trends/place.json?id=${woeid}`;

      this._makeRequest('GET', path)
        .then(data => {
          const trends = data[0]?.trends || [];
          this._updateRateLimit(data.headers);
          console.log(`🐦 Found ${trends.length} trending topics`);
          resolve(trends);
        })
        .catch(reject);
    });
  }

  /**
     * Make HTTP request to Twitter API
     * @private
     */
  _makeRequest(method, path) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseUrl,
        path: path,
        method: method,
        headers: {
          'Authorization': `Bearer ${this.bearerToken}`,
          'Content-Type': 'application/json'
        },
        timeout: 7000
      };

      const req = https.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const parsed = JSON.parse(data);

            // Check for errors
            if (res.statusCode !== 200) {
              if (parsed.errors && parsed.errors.length > 0) {
                reject(new Error(`Twitter API error: ${parsed.errors[0].message} (${res.statusCode})`));
              } else {
                reject(new Error(`Twitter API error: ${res.statusCode}`));
              }
              return;
            }

            // Add rate limit info from headers
            parsed.headers = {
              'x-rate-limit-remaining': res.headers['x-rate-limit-remaining'],
              'x-rate-limit-reset': res.headers['x-rate-limit-reset'],
              'x-rate-limit-limit': res.headers['x-rate-limit-limit']
            };

            resolve(parsed);
          } catch (e) {
            reject(new Error(`Failed to parse response: ${e.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`Twitter API request error: ${error.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Twitter API request timeout'));
      });

      req.end();
    });
  }

  /**
     * Update rate limit info from response headers
     * @private
     */
  _updateRateLimit(headers) {
    if (!headers) return;

    const remaining = headers['x-rate-limit-remaining'];
    const reset = headers['x-rate-limit-reset'];
    const limit = headers['x-rate-limit-limit'];

    if (remaining !== undefined) {
      this.rateLimit.remaining = parseInt(remaining);
    }
    if (reset !== undefined) {
      this.rateLimit.reset = parseInt(reset) * 1000;
    }
    if (limit !== undefined) {
      this.rateLimit.limit = parseInt(limit);
    }

    // Warn if approaching rate limit
    if (this.rateLimit.remaining < this.rateLimit.limit * 0.1) {
      console.warn(`⚠️ Twitter API rate limit low: ${this.rateLimit.remaining}/${this.rateLimit.limit} remaining`);
    }
  }

  /**
     * Wait for rate limit reset if needed
     */
  async waitForRateLimitReset() {
    if (this.rateLimit.remaining === 0 && this.rateLimit.reset) {
      const waitTime = this.rateLimit.reset - Date.now();
      if (waitTime > 0) {
        console.log(`⏳ Twitter API rate limit reached. Waiting ${Math.ceil(waitTime / 1000)}s for reset...`);
        await new Promise(resolve => setTimeout(resolve, Math.min(waitTime, 60000)));
      }
    }
  }

  /**
     * Search tweets by query (with AI fallback)
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Array>} Array of tweets or AI-generated response
     */
  async searchTweets(query, options = {}) {
    const { maxResults = 10, searchType = 'recent', locale = 'en-US' } = options;

    // Try real Twitter API first if enabled
    if (this.enabled) {
      try {
        await this.waitForRateLimitReset();
        return await this._searchTweetsReal(query, maxResults, searchType);
      } catch (error) {
        console.warn(`⚠️ Twitter API failed, falling back to AI: ${error.message}`);
        // Fall through to AI fallback
      }
    }

    // Use AI fallback
    return await this._searchTweetsAI(query, locale, maxResults);
  }

  async _searchTweetsReal(query, maxResults, searchType) {
    return new Promise((resolve, reject) => {
      const path = `/2/search/2/tweets?query=${encodeURIComponent(query)}&max_results=${maxResults}&tweet.fields=created_at,public_metrics,text,author_id,lang`;

      this._makeRequest('GET', path)
        .then(data => {
          const tweets = data.data || [];
          this._updateRateLimit(data.headers);
          console.log(`🐦 Found ${tweets.length} tweets for "${query}"`);
          resolve(tweets);
        })
        .catch(reject);
    });
  }

  async _searchTweetsAI(query, locale, count) {
    console.log(`🤖 Using AI fallback for Twitter search: "${query}"`);

    const prompt = `Simulate a search of Twitter/X for recent tweets about: "${query}".
        Provide a comprehensive summary of what people are currently discussing.
        Include 3-4 representative tweet-like responses that sound authentic and current.
        Add relevant hashtags naturally.
        Keep it engaging and conversational (under 200 words).
        ${this._getLanguagePrompt(locale)}`;

    const systemPrompt = `You are simulating a Twitter search assistant. Provide engaging summaries
        of social media discussions. Use casual, conversational language typical of Twitter.
        Include relevant hashtags like #${query.replace(/\s+/g, '')} or #trending naturally.
        Keep responses realistic and current-sounding.`;

    try {
      const response = await this._callAI(prompt, systemPrompt);
      if (response) {
        const result = {
          simulated: true,
          tweets: response,
          count: count,
          timestamp: new Date().toISOString()
        };

        // Validate AI response
        const validationResult = this.validator.validateTwitterResponse(result);
        if (!validationResult.valid) {
          console.warn(`[Twitter] AI response validation warning: ${validationResult.error}`);
          result.validationWarning = validationResult.error;
        }

        return result;
      }
    } catch (error) {
      console.error('❌ AI Twitter search failed:', error);
    }

    // Fallback response
    return {
      simulated: true,
      tweets: this._getFallbackText(query, locale),
      error: 'Unable to search Twitter at this time'
    };
  }

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

    for (const provider of providers) {
      try {
        console.log(`🤖 Calling ${provider.name} for Twitter...`);
        const result = await provider.call();
        if (result) {
          console.log(`✅ ${provider.name} Twitter response received`);
          return result;
        }
      } catch (error) {
        console.warn(`⚠️ ${provider.name} Twitter API failed:`, error.message);
        continue;
      }
    }

    return null;
  }

  _getLanguagePrompt(locale) {
    const languagePrompts = {
      'en-IN-hinglish': 'Include some Hinglish elements naturally in your Twitter-like responses.',
      'es-US': 'Respond in Spanish with Twitter-like language.',
      'hi-IN': 'Respond in Hindi with Twitter-like language.',
      'bn-IN': 'Respond in Bengali with Twitter-like language.'
    };
    return languagePrompts[locale] || 'Respond in English with Twitter-like language.';
  }

  _getFallbackText(query, locale) {
    if (locale === 'en-IN-hinglish') {
      return `Twitter pe "${query}" ke baare mein log baat kar rahe hain. Kisi specific cheez ke baare mein jaanna chahte ho?`;
    }
    return `I looked for Twitter discussions about "${query}". People seem to be discussing various aspects of this topic. Would you like me to search for something specific?`;
  }

  /**
     * Check if Twitter API is enabled
     */
  isEnabled() {
    return this.enabled || this.aiFallbackEnabled;
  }

  /**
     * Check if using AI fallback mode
     */
  isUsingAIFallback() {
    return !this.enabled && this.aiFallbackEnabled;
  }

  /**
     * Check if query is Twitter-related
     */
  isTwitterQuery(query) {
    const twitterIndicators = ['twitter', 'tweet', 'hashtag', 'x.com', 'social media',
      'trending', 'viral', 'post', 'mention', 'handle'];
    return twitterIndicators.some(indicator => query.toLowerCase().includes(indicator.toLowerCase()));
  }

  /**
     * Extract hashtag from query
     */
  extractHashtag(query) {
    const hashtagMatch = query.match(/#(\w+)/);
    if (hashtagMatch) {
      return hashtagMatch[1];
    }
    return null;
  }

  /**
     * Extract Twitter query from text
     */
  extractTwitterQuery(query) {
    const lowerQuery = query.toLowerCase();

    // Check for specific patterns like "search twitter for X" or "find tweets about X"
    const searchPatterns = [
      /(?:search|find|look\s+for|get)\s+(?:twitter|tweets?\s*(?:about|for)?)\s+(.+?)(?:\s*(?:\.|$)|$)/i,
      /(?:twitter|tweets?)\s*(?:about|for|on)\s+(.+?)(?:\s*(?:\.|$)|$)/i
    ];

    for (const pattern of searchPatterns) {
      const match = query.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    // Return original query if no pattern matches
    return query;
  }

  /**
     * Get current rate limit status
     */
  getRateLimitStatus() {
    return {
      enabled: this.enabled,
      remaining: this.rateLimit.remaining,
      limit: this.rateLimit.limit,
      resetAt: this.rateLimit.reset ? new Date(this.rateLimit.reset).toISOString() : null
    };
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

module.exports = TwitterClient;
