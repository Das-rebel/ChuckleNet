/**
 * OmniClaw Alexa Bridge - Full OmniClaw 2.0 Integration
 * Includes: AgentOrchestrator, PersonaGenerator, ServiceMesh, StoryOrchestrator
 */

const { getClient, multiProviderQuery, getHealthStatus } = require('./resilient-clients');
const { StoryOrchestrator } = require('./clients/story-orchestrator-wrapper');
const AgentOrchestrator = require('./core/agent_orchestrator');
const ServiceMesh = require('./core/service_mesh');
const PersonaGenerator = require('./shared/persona/persona_generator');
const { ConversationMemory } = require('./shared/memory/conversation-memory');
const { AttentionWeightedMemory } = require('./shared/memory/attention-weighted-memory');
const { TaskGuidedCompressor } = require('./shared/memory/task-guided-compressor');
const KodiClient = require('./clients/kodi_client');

// Initialize OmniClaw 2.0 components
let agentOrchestrator = null;
let serviceMesh = null;
let personaGenerator = null;
let storyOrchestrator = null;
let conversationMemory = null;
let attentionWeightedMemory = null;
let taskGuidedCompressor = null;

function initializeOmniClaw2() {
  if (!agentOrchestrator) {
    console.log('🚀 Initializing OmniClaw 2.0 components...');
    agentOrchestrator = new AgentOrchestrator();
    serviceMesh = new ServiceMesh();
    personaGenerator = new PersonaGenerator();
    conversationMemory = new ConversationMemory();
    attentionWeightedMemory = new AttentionWeightedMemory();
    taskGuidedCompressor = new TaskGuidedCompressor(attentionWeightedMemory);
    console.log('✅ OmniClaw 2.0 components ready');
  }
  return { agentOrchestrator, serviceMesh, personaGenerator, conversationMemory, attentionWeightedMemory, taskGuidedCompressor };
}

function getStoryOrchestrator() {
  if (!storyOrchestrator) {
    const aiClient = getClient('UnifiedGLMClient');
    storyOrchestrator = new StoryOrchestrator(aiClient, { language: 'hinglish' });
  }
  return storyOrchestrator;
}

const RANDOM_EXAMPLES = [
  { query: 'play my road trip playlist on Spotify', desc: 'Spotify' },
  { query: 'search Twitter for AI news', desc: 'Twitter' },
  { query: 'tell me a story about a brave knight', desc: 'Story Mode' },
  { query: 'translate "how are you" to Hindi', desc: 'Translator' },
  { query: 'who is Albert Einstein', desc: 'Wikipedia' },
  { query: 'send a WhatsApp message to Rahul saying running late', desc: 'WhatsApp' },
  { query: 'control Kodi and play the last movie', desc: 'Kodi Control' },
  { query: 'search Reddit for programming jokes', desc: 'Reddit' },
  { query: 'narrate the news for me', desc: 'News Reader' }
];

function getRandomExample() {
  return RANDOM_EXAMPLES[Math.floor(Math.random() * RANDOM_EXAMPLES.length)];
}

function getTimeOfDayGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  if (hour < 21) return 'Good evening';
  return 'Hey';
}

/**
 * Health check endpoint with detailed component status
 */
exports.healthHandler = async (req, res) => {
  const resilienceHealth = getHealthStatus();
  const { agentOrchestrator, serviceMesh, personaGenerator, attentionWeightedMemory } = initializeOmniClaw2();

  let agentMetrics = {};
  let serviceMetrics = {};
  let clientHealth = {};

  try {
    if (agentOrchestrator && agentOrchestrator.getPerformanceMetrics) {
      agentMetrics = agentOrchestrator.getPerformanceMetrics();
    }
  } catch (e) {
    agentMetrics = { error: e.message };
  }

  try {
    if (serviceMesh && serviceMesh.getServiceMetrics) {
      serviceMetrics = serviceMesh.getServiceMetrics();
    }
  } catch (e) {
    serviceMetrics = { error: e.message };
  }

  // Get detailed client health status
  try {
    const { testClientHealth, originalClients } = require('./resilient-clients');
    const clientNames = Object.keys(originalClients);
    const healthPromises = clientNames.map(async (name) => {
      try {
        const healthy = await testClientHealth(name);
        return { name, status: healthy ? 'available' : 'unavailable' };
      } catch (e) {
        return { name, status: 'error', error: e.message };
      }
    });
    const results = await Promise.all(healthPromises);
    results.forEach(r => {
      clientHealth[r.name] = r.status;
    });
  } catch (e) {
    console.error('Client health check error:', e.message);
  }

  // Get service mesh registered services
  let meshServices = [];
  if (serviceMesh && serviceMesh.serviceRegistry) {
    for (const [serviceType, instances] of serviceMesh.serviceRegistry.entries()) {
      for (const [instanceId, instance] of instances.entries()) {
        meshServices.push({
          type: serviceType,
          id: instanceId,
          health: instance.healthStatus,
          requests: instance.metrics.requestCount,
          circuitBreaker: instance.circuitBreaker.state
        });
      }
    }
  }

  const workingClients = Object.entries(clientHealth).filter(([_, s]) => s === 'available').map(([n, _]) => n);
  const unavailableClients = Object.entries(clientHealth).filter(([_, s]) => s !== 'available').map(([n, _]) => n);

  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '2.0.0',
    message: 'OmniClaw 2.0 Personal Assistant is operational',
    components: {
      resilience: 'active',
      circuitBreakers: resilienceHealth.circuitBreakers || [],
      clients: {
        total: Object.keys(clientHealth).length,
        working: workingClients.length,
        unavailable: unavailableClients.length,
        available: workingClients,
        unavailableList: unavailableClients
      },
      agentOrchestrator: agentMetrics.system ? 'active' : 'initializing',
      serviceMesh: serviceMetrics.totalServices ? 'active' : 'initializing',
      serviceMeshDetails: {
        totalServices: meshServices.length,
        services: meshServices,
        metrics: serviceMetrics
      },
      personaGenerator: personaGenerator ? 'available' : 'unavailable',
      attentionWeightedMemory: attentionWeightedMemory ? 'active' : 'inactive',
      taskGuidedCompressor: taskGuidedCompressor ? 'active' : 'inactive',
      storyOrchestrator: 'available',
      region: 'asia-south1'
    },
    performance: agentMetrics.system || {},
    serviceHandler: meshServices.length > 0 ? `Mesh managing ${meshServices.length} services` : 'Standalone mode'
  });
};

/**
 * Main Alexa handler with full OmniClaw 2.0 integration
 */
exports.alexaHandler = async (req, res) => {
  // CORS headers
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }

  try {
    const body = req.body || {};

    // Log the request
    console.log('Alexa request received:', {
      version: body.version,
      type: body.request?.type,
      requestId: body.request?.requestId,
      intent: body.request?.intent?.name
    });

    // Handle LaunchRequest
    if (body.request?.type === 'LaunchRequest' || !body.request) {
      const { personaGenerator } = initializeOmniClaw2();
      const example = getRandomExample();
      const timeOfDay = getTimeOfDayGreeting();
      const incomingSessionAttributes = body.session?.attributes || {};

      // Get current persona from session or use default
      const currentPersona = incomingSessionAttributes.currentPersona || 'professional';

      // Get persona-adapted greeting
      let greeting = `${timeOfDay}! I'm OmniClaw 2.0, your personal assistant.`;

      try {
        const persona = await personaGenerator.generatePersona('default_user', {
          timeOfDay,
          context: 'greeting',
          personaType: currentPersona
        });
        if (persona) {
          greeting = await personaGenerator.applyPersonaToResponse(greeting, persona, { context: 'greeting' });
        }
      } catch (e) {
        // Use default greeting
      }

      greeting += ` I can play music on Spotify, control your TV with Kodi, send WhatsApp messages, search Twitter and Reddit, tell you Wikipedia facts, translate languages, and spin epic stories. For example, try saying: "${example.query}" - that's our ${example.desc} feature in action! What can I help you with?`;

      res.json({
        version: '1.0',
        response: {
          outputSpeech: {
            type: 'PlainText',
            text: greeting
          },
          shouldEndSession: false,
          card: {
            type: 'Simple',
            title: 'OmniClaw 2.0 Personal Assistant',
            content: `Powered by AgentOrchestrator + PersonaGenerator + ServiceMesh | Persona: ${currentPersona}`
          }
        },
        sessionAttributes: {
          lastQuery: '',
          conversationCount: 0,
          lastTopic: '',
          currentPersona: currentPersona,
          version: '2.0'
        }
      });
      return;
    }

    // Handle IntentRequest
    if (body.request?.type === 'IntentRequest') {
      const intentName = body.request.intent?.name;
      const slots = body.request.intent?.slots || {};
      const { agentOrchestrator, personaGenerator, attentionWeightedMemory, taskGuidedCompressor } = initializeOmniClaw2();

      // QueryIntent - Use AgentOrchestrator for intelligent routing
      if (intentName === 'QueryIntent' || intentName === 'AMAZON.HelpIntent') {
        const query = slots.Query?.value || 'general help';
        const sessionId = body.session?.sessionId || 'alexa_session';
        const incomingSessionAttributes = body.session?.attributes || {};

        // Get or initialize session attributes
        const conversationCount = (incomingSessionAttributes.conversationCount || 0) + 1;
        const lastTopic = incomingSessionAttributes.lastTopic || query;
        const currentPersona = incomingSessionAttributes.currentPersona || 'professional';

        // Store user message in attention-weighted memory
        attentionWeightedMemory.storeMessage(sessionId, 'user', query, { intent: 'query' });

        // Determine which service handled the request (for logging)
        let serviceHandler = 'agentOrchestrator';
        let compressionStats = null;

        try {
          // Get task-specific compressed context using attention-weighted memory
          const compressedContext = await taskGuidedCompressor.compressForTask(sessionId, query);
          compressionStats = {
            originalMessages: compressedContext.originalCount,
            compressedMessages: compressedContext.compressedCount,
            compressionRatio: compressedContext.compressionRatio,
            tokenCount: compressedContext.tokenCount,
            taskType: taskGuidedCompressor.classifyTask(query)
          };

          // Use agent orchestrator for intelligent processing with compressed context
          const result = await agentOrchestrator.processRequest(query, {
            userId: 'alexa_user',
            sessionId: sessionId,
            intent: 'query',
            usePersona: true,
            conversationHistory: compressedContext.context,
            conversationCount: conversationCount,
            lastTopic: lastTopic,
            personaType: currentPersona
          });

          // Store assistant response in attention-weighted memory
          let responseText = result.response || result.data?.response || result.message || "I'm OmniClaw 2.0";
          attentionWeightedMemory.storeMessage(sessionId, 'assistant', responseText, { serviceUsed: result.serviceUsed });

          // Log which service handled the request
          if (result.serviceUsed) {
            serviceHandler = result.serviceUsed;
            console.log(`Request handled by: ${serviceHandler}`);
          }

          // Apply persona to response using stored persona type
          try {
            const persona = await personaGenerator.generatePersona('alexa_user', {
              query,
              personaType: currentPersona
            });
            responseText = await personaGenerator.applyPersonaToResponse(responseText, persona, { query });
          } catch (e) {
            // Use default response
          }

          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: responseText },
              shouldEndSession: false
            },
            sessionAttributes: {
              lastQuery: query,
              conversationCount: conversationCount,
              lastTopic: lastTopic,
              currentPersona: currentPersona,
              lastServiceHandler: serviceHandler,
              compressionStats: compressionStats,
              version: '2.0'
            }
          });
          return;
        } catch (e) {
          console.error('Agent orchestrator error:', e.message);
          // Fallback to multi-provider query
          try {
            serviceHandler = 'multiProviderQuery';
            const result = await multiProviderQuery(query);
            let responseText = result || "I'm OmniClaw 2.0, ready to help!";

            // Apply persona to fallback response
            try {
              const persona = await personaGenerator.generatePersona('alexa_user', { query, personaType: currentPersona });
              responseText = await personaGenerator.applyPersonaToResponse(responseText, persona, { query });
            } catch (e2) {
              // Use raw response
            }

            // Store fallback response in attention-weighted memory
            attentionWeightedMemory.storeMessage(sessionId, 'assistant', responseText, { fallback: true });

            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: responseText },
                shouldEndSession: false
              },
              sessionAttributes: {
                lastQuery: query,
                conversationCount: conversationCount,
                lastTopic: lastTopic,
                currentPersona: currentPersona,
                lastServiceHandler: serviceHandler,
                version: '2.0'
              }
            });
            return;
          } catch (e2) {
            // Final fallback
          }
        }

        res.json({
          version: '1.0',
          response: {
            outputSpeech: {
              type: 'PlainText',
              text: "I'm OmniClaw 2.0, your personal assistant with 19 integrated services. I can help with news, Twitter, Reddit, Wikipedia, translations, stories, and more!"
            },
            shouldEndSession: false
          },
          sessionAttributes: {
            lastQuery: query,
            conversationCount: conversationCount,
            lastTopic: lastTopic,
            currentPersona: currentPersona,
            lastServiceHandler: serviceHandler,
            version: '2.0'
          }
        });
        return;
      }

      // SearchIntent - search news, reddit, twitter
      if (intentName === 'SearchIntent') {
        const searchQuery = slots.SearchQuery?.value || slots.Query?.value;
        const searchSource = slots.Source?.value || 'news';

        if (searchQuery) {
          try {
            let result = '';
            if (searchSource.toLowerCase().includes('twitter')) {
              // Use original (unprotected) client to avoid resilience wrapper issues
              const client = getClient('TwitterClient', false);
              const tweets = await client.searchTweets(searchQuery);
              // Handle both real API response (array) and AI fallback (object with tweets string or array)
              if (tweets.simulated) {
                // AI fallback returns {simulated: true, tweets: "string or array"}
                const tweetText = typeof tweets.tweets === 'string' ? tweets.tweets : (tweets.tweets?.[0] || 'No results');
                result = `Simulated Twitter search for ${searchQuery}: ${tweetText}`;
              } else {
                // Real API response
                const tweetCount = Array.isArray(tweets) ? tweets.length : (tweets?.data?.length || 0);
                result = `Found ${tweetCount} tweets about ${searchQuery}. First one: ${tweets[0]?.text || tweets?.data?.[0]?.text || 'No results'}`;
              }
            } else if (searchSource.toLowerCase().includes('reddit')) {
              // Use original (unprotected) client to avoid resilience wrapper issues
              const client = getClient('RedditClient', false);
              const posts = await client.searchReddit(searchQuery);
              // Handle Reddit response - could be array (real API) or object with simulated string
              if (posts.simulated) {
                // AI fallback returns {simulated: true, posts: "string"}
                result = `Simulated Reddit search for ${searchQuery}: ${posts.posts}`;
              } else {
                // Real API response
                const postArray = posts.posts || posts.data || posts;
                const postCount = Array.isArray(postArray) ? postArray.length : 0;
                result = `Found ${postCount} Reddit posts about ${searchQuery}. First one: ${postArray[0]?.title || 'No results'}`;
              }
            } else {
              // Use original (unprotected) client for News to avoid resilience wrapper issues
              const client = getClient('NewsClient', false);
              const articles = await client.searchNews(searchQuery);
              result = `Found news about ${searchQuery}. ${articles?.news || 'Check the first result for details.'}`;
            }
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result },
                shouldEndSession: false
              }
            });
            return;
          } catch (e) {
            console.error('Search error:', e.message);
          }
        }
      }

      // TranslateIntent
      if (intentName === 'TranslateIntent') {
        const text = slots.Text?.value;
        const targetLang = slots.Language?.value || 'english';

        if (text) {
          try {
            // Use original (unprotected) client to avoid resilience wrapper transforming errors into objects
            const client = getClient('GoogleTranslateClient', false);
            const translation = await client.translate(text, targetLang);
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: `The translation to ${targetLang} is: ${translation}` },
                shouldEndSession: false
              }
            });
            return;
          } catch (e) {
            console.error('Translation error:', e.message);
          }
        }
      }

      // PersonaIntent - Switch to a different persona/style
      if (intentName === 'PersonaIntent') {
        const personaType = (slots.PersonaType?.value || 'professional').toLowerCase();
        const { personaGenerator } = initializeOmniClaw2();

        // Map common variations to valid template names
        const personaMap = {
          'friendly': 'friendly',
          'warm': 'friendly',
          'casual': 'friendly',
          'professional': 'professional',
          'formal': 'professional',
          'technical': 'technical',
          'expert': 'technical',
          'creative': 'creative',
          'artistic': 'creative',
          'empathetic': 'empathetic',
          'supportive': 'empathetic',
          'fun': 'playful',
          'playful': 'playful',
          'humorous': 'playful'
        };

        const mappedPersona = personaMap[personaType] || 'professional';

        try {
          const persona = await personaGenerator.generatePersona('alexa_user', {
            personaType: mappedPersona
          });

          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: `Switched to ${mappedPersona} persona. I'll be more ${mappedPersona} in my responses from now on.` },
              shouldEndSession: false
            },
            sessionAttributes: {
              currentPersona: mappedPersona
            }
          });
          return;
        } catch (e) {
          console.error('Persona switch error:', e.message);
        }
      }

      // KnowledgeGraphIntent - Search my personal knowledge graph
      if (intentName === 'KnowledgeGraphIntent' || intentName === 'SearchKnowledgeIntent') {
        const query = slots.Query?.value || slots.Topic?.value || slots.SearchQuery?.value;

        if (query) {
          try {
            // Call KGR Cloud Run service via HTTP
            const kgrUrl = process.env.KGR_SERVICE_URL || 'https://omniclaw-kgr-search-338789220059.asia-south1.run.app';

            const response = await fetch(`${kgrUrl}/api/search`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query, options: { maxResults: 5 } })
            });

            const result = await response.json();

            let responseText;
            if (!result.success) {
              responseText = `I had trouble searching your knowledge graph. Please try again.`;
            } else if (result.resultCount === 0) {
              responseText = `I searched your knowledge graph for "${query}" but found no matching results. Try a different search term.`;
            } else {
              const top = result.sources?.[0];
              responseText = `Found ${result.resultCount} results for "${query}" in ${result.responseTime}ms. Top match: ${top?.name || 'result'}.`;
            }

            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: responseText },
                shouldEndSession: false
              },
              sessionAttributes: {
                lastKgrQuery: query,
                kgrResultCount: result.resultCount || 0
              }
            });
            return;
          } catch (e) {
            console.error('Knowledge graph search error:', e.message);
          }
        }
      }

      // WikipediaIntent - Get Wikipedia facts
      if (intentName === 'WikipediaIntent') {
        const topic = slots.Topic?.value || slots.Query?.value;
        if (!topic) {
          res.json({
            version: '1.0',
            response: { outputSpeech: { type: 'PlainText', text: 'What topic would you like to learn about?' }, shouldEndSession: false }
          });
          return;
        }
        try {
          const client = getClient('WikipediaClient', false);
          // Search and get summary directly
          const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic)}`;
          const response = await fetch(url, {
            headers: { 'User-Agent': 'OmniClaw/1.0' },
            signal: AbortSignal.timeout(8000)
          });
          if (response.ok) {
            const data = await response.json();
            res.json({
              version: '1.0',
              response: { outputSpeech: { type: 'PlainText', text: `${topic}: ${data.extract || 'No information found.'}` }, shouldEndSession: false }
            });
          } else {
            res.json({
              version: '1.0',
              response: { outputSpeech: { type: 'PlainText', text: `I couldn't find information about ${topic}.` }, shouldEndSession: false }
            });
          }
          return;
        } catch (e) {
          console.error('Wikipedia error:', e.message);
          res.json({
            version: '1.0',
            response: { outputSpeech: { type: 'PlainText', text: `I couldn't find information about ${topic}.` }, shouldEndSession: false }
          });
          return;
        }
      }

      // NewsIntent
      if (intentName === 'NewsIntent') {
        try {
          const client = getClient('NewsClient');
          const newsResult = await client.getHeadlines();
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: `Here are the top news headlines: ${newsResult.headlines || newsResult.news || 'Unable to fetch news at this time.'}` },
              shouldEndSession: false
            }
          });
          return;
        } catch (e) {
          console.error('News error:', e.message);
        }
      }

      // StoryIntent - Generate a story with characters
      if (intentName === 'StoryIntent' || intentName === 'TellMeAStoryIntent') {
        const storyTheme = slots.Theme?.value || slots.Topic?.value || 'an adventure in a magical kingdom';
        const storySetting = slots.Setting?.value || 'a mystical land';

        try {
          const orchestrator = getStoryOrchestrator();
          const story = await orchestrator.autoGenerateStory({
            theme: storyTheme,
            setting: storySetting,
            genre: 'adventure'
          });

          // Build story text from segments
          const storyText = story.segments
            .map(s => s.type === 'narration' ? s.text : `${s.character} says: ${s.text}`)
            .join('. ');

          res.json({
            version: '1.0',
            response: {
              outputSpeech: {
                type: 'PlainText',
                text: `Here's your story about ${storyTheme}: ${storyText}. Would you like me to continue the story?`
              },
              shouldEndSession: false,
              card: {
                type: 'Simple',
                title: `Story: ${storyTheme}`,
                content: `Characters: ${story.characters.map(c => c.name).join(', ')}`
              }
            }
          });
          return;
        } catch (e) {
          console.error('Story error:', e.message);
          // Fallback response
          res.json({
            version: '1.0',
            response: {
              outputSpeech: {
                type: 'PlainText',
                text: `Once upon a time, in a magical kingdom, there lived a brave hero. Together with loyal friends, they embarked on an adventure filled with wonder and discovery. The end... or is it just the beginning?`
              },
              shouldEndSession: false
            }
          });
          return;
        }
      }

      // SpotifyIntent - Control Spotify playback
      if (intentName === 'SpotifyIntent') {
        let action = (slots.Action?.value || '').toLowerCase();
        let query = slots.Query?.value;

        // Handle "play <song>" format in query slot
        if (!action && query) {
          const playMatch = query.match(/^(play|search|find)\s+(.+)$/i);
          if (playMatch) {
            action = 'play';
            query = playMatch[2];
          }
        }

        try {
          const client = getClient('SpotifyClient', false);

          // Check if credentials are configured
          if (!client.clientId || !client.clientSecret) {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: 'Spotify is not configured. Please add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to enable this feature.' },
                shouldEndSession: false
              }
            });
            return;
          }

          if (action === 'play' || action === 'resume') {
            if (query) {
              const result = await client.searchTracks(query, 1);
              if (result.success && result.tracks.length > 0) {
                await client.play({ uri: result.tracks[0].uri });
                res.json({
                  version: '1.0',
                  response: {
                    outputSpeech: { type: 'PlainText', text: `Playing "${result.tracks[0].name}" by ${result.tracks[0].artists} on Spotify.` },
                    shouldEndSession: false
                  }
                });
              } else {
                res.json({
                  version: '1.0',
                  response: {
                    outputSpeech: { type: 'PlainText', text: `Could not find "${query}" on Spotify.` },
                    shouldEndSession: false
                  }
                });
              }
            } else {
              await client.play();
              res.json({
                version: '1.0',
                response: {
                  outputSpeech: { type: 'PlainText', text: 'Resuming Spotify playback.' },
                  shouldEndSession: false
                }
              });
            }
            return;
          } else if (action === 'pause' || action === 'stop') {
            await client.pause();
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: 'Pausing Spotify playback.' },
                shouldEndSession: false
              }
            });
            return;
          }

          // Default - get playback state
          const state = await client.getCurrentPlayback();
          if (state.item) {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: `Currently playing "${state.item.name}" by ${state.item.artists} on Spotify.` },
                shouldEndSession: false
              }
            });
          } else {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: 'Nothing is currently playing on Spotify.' },
                shouldEndSession: false
              }
            });
          }
          return;
        } catch (e) {
          console.error('Spotify error:', e.message);
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'Failed to control Spotify. Please try again.' },
              shouldEndSession: false
            }
          });
          return;
        }
      }

      // YouTubeIntent - Search and get video information
      if (intentName === 'YouTubeIntent') {
        const query = slots.Query?.value;
        const action = (slots.Action?.value || 'search').toLowerCase();

        if (!query) {
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'What would you like me to search on YouTube?' },
              shouldEndSession: false
            }
          });
          return;
        }

        try {
          const client = getClient('YouTubeClient', false);
          const result = await client.searchVideos(query, 5);

          if (result.success && result.videos.length > 0) {
            const firstVideo = result.videos[0];
            const responseText = `Found "${firstVideo.title}" by ${firstVideo.channel}. ${firstVideo.summary}`;

            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: responseText },
                shouldEndSession: false
              }
            });
          } else {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: `No YouTube videos found for "${query}".` },
                shouldEndSession: false
              }
            });
          }
          return;
        } catch (e) {
          console.error('YouTube error:', e.message);
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'Failed to search YouTube. Please try again.' },
              shouldEndSession: false
            }
          });
          return;
        }
      }

      // ArxivIntent - Search academic papers
      if (intentName === 'ArxivIntent' || intentName === 'AcademicIntent') {
        const topic = slots.Topic?.value;

        if (!topic) {
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'What topic would you like me to search for in academic papers?' },
              shouldEndSession: false
            }
          });
          return;
        }

        try {
          const client = getClient('ArxivClient', false);
          const result = await client.searchArxiv(topic, 5);

          if (result.success && result.papers.length > 0) {
            const firstPaper = result.papers[0];
            const responseText = `Found paper: "${firstPaper.title}" by ${firstPaper.authors}. ${firstPaper.summary}`;

            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: responseText },
                shouldEndSession: false
              }
            });
          } else {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: `No academic papers found for "${topic}".` },
                shouldEndSession: false
              }
            });
          }
          return;
        } catch (e) {
          console.error('Arxiv error:', e.message);
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'Failed to search academic papers. Please try again.' },
              shouldEndSession: false
            }
          });
          return;
        }
      }

      // KodiIntent - Control Kodi/XBMC media center
      if (intentName === 'KodiIntent') {
        let action = (slots.Action?.value || slots.Command?.value || '').toLowerCase();
        const kodiHost = process.env.KODI_HOST;
        const kodiRelayUrl = process.env.KODI_RELAY_URL;

        // Use relay if configured (for local network access)
        if (kodiRelayUrl) {
          try {
            const relayEndpoint = kodiRelayUrl.replace(/\/$/, '');

            // Check for "play X on seren/fen" pattern - use Trakt for direct playback
            const playMatch = action.match(/^play\s+(.+?)\s+on\s+(seren|fen)/i);
            if (playMatch) {
              const query = playMatch[1];
              const addon = playMatch[2];

              // First do Trakt search to get the trakt ID (Seren needs trakt ID, not TMDB)
              let traktId = null;
              try {
                const traktResponse = await fetch(`https://api.trakt.tv/search/movie?query=${encodeURIComponent(query)}&fields=title,ids`, {
                  headers: {
                    'Content-Type': 'application/json',
                    'trakt-api-key': '0362f0bc45385818ae33a18df9c9902923a6dcbecca34693c5c84dd44927846f',
                    'trakt-api-version': '2'
                  },
                  signal: AbortSignal.timeout(10000)
                });
                if (traktResponse.ok) {
                  const traktData = await traktResponse.json();
                  if (traktData && traktData.length > 0) {
                    traktId = traktData[0].ids.trakt;
                  }
                }
              } catch (e) {
                console.error('Trakt lookup failed:', e.message);
              }

              // Use play-movie endpoint with trakt ID for proper Seren playback
              const relayRes = await fetch(`${relayEndpoint}/kodi/play-movie`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, addon: `plugin.video.${addon}`, traktId: traktId }),
                signal: AbortSignal.timeout(15000)
              });
              const relayData = await relayRes.json();
              if (relayData.success) {
                res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: `Opening ${relayData.movie} in ${addon}. Press play on your TV to start streaming.` }, shouldEndSession: false } });
              } else {
                res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: `Failed: ${relayData.error}` }, shouldEndSession: false } });
              }
              return;
            } else if (action === 'play' || action.startsWith('play ')) {
              // Simple play or "play X" without addon
              const query = action === 'play' ? null : action.replace(/^play\s+/i, '').trim();
              const relayRes = await fetch(`${relayEndpoint}/kodi/play`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query }),
                signal: AbortSignal.timeout(10000)
              });
              const relayData = await relayRes.json();
              res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: relayData.success ? 'Playing on Kodi.' : `Kodi: ${relayData.error}` }, shouldEndSession: false } });
              return;
            } else if (action === 'pause') {
              const relayRes = await fetch(`${relayEndpoint}/kodi/pause`, { method: 'POST', signal: AbortSignal.timeout(10000) });
              const relayData = await relayRes.json();
              res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: relayData.success ? 'Pausing Kodi.' : `Kodi: ${relayData.error}` }, shouldEndSession: false } });
              return;
            } else if (action.includes('seren')) {
              const relayRes = await fetch(`${relayEndpoint}/kodi/open-addon`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ addonid: 'plugin.video.seren' }), signal: AbortSignal.timeout(10000) });
              const relayData = await relayRes.json();
              res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: relayData.success ? 'Opening Seren on Kodi.' : `Seren: ${relayData.error}` }, shouldEndSession: false } });
              return;
            } else if (action.includes('fen')) {
              const relayRes = await fetch(`${relayEndpoint}/kodi/open-addon`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ addonid: 'plugin.video.fen' }), signal: AbortSignal.timeout(10000) });
              const relayData = await relayRes.json();
              res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: relayData.success ? 'Opening Fen on Kodi.' : `Fen: ${relayData.error}` }, shouldEndSession: false } });
              return;
            } else {
              // Default - get status via relay
              const relayRes = await fetch(`${relayEndpoint}/kodi/status`, { signal: AbortSignal.timeout(10000) });
              const relayData = await relayRes.json();
              if (relayData.isPlaying) {
                res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: `Kodi is playing: ${relayData.item?.title || 'unknown'}` }, shouldEndSession: false } });
              } else {
                res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: 'Kodi is not playing anything.' }, shouldEndSession: false } });
              }
              return;
            }
          } catch (e) {
            console.error('Kodi relay error:', e.message);
            res.json({ version: '1.0', response: { outputSpeech: { type: 'PlainText', text: 'Failed to control Kodi.' }, shouldEndSession: false } });
            return;
          }
        }

        if (!kodiHost) {
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'Kodi is not configured. Please set KODI_HOST or KODI_RELAY_URL environment variable.' },
              shouldEndSession: false
            }
          });
          return;
        }

        try {
          const kodiClient = new KodiClient({ host: kodiHost });

          if (action === 'play') {
            const result = await kodiClient.play();
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result.success ? 'Playing on Kodi.' : `Kodi error: ${result.error}` },
                shouldEndSession: false
              }
            });
            return;
          } else if (action === 'pause') {
            const result = await kodiClient.pause();
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result.success ? 'Pausing Kodi.' : `Kodi error: ${result.error}` },
                shouldEndSession: false
              }
            });
            return;
          } else if (action === 'stop') {
            const result = await kodiClient.stop();
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result.success ? 'Stopping Kodi.' : `Kodi error: ${result.error}` },
                shouldEndSession: false
              }
            });
            return;
          } else if (action.includes('movie')) {
            const result = await kodiClient.showMovies(5);
            if (result.success && result.movies.length > 0) {
              const movieList = result.movies.map(m => `${m.title} (${m.year})`).join(', ');
              res.json({
                version: '1.0',
                response: {
                  outputSpeech: { type: 'PlainText', text: `Movies on Kodi: ${movieList}` },
                  shouldEndSession: false
                }
              });
            } else {
              res.json({
                version: '1.0',
                response: {
                  outputSpeech: { type: 'PlainText', text: 'No movies found on Kodi.' },
                  shouldEndSession: false
                }
              });
            }
            return;
          } else if (action.includes('seren')) {
            const result = await kodiClient.openAddon('plugin.video.seren');
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result.success ? 'Opening Seren on Kodi.' : `Seren error: ${result.error}` },
                shouldEndSession: false
              }
            });
            return;
          } else if (action.includes('fen')) {
            const result = await kodiClient.openAddon('plugin.video.fen');
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: result.success ? 'Opening Fen on Kodi.' : `Fen error: ${result.error}` },
                shouldEndSession: false
              }
            });
            return;
          }

          // Default - get playback state
          const state = await kodiClient.getPlaybackState();
          if (state.success && state.item) {
            const itemName = state.item.title || state.item.name || 'Unknown';
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: `Kodi is ${state.playing ? 'playing' : 'paused'}: ${itemName}` },
                shouldEndSession: false
              }
            });
          } else {
            res.json({
              version: '1.0',
              response: {
                outputSpeech: { type: 'PlainText', text: 'Kodi is not playing anything.' },
                shouldEndSession: false
              }
            });
          }
          return;
        } catch (e) {
          console.error('Kodi error:', e.message);
          res.json({
            version: '1.0',
            response: {
              outputSpeech: { type: 'PlainText', text: 'Failed to control Kodi. Please try again.' },
              shouldEndSession: false
            }
          });
          return;
        }
      }
    }

    // Handle SessionEndedRequest
    if (body.request?.type === 'SessionEndedRequest') {
      res.json({ version: '1.0' });
      return;
    }

    // Default response
    res.json({
      version: '1.0',
      response: {
        outputSpeech: {
          type: 'PlainText',
          text: "I didn't understand that request. I can help you with questions, news, searches, translations, stories, and more. Just ask!"
        },
        shouldEndSession: false
      }
    });

  } catch (error) {
    console.error('Error processing request:', error);
    res.status(500).json({
      version: '1.0',
      response: {
        outputSpeech: {
          type: 'PlainText',
          text: 'I encountered an error. Please try again.'
        },
        shouldEndSession: true
      }
    });
  }
};
