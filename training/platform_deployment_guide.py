#!/usr/bin/env python3
"""
GCACU Unified Platform - Production Deployment Guide
====================================================

Complete deployment documentation and automation for the GCACU Unified Platform.
Includes Docker containerization, cloud deployment, monitoring setup, and scaling strategies.

Author: GCACU Development Team
Date: 2026-04-03
Version: 1.0.0
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import subprocess
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: str  # development, staging, production
    platform_preset: str
    hardware: Dict[str, Any]
    scaling: Dict[str, Any]
    monitoring: Dict[str, Any]
    api_config: Dict[str, Any]


class DeploymentManager:
    """
    Manages deployment operations for the GCACU Unified Platform.

    Provides:
    - Docker containerization
    - Cloud deployment scripts (AWS, GCP, Azure)
    - Monitoring and logging setup
    - Auto-scaling configuration
    - Health checks and failover
    """

    def __init__(self, deployment_config: DeploymentConfig):
        """Initialize deployment manager"""
        self.config = deployment_config
        self.deployment_dir = Path(__file__).parent / "deployment"
        self.deployment_dir.mkdir(exist_ok=True)

    def create_docker_setup(self):
        """Create Docker deployment files"""
        logger.info("Creating Docker deployment setup...")

        # Create Dockerfile
        dockerfile = self._generate_dockerfile()
        dockerfile_path = self.deployment_dir / "Dockerfile"
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile)

        # Create docker-compose.yml
        docker_compose = self._generate_docker_compose()
        compose_path = self.deployment_dir / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            f.write(docker_compose)

        # Create .dockerignore
        dockerignore = self._generate_dockerignore()
        ignore_path = self.deployment_dir / ".dockerignore"
        with open(ignore_path, 'w') as f:
            f.write(dockerignore)

        logger.info(f"✅ Docker setup created in {self.deployment_dir}")

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for the platform"""
        return '''# GCACU Unified Platform - Production Docker Image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/models /app/cache /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GCACU_ENVIRONMENT=production

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "gcacu_unified_platform", "--mode", "production", "--port", "8080"]
'''

    def _generate_docker_compose(self) -> str:
        """Generate docker-compose.yml file"""
        return f'''version: '3.8'

services:
  gcacu-platform:
    build: .
    container_name: gcacu-unified-platform
    ports:
      - "8080:8080"
    environment:
      - GCACU_ENVIRONMENT={self.config.environment}
      - GCACU_MODE={self.config.platform_preset}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
      - ./cache:/app/cache
      - ./data:/app/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: {self.config.hardware.get('memory_limit', '8G')}
        reservations:
          memory: {self.config.hardware.get('memory_reservation', '4G')}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - gcacu-network

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    container_name: gcacu-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - gcacu-network

  # Optional: Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: gcacu-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped
    networks:
      - gcacu-network

  # Optional: Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: gcacu-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped
    networks:
      - gcacu-network

volumes:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  gcacu-network:
    driver: bridge
'''

    def _generate_dockerignore(self) -> str:
        """Generate .dockerignore file"""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/_build/
*.md

# Logs
*.log
logs/

# Data and cache
data/*.csv
data/*.json
cache/
*.pkl
*.h5

# Git
.git/
.gitignore

# Docker
.dockerignore
Dockerfile
docker-compose.yml

# Development files
requirements-dev.txt
setup.py
'''

    def create_kubernetes_deployment(self):
        """Create Kubernetes deployment files"""
        logger.info("Creating Kubernetes deployment files...")

        k8s_dir = self.deployment_dir / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)

        # Create deployment yaml
        deployment = self._generate_kubernetes_deployment()
        with open(k8s_dir / "deployment.yaml", 'w') as f:
            f.write(deployment)

        # Create service yaml
        service = self._generate_kubernetes_service()
        with open(k8s_dir / "service.yaml", 'w') as f:
            f.write(service)

        # Create configmap
        configmap = self._generate_kubernetes_configmap()
        with open(k8s_dir / "configmap.yaml", 'w') as f:
            f.write(configmap)

        # Create horizontal pod autoscaler
        hpa = self._generate_kubernetes_hpa()
        with open(k8s_dir / "hpa.yaml", 'w') as f:
            f.write(hpa)

        logger.info(f"✅ Kubernetes files created in {k8s_dir}")

    def _generate_kubernetes_deployment(self) -> str:
        """Generate Kubernetes deployment YAML"""
        return f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: gcacu-platform
  labels:
    app: gcacu-platform
    version: v1
spec:
  replicas: {self.config.scaling.get('min_replicas', 2)}
  selector:
    matchLabels:
      app: gcacu-platform
  template:
    metadata:
      labels:
        app: gcacu-platform
        version: v1
    spec:
      containers:
      - name: gcacu-platform
        image: gcacu-platform:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: GCACU_ENVIRONMENT
          value: "{self.config.environment}"
        - name: GCACU_MODE
          value: "{self.config.platform_preset}"
        - name: PYTHONUNBUFFERED
          value: "1"
        resources:
          requests:
            memory: "{self.config.hardware.get('memory_request', '4Gi')}"
            cpu: "{self.config.hardware.get('cpu_request', '2000m')}"
          limits:
            memory: "{self.config.hardware.get('memory_limit', '8Gi')}"
            cpu: "{self.config.hardware.get('cpu_limit', '4000m')}"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: cache
          mountPath: /app/cache
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: cache
        emptyDir: {{}}
      - name: logs
        emptyDir: {{}}
'''

    def _generate_kubernetes_service(self) -> str:
        """Generate Kubernetes service YAML"""
        return '''apiVersion: v1
kind: Service
metadata:
  name: gcacu-platform-service
  labels:
    app: gcacu-platform
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: gcacu-platform
'''

    def _generate_kubernetes_configmap(self) -> str:
        """Generate Kubernetes ConfigMap"""
        return f'''apiVersion: v1
kind: ConfigMap
metadata:
  name: gcacu-config
data:
  environment: "{self.config.environment}"
  mode: "{self.config.platform_preset}"
  log_level: "INFO"
  enable_monitoring: "true"
'''

    def _generate_kubernetes_hpa(self) -> str:
        """Generate Kubernetes Horizontal Pod Autoscaler"""
        return f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gcacu-platform-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gcacu-platform
  minReplicas: {self.config.scaling.get('min_replicas', 2)}
  maxReplicas: {self.config.scaling.get('max_replicas', 10)}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {self.config.scaling.get('target_cpu_utilization', 70)}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {self.config.scaling.get('target_memory_utilization', 80)}
'''

    def create_monitoring_setup(self):
        """Create monitoring and alerting configuration"""
        logger.info("Creating monitoring setup...")

        monitoring_dir = self.deployment_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)

        # Create Prometheus configuration
        prometheus_config = self._generate_prometheus_config()
        with open(monitoring_dir / "prometheus.yml", 'w') as f:
            f.write(prometheus_config)

        # Create Grafana dashboard
        grafana_dashboard = self._generate_grafana_dashboard()
        with open(monitoring_dir / "grafana_dashboard.json", 'w') as f:
            json.dump(grafana_dashboard, f, indent=2)

        # Create alert rules
        alert_rules = self._generate_alert_rules()
        with open(monitoring_dir / "alert_rules.yml", 'w') as f:
            f.write(alert_rules)

        logger.info(f"✅ Monitoring setup created in {monitoring_dir}")

    def _generate_prometheus_config(self) -> str:
        """Generate Prometheus configuration"""
        return '''global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - 'alert_rules.yml'

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093

scrape_configs:
  - job_name: 'gcacu-platform'
    static_configs:
      - targets: ['gcacu-platform:8080']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
'''

    def _generate_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        return {
            "dashboard": {
                "title": "GCACU Platform Monitoring",
                "panels": [
                    {
                        "title": "Request Rate",
                        "targets": [{
                            "expr": "rate(gcacu_requests_total[1m])"
                        }]
                    },
                    {
                        "title": "Prediction Latency",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, rate(gcacu_prediction_duration_seconds_bucket[5m]))"
                        }]
                    },
                    {
                        "title": "Memory Usage",
                        "targets": [{
                            "expr": "process_resident_memory_bytes / 1024 / 1024"
                        }]
                    },
                    {
                        "title": "CPU Usage",
                        "targets": [{
                            "expr": "rate(process_cpu_seconds_total[1m]) * 100"
                        }]
                    },
                    {
                        "title": "Cache Hit Rate",
                        "targets": [{
                            "expr": "gcacu_cache_hits / gcacu_cache_total"
                        }]
                    },
                    {
                        "title": "Average Confidence",
                        "targets": [{
                            "expr": "avg(gcacu_prediction_confidence)"
                        }]
                    }
                ]
            }
        }

    def _generate_alert_rules(self) -> str:
        """Generate Prometheus alert rules"""
        return '''groups:
- name: gcacu_platform_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(gcacu_errors_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors/sec"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(gcacu_prediction_duration_seconds_bucket[5m])) > 2
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High prediction latency"
      description: "95th percentile latency is {{ $value }} seconds"

  - alert: LowCacheHitRate
    expr: gcacu_cache_hits / gcacu_cache_total < 0.5
    for: 15m
    labels:
      severity: info
    annotations:
      summary: "Low cache hit rate"
      description: "Cache hit rate is {{ $value | humanizePercentage }}"

  - alert: HighMemoryUsage
    expr: process_resident_memory_bytes / 1024 / 1024 > 7000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}MB"

  - alert: ServiceDown
    expr: up{job="gcacu-platform"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "GCACU Platform is down"
      description: "The GCACU Platform service has been down for more than 2 minutes"
'''

    def create_ci_cd_pipeline(self):
        """Create CI/CD pipeline configuration"""
        logger.info("Creating CI/CD pipeline...")

        cicd_dir = self.deployment_dir / "cicd"
        cicd_dir.mkdir(exist_ok=True)

        # Create GitHub Actions workflow
        github_workflow = self._generate_github_workflow()
        with open(cicd_dir / "github_actions.yml", 'w') as f:
            f.write(github_workflow)

        # Create GitLab CI configuration
        gitlab_ci = self._generate_gitlab_ci()
        with open(cicd_dir / ".gitlab-ci.yml", 'w') as f:
            f.write(gitlab_ci)

        logger.info(f"✅ CI/CD pipeline created in {cicd_dir}")

    def _generate_github_workflow(self) -> str:
        """Generate GitHub Actions workflow"""
        return '''name: GCACU Platform CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ -v --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: |
        docker build -t gcacu-platform:${{ github.sha }} .
        docker tag gcacu-platform:${{ github.sha }} gcacu-platform:latest

    - name: Run security scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: gcacu-platform:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Docker image
      if: github.ref == 'refs/heads/main'
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push gcacu-platform:${{ github.sha }}
        docker push gcacu-platform:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      run: |
        # Add deployment commands here
        echo "Deploying to production..."
'''

    def _generate_gitlab_ci(self) -> str:
        """Generate GitLab CI configuration"""
        return r'''stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: gcacu-platform
  DOCKER_TAG: $CI_COMMIT_SHORT_SHA

test:
  stage: test
  image: python:3.10
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
    - pytest tests/ -v --cov=. --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
    - docker tag $DOCKER_IMAGE:$DOCKER_TAG $DOCKER_IMAGE:latest
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $DOCKER_IMAGE:$DOCKER_TAG
    - docker push $DOCKER_IMAGE:latest

deploy_production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/gcacu-platform gcacu-platform=$DOCKER_IMAGE:$DOCKER_TAG
    - kubectl rollout status deployment/gcacu-platform
  only:
    - main
  when: manual
'''

    def generate_deployment_script(self, platform: str = 'docker') -> str:
        """Generate deployment script for specific platform"""
        if platform == 'docker':
            return self._generate_docker_deployment_script()
        elif platform == 'kubernetes':
            return self._generate_kubernetes_deployment_script()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _generate_docker_deployment_script(self) -> str:
        """Generate Docker deployment script"""
        return '''#!/bin/bash
# GCACU Platform Docker Deployment Script

set -e

echo "🚀 Deploying GCACU Platform with Docker..."

# Build Docker image
echo "Building Docker image..."
docker build -t gcacu-platform:latest .

# Stop existing container
if [ "$(docker ps -q -f name=gcacu-platform)" ]; then
    echo "Stopping existing container..."
    docker stop gcacu-platform
    docker rm gcacu-platform
fi

# Start new container
echo "Starting new container..."
docker run -d \\
    --name gcacu-platform \\
    -p 8080:8080 \\
    -e GCACU_ENVIRONMENT=production \\
    -e GCACU_MODE=production \\
    -v $(pwd)/logs:/app/logs \\
    -v $(pwd)/models:/app/models \\
    -v $(pwd)/cache:/app/cache \\
    --restart unless-stopped \\
    gcacu-platform:latest

# Wait for container to be healthy
echo "Waiting for container to be healthy..."
sleep 10

# Check container status
if docker ps | grep -q gcacu-platform; then
    echo "✅ GCACU Platform deployed successfully!"
    echo "📍 API available at: http://localhost:8080"
    echo "📊 Health check: curl http://localhost:8080/health"
else
    echo "❌ Deployment failed!"
    docker logs gcacu-platform
    exit 1
fi
'''

    def _generate_kubernetes_deployment_script(self) -> str:
        """Generate Kubernetes deployment script"""
        return '''#!/bin/bash
# GCACU Platform Kubernetes Deployment Script

set -e

echo "🚀 Deploying GCACU Platform to Kubernetes..."

# Build and push Docker image
echo "Building Docker image..."
docker build -t gcacu-platform:latest .

# Tag for registry (update with your registry)
echo "Tagging image for registry..."
docker tag gcacu-platform:latest your-registry/gcacu-platform:latest

# Push to registry
echo "Pushing to registry..."
docker push your-registry/gcacu-platform:latest

# Apply Kubernetes configurations
echo "Applying Kubernetes configurations..."
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml
kubectl apply -f deployment/kubernetes/hpa.yaml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s \\
    deployment/gcacu-platform -n default

# Get service information
echo "Getting service information..."
kubectl get services gcacu-platform-service

echo "✅ GCACU Platform deployed to Kubernetes successfully!"
'''

    def create_health_check_script(self):
        """Create health check script"""
        health_script = '''#!/bin/bash
# GCACU Platform Health Check Script

HEALTH_URL="http://localhost:8080/health"
TIMEOUT=10

echo "🏥 Checking GCACU Platform health..."

if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT $HEALTH_URL || echo "000")

    if [ "$RESPONSE" = "200" ]; then
        echo "✅ Platform is healthy"
        exit 0
    else
        echo "❌ Platform health check failed (HTTP $RESPONSE)"
        exit 1
    fi
else
    echo "❌ curl command not available"
    exit 1
fi
'''

        health_check_path = self.deployment_dir / "health_check.sh"
        with open(health_check_path, 'w') as f:
            f.write(health_script)

        # Make executable
        health_check_path.chmod(0o755)

        logger.info(f"✅ Health check script created at {health_check_path}")


def create_deployment_guide():
    """Create comprehensive deployment guide"""
    guide = '''# GCACU Unified Platform - Deployment Guide

## Quick Start

### Docker Deployment (Recommended for Development)

1. **Build the Docker image:**
   ```bash
   docker build -t gcacu-platform:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \\
     --name gcacu-platform \\
     -p 8080:8080 \\
     -e GCACU_MODE=production \\
     gcacu-platform:latest
   ```

3. **Verify deployment:**
   ```bash
   curl http://localhost:8080/health
   ```

### Kubernetes Deployment (Recommended for Production)

1. **Apply configurations:**
   ```bash
   kubectl apply -f deployment/kubernetes/
   ```

2. **Check deployment status:**
   ```bash
   kubectl get pods -l app=gcacu-platform
   kubectl get services gcacu-platform-service
   ```

3. **Scale deployment:**
   ```bash
   kubectl scale deployment gcacu-platform --replicas=3
   ```

## Configuration

### Environment Variables

- `GCACU_MODE`: Processing mode (production, development, testing)
- `GCACU_ENVIRONMENT`: Environment name (production, staging, development)
- `GCACU_MAX_MEMORY_GB`: Maximum memory usage in GB
- `GCACU_WORKERS`: Number of worker processes
- `GCACU_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Hardware Requirements

**Minimum Requirements:**
- CPU: 2 cores
- Memory: 4GB RAM
- Storage: 10GB

**Recommended for Production:**
- CPU: 4+ cores
- Memory: 8GB+ RAM
- Storage: 50GB SSD
- GPU: Optional (for faster inference)

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up --scale gcacu-platform=3

# Kubernetes
kubectl scale deployment gcacu-platform --replicas=5
```

### Vertical Scaling

```bash
# Increase resources in deployment.yaml
resources:
  requests:
    memory: "16Gi"
    cpu: "8000m"
```

## Monitoring

### Prometheus Metrics

Available at `http://localhost:9090`

Key metrics:
- `gcacu_requests_total`: Total request count
- `gcacu_prediction_duration_seconds`: Prediction latency
- `gcacu_cache_hits`: Cache hit count
- `gcacu_errors_total`: Error count

### Grafana Dashboards

Available at `http://localhost:3000`

Default credentials:
- Username: `admin`
- Password: `admin`

## Troubleshooting

### Common Issues

**High Memory Usage:**
- Use memory-optimized preset
- Reduce batch size
- Enable result caching

**Slow Performance:**
- Use MLX optimization (Mac)
- Enable parallel processing
- Use faster model architecture

**Deployment Failures:**
- Check Docker logs: `docker logs gcacu-platform`
- Check pod logs: `kubectl logs <pod-name>`
- Verify resource allocation
- Check network connectivity

### Health Checks

```bash
# Manual health check
curl http://localhost:8080/health

# Detailed health status
curl http://localhost:8080/health/detailed

# Platform metrics
curl http://localhost:8080/metrics
```

## Backup and Recovery

### Data Backup

```bash
# Backup models
docker cp gcacu-platform:/app/models ./backup/models

# Backup cache
docker cp gcacu-platform:/app/cache ./backup/cache

# Backup logs
docker cp gcacu-platform:/app/logs ./backup/logs
```

### Recovery

```bash
# Restore from backup
docker cp ./backup/models gcacu-platform:/app/models
docker restart gcacu-platform
```

## Security

### Recommended Security Practices

1. **Network Security:**
   - Use HTTPS in production
   - Implement rate limiting
   - Configure firewall rules

2. **Container Security:**
   - Run as non-root user
   - Scan images for vulnerabilities
   - Keep dependencies updated

3. **API Security:**
   - Implement authentication
   - Validate input data
   - Use secure headers

## Performance Tuning

### Optimization Tips

1. **Caching:**
   - Enable result caching for repeated queries
   - Use Redis for distributed caching
   - Set appropriate cache TTL

2. **Batch Processing:**
   - Use batch API for multiple requests
   - Adjust batch size based on load
   - Enable parallel processing

3. **Model Selection:**
   - Use baseline models for speed
   - Use ensemble models for accuracy
   - Enable MLX optimization on Mac

## Maintenance

### Regular Maintenance Tasks

- Monitor system logs daily
- Review performance metrics weekly
- Update dependencies monthly
- Backup data before updates
- Test failover procedures quarterly

### Log Management

```bash
# View logs
docker logs -f gcacu-platform

# Rotate logs
docker exec gcacu-platform logrotate /etc/logrotate.d/gcacu

# Archive old logs
docker exec gcacu-platform find /app/logs -name "*.log" -mtime +30 -delete
```

## Support and Documentation

For detailed documentation, visit:
- GitHub: [gcacu-platform](https://github.com/your-org/gcacu-platform)
- Docs: [Full Documentation](https://docs.gcacu-platform.com)
- Issues: [Issue Tracker](https://github.com/your-org/gcacu-platform/issues)

## License

GCACU Unified Platform - MIT License
Copyright (c) 2026 GCACU Development Team
'''

    guide_path = Path(__file__).parent / "DEPLOYMENT_GUIDE.md"
    with open(guide_path, 'w') as f:
        f.write(guide)

    logger.info(f"✅ Deployment guide created at {guide_path}")


# Main execution
if __name__ == "__main__":
    # Example deployment setup
    deployment_config = DeploymentConfig(
        environment="production",
        platform_preset="production",
        hardware={
            'memory_limit': '8Gi',
            'memory_request': '4Gi',
            'cpu_limit': '4000m',
            'cpu_request': '2000m'
        },
        scaling={
            'min_replicas': 2,
            'max_replicas': 10,
            'target_cpu_utilization': 70,
            'target_memory_utilization': 80
        },
        monitoring={
            'enabled': True,
            'prometheus_port': 9090,
            'grafana_port': 3000
        },
        api_config={
            'port': 8080,
            'workers': 4,
            'timeout': 30
        }
    )

    manager = DeploymentManager(deployment_config)

    # Create deployment files
    manager.create_docker_setup()
    manager.create_kubernetes_deployment()
    manager.create_monitoring_setup()
    manager.create_ci_cd_pipeline()
    manager.create_health_check_script()
    create_deployment_guide()

    print("✅ Deployment setup complete!")
    print(f"📁 Deployment files created in: {manager.deployment_dir}")
    print("📖 Read DEPLOYMENT_GUIDE.md for detailed instructions")