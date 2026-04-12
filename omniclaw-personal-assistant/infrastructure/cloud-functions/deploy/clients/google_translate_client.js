/**
 * Google Translate Public API Client - Language Detection
 *
 * Uses Google Translate's public API endpoint for accurate language detection
 * No API key required for basic usage
 *
 * Features:
 * - High-accuracy language detection using Google's machine learning
 * - Support for Hindi, Bengali, English, Hinglish, and Benglish
 * - Fallback to enhanced detector when Google fails
 * - Comprehensive error handling and retry logic
 * - Performance metrics tracking
 */

const { createValidator } = require('./response_validator');

let EnhancedLanguageDetector = null;
try {
  const detectorModule = require('./enhanced_language_detector');
  EnhancedLanguageDetector = detectorModule.EnhancedLanguageDetector;
  if (!EnhancedLanguageDetector) {
    console.warn('[GoogleTranslate] EnhancedLanguageDetector not found in module');
    EnhancedLanguageDetector = null;
  }
} catch (e) {
  console.warn('[GoogleTranslate] EnhancedLanguageDetector not available:', e.message);
}

class GoogleTranslateClient {
  constructor(options = {}) {
    this.baseUrl = 'https://translate.googleapis.com/translate_a/single';
    this.enhancedDetector = EnhancedLanguageDetector ? new EnhancedLanguageDetector() : null;
    this.validator = createValidator('GoogleTranslate');
    this.timeout = options.timeout || 10000; // 10 second default timeout
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;

    // Performance metrics
    this.metrics = {
      googleDetections: 0,
      googleSuccesses: 0,
      fallbackDetections: 0,
      fallbackSuccesses: 0,
      averageGoogleTime: 0,
      averageFallbackTime: 0,
      detectionMethodDistribution: {}
    };

    // Language code mappings
    this.languageMappings = {
      'hi': 'hi',      // Hindi
      'bn': 'bn',      // Bengali
      'en': 'en',      // English
      'hi-latn': 'hi', // Hinglish -> Hindi
      'bn-latn': 'bn', // Benglish -> Bengali
      'ur': 'hi',      // Urdu -> Hindi (similar)
      'ne': 'hi',      // Nepali -> Hindi (similar)
      'as': 'hi',      // Assamese -> Hindi (similar)
      'mr': 'hi',      // Marathi -> Hindi (similar)
      'gu': 'hi'      // Gujarati -> Hindi (similar)
    };

    console.log('[GoogleTranslate] Client initialized' + (this.enhancedDetector ? ' with enhanced fallback' : ''));
  }

  /**
     * Detect language using Google Translate API with fallback
     * @param {string} text - Text to detect language from
     * @returns {Promise<Object>} Detection result with language code and metadata
     */
  async detectLanguage(text) {
    const startTime = Date.now();

    try {
      // Try Google Translate API first
      console.log('[GoogleTranslate] Attempting Google API detection...');
      const googleResult = await this.detectWithGoogleTranslate(text);

      // Track success
      const googleTime = Date.now() - startTime;
      this.metrics.googleDetections++;
      this.metrics.googleSuccesses++;
      this.updateAverageTime('google', googleTime);
      this.trackDetectionMethod('google');

      console.log(`[GoogleTranslate] Google API successful: ${googleResult.language} (${googleTime}ms)`);

      // Validate Google response
      const validationResult = this.validator.validateGoogleTranslateResponse(googleResult);
      if (!validationResult.valid) {
        console.warn(`[GoogleTranslate] Response validation warning: ${validationResult.error}`);
        googleResult.validationWarning = validationResult.error;
      } else {
        console.log('[GoogleTranslate] Response validation passed');
      }

      return {
        ...googleResult,
        method: 'google',
        processingTime: googleTime,
        fallbackUsed: false
      };

    } catch (error) {
      console.log(`[GoogleTranslate] Google API failed: ${error.message}`);
      console.log('[GoogleTranslate] Falling back to enhanced detector...');

      // Fallback to enhanced detector
      const fallbackResult = await this.detectWithFallback(text, startTime);

      this.metrics.fallbackDetections++;
      this.metrics.fallbackSuccesses++;
      this.trackDetectionMethod('enhanced_fallback');

      return fallbackResult;
    }
  }

  /**
     * Detect language using Google Translate API
     * @param {string} text - Text to detect language from
     * @returns {Promise<Object>} Detection result
     */
  async detectWithGoogleTranslate(text) {
    try {
      // Prepare request parameters - use POST for better encoding handling
      const params = new URLSearchParams({
        client: 'gtx',           // Free tier
        sl: 'auto',              // Auto-detect source
        tl: 'en',                // Target language (doesn't matter for detection)
        dt: 'at',                // Request alternative translations (includes detection)
        q: text
      });

      console.log(`[GoogleTranslate] Calling Google API (text length: ${text.length} chars)`);

      // Use POST method to avoid URL encoding issues with non-ASCII text
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      let lastError;
      for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
        try {
          const response = await fetch(this.baseUrl, {
            method: 'POST',
            signal: controller.signal,
            headers: {
              'Accept': '*/*',
              'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw/1.0)',
              'Accept-Language': 'en-US,en;q=0.9',
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: params.toString()
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`Google API returned status ${response.status}`);
          }

          const data = await response.json();
          const result = this.parseGoogleResponse(data, text);

          console.log(`[GoogleTranslate] Detection successful (attempt ${attempt})`);
          return result;

        } catch (error) {
          lastError = error;

          if (attempt < this.maxRetries) {
            console.log(`[GoogleTranslate] Attempt ${attempt} failed, retrying... (${error.message})`);
            await this.sleep(this.retryDelay * attempt); // Exponential backoff
          }
        }
      }

      throw lastError || new Error('All retry attempts failed');

    } catch (error) {
      console.error('[GoogleTranslate] Google API detection failed:', error.message);
      throw error; // Re-throw to trigger fallback
    }
  }

  /**
     * Parse Google Translate API response
     * @param {Array} data - Raw response from Google API
     * @param {string} originalText - Original text for verification
     * @returns {Object} Parsed detection result
     */
  parseGoogleResponse(data, originalText) {
    try {
      // Google returns nested arrays with detection information
      // Based on API testing, language detection is in:
      // - data[2] as a string (primary language code)
      // - data[8] as an array with language info

      let detectedLang = 'en';
      let confidence = 0.8;

      // Method 1: Check data[2] for direct language code string (MOST RELIABLE)
      if (data && data.length > 2 && data[2] && typeof data[2] === 'string') {
        detectedLang = data[2].trim();
        confidence = 0.85; // High confidence for direct string
        console.log(`[GoogleTranslate] Found language in data[2]: "${detectedLang}"`);
      }
      // Method 2: Check data[8] for language array (SECONDARY)
      else if (data && data.length > 8 && data[8] && Array.isArray(data[8]) && data[8].length > 0) {
        const langArray = data[8][0];
        if (Array.isArray(langArray) && langArray[0]) {
          detectedLang = langArray[0];
          confidence = 0.80; // Good confidence for array method
          console.log(`[GoogleTranslate] Found language in data[8]: "${detectedLang}"`);
        }
      }
      // Method 3: Fallback to checking data[6] for confidence score
      if (data && data.length > 6 && typeof data[6] === 'number') {
        // data[6] appears to be a confidence score (0.9895866 for clear English)
        confidence = data[6];
        console.log(`[GoogleTranslate] Found confidence in data[6]: ${confidence.toFixed(3)}`);
      }

      // Map Google's language codes to our standard codes
      const mappedLang = this.mapLanguageCode(detectedLang);

      const transliterationHint = this.detectTransliterationHint(originalText);
      const isTransliterated = mappedLang === 'en'
        ? transliterationHint.isTransliterated
        : this.detectTransliteratedLanguage(originalText, mappedLang);

      if (mappedLang === 'en' && transliterationHint.isTransliterated) {
        confidence = Math.min(confidence, 0.6);
      }

      console.log(`[GoogleTranslate] Final detection: ${detectedLang} -> ${mappedLang} (confidence: ${confidence.toFixed(2)})`);

      return {
        language: mappedLang,
        confidence: confidence,
        googleLanguage: detectedLang,
        isTransliterated,
        transliterationHint,
        originalDetection: { detectedLang, confidence },
        detectedBy: 'google_translate'
      };

    } catch (error) {
      console.error('[GoogleTranslate] Failed to parse Google response:', error);
      throw error;
    }
  }

  /**
     * Map Google's language codes to our standard codes
     * @param {string} googleLang - Google's language code
     * @returns {string} Mapped language code
     */
  mapLanguageCode(googleLang) {
    if (!googleLang) return 'en';

    // Normalize the language code
    const normalized = googleLang.toLowerCase().trim();

    // Direct mapping
    if (this.languageMappings[normalized]) {
      return this.languageMappings[normalized];
    }

    // Handle compound codes like 'hi-Latn'
    const [baseLang, script] = normalized.split('-');
    if (this.languageMappings[baseLang]) {
      return this.languageMappings[baseLang];
    }

    // Handle transliterated variants
    if (script === 'latn') {
      return this.languageMappings[baseLang] || baseLang;
    }

    // Default to English for unknown languages
    return 'en';
  }

  /**
     * Detect if text is transliterated Hinglish/Benglish
     * @param {string} text - Original text
     * @param {string} baseLanguage - Detected base language
     * @returns {boolean} True if transliterated
     */
  detectTransliteratedLanguage(text, baseLanguage) {
    // Check for Latin script with Indian language characteristics
    const hasLatinScript = /^[a-zA-Z\s.,!?'"-]+$/.test(text);

    if (!hasLatinScript) {
      return false;
    }

    if (baseLanguage === 'hi') {
      // Check for Hinglish patterns
      return this.hasHinglishCharacteristics(text);
    } else if (baseLanguage === 'bn') {
      // Check for Benglish patterns
      return this.hasBenglishCharacteristics(text);
    }

    return false;
  }

  /**
     * Detect transliteration hints even when Google returns English
     * @param {string} text - Original text
     * @returns {{isTransliterated: boolean, language: string | null}}
     */
  detectTransliterationHint(text) {
    const hasLatinScript = /^[a-zA-Z\s.,!?'"-]+$/.test(text);
    if (!hasLatinScript) {
      return { isTransliterated: false, language: null };
    }

    const hasHinglish = this.hasHinglishCharacteristics(text);
    const hasBenglish = this.hasBenglishCharacteristics(text);

    if (!hasHinglish && !hasBenglish) {
      return { isTransliterated: false, language: null };
    }

    if (hasBenglish && !hasHinglish) {
      return { isTransliterated: true, language: 'bn' };
    }

    if (hasHinglish && !hasBenglish) {
      return { isTransliterated: true, language: 'hi' };
    }

    return { isTransliterated: true, language: 'mixed' };
  }

  /**
     * Check for Hinglish characteristics
     * @param {string} text - Text to check
     * @returns {boolean} True if Hinglish detected
     */
  hasHinglishCharacteristics(text) {
    const hinglishIndicators = [
      /kya|kaise|batao|karo|chahiye/gi,
      /hai|na|yaar|bhai|arrey|achha/gi,
      /namaste|dhanyavad|theek|thik|sahi/gi,
      /double.*vowel|aa.*ee|ii.*oo/gi, // Double vowels
      /[khghchjthdhn][a-z]/gi // Indian consonant clusters
    ];

    return hinglishIndicators.some(pattern => pattern.test(text));
  }

  /**
     * Check for Benglish characteristics
     * @param {string} text - Text to check
     * @returns {boolean} True if Benglish detected
     */
  hasBenglishCharacteristics(text) {
    const benglishIndicators = [
      /ki|kivabe|kibhabe|kemon|kotha|kothay|koto|kobe|keno/gi,
      /balo|bolo|koro|korchi|korcho|korbe|dorkar|lagbe|chai/gi,
      /bhalo|thik|ache|achi|bhai|dada|are/gi,
      /namaskar|nomoskar|dhonnobad|tumi|ami|amar|apni|tomar/gi,
      /ou.*ou|double.*ou/gi, // Double 'ou' common in Bengali
      /[kkgbjtdhn][a-z]/gi // Bengali consonant clusters
    ];

    return benglishIndicators.some(pattern => pattern.test(text));
  }

  /**
     * Fallback detection using enhanced detector
     * @param {string} text - Text to detect
     * @param {number} startTime - Start time for performance tracking
     * @returns {Promise<Object>} Fallback detection result
     */
  async detectWithFallback(text, startTime) {
    try {
      console.log('[GoogleTranslate] Using enhanced language detector as fallback...');

      const enhancedResult = await this.enhancedDetector.detectLanguage(text);
      const fallbackTime = Date.now() - startTime;

      this.updateAverageTime('fallback', fallbackTime);

      return {
        language: enhancedResult.language,
        confidence: enhancedResult.confidence * 0.9, // Slightly reduce confidence
        method: 'enhanced_fallback',
        processingTime: fallbackTime,
        fallbackUsed: true,
        enhancedDetails: enhancedResult.details,
        detectedBy: 'enhanced_detector'
      };

    } catch (error) {
      console.error('[GoogleTranslate] Fallback detection also failed:', error);

      // Ultimate fallback: basic script detection
      return this.ultimateFallback(text, startTime);
    }
  }

  /**
     * Ultimate fallback using basic script detection
     * @param {string} text - Text to detect
     * @param {number} startTime - Start time
     * @returns {Object} Basic detection result
     */
  ultimateFallback(text, startTime) {
    console.log('[GoogleTranslate] Using ultimate fallback detection...');

    const hindiPattern = /[\u0900-\u097F]/g;
    const bengaliPattern = /[\u0980-\u09FF]/g;

    const hindiChars = (text.match(hindiPattern) || []).length;
    const bengaliChars = (text.match(bengaliPattern) || []).length;
    const totalLength = text.length;

    let language = 'en';
    let confidence = 0.5;

    if (hindiChars > totalLength * 0.1) {
      language = 'hi';
      confidence = 0.6;
    } else if (bengaliChars > totalLength * 0.1) {
      language = 'bn';
      confidence = 0.6;
    } else {
      // Check for transliterated
      const lowerText = text.toLowerCase();
      if (this.hasHinglishCharacteristics(lowerText)) {
        language = 'hi';
        confidence = 0.5;
      } else if (this.hasBenglishCharacteristics(lowerText)) {
        language = 'bn';
        confidence = 0.5;
      }
    }

    const processingTime = Date.now() - startTime;

    return {
      language,
      confidence,
      method: 'ultimate_fallback',
      processingTime,
      fallbackUsed: true,
      detectedBy: 'basic_script_detection'
    };
  }

  /**
     * Sleep utility for retry delays
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise} Resolves after delay
     */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
     * Update average processing time
     * @param {string} method - 'google' or 'fallback'
     * @param {number} time - Processing time in ms
     */
  updateAverageTime(method, time) {
    const key = method === 'google' ? 'averageGoogleTime' : 'averageFallbackTime';
    const count = method === 'google' ? this.metrics.googleDetections : this.metrics.fallbackDetections;

    if (count > 1) {
      this.metrics[key] = ((this.metrics[key] * (count - 1)) + time) / count;
    } else {
      this.metrics[key] = time;
    }
  }

  /**
     * Track detection method distribution
     * @param {string} method - Detection method name
     */
  trackDetectionMethod(method) {
    this.metrics.detectionMethodDistribution[method] =
            (this.metrics.detectionMethodDistribution[method] || 0) + 1;
  }

  /**
     * Get performance metrics
     * @returns {Object} Current performance metrics
     */
  getMetrics() {
    const totalDetections = this.metrics.googleDetections + this.metrics.fallbackDetections;
    const totalSuccesses = this.metrics.googleSuccesses + this.metrics.fallbackSuccesses;

    return {
      totalDetections,
      totalSuccesses,
      successRate: totalDetections > 0 ? ((totalSuccesses / totalDetections) * 100).toFixed(1) + '%' : '0%',
      googleDetections: this.metrics.googleDetections,
      googleSuccesses: this.metrics.googleSuccesses,
      googleSuccessRate: this.metrics.googleDetections > 0 ?
        ((this.metrics.googleSuccesses / this.metrics.googleDetections) * 100).toFixed(1) + '%' : '0%',
      fallbackDetections: this.metrics.fallbackDetections,
      fallbackSuccesses: this.metrics.fallbackSuccesses,
      averageGoogleTime: this.metrics.averageGoogleTime.toFixed(1) + 'ms',
      averageFallbackTime: this.metrics.averageFallbackTime.toFixed(1) + 'ms',
      methodDistribution: this.metrics.detectionMethodDistribution,
      primaryMethodRate: this.metrics.googleDetections > 0 ?
        ((this.metrics.googleDetections / totalDetections) * 100).toFixed(1) + '%' : '0%'
    };
  }

  /**
     * Reset metrics
     */
  resetMetrics() {
    this.metrics = {
      googleDetections: 0,
      googleSuccesses: 0,
      fallbackDetections: 0,
      fallbackSuccesses: 0,
      averageGoogleTime: 0,
      averageFallbackTime: 0,
      detectionMethodDistribution: {}
    };
    console.log('[GoogleTranslate] Metrics reset');
  }

  /**
     * Health check for Google Translate API
     * @returns {Promise<boolean>} True if API is accessible
     */
  async healthCheck() {
    try {
      const testResult = await this.detectWithGoogleTranslate('Hello world');
      console.log('[GoogleTranslate] Health check passed');
      return true;
    } catch (error) {
      console.error('[GoogleTranslate] Health check failed:', error.message);
      return false;
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

  /**
     * Translate text to target language using Google Translate API
     * @param {string} text - Text to translate
     * @param {string} targetLang - Target language code (e.g., 'hi', 'bn', 'es')
     * @returns {Promise<string>} Translated text
     */
  async translate(text, targetLang) {
    const langCode = this.getLanguageCode(targetLang);
    const url = `${this.baseUrl}?client=web&sl=auto&tl=${langCode}&dt=t&q=${encodeURIComponent(text)}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Google Translate API response structure:
      // [[[translated_text, original_text, null, ...]], null, original_lang]
      if (Array.isArray(data) && data[0] && Array.isArray(data[0]) && data[0][0]) {
        const translated = data[0][0][0];
        if (typeof translated === 'string' && translated.length > 0) {
          return translated;
        }
      }

      // If we can't parse the response, return original with indicator
      console.warn('[GoogleTranslate] Could not parse translation response, returning original');
      return `[could not translate: ${text}]`;

    } catch (error) {
      console.error('[GoogleTranslate] Translation error:', error.message);
      throw error;
    }
  }

  /**
     * Map target language name to language code
     * @param {string} targetLang - Language name or code
     * @returns {string} Language code
     */
  getLanguageCode(targetLang) {
    const langMap = {
      'hindi': 'hi',
      'hi': 'hi',
      'bengali': 'bn',
      'bn': 'bn',
      'english': 'en',
      'en': 'en',
      'spanish': 'es',
      'es': 'es',
      'french': 'fr',
      'fr': 'fr',
      'german': 'de',
      'de': 'de',
      'japanese': 'ja',
      'ja': 'ja',
      'chinese': 'zh',
      'zh': 'zh',
      'korean': 'ko',
      'ko': 'ko',
      'arabic': 'ar',
      'ar': 'ar',
      'russian': 'ru',
      'ru': 'ru',
      'portuguese': 'pt',
      'pt': 'pt'
    };

    const normalized = targetLang.toLowerCase().trim();
    return langMap[normalized] || 'en';
  }

  /**
     * Test detection with sample texts
     * @returns {Promise<Object>} Test results
     */
  async runTests() {
    console.log('[GoogleTranslate] Running detection tests...');

    const testCases = [
      { text: 'Hello, how are you?', expected: 'en', name: 'English' },
      { text: 'नमस्ते, आप कैसे हैं?', expected: 'hi', name: 'Hindi' },
      { text: 'হ্যালো, তুমি কেমন আছ?', expected: 'bn', name: 'Bengali' },
      { text: 'Kya haal hai, bhai?', expected: 'hi', name: 'Hinglish' },
      { text: 'Ki khobor, bhai?', expected: 'bn', name: 'Benglish' },
      { text: 'I need help with code banao', expected: 'hi', name: 'Mixed Hinglish' },
      { text: 'Can you help me code banao please', expected: 'hi', name: 'English-Hinglish' }
    ];

    const results = {
      total: testCases.length,
      passed: 0,
      failed: 0,
      details: []
    };

    for (const testCase of testCases) {
      try {
        const result = await this.detectLanguage(testCase.text);
        const passed = result.language === testCase.expected;

        results.details.push({
          ...testCase,
          detected: result.language,
          confidence: result.confidence,
          method: result.method,
          passed
        });

        if (passed) {
          results.passed++;
        } else {
          results.failed++;
          console.warn(`[GoogleTranslate] Test failed: ${testCase.name} - Expected ${testCase.expected}, got ${result.language}`);
        }
      } catch (error) {
        results.failed++;
        results.details.push({
          ...testCase,
          error: error.message,
          passed: false
        });
        console.error(`[GoogleTranslate] Test error for ${testCase.name}:`, error.message);
      }
    }

    results.successRate = ((results.passed / results.total) * 100).toFixed(1) + '%';

    console.log(`[GoogleTranslate] Tests completed: ${results.passed}/${results.total} passed (${results.successRate})`);
    return results;
  }
}

module.exports = GoogleTranslateClient;
