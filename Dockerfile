FROM python:3.11-slim

LABEL maintainer="ChuckleNet Team"
LABEL description="Biosemiotic AI for Computational Humor Recognition"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY models/ ./models/ 2>/dev/null || true
COPY docs/ ./docs/
COPY README.md .
COPY LICENSE .

ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models/best_model
ENV DEVICE=cpu

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]