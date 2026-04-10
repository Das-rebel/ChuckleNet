#!/bin/bash

# Setup and Run Multi-Provider TMLPD Testing System
# This script helps configure API keys and execute accelerated testing

echo "🚀 TMLPD Multi-Provider Setup and Execution"
echo "============================================================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install required dependencies
echo "📦 Checking required dependencies..."
pip3 install aiohttp 2>&1 | grep -q "Requirement already satisfied" || echo "   Installing aiohttp..."

# Check API keys
echo ""
echo "🔑 Checking API Keys Configuration..."
echo "--------------------------------------------"

required_keys=(
    "ANTHROPIC_API_KEY"
    "GROQ_API_KEY" 
    "CEREBRAS_API_KEY"
    "OPENROUTER_API_KEY"
    "DEEPSEEK_API_KEY"
    "TOGETHER_API_KEY"
)

available_keys=0
missing_keys=()

for key in "${required_keys[@]}"; do
    if [ -n "${!key}" ]; then
        echo "✅ $key: Configured"
        available_keys=$((available_keys + 1))
    else
        echo "❌ $key: Missing"
        missing_keys+=("$key")
    fi
done

echo ""
echo "📊 Key Configuration Summary:"
echo "   Available: $available_keys/7"
echo "   Missing: ${#missing_keys[@]}/7"

if [ ${#missing_keys[@]} -eq 0 ]; then
    echo ""
    echo "✅ All API keys configured! Ready to execute."
else
    echo ""
    echo "⚠️  Some API keys are missing."
    echo ""
    echo "To configure API keys, you can:"
    echo "1. Add to your .bashrc or .zshrc:"
    for key in "${missing_keys[@]}"; do
        echo "   export $key='your_api_key_here'"
    done
    echo ""
    echo "2. Or create a .env file:"
    for key in "${missing_keys[@]}"; do
        echo "   $key='your_api_key_here'"
    done
    echo ""
    echo "3. Or set them temporarily:"
    for key in "${missing_keys[@]}"; do
        echo "   export $key='your_api_key_here'"
    done
    echo ""
    echo "After setting keys, run this script again."
    exit 0
fi

echo ""
echo "⚡ Starting Multi-Provider TMLPD Execution..."
echo "============================================================"
echo ""

# Create necessary directories
mkdir -p tests/data
mkdir -p reports

# Check if the main script exists
if [ ! -f "tmlpd_multi_provider_parallel_testing.py" ]; then
    echo "❌ Main script not found: tmlpd_multi_provider_parallel_testing.py"
    exit 1
fi

# Run the multi-provider test executor
python3 tmlpd_multi_provider_parallel_testing.py

# Check exit status
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ Multi-Provider TMLPD Testing completed successfully!"
    echo ""
    echo "📄 Check the generated report:"
    echo "   cat reports/tmlpd_multi_provider_report.md"
else
    echo ""
    echo "❌ Multi-Provider TMLPD Testing failed with exit code: $exit_code"
fi

exit $exit_code