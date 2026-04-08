#!/bin/bash
# Complete Production Deployment for GCACU Autonomous Laughter Prediction System

set -e  # Exit on error

echo "🚀 GCACU Autonomous Laughter Prediction - Production Deployment"
echo "================================================================"

# Configuration
PROJECT_DIR="/Users/Subho/autonomous_laughter_prediction"
MODEL_DIR="${PROJECT_DIR}/models/xlmr_turboquant_training"
API_PORT=8080
LOG_DIR="${PROJECT_DIR}/logs"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${MODEL_DIR}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 not found"
        exit 1
    fi

    # Check for required packages
    REQUIRED_PACKAGES="torch transformers flask flask-cors psutil"
    for package in $REQUIRED_PACKAGES; do
        if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
            log_warn "Package ${package} not installed. Installing..."
            pip3 install "${package}"
        fi
    done

    log_info "✅ All dependencies satisfied"
}

# Check if model exists
check_model() {
    log_info "Checking model availability..."

    if [ ! -d "${MODEL_DIR}" ] || [ -z "$(ls -A ${MODEL_DIR})" ]; then
        log_warn "Model not found at ${MODEL_DIR}"
        log_info "Please ensure training has completed successfully"
        log_info "Run training script: python3 training/train_with_turboquant.py"
        return 1
    fi

    # Check for required model files
    REQUIRED_FILES=("pytorch_model.bin" "config.json" "tokenizer_config.json")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "${MODEL_DIR}/${file}" ]; then
            log_warn "Missing model file: ${file}"
            return 1
        fi
    done

    log_info "✅ Model files validated"
    return 0
}

# Start API server
start_api_server() {
    log_info "Starting API server on port ${API_PORT}..."

    cd "${PROJECT_DIR}"

    # Set environment variables
    export MODEL_PATH="${MODEL_DIR}"
    export API_PORT="${API_PORT}"
    export USE_TURBOQUANT="true"

    # Start server in background
    nohup python3 api/laughter_prediction_api.py > "${LOG_DIR}/api_server.log" 2>&1 &
    API_PID=$!

    # Save PID for later management
    echo $API_PID > "${LOG_DIR}/api_server.pid"

    # Wait for server to start
    sleep 5

    # Check if server is running
    if ps -p $API_PID > /dev/null; then
        log_info "✅ API server started (PID: ${API_PID})"
        log_info "API available at: http://localhost:${API_PORT}"
    else
        log_error "Failed to start API server"
        cat "${LOG_DIR}/api_server.log"
        return 1
    fi

    return 0
}

# Start monitoring system
start_monitoring() {
    log_info "Starting monitoring system..."

    cd "${PROJECT_DIR}"

    # Start performance monitor in background
    nohup python3 -c "
from monitoring.performance_monitor import get_monitor
import time

monitor = get_monitor()
monitor.start_background_monitoring(interval_seconds=60)
log_info('Monitoring system started')

# Keep process running
try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    log_info('Monitoring stopped')
" > "${LOG_DIR}/monitoring.log" 2>&1 &
    MONITOR_PID=$!

    echo $MONITOR_PID > "${LOG_DIR}/monitoring.pid"

    sleep 2

    if ps -p $MONITOR_PID > /dev/null; then
        log_info "✅ Monitoring system started (PID: ${MONITOR_PID})"
    else
        log_warn "Failed to start monitoring system"
    fi

    return 0
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Wait for API to be ready
    sleep 3

    # Check API health endpoint
    if command -v curl &> /dev/null; then
        HEALTH_CHECK=$(curl -s http://localhost:${API_PORT}/health)
        if [ $? -eq 0 ]; then
            log_info "✅ API health check passed"
            log_info "Response: ${HEALTH_CHECK}"
        else
            log_error "API health check failed"
            return 1
        fi
    else
        log_warn "curl not available, skipping health check"
    fi

    return 0
}

# Display deployment status
display_status() {
    echo ""
    echo "🎯 Deployment Status"
    echo "===================="

    if [ -f "${LOG_DIR}/api_server.pid" ]; then
        API_PID=$(cat "${LOG_DIR}/api_server.pid")
        if ps -p $API_PID > /dev/null; then
            echo -e "✅ ${GREEN}API Server${NC}: Running (PID: ${API_PID})"
            echo "   Endpoint: http://localhost:${API_PORT}"
        else
            echo -e "❌ ${RED}API Server${NC}: Not running"
        fi
    fi

    if [ -f "${LOG_DIR}/monitoring.pid" ]; then
        MONITOR_PID=$(cat "${LOG_DIR}/monitoring.pid")
        if ps -p $MONITOR_PID > /dev/null; then
            echo -e "✅ ${GREEN}Monitoring${NC}: Running (PID: ${MONITOR_PID})"
        else
            echo -e "❌ ${RED}Monitoring${NC}: Not running"
        fi
    fi

    echo ""
    echo "📁 Log Files:"
    echo "   API Server: ${LOG_DIR}/api_server.log"
    echo "   Monitoring: ${LOG_DIR}/monitoring.log"
    echo ""
}

# Cleanup function
cleanup() {
    log_info "Stopping services..."

    if [ -f "${LOG_DIR}/api_server.pid" ]; then
        API_PID=$(cat "${LOG_DIR}/api_server.pid}")
        kill $API_PID 2>/dev/null || true
        rm "${LOG_DIR}/api_server.pid"
        log_info "API server stopped"
    fi

    if [ -f "${LOG_DIR}/monitoring.pid" ]; then
        MONITOR_PID=$(cat "${LOG_DIR}/monitoring.pid")
        kill $MONITOR_PID 2>/dev/null || true
        rm "${LOG_DIR}/monitoring.pid"
        log_info "Monitoring stopped"
    fi
}

# Main deployment function
main() {
    cd "${PROJECT_DIR}"

    # Check dependencies
    check_dependencies

    # Check model (optional, allow deployment without model for testing)
    if ! check_model; then
        log_warn "Continuing deployment without trained model..."
        log_warn "API will return errors until model is trained"
    fi

    # Start services
    start_api_server
    start_monitoring

    # Run health checks
    run_health_checks

    # Display status
    display_status

    echo ""
    log_info "🎉 Deployment complete!"
    echo ""
    echo "Quick Test Commands:"
    echo "  # Health check"
    echo "  curl http://localhost:${API_PORT}/health"
    echo ""
    echo "  # Prediction test"
    echo '  curl -X POST http://localhost:'${API_PORT}'/predict \'
    echo '    -H "Content-Type: application/json" \'
    echo '    -d '"'"'{"text": "why did the chicken cross the road"}"'"
    echo ""
    echo "Management:"
    echo "  Stop services: kill \$(cat ${LOG_DIR}/api_server.pid)"
    echo "  View logs: tail -f ${LOG_DIR}/api_server.log"
    echo ""
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Run main function
main "$@"