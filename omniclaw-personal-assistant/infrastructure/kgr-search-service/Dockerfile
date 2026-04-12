FROM node:20-slim

WORKDIR /app

# Install curl for downloading knowledge graph
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY *.js ./

# Create data directory
RUN mkdir -p /app/data

# Download knowledge graph from GCS
ENV KG_GCS_URL=https://storage.googleapis.com/omniclaw-knowledge-graph/unified_knowledge_graph.json
ENV KG_PATH=/app/data/unified_knowledge_graph.json

RUN curl -sL ${KG_GCS_URL} -o ${KG_PATH}

EXPOSE 8080

ENV PORT=8080

CMD ["node", "standalone-search-file-based.js"]