# OmniClaw System Architecture

## Executive Overview

OmniClaw is a **serverless, event-driven personal assistant system** built on Google Cloud Platform that transforms Alexa into a comprehensive digital life manager. The architecture preserves 100% of OpenClaw's capabilities while adding four major new feature domains.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Alexa Skills Kit                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS Webhook
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GCP Cloud Functions                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Alexa Intent Handler Function                   │   │
│  │  • Request validation & authentication                    │   │
│  │  • Intent routing & execution                             │   │
│  │  • Response synthesis                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Event-Driven Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Pub/Sub    │  │    Cloud     │  │     Scheduler        │   │
│  │   Topics     │  │    Tasks     │  │   (Cron Jobs)        │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Feature Processing Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │    Email     │  │    Price     │  │      Media           │   │
│  │  Intelligence │  │   Tracking   │  │    Streaming         │   │
│  │   (CrewAI)   │  │  (Crawlee)   │  │   (Spotify/YT)       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│  ┌──────────────┐                                               │
│  │    Story     │                                               │
│  │   Narrator   │                                               │
│  │  (TTS Engine)│                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Firestore   │  │    Redis     │  │   Cloud Storage      │   │
│  │  (NoSQL DB)  │  │  (Memcached) │  │   (Media Files)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │    Gmail     │  │   Spotify    │  │      ElevenLabs      │   │
│  │   Outlook    │  │   YouTube    │  │     (TTS)            │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │   Amazon     │  │   Flipkart   │                             │
│  │  (Products)  │  │  (Products)  │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## Core Architectural Principles

### 1. Serverless-First Design
- **Cloud Functions**: For HTTP endpoints and event handlers
- **Cloud Run**: For long-running background jobs
- **Cloud Scheduler**: For cron-based tasks
- **Pub/Sub**: For asynchronous messaging

### 2. Event-Driven Communication
```javascript
// Example: Price drop event flow
Price Scraper (Cloud Run)
  → Pub/Sub Topic (price-drop-detected)
    → Cloud Function (Notification Service)
      → Alexa Skills Kit
        → User Notification
```

### 3. Microservices by Feature
Each major feature is isolated as a separate microservice:
- **Email Intelligence**: CrewAI agents with Gmail/Outlook integration
- **Price Tracking**: Scraping service with alerting
- **Media Streaming**: Platform-specific integrations
- **Story Narrator**: TTS engine with voice profiles

### 4. Robustness Layer (Shared)
```
shared/
├── resilience/          # Timeout, retry, circuit breaker
├── security/            # Auth, validation, rate limiting
├── monitoring/          # Logging, metrics, health checks
└── utils/               # Common utilities
```

## Component Architecture

### Alexa Integration Layer

**File**: `preserved/src/alexa_handler.js`

```javascript
// Request flow
Alexa Request
  → Intent Validation
    → Parameter Extraction
      → Feature Routing
        → Business Logic
          → Response Synthesis
            → TTS Generation
              → Alexa Response
```

**Key Features**:
- HALO orchestration for LLM routing
- 9+ provider support (Anthropic, OpenAI, Cerebras, etc.)
- Multi-language support (Hinglish via Sarvam AI)
- Voice-first interaction design

### Email Intelligence System

**Architecture**: CrewAI Multi-Agent System

```python
# Agent roles
Manager Agent     → Task orchestration & prioritization
Inbox Agent       → Email fetching & parsing
Draft Agent       → Response composition
Send Agent        → Email delivery & tracking
```

**Technology Stack**:
- **CrewAI**: Multi-agent orchestration
- **Gmail API**: OAuth2 authentication
- **Outlook API**: Microsoft Graph integration
- **Firestore**: Conversation state storage

**Data Flow**:
```
Voice Input
  → Intent Analysis
    → Manager Agent
      → Inbox Agent (fetch emails)
        → Draft Agent (compose summary)
          → TTS Generation
            → Voice Output
```

### Price Tracking System

**Architecture**: Event-Driven Scraping Pipeline

```javascript
// Scraping pipeline
Scheduler (Cloud Scheduler)
  → Cloud Run (Scraper)
    → Playwright (Browser automation)
      → Redis Streams (Queue)
        → Price Comparison Engine
          → Pub/Sub (Alert events)
            → Notification Service
```

**Anti-Detection Measures**:
- Residential proxies
- Browser fingerprint rotation
- Request randomization
- CAPTCHA handling

**Checking Frequencies**:
- **High Priority**: 2 hours
- **Standard**: 6 hours
- **Low Priority**: 24 hours

### Media Streaming Integration

**Supported Platforms**:
- **Spotify**: Web API with OAuth2
- **YouTube**: Data API v3
- **Fen/Kodi**: JSON-RPC via Real-Debrid
- **Trakt.tv**: Metadata enrichment

**Unified Control Interface**:
```javascript
// Platform-agnostic commands
{
  "action": "play",
  "query": "happy music",
  "platform": "auto-detect"
}

// Resolution logic
Mood Detection → Platform Selection → API Call → Playback Confirmation
```

### Story Narrator Engine

**Pipeline**:
```
Story Text
  → Character Detection
    → Voice Assignment
      → Emotional Analysis
        → TTS Synthesis (ElevenLabs)
          → Audio Streaming (<400ms latency)
```

**Features**:
- 5+ distinct voice profiles
- Emotional modulation (angry, sad, excited)
- Interactive branching stories
- Indian language support

## Data Architecture

### Firestore Schema

```javascript
// Email conversations
emails {
  conversation_id: string,
  thread_id: string,
  participants: array,
  messages: array,
  summary: string,
  urgency_score: number,
  last_updated: timestamp
}

// Price tracking
products {
  product_id: string,
  url: string,
  title: string,
  current_price: number,
  price_history: array,
  last_checked: timestamp
}

// User preferences
users {
  user_id: string,
  email_settings: object,
  price_alerts: array,
  media_preferences: object,
  voice_profiles: array
}
```

### Redis Data Structures

```
# Caching
email:summary:{conversation_id} → String (TTL: 1h)
product:price:{product_id} → String (TTL: 6h)

# Queues
price:check:queue → Stream
story:narration:queue → Stream

# Rate limiting
user:rate:{user_id}:{feature} → String (TTL: 1m)
```

## Security Architecture

### Authentication & Authorization

```javascript
// OAuth2 flow for external services
Gmail/Outlook
  → OAuth2 with PKCE
    → Access Token (Firestore)
      → Refresh Token (Secret Manager)
```

### Data Protection

- **Encryption at Rest**: AES-256 (Firestore default)
- **Encryption in Transit**: TLS 1.3
- **Secret Management**: Google Secret Manager
- **API Security**: Request validation & rate limiting

### Access Control

```javascript
// Permission model
const permissions = {
  email_read: ['gmail.readonly'],
  email_send: ['gmail.send'],
  price_track: ['webshopping'],
  media_control: ['spotify.stream', 'youtube.watch']
};
```

## Performance & Scalability

### Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| **P95 Latency** | < 3s | Edge caching, optimization |
| **TTS Generation** | < 400ms | ElevenLabs streaming |
| **API Throughput** | 100 req/s | Cloud Functions auto-scaling |
| **Cache Hit Rate** | > 30% | Redis memorystore |

### Scalability Design

```javascript
// Auto-scaling configuration
Cloud Functions:
  - Min instances: 0 (scale to zero)
  - Max instances: 1000
  - Concurrency: 40

Cloud Run:
  - Min instances: 1
  - Max instances: 100
  - CPU: 2-4 vCPUs
```

## Monitoring & Observability

### Logging Strategy

```javascript
// Structured logging with Winston
logger.info({
  component: 'email_intelligence',
  action: 'fetch_emails',
  user_id: 'user_123',
  execution_time: 2450,
  status: 'success'
});
```

### Metrics Collection

- **Response Times**: p50, p95, p99
- **Error Rates**: By feature, by endpoint
- **Business Metrics**: Emails processed, price drops detected
- **Cost Tracking**: Per-feature cost attribution

### Health Monitoring

```javascript
// Health check endpoints
GET /health                    // Overall system health
GET /health/email              // Email service status
GET /health/price-tracking     // Price scraping status
GET /health/media-streaming    // Media platform status
```

## Deployment Architecture

### Infrastructure as Code

```yaml
# Terraform structure
infrastructure/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── cloud_functions/
│   │   ├── cloud_run/
│   │   ├── firestore/
│   │   └── redis/
```

### CI/CD Pipeline

```yaml
# GitHub Actions workflow
on: push
jobs:
  test:
    - Run unit tests
    - Run integration tests
  deploy:
    - Build container images
    - Deploy to GCP
    - Run smoke tests
```

## Disaster Recovery & Business Continuity

### Backup Strategy
- **Firestore**: 7-day automatic backups
- **Redis**: AOF persistence enabled
- **Cloud Storage**: Multi-region replication

### Failover Mechanisms
```javascript
// Circuit breaker pattern
if (failure_count > threshold) {
  circuit.state = 'OPEN';
  return fallback_response();
}

// Graceful degradation
if (service_unavailable) {
  return cached_response || simplified_response;
}
```

## Future Architecture Evolution

### Planned Enhancements (Q3-Q4 2026)
- **Edge Computing**: Cloudflare Workers for global latency
- **GraphQL API**: Unified query interface
- **Real-time Updates**: WebSocket connections
- **ML Pipelines**: Vertex AI for personalization

---

**Document Version**: 1.0
**Last Updated**: 2026-03-28
**Maintainer**: OmniClaw Architecture Team