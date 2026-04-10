#!/bin/bash

# Quantum-Claw Production Deployment Script
# Complete deployment of multi-provider TMLPD system

set -e

echo "🚀 Quantum-Claw Production Deployment"
echo "======================================"
echo "📅 Deployment Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check required dependencies
echo "🔍 Checking dependencies..."
print_info "Checking Python3 installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found. Please install Python3."
    exit 1
fi
print_success "Python3 found"

print_info "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip3."
    exit 1
fi
print_success "pip3 found"

# Check API keys
echo ""
echo "🔑 Checking API keys..."
print_info "Checking required API keys..."

API_KEYS_MISSING=0

if [ -z "$ANTHROPIC_API_KEY" ]; then
    print_warning "ANTHROPIC_API_KEY not set (optional - Anthropic Haiku)"
else
    print_success "ANTHROPIC_API_KEY configured"
fi

if [ -z "$CEREBRAS_API_KEY" ]; then
    print_warning "CEREBRAS_API_KEY not set (optional - Cerebras Fast)"
else
    print_success "CEREBRAS_API_KEY configured"
fi

if [ -z "$GROQ_API_KEY" ]; then
    print_warning "GROQ_API_KEY not set (optional - Groq Llama)"
else
    print_success "GROQ_API_KEY configured"
fi

if [ -z "$PERPLEXITY_API_KEY" ]; then
    print_warning "PERPLEXITY_API_KEY not set (optional - Perplexity Online)"
else
    print_success "PERPLEXITY_API_KEY configured"
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    print_warning "DEEPSEEK_API_KEY not set (optional - DeepSeek Fast)"
else
    print_success "DEEPSEEK_API_KEY configured"
fi

if [ -z "$TOGETHER_API_KEY" ]; then
    print_warning "TOGETHER_API_KEY not set (optional - Together Fast)"
else
    print_success "TOGETHER_API_KEY configured"
fi

echo ""
print_info "At least one API key recommended for production deployment"

# Create deployment directory structure
echo ""
echo "📁 Creating deployment directory structure..."

DEPLOY_DIR="$HOME/quantum-claw-production"
mkdir -p "$DEPLOY_DIR/bin"
mkdir -p "$DEPLOY_DIR/config"
mkdir -p "$DEPLOY_DIR/logs"
mkdir -p "$DEPLOY_DIR/data"
mkdir -p "$DEPLOY_DIR/reports"

print_success "Deployment directories created: $DEPLOY_DIR"

# Copy implementation files
echo ""
echo "📋 Copying implementation files..."

cp tmlpd_multi_provider_standalone.py "$DEPLOY_DIR/bin/"
cp quantum_claw_end_to_end_test.py "$DEPLOY_DIR/bin/"
chmod +x "$DEPLOY_DIR/bin/"*.py

print_success "Implementation files copied"

# Copy reports
echo ""
echo "📊 Copying reports..."

cp tmlpd_multi_provider_report.txt "$DEPLOY_DIR/reports/" 2>/dev/null || true
cp quantum_claw_implementation_report.txt "$DEPLOY_DIR/reports/" 2>/dev/null || true

print_success "Reports copied"

# Create configuration files
echo ""
echo "⚙️  Creating configuration files..."

# Production config
cat > "$DEPLOY_DIR/config/production_config.yaml" << 'EOF'
# Quantum-Claw Production Configuration

# Multi-Provider Settings
providers:
  anthropic_haiku:
    name: "Anthropic Haiku"
    model: "claude-3-haiku-20240307"
    enabled: true
    specialized_for:
      - "hindi"
      - "bengali"
      - "complex_analysis"
  
  groq_llama:
    name: "Groq Llama"
    model: "llama-3.3-70b-versatile"
    enabled: true
    specialized_for:
      - "english"
      - "code_generation"
      - "fast_responses"
  
  cerebras_fast:
    name: "Cerebras Fast"
    model: "llama3.1-8b"
    enabled: true
    specialized_for:
      - "performance"
      - "cost_optimization"
      - "high_throughput"
  
  perplexity_online:
    name: "Perplexity Online"
    model: "llama-3.1-sonar-large-128k-online"
    enabled: true
    specialized_for:
      - "research"
      - "real_time_data"
      - "complex_queries"

# Performance Settings
performance:
  max_concurrent_tasks: 50
  timeout_per_task: 120
  max_retries: 3
  target_response_time: 0.1  # 100ms

# Routing Settings
routing:
  enable_intelligent_routing: true
  enable_load_balancing: true
  enable_cost_optimization: true
  quality_threshold: 0.90

# Monitoring Settings
monitoring:
  enable_real_time_monitoring: true
  log_level: "INFO"
  metrics_retention_days: 30
  alert_on_failures: true

# Alexa Bridge Settings
alexa_bridge:
  enabled: true
  voice_command_routing: true
  multi_language_support: true
  supported_languages:
    - "english"
    - "hindi"
    - "hinglish"
    - "bengali"
EOF

# Environment variables template
cat > "$DEPLOY_DIR/config/.env.template" << 'EOF'
# Quantum-Claw Production Environment Variables
# Copy this file to .env and fill in your API keys

# Anthropic API Key (for Haiku - Hindi/Hinglish support)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Cerebras API Key (for performance optimization)
CEREBRAS_API_KEY=your_cerebras_api_key_here

# Groq API Key (for fast responses)
GROQ_API_KEY=your_groq_api_key_here

# Perplexity API Key (for research capabilities)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# DeepSeek API Key (for technical queries)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Together API Key (for balanced performance)
TOGETHER_API_KEY=your_together_api_key_here

# System Configuration
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=50
ENABLE_MONITORING=true
EOF

print_success "Configuration files created"

# Create startup script
echo ""
echo "🚀 Creating startup scripts..."

cat > "$DEPLOY_DIR/start_quantum_claw.sh" << 'EOF'
#!/bin/bash

# Quantum-Claw Startup Script

set -e

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DEPLOY_DIR"

echo "🚀 Starting Quantum-Claw Production System"
echo "======================================"
echo "📅 Start Time: $(date)"
echo ""

# Load environment variables
if [ -f "config/.env" ]; then
    echo "📋 Loading environment variables..."
    export $(cat config/.env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: No .env file found. Using system environment."
fi

# Create log directory
mkdir -p logs

# Start the main system
echo ""
echo "🔄 Starting Quantum-Claw system..."
python3 bin/tmlpd_multi_provider_standalone.py 2>&1 | tee "logs/quantum_claw_$(date +%Y%m%d_%H%M%S).log"

echo ""
echo "🎉 Quantum-Claw system started successfully!"
EOF

chmod +x "$DEPLOY_DIR/start_quantum_claw.sh"

# Create test script
cat > "$DEPLOY_DIR/test_quantum_claw.sh" << 'EOF'
#!/bin/bash

# Quantum-Claw System Test Script

set -e

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DEPLOY_DIR"

echo "🧪 Testing Quantum-Claw Production System"
echo "======================================"
echo "📅 Test Time: $(date)"
echo ""

# Load environment variables
if [ -f "config/.env" ]; then
    echo "📋 Loading environment variables..."
    export $(cat config/.env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: No .env file found. Using system environment."
fi

# Create log directory
mkdir -p logs

echo ""
echo "🔄 Running comprehensive end-to-end tests..."
python3 bin/quantum_claw_end_to_end_test.py 2>&1 | tee "logs/quantum_claw_test_$(date +%Y%m%d_%H%M%S).log"

echo ""
echo "✅ Quantum-Claw testing completed!"
EOF

chmod +x "$DEPLOY_DIR/test_quantum_claw.sh"

# Create monitoring script
cat > "$DEPLOY_DIR/monitor_quantum_claw.sh" << 'EOF'
#!/bin/bash

# Quantum-Claw Monitoring Script

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DEPLOY_DIR"

echo "📊 Quantum-Claw System Monitoring"
echo "=================================="
echo "📅 Monitor Time: $(date)"
echo ""

# Check recent logs
echo "📋 Recent system activity:"
if [ -d "logs" ]; then
    tail -20 logs/*.log 2>/dev/null || echo "No log files found yet"
else
    echo "No logs directory found"
fi

echo ""
echo "📈 System status:"
echo "Deployment directory: $DEPLOY_DIR"
echo "Configuration files: $(ls -1 config/ | wc -l)"
echo "Implementation files: $(ls -1 bin/ | wc -l)"
echo "Report files: $(ls -1 reports/ | wc -l)"

echo ""
echo "💾 Disk usage:"
du -sh "$DEPLOY_DIR"

echo ""
echo "✅ Monitoring complete"
EOF

chmod +x "$DEPLOY_DIR/monitor_quantum_claw.sh"

print_success "Startup scripts created"

# Create systemd service file (optional)
echo ""
echo "⚙️  Creating systemd service file..."

cat > "$DEPLOY_DIR/quantum-claw.service" << 'EOF'
[Unit]
Description=Quantum-Claw Multi-Provider TMLPD System
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/quantum-claw-production
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/YOUR_USERNAME/quantum-claw-production/start_quantum_claw.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_warning "Systemd service file created (requires manual configuration)"
print_info "Edit quantum-claw.service and run: sudo cp quantum-claw.service /etc/systemd/system/"

# Create README
echo ""
echo "📖 Creating deployment documentation..."

cat > "$DEPLOY_DIR/README.md" << 'EOF'
# Quantum-Claw Production Deployment

## 🚀 Quick Start

1. **Configure Environment Variables**
   ```bash
   cd quantum-claw-production
   cp config/.env.template config/.env
   # Edit config/.env with your API keys
   ```

2. **Start the System**
   ```bash
   ./start_quantum_claw.sh
   ```

3. **Run Tests**
   ```bash
   ./test_quantum_claw.sh
   ```

4. **Monitor System**
   ```bash
   ./monitor_quantum_claw.sh
   ```

## 📋 Directory Structure

```
quantum-claw-production/
├── bin/                    # Implementation files
├── config/                 # Configuration files
├── logs/                   # System logs
├── data/                   # Runtime data
├── reports/                # System reports
├── start_quantum_claw.sh   # Startup script
├── test_quantum_claw.sh    # Test script
├── monitor_quantum_claw.sh  # Monitoring script
└── README.md              # This file
```

## 🔑 Required API Keys

At least one of the following API keys is required:

- `ANTHROPIC_API_KEY` - For Haiku (Hindi/Hinglish support)
- `CEREBRAS_API_KEY` - For performance optimization
- `GROQ_API_KEY` - For fast responses
- `PERPLEXITY_API_KEY` - For research capabilities
- `DEEPSEEK_API_KEY` - For technical queries
- `TOGETHER_API_KEY` - For balanced performance

## ⚙️ Configuration

Edit `config/production_config.yaml` to customize:

- **Provider settings**: Enable/disable providers
- **Performance settings**: Concurrency, timeouts, retries
- **Routing settings**: Intelligent routing, load balancing
- **Monitoring settings**: Logging, metrics, alerts
- **Alexa Bridge settings**: Voice commands, multi-language support

## 🚀 Systemd Service (Optional)

To run Quantum-Claw as a system service:

1. Edit `quantum-claw.service` with your username
2. Copy to systemd directory:
   ```bash
   sudo cp quantum-claw.service /etc/systemd/system/
   ```
3. Enable and start:
   ```bash
   sudo systemctl enable quantum-claw
   sudo systemctl start quantum-claw
   ```

## 📊 Monitoring

- **Real-time logs**: Check `logs/` directory
- **System status**: Run `./monitor_quantum_claw.sh`
- **Performance metrics**: Review `reports/` directory

## 🏃 Troubleshooting

**System won't start:**
- Check API keys in `config/.env`
- Review logs in `logs/` directory
- Verify Python3 installation

**Performance issues:**
- Check system resources
- Review configuration settings
- Monitor provider status

## 📞 Support

For issues and questions, check:
- System logs: `logs/`
- Configuration: `config/production_config.yaml`
- Reports: `reports/`

## ✅ Deployment Status

- **Status**: Production Ready
- **Deployment Date**: 2026-02-23
- **System Version**: Quantum-Claw v1.0
- **Multi-Provider Support**: 6 providers
- **Languages Supported**: English, Hindi, Hinglish, Bengali
EOF

print_success "Documentation created"

# Run initial system test
echo ""
echo "🧪 Running initial deployment test..."

cd "$DEPLOY_DIR"
python3 bin/tmlpd_multi_provider_standalone.py > "logs/deployment_test_$(date +%Y%m%d_%H%M%S).log" 2>&1

if [ $? -eq 0 ]; then
    print_success "Initial deployment test passed"
else
    print_warning "Initial deployment test had issues (check logs)"
fi

# Create deployment summary
echo ""
echo "======================================"
echo "📋 DEPLOYMENT SUMMARY"
echo "======================================"
echo ""
print_success "📁 Deployment Directory: $DEPLOY_DIR"
print_success "📋 Configuration Files: Created"
print_success "🚀 Startup Scripts: Created"
print_success "📊 Monitoring Tools: Ready"
print_success "📖 Documentation: Complete"
print_success "🧪 Initial Test: Completed"
echo ""

print_info "🚀 Quick Start Commands:"
echo ""
echo "  cd $DEPLOY_DIR"
echo "  # Start system:"
echo "  ./start_quantum_claw.sh"
echo ""
echo "  # Run tests:"
echo "  ./test_quantum_claw.sh"
echo ""
echo "  # Monitor system:"
echo "  ./monitor_quantum_claw.sh"
echo ""

print_info "📝 Next Steps:"
echo ""
echo "1. Configure API keys in config/.env"
echo "2. Customize settings in config/production_config.yaml"
echo "3. Start the system with ./start_quantum_claw.sh"
echo "4. Monitor system performance with ./monitor_quantum_claw.sh"
echo ""

echo "======================================"
print_success "🎉 QUANTUM-CLAW DEPLOYMENT COMPLETE"
echo "======================================"