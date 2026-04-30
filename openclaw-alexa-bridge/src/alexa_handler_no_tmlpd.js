/**
 * Alexa Request Handler - TMLPD-Free Version
 *
 * This version removes TMLPD dependency completely and uses direct AI API calls.
 * Simplifies architecture and improves reliability by eliminating single point of failure.
 *
 * Responsibilities:
 * - Parse Alexa request format
 * - Detect language using Google Translate API
 * - Translate if needed using Sarvam API
 * - Call AI APIs directly (OpenAI, Anthropic, etc.)
 * - Format responses for Alexa
 */

const SarvamClient = require('./sarvam_client');
const GoogleTranslateClient = require('./google_translate_client');
const { hashValue } = require('./logger');

class AlexaRequestHandlerNoTMLPD {
    constructor(options = {}) {
        this.sarvamClient = new SarvamClient(options.sarvamApiKey);
        this.googleTranslateClient = new GoogleTranslateClient(options.googleTranslate || {});
        this.voiceConfig = options.voice || null;
        this.logVerbose = Boolean(options.logVerbose);
        this.userLanguagePrefs = new Map(); // userId -> language preference
        
        // Language detection method tracking
        this.detectionMethodStats = {
            google: 0,
            enhanced: 0,
            fallback: 0,
            total: 0
        };

        // AI API configuration
        this.aiConfig = options.ai || {};
        this.primaryAIProvider = options.ai?.primary || 'openai';
        this.fallbackAIProviders = options.ai?.fallbacks || ['groq', 'anthropic', 'google', 'cerebras'];
    }

    /**
     * Initialize AI API connections
     */
    async initialize() {
        console.log('[Alexa] Initializing TMLPD-free Alexa handler...');

        // Check Sarvam API
        const sarvamStatus = await this.sarvamClient.healthCheck();
        console.log('[Alexa] Sarvam API Status:', sarvamStatus.status);

        // Check Google Translate API
        const googleHealth = await this.googleTranslateClient.healthCheck();
        console.log('[Alexa] Google Translate API Status:', googleHealth ? 'Healthy' : 'Unhealthy');

        // Configure AI API clients
        await this.initializeAIClients();
    }

    /**
     * Initialize direct AI API clients
     */
    async initializeAIClients() {
        const providers = ['openai', 'anthropic', 'google', 'groq', 'cerebras', 'claude', 'openrouter'];
        
        for (const provider of providers) {
            try {
                const client = await this.createAIClient(provider);
                if (client) {
                    console.log(`[Alexa] ${provider} AI client initialized`);
                }
            } catch (error) {
                console.warn(`[Alexa] Failed to initialize ${provider} client:`, error.message);
            }
        }
    }

    /**
     * Call Hugging Face Inference API (Free alternative)
     */
    async callHuggingFaceAI(prompt, options = {}) {
        const apiKey = process.env.HUGGINGFACE_API_KEY || this.aiConfig.huggingface?.apiKey;
        if (!apiKey) {
            throw new Error('Hugging Face API key not configured');
        }

        const model = options.model || this.aiConfig.huggingface?.model || 'meta-llama/Llama-3.2-3B-Instruct';

        console.log(`[Alexa] Calling Hugging Face API with model: ${model}`);

        const response = await fetch(`https://api-inference.huggingface.co/models/${model}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options.maxTokens || 500,
                temperature: options.temperature || 0.7
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] Hugging Face API error ${response.status}: ${errorText.substring(0, 200)}`);
            throw new Error(`Hugging Face API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] Hugging Face response structure:`, Object.keys(data));

        return data.choices[0]?.message?.content || data[0]?.generated_text || 'I apologize, but I could not generate a response.';
    }

    /**
     * Create AI client for specific provider
     */
    async createAIClient(provider) {
        switch (provider) {
            case 'openai':
                return {
                    provider: 'openai',
                    execute: async (prompt, options = {}) => {
                        return await this.callOpenAI(prompt, options);
                    }
                };
            case 'anthropic':
                return {
                    provider: 'anthropic', 
                    execute: async (prompt, options = {}) => {
                        return await this.callAnthropic(prompt, options);
                    }
                };
            case 'google':
                return {
                    provider: 'google',
                    execute: async (prompt, options = {}) => {
                        return await this.callGoogleAI(prompt, options);
                    }
                };
            case 'huggingface':
                return {
                    provider: 'huggingface',
                    execute: async (prompt, options = {}) => {
                        return await this.callHuggingFaceAI(prompt, options);
                    }
                };
            case 'openrouter':
                return {
                    provider: 'openrouter',
                    execute: async (prompt, options = {}) => {
                        return await this.callOpenRouter(prompt, options);
                    }
                };
            case 'cerebras':
                return {
                    provider: 'cerebras',
                    execute: async (prompt, options = {}) => {
                        return await this.callCerebras(prompt, options);
                    }
                };
            case 'groq':
                return {
                    provider: 'groq',
                    execute: async (prompt, options = {}) => {
                        return await this.callGroq(prompt, options);
                    }
                };
            default:
                return null;
        }
    }

    /**
     * Call OpenAI API directly
     */
    async callOpenAI(prompt, options = {}) {
        const apiKey = process.env.OPENAI_API_KEY || this.aiConfig.openai?.apiKey;
        if (!apiKey) {
            throw new Error('OpenAI API key not configured');
        }

        console.log(`[Alexa] Calling OpenAI API with key starting with: ${apiKey.substring(0, 10)}...`);

        // Use standard OpenAI API endpoint with fallback model
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: options.model || 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options.maxTokens || 500,
                temperature: options.temperature || 0.7
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] OpenAI API error ${response.status}: ${errorText.substring(0, 200)}`);
            throw new Error(`OpenAI API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] OpenAI response structure:`, Object.keys(data));
        return data.choices[0]?.message?.content || 'I apologize, but I could not generate a response.';
    }

    /**
     * Call z.ai GLM models (Pro subscription)
     */
    async callAnthropic(prompt, options = {}) {
        const apiKey = process.env.ANTHROPIC_AUTH_TOKEN || process.env.ANTHROPIC_API_KEY || this.aiConfig.anthropic?.apiKey;
        if (!apiKey) {
            throw new Error('z.ai API key not configured');
        }

        console.log(`[Alexa] Calling z.ai GLM API...`);

        // Try different z.ai API endpoints for GLM models
        const endpoints = [
            'https://api.z.ai/v1/chat/completions',
            'https://api.z.ai/v1/glm/chat/completions',
            'https://api.z.ai/api/v1/chat/completions'
        ];

        for (const endpoint of endpoints) {
            try {
                console.log(`[Alexa] Trying z.ai endpoint: ${endpoint}`);

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: options.model || 'glm-4-plus',
                        messages: [{ role: 'user', content: prompt }],
                        max_tokens: options.maxTokens || 500,
                        temperature: options.temperature || 0.7
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log(`[Alexa] z.ai response structure:`, Object.keys(data));

                    // Handle different response formats
                    if (data.choices && Array.isArray(data.choices) && data.choices[0]) {
                        return data.choices[0].message?.content || data.choices[0].text || 'I apologize, but I could not generate a response.';
                    } else if (data.content && Array.isArray(data.content) && data.content[0]) {
                        return data.content[0].text || 'I apologize, but I could not generate a response.';
                    } else if (data.message) {
                        return data.message.content || data.message;
                    } else if (data.text) {
                        return data.text;
                    } else if (typeof data === 'string') {
                        return data;
                    } else {
                        console.log('[Alexa] z.ai full response:', JSON.stringify(data).substring(0, 500));
                        return 'I apologize, but I could not generate a response.';
                    }
                }
            } catch (error) {
                console.log(`[Alexa] z.ai endpoint ${endpoint} failed:`, error.message);
                continue;
            }
        }

        throw new Error('All z.ai API endpoints failed');
    }

    /**
     * Call Google AI API directly using Gemini
     */
    async callGoogleAI(prompt, options = {}) {
        const apiKey = process.env.GOOGLE_AI_API_KEY || this.aiConfig.google?.apiKey;
        const model = options.model || this.aiConfig.google?.model || 'gemini-2.0-flash';
        
        if (!apiKey) {
            throw new Error('Google AI API key not configured');
        }

        console.log(`[Alexa] Calling Google AI API with Gemini model: ${model}`);

        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{ text: prompt }],
                    role: 'user'
                }],
                generationConfig: {
                    temperature: options.temperature || 0.7,
                    maxOutputTokens: options.maxTokens || 500
                }
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] Google AI API error ${response.status}: ${errorText.substring(0, 200)}`);
            throw new Error(`Google AI API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] Google AI response structure:`, Object.keys(data));
        
        return data.candidates[0]?.content?.parts[0]?.text || 'I apologize, but I could not generate a response.';
    }

    /**
     * Call Groq API for fast inference
     */
    async callGroq(prompt, options = {}) {
        const apiKey = process.env.GROQ_API_KEY || this.aiConfig.groq?.apiKey;
        
        // Use fast Groq models optimized for speed
        const model = options.model || this.aiConfig.groq?.model || 'llama-3.3-70b-versatile';
        
        if (!apiKey) {
            throw new Error('Groq API key not configured');
        }

        console.log(`[Alexa] Calling Groq API with fast model: ${model}`);

        const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options.maxTokens || 500,
                temperature: options.temperature || 0.7
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] Groq API error ${response.status}: ${errorText.substring(0, 200)}`);
            
            // Handle specific Groq API errors
            if (response.status === 401) {
                throw new Error('Groq API authentication failed. Please check your API key.');
            } else if (response.status === 429) {
                throw new Error('Groq API rate limit exceeded. Please try again later.');
            } else if (response.status === 500) {
                throw new Error('Groq API server error. Please try again later.');
            }
            
            throw new Error(`Groq API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] Groq response structure:`, Object.keys(data));
        
        return data.choices[0]?.message?.content || 'I apologize, but I could not generate a response.';
    }

    /**
     * Call OpenRouter API for unified access to multiple LLM models
     */
    async callOpenRouter(prompt, options = {}) {
        const apiKey = process.env.OPENROUTER_API_KEY || this.aiConfig.openrouter?.apiKey;
        if (!apiKey) {
            throw new Error('OpenRouter API key not configured');
        }

        // Support multiple models through OpenRouter's unified interface
        const model = options.model || this.aiConfig.openrouter?.model || 'openai/gpt-3.5-turbo';
        
        console.log(`[Alexa] Calling OpenRouter API with model: ${model}`);
        console.log(`[Alexa] API key starting with: ${apiKey.substring(0, 10)}...`);

        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`,
                'HTTP-Referer': 'https://github.com/Subho/openclaw-alexa-bridge',
                'X-Title': 'OpenClaw Alexa Bridge'
            },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options.maxTokens || 500,
                temperature: options.temperature || 0.7
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] OpenRouter API error ${response.status}: ${errorText.substring(0, 200)}`);
            
            // Handle specific OpenRouter error scenarios
            if (response.status === 401) {
                throw new Error('OpenRouter authentication failed. Check your API key.');
            } else if (response.status === 402) {
                throw new Error('OpenRouter insufficient credits. Please check your account balance.');
            } else if (response.status === 429) {
                throw new Error('OpenRouter rate limit exceeded. Please try again later.');
            } else if (response.status === 400) {
                throw new Error('OpenRouter invalid request. Check the model name and parameters.');
            }
            
            throw new Error(`OpenRouter API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] OpenRouter response structure:`, Object.keys(data));

        // Handle OpenRouter response format (similar to OpenAI)
        return data.choices[0]?.message?.content || 'I apologize, but I could not generate a response.';
    }

    /**
     * Call Cerebras API directly for ultra-fast inference
     */
    async callCerebras(prompt, options = {}) {
        const apiKey = process.env.CEREBRAS_API_KEY || this.aiConfig.cerebras?.apiKey;
        if (!apiKey) {
            throw new Error('Cerebras API key not configured');
        }

        // Use fast Llama models on Cerebras
        const model = options.model || this.aiConfig.cerebras?.model || 'llama-3.3-70b-8192';

        console.log(`[Alexa] Calling Cerebras API with fast model: ${model}`);
        console.log(`[Alexa] API key starting with: ${apiKey.substring(0, 10)}...`);

        const response = await fetch('https://api.cerebras.ai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: model,
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options.maxTokens || 500,
                temperature: options.temperature || 0.7
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.log(`[Alexa] Cerebras API error ${response.status}: ${errorText.substring(0, 200)}`);

            // Handle specific Cerebras error scenarios
            if (response.status === 401) {
                throw new Error('Cerebras authentication failed. Check your API key.');
            } else if (response.status === 403) {
                throw new Error('Cerebras access forbidden. Check your API permissions.');
            } else if (response.status === 429) {
                throw new Error('Cerebras rate limit exceeded. Please try again later.');
            } else if (response.status === 400) {
                throw new Error('Cerebras invalid request. Check the model name and parameters.');
            }

            throw new Error(`Cerebras API error: ${response.status}`);
        }

        const data = await response.json();
        console.log(`[Alexa] Cerebras response structure:`, Object.keys(data));

        // Handle Cerebras response format (similar to OpenAI)
        return data.choices[0]?.message?.content || 'I apologize, but I could not generate a response.';
    }

    /**
     * Handle incoming Alexa request
     */
    async handleRequest(request) {
        try {
            // 1. Parse Alexa request
            const intent = this.parseIntent(request);
            const userId = this.getUserId(request);
            const query = this.extractQuery(request, intent);

            const userHash = hashValue(userId);
            console.log(`[Alexa] Request: intent=${intent.name}, user=${userHash || 'unknown'}`);
            if (this.logVerbose) {
                console.log(`[Alexa] Query: ${query}`);
            }

            // 2. Detect language using Google Translate API with fallback
            const detectionResult = await this.detectLanguageWithFallback(query);
            const detectedLang = detectionResult.language;
            const detectionMethod = detectionResult.method;
            const detectionConfidence = detectionResult.confidence;
            
            // Track detection method statistics
            this.trackDetectionMethod(detectionMethod);
            
            const userLangPref = this.userLanguagePrefs.get(userId);
            const targetLang = userLangPref || detectedLang;

            let translatedQuery = query;
            let originalLanguage = detectedLang;
            const isMixedLanguage = detectionResult.isTransliterated || detectionResult.enhancedDetails?.isMixedLanguage;

            // 3. Translate if needed
            if (isMixedLanguage) {
                console.log(`[Alexa] Mixed language detected (${detectedLang}-EN) using ${detectionMethod}`);
                console.log(`[Alexa] Detection confidence: ${(detectionConfidence * 100).toFixed(1)}%`);
                
                if (detectedLang !== 'en') {
                    translatedQuery = await this.translateWithSarvamOrFallback(query, detectedLang);
                }
            } else if (detectedLang !== 'en') {
                console.log(`[Alexa] Language detected: ${detectedLang} using ${detectionMethod} (confidence: ${(detectionConfidence * 100).toFixed(1)}%)`);
                translatedQuery = await this.translateWithSarvamOrFallback(query, detectedLang);
            }
            
            if (this.logVerbose) {
                console.log(`[Alexa] Original query: ${query}`);
                console.log(`[Alexa] Translated query: ${translatedQuery}`);
            }

            // 4. Execute via direct AI API (simplified flow)
            const aiResponse = await this.executeViaDirectAI(translatedQuery, detectedLang);

            // 5. Translate response back to original language if needed
            let finalResponse = aiResponse;
            if (originalLanguage !== 'en' && aiResponse) {
                console.log(`[Alexa] Translating response back to ${originalLanguage}...`);
                const translatedBack = await this.sarvamClient.translateFromEnglish(
                    aiResponse,
                    originalLanguage
                );
                finalResponse = {
                    originalEnglish: aiResponse,
                    content: translatedBack,
                    language: originalLanguage
                };
                if (this.logVerbose) {
                    console.log(`[Alexa] Translated response: ${translatedBack.substring(0, 100)}...`);
                }
            } else {
                finalResponse = {
                    content: aiResponse,
                    language: 'en'
                };
            }

            // 6. Format for Alexa
            return this.formatAlexaResponse(finalResponse);

        } catch (error) {
            console.error('[Alexa] Request failed:', error);
            return this.handleError(error);
        }
    }

    /**
     * Execute query via direct AI API calls
     */
    async executeViaDirectAI(query, language, options = {}) {
        console.log(`[Alexa] Executing via direct AI API (language: ${language})`);
        
        // Build prompt for AI with context
        const prompt = this.buildAIPrompt(query, language, options);
        
        // Try primary AI provider first
        try {
            const primaryClient = await this.createAIClient(this.primaryAIProvider);
            if (primaryClient) {
                console.log(`[Alexa] Using primary AI provider: ${this.primaryAIProvider}`);
                return await primaryClient.execute(prompt, options);
            }
        } catch (primaryError) {
            console.warn(`[Alexa] Primary AI provider failed: ${primaryError.message}`);
            
            // Try fallback providers
            for (const fallbackProvider of this.fallbackAIProviders) {
                try {
                    const fallbackClient = await this.createAIClient(fallbackProvider);
                    if (fallbackClient) {
                        console.log(`[Alexa] Using fallback AI provider: ${fallbackProvider}`);
                        return await fallbackClient.execute(prompt, options);
                    }
                } catch (fallbackError) {
                    console.warn(`[Alexa] Fallback provider ${fallbackProvider} failed: ${fallbackError.message}`);
                    continue;
                }
            }
            
            // All AI providers failed - return helpful fallback response
            throw new Error('All AI providers unavailable');
        }
    }

    /**
     * Build prompt for AI API
     */
    buildAIPrompt(query, language, options = {}) {
        let prompt = query;
        
        // Add language context
        if (language !== 'en') {
            prompt += `\n\n[Language Context: Query is in ${language === 'hi' ? 'Hindi' : language === 'bn' ? 'Bengali' : language}]`;
        }
        
        // Add platform context
        prompt += '\n\n[Platform: Alexa Voice Assistant]';
        
        // Add system prompt for better responses
        prompt += '\n\nYou are a helpful Alexa voice assistant. Provide clear, concise responses that work well with voice output. Avoid markdown, code blocks, or complex formatting.';
        
        return prompt;
    }

    /**
     * Parse intent from Alexa request
     */
    parseIntent(request) {
        // Handle different request structures with fallbacks
        const intent = request.request?.intent || request.body?.request?.intent;

        return {
            name: intent?.name || 'GeneralQueryIntent',
            slots: intent?.slots || {},
            confirmationStatus: intent?.confirmationStatus || 'NONE'
        };
    }

    /**
     * Extract user ID from Alexa request
     */
    getUserId(request) {
        // Handle different request structures
        if (request.session?.user?.userId) {
            return request.session.user.userId;
        } else if (request.context?.System?.user?.userId) {
            return request.context.System.user.userId;
        } else if (request.requestId) {
            // Fallback to using request ID as user identifier
            return `user_${request.requestId.substring(0, 8)}`;
        } else {
            // Final fallback for testing
            return 'test_user';
        }
    }

    /**
     * Extract query from Alexa request
     */
    extractQuery(request, intent) {
        // Try to get from intent slot (handle both uppercase and lowercase slot names)
        if (intent.slots) {
            // Check for lowercase 'query' slot (Alexa standard)
            if (intent.slots.query && intent.slots.query.value) {
                return intent.slots.query.value;
            }
            // Check for uppercase 'Query' slot (fallback)
            if (intent.slots.Query && intent.slots.Query.value) {
                return intent.slots.Query.value;
            }
            // Check for WhatsApp 'fullRequest' slot
            if (intent.slots.fullRequest && intent.slots.fullRequest.value) {
                return intent.slots.fullRequest.value;
            }
        }

        // Fallback with multiple options for different request structures
        return request.request?.intent?.name ||
               request.body?.request?.intent?.name ||
               'General query';
    }

    /**
     * Detect language using Google Translate API with intelligent fallback
     */
    async detectLanguageWithFallback(text) {
        try {
            // Try Google Translate API first
            console.log(`[Alexa] Attempting Google Translate API detection...`);
            const googleResult = await this.googleTranslateClient.detectLanguage(text);
            
            console.log(`[Alexa] Google Translate detection successful: ${googleResult.language} (confidence: ${(googleResult.confidence * 100).toFixed(1)}%)`);
            
            // Return enhanced result with metadata
            return {
                language: googleResult.language,
                confidence: googleResult.confidence,
                method: 'google',
                processingTime: googleResult.processingTime || 0,
                isTransliterated: googleResult.isTransliterated || false,
                googleLanguage: googleResult.googleLanguage || googleResult.language,
                enhancedDetails: null
            };
            
        } catch (error) {
            console.log(`[Alexa] Google Translate API failed: ${error.message}`);
            console.log(`[Alexa] Falling back to enhanced language detector...`);
            
            // Fallback to enhanced detector
            try {
                const enhancedResult = await this.sarvamClient.enhancedDetector.detectLanguage(text);
                
                return {
                    language: enhancedResult.language,
                    confidence: enhancedResult.confidence,
                    method: 'enhanced_fallback',
                    processingTime: enhancedResult.details?.processingTime || 'unknown',
                    isTransliterated: enhancedResult.isMixedLanguage || false,
                    googleLanguage: null,
                    enhancedDetails: enhancedResult
                };
            } catch (fallbackError) {
                console.error(`[Alexa] Both detection methods failed: ${fallbackError.message}`);
                
                // Ultimate fallback to basic detection
                return {
                    language: 'en',
                    confidence: 0.5,
                    method: 'ultimate_fallback',
                    processingTime: 0,
                    isTransliterated: false,
                    googleLanguage: null,
                    enhancedDetails: null,
                    error: fallbackError.message
                };
            }
        }
    }

    /**
     * Translate using Sarvam API with fallback to alternative services
     */
    async translateWithSarvamOrFallback(text, sourceLang) {
        try {
            // Primary: Use Sarvam API for translation
            console.log(`[Alexa] Attempting Sarvam API translation from ${sourceLang} to English...`);
            
            const translated = await this.sarvamClient.translateToEnglish(text, sourceLang);
            console.log(`[Alexa] Sarvam API translation successful`);
            
            return translated;
            
        } catch (sarvamError) {
            console.warn(`[Alexa] Sarvam API translation failed: ${sarvamError.message}`);
            console.log(`[Alexa] Falling back to alternative translation services...`);
            
            // Secondary: Try LibreTranslate
            try {
                const libreTranslated = await this.translateWithLibreTranslate(text, sourceLang, 'en');
                console.log(`[Alexa] LibreTranslate fallback successful`);
                return libreTranslated;
            } catch (libreError) {
                console.warn(`[Alexa] LibreTranslate failed: ${libreError.message}`);
                
                // Tertiary: Try MyMemory
                try {
                    const memoryTranslated = await this.translateWithMyMemory(text, sourceLang, 'en');
                    console.log(`[Alexa] MyMemory fallback successful`);
                    return memoryTranslated;
                } catch (memoryError) {
                    console.error(`[Alexa] All translation services failed: ${memoryError.message}`);
                    // Ultimate fallback: Return original text
                    return text;
                }
            }
        }
    }

    /**
     * Translate using LibreTranslate
     */
    async translateWithLibreTranslate(text, source, target) {
        const response = await fetch('https://libretranslate.de/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                q: text,
                source: source === 'hi' ? 'hi' : source === 'bn' ? 'bn' : 'en',
                target: target === 'en' ? 'en' : 'en',
                format: 'text'
            })
        });

        if (!response.ok) {
            throw new Error(`LibreTranslate error: ${response.status}`);
        }

        const data = await response.json();
        return data.translatedText || text;
    }

    /**
     * Translate using MyMemory
     */
    async translateWithMyMemory(text, source, target) {
        const response = await fetch('https://api.mymemory.translated.net/objs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source: source === 'hi' ? 'hi' : source === 'bn' ? 'bn' : 'en',
                target: target === 'en' ? 'en' : 'en',
                input: text,
                format: 'text'
            })
        });

        if (!response.ok) {
            throw new Error(`MyMemory error: ${response.status}`);
        }

        const data = await response.json();
        return data.responseData.translatedText || text;
    }

    /**
     * Format AI response for Alexa
     */
    formatAlexaResponse(aiResponse) {
        let text;

        // Handle different response formats
        if (typeof aiResponse === 'string') {
            text = aiResponse;
        } else if (aiResponse.content) {
            text = aiResponse.content;
        } else if (aiResponse.responses && aiResponse.responses.length > 0) {
            // Use best response from parallel execution
            const bestResponse = aiResponse.responses[0];
            text = bestResponse.content || bestResponse;
        } else {
            text = "I apologize, but I couldn't process that request.";
        }

        // Clean up text for voice output
        text = this.cleanTextForAlexa(text);

        // Build Alexa response
        const response = {
            version: "1.0",
            response: {
                outputSpeech: this.buildSpeech(text),
                shouldEndSession: true
            }
        };

        return response;
    }

    /**
     * Build speech output (with or without voice)
     */
    buildSpeech(text) {
        const escapedText = this.escapeXml(text);
        
        if (this.voiceConfig && this.voiceConfig.voice) {
            return {
                type: 'SSML',
                ssml: `<speak><voice name="${this.voiceConfig.voice}">${escapedText}</voice></speak>`
            };
        }

        return {
            type: 'PlainText',
            text: text
        };
    }

    /**
     * Clean text for Alexa speech
     */
    cleanTextForAlexa(text) {
        return text
            .replace(/```[\s\S]*?```/g, 'See code for details.') // Remove code blocks
            .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markdown
            .replace(/\*([^*]+)\*/g, '$1') // Remove italic markdown
            .replace(/#{1,6}\s/g, '') // Remove headers
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
            .replace(/\n{3,}/g, '\n\n') // Reduce excessive newlines
            .trim();
    }

    /**
     * Escape XML for SSML
     */
    escapeXml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;');
    }

    /**
     * Handle errors with enhanced recovery logic
     */
    handleError(error) {
        console.error('[Alexa] Error:', error);

        // Determine error type and recovery strategy
        let recoveryStrategy = this.determineRecoveryStrategy(error);

        switch (recoveryStrategy) {
            case 'translation_error':
                return this.handleTranslationError(error);
                
            case 'ai_error':
                return this.handleAIError(error);
                
            case 'network_error':
                return this.handleNetworkError(error);
                
            case 'user_input_error':
                return this.handleUserInputError(error);
                
            case 'system_error':
                return this.handleSystemError(error);
                
            default:
                return this.handleGenericError(error);
        }
    }

    /**
     * Determine recovery strategy based on error type
     */
    determineRecoveryStrategy(error) {
        const errorMessage = error.message?.toLowerCase() || error.toString().toLowerCase();

        // AI API errors (check these first to avoid catching "api" in translation errors)
        if (errorMessage.includes('ai') ||
            errorMessage.includes('openai') ||
            errorMessage.includes('anthropic') ||
            errorMessage.includes('claude') ||
            errorMessage.includes('google') ||
            errorMessage.includes('openrouter') ||
            errorMessage.includes('cerebras') ||
            errorMessage.includes('groq') ||
            errorMessage.includes('model')) {
            return 'ai_error';
        }

        // Translation errors
        if (errorMessage.includes('translation') || 
            errorMessage.includes('sarvam') ||
            errorMessage.includes('translate')) {
            return 'translation_error';
        }

        // Generic API errors (only if not already classified)
        if (errorMessage.includes('api')) {
            return 'system_error';
        }

        // Network errors
        if (errorMessage.includes('network') ||
            errorMessage.includes('connection') ||
            errorMessage.includes('timeout') ||
            errorMessage.includes('fetch') ||
            errorMessage.includes('econnrefused')) {
            return 'network_error';
        }

        // User input errors
        if (errorMessage.includes('invalid') ||
            errorMessage.includes('undefined') ||
            errorMessage.includes('null') ||
            errorMessage.includes('format')) {
            return 'user_input_error';
        }

        // System errors
        return 'system_error';
    }

    /**
     * Handle translation errors with user-friendly messages
     */
    handleTranslationError(error) {
        console.log('[Alexa] Translation error detected, activating recovery...');

        const errorMessages = [
            "I'm having trouble translating that right now. Let me try a different approach.",
            "Translation service is temporarily unavailable. I'll use my fallback system.",
            "I can process your request, but I'm having translation issues.",
            "Let me help you with that using English instead."
        ];

        const userMessage = errorMessages[Math.floor(Math.random() * errorMessages.length)];

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: userMessage
                },
                shouldEndSession: false,
                card: {
                    type: 'Simple',
                    title: 'Translation Service Issue',
                    content: userMessage + " I'm working to improve this experience."
                }
            }
        };
    }

    /**
     * Handle AI API errors with fallback
     */
    handleAIError(error) {
        console.log('[Alexa] AI API error detected, activating fallback...');

        const fallbackResponses = [
            "I'm having some technical difficulties right now. Let me try to help you differently.",
            "Let me provide you with some general information instead.",
            "I'm working on improving my responses for you.",
            "Thank you for your patience while I resolve this issue."
        ];

        const fallbackMessage = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: fallbackMessage
                },
                shouldEndSession: false,
                card: {
                    type: 'Simple',
                    title: 'Technical Issue',
                    content: fallbackMessage + " I'm experiencing some technical challenges."
                }
            }
        };
    }

    /**
     * Handle network errors with retry logic
     */
    handleNetworkError(error) {
        console.log('[Alexa] Network error detected, implementing retry logic...');

        const retryMessages = [
            "I'm having trouble connecting right now. Let me try again.",
            "Network connection seems unstable. Please try again in a moment.",
            "I'm experiencing some connectivity issues. Let me help you with what I can do."
        ];

        const retryMessage = retryMessages[Math.floor(Math.random() * retryMessages.length)];

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: retryMessage
                },
                shouldEndSession: false,
                card: {
                    type: 'Simple',
                    title: 'Connection Issue',
                    content: retryMessage + " I'll keep trying to provide the best service possible."
                }
            }
        };
    }

    /**
     * Handle user input errors with helpful guidance
     */
    handleUserInputError(error) {
        console.log('[Alexa] User input error, providing guidance...');

        const guidanceMessages = [
            "I didn't quite catch that. Could you please say it differently?",
            "I'm having some trouble understanding. Could you rephrase that?",
            "Let's try a different approach. What would you like to know about?",
            "I want to make sure I'm giving you the best help possible."
        ];

        const guidanceMessage = guidanceMessages[Math.floor(Math.random() * guidanceMessages.length)];

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: guidanceMessage
                },
                shouldEndSession: false,
                card: {
                    type: 'Simple',
                    title: 'Understanding Issue',
                    content: guidanceMessage + " I'm here to help you in the best way I can."
                }
            }
        };
    }

    /**
     * Handle system errors gracefully
     */
    handleSystemError(error) {
        console.log('[Alexa] System error, using graceful degradation...');

        const gracefulMessages = [
            "I'm experiencing some technical difficulties. Thank you for your patience.",
            "My systems are working hard to serve you better.",
            "I apologize for the inconvenience. I'm improving my services.",
            "Thank you for your understanding as I work through this technical challenge."
        ];

        const gracefulMessage = gracefulMessages[Math.floor(Math.random() * gracefulMessages.length)];

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: gracefulMessage
                },
                shouldEndSession: false,
                card: {
                    type: 'Simple',
                    title: 'Service Improvement',
                    content: gracefulMessage + " I'm continuously working to enhance your experience."
                }
            }
        };
    }

    /**
     * Handle generic errors with fallback
     */
    handleGenericError(error) {
        console.error('[Alexa] Unhandled error:', error);

        return {
            version: "1.0",
            response: {
                outputSpeech: {
                    type: 'PlainText',
                    text: "I'm sorry, but I encountered an unexpected issue. Please try again."
                },
                shouldEndSession: true
            }
        };
    }

    /**
     * Track detection method usage statistics
     */
    trackDetectionMethod(method) {
        this.detectionMethodStats.total++;

        if (method === 'google') {
            this.detectionMethodStats.google++;
        } else if (method === 'enhanced_fallback') {
            this.detectionMethodStats.enhanced++;
        } else {
            this.detectionMethodStats.fallback++;
        }

        // Log statistics periodically
        if (this.detectionMethodStats.total % 10 === 0) {
            console.log('[Alexa] Detection method statistics:', this.getDetectionMethodStats());
        }
    }

    /**
     * Get detection method statistics
     */
    getDetectionMethodStats() {
        const stats = { ...this.detectionMethodStats };
        const total = stats.total || 1; // Avoid division by zero

        stats.googlePercentage = ((stats.google / total) * 100).toFixed(1) + '%';
        stats.enhancedPercentage = ((stats.enhanced / total) * 100).toFixed(1) + '%';
        stats.fallbackPercentage = ((stats.fallback / total) * 100).toFixed(1) + '%';

        return stats;
    }

    /**
     * Get comprehensive language detection performance metrics
     */
    getLanguageDetectionMetrics() {
        return {
            googleTranslate: this.googleTranslateClient.getPerformanceMetrics(),
            enhancedDetector: this.sarvamClient.enhancedDetector.getPerformanceMetrics(),
            methodStatistics: this.getDetectionMethodStats(),
            overallSuccessRate: this.calculateOverallSuccessRate()
        };
    }

    /**
     * Calculate overall success rate across detection methods
     */
    calculateOverallSuccessRate() {
        const googleMetrics = this.googleTranslateClient.getMetrics();
        const totalDetections = googleMetrics.totalDetections;
        const totalSuccesses = googleMetrics.totalSuccesses;

        if (totalDetections > 0) {
            return ((totalSuccesses / totalDetections) * 100).toFixed(1) + '%';
        }
        return '0%';
    }

    /**
     * Reset detection statistics
     */
    resetDetectionStats() {
        this.detectionMethodStats = {
            google: 0,
            enhanced: 0,
            fallback: 0,
            total: 0
        };
        this.googleTranslateClient.resetMetrics();
        this.sarvamClient.enhancedDetector.resetMetrics();
        console.log('[Alexa] Detection statistics reset');
    }

    /**
     * Close connection
     */
    close() {
        console.log('[Alexa] Shutting down TMLPD-free Alexa handler...');
        this.resetDetectionStats();
    }
}

module.exports = AlexaRequestHandlerNoTMLPD;