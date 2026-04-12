/**
 * News Client
 * Provides news search functionality using AI APIs
 */

const { createValidator } = require('./response_validator');

class NewsClient {
  constructor(config = {}) {
    this.cerebrasKey = config.cerebrasApiKey || process.env.CEREBRAS_API_KEY;
    this.groqKey = config.groqApiKey || process.env.GROQ_API_KEY;
    this.cerebrasBaseUrl = 'https://api.cerebras.ai/v1';
    this.groqBaseUrl = 'https://api.groq.com/openai/v1';
    this.validator = createValidator('News');

    console.log('📰 News Client initialized');
  }

  async searchNews(query, options = {}) {
    const { locale = 'en-US', source = null } = options;

    console.log(`📰 Searching news: "${query}" (locale: ${locale}, source: ${source || 'various'})`);

    const sourceInfo = source ? `from ${source}` : 'from various sources';

    const prompt = `Provide a brief, factual summary of the latest news about: "${query}".
        Focus on recent developments and provide 2-3 key points.
        Keep it concise (under 150 words) and conversational.
        ${this._getLanguagePrompt(locale)}
        ${source ? `Focus specifically on news ${sourceInfo}.` : ''}`;

    const systemPrompt = `You are a helpful news assistant. Provide accurate, current news summaries.
        ${source ? `When possible, mention ${sourceInfo}.` : ''}
        Be concise and conversational. Avoid speculation.`;

    try {
      const response = await this._callAI(prompt, systemPrompt);
      if (response) {
        const result = {
          success: true,
          news: response,
          source: source,
          locale: locale,
          timestamp: new Date().toISOString()
        };

        // Validate response
        try {
          this.validator.validateNewsResponse(result);
        } catch (validationError) {
          console.warn(`[News] Response validation warning: ${validationError.message}`);
        }

        return result;
      }
    } catch (error) {
      console.error('❌ News search failed:', error);
    }

    // Fallback response
    const fallbackText = this._getFallbackText(query, sourceInfo, locale);
    return {
      success: false,
      news: fallbackText,
      source: source,
      locale: locale,
      error: 'Unable to retrieve latest news at this time'
    };
  }

  async getHeadlines(options = {}) {
    const { locale = 'en-US', category = null } = options;

    console.log(`📰 Getting headlines (locale: ${locale}, category: ${category || 'general'})`);

    const prompt = `Provide a brief summary of 3-4 major news headlines for today.
        ${category ? `Focus specifically on ${category} news.` : 'Cover major general news categories.'}
        Keep it concise (under 200 words) and conversational.
        ${this._getLanguagePrompt(locale)}`;

    const systemPrompt = `You are a helpful news assistant. Provide accurate, current news headlines.
        Be concise and conversational. Group by category if relevant.`;

    try {
      const response = await this._callAI(prompt, systemPrompt);
      if (response) {
        return {
          success: true,
          headlines: response,
          locale: locale,
          category: category,
          timestamp: new Date().toISOString()
        };
      }
    } catch (error) {
      console.error('❌ Headlines retrieval failed:', error);
    }

    return {
      success: false,
      headlines: this._getHeadlinesFallback(locale),
      locale: locale,
      error: 'Unable to retrieve headlines at this time'
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
              temperature: 0.7
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
              temperature: 0.7
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
        console.log(`🤖 Calling ${provider.name} for news...`);
        const result = await provider.call();
        if (result) {
          console.log(`✅ ${provider.name} news response received`);
          return result;
        }
      } catch (error) {
        console.warn(`⚠️ ${provider.name} news API failed:`, error.message);
        continue;
      }
    }

    return null;
  }

  _getLanguagePrompt(locale) {
    const languagePrompts = {
      'en-IN-hinglish': 'Include some Hinglish elements naturally in your response.',
      'es-US': 'Respond in Spanish.',
      'hi-IN': 'Respond in Hindi.',
      'bn-IN': 'Respond in Bengali.'
    };
    return languagePrompts[locale] || 'Respond in English.';
  }

  _getFallbackText(query, sourceInfo, locale) {
    if (locale === 'en-IN-hinglish') {
      return `Maine news search kiya "${query}" ${sourceInfo}, par abhi latest information nahi mil rahi hai. Thodi der baad try karein.`;
    }
    return `I searched for news about "${query}" ${sourceInfo}, but couldn't retrieve the latest information right now. Please try again in a moment.`;
  }

  _getHeadlinesFallback(locale) {
    if (locale === 'en-IN-hinglish') {
      return 'Maine headlines ki koshish ki, par abhi server issue hai. Thodi der baad try karein.';
    }
    return 'I tried to get the latest headlines, but am experiencing some technical difficulties. Please try again shortly.';
  }

  extractNewsSource(query) {
    const sources = {
      cnn: ['cnn', 'from cnn', 'cnn news', 'cnn.com'],
      nyt: ['new york times', 'nyt', 'nytimes', 'from nyt', 'times', 'new york'],
      fox: ['fox', 'fox news', 'from fox', 'foxnews'],
      bbc: ['bbc', 'from bbc', 'bbc news', 'bbc.com'],
      reuters: ['reuters', 'from reuters', 'reuters.com'],
      msnbc: ['msnbc', 'from msnbc', 'msnbc.com'],
      abc: ['abc', 'abc news', 'from abc', 'abcnews']
    };

    const lowerQuery = query.toLowerCase();
    for (const [key, keywords] of Object.entries(sources)) {
      for (const keyword of keywords) {
        if (lowerQuery.includes(keyword)) {
          return { key, name: key.toUpperCase(), url: keywords.find(k => k.includes('.')) || '' };
        }
      }
    }
    return null;
  }

  isNewsQuery(query) {
    const newsIndicators = ['news', 'headlines', 'latest', 'breaking', 'update', 'trending',
      'headlines', 'stories', 'article', 'report', 'politics',
      'technology', 'business', 'world', 'international', 'market', 'stock',
      'election', 'congress'];
    return newsIndicators.some(indicator => query.toLowerCase().includes(indicator.toLowerCase()));
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

module.exports = NewsClient;
