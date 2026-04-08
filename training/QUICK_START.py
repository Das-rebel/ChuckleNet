#!/usr/bin/env python3
"""
GCACU Unified Platform - Quick Start Guide
==========================================

Get started with the GCACU Unified Platform in minutes!
This guide will walk you through installation, basic usage, and advanced features.

Author: GCACU Development Team
Date: 2026-04-03
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path

# Add project directory to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * len(title))


def quick_start_demo():
    """Run quick start demonstration"""
    print_section("🎭 GCACU Unified Platform - Quick Start Guide")

    print("""
🚀 Welcome to the GCACU Unified Platform!

This revolutionary platform combines all GCACU components into one seamless
system for autonomous laughter prediction with cultural intelligence.

Let's get you started in 3 simple steps:
    """)

    # Step 1: Installation
    print_section("Step 1: Installation")
    print("""
Install the required dependencies:

    pip install -r requirements.txt

Or install core dependencies only:

    pip install torch transformers numpy pandas scikit-learn scipy matplotlib seaborn
    """)

    # Step 2: Basic Usage
    print_section("Step 2: Basic Usage")
    print("""
Start with this simple example:

    from training.gcacu_unified_platform import GCACUUnifiedPlatform, PlatformConfig

    # Initialize the platform
    platform = GCACUUnifiedPlatform(PlatformConfig())

    # Make a prediction
    result = platform.predict_laughter(
        "So I was at this restaurant, and the waitress comes over..."
    )

    print(f"Laughter probability: {result.prediction:.3f}")
    print(f"Confidence: {result.confidence:.3f}")
    """)

    # Step 3: Advanced Features
    print_section("Step 3: Advanced Features")
    print("""
The platform offers many advanced features:

✅ Cultural Intelligence - Understand US/UK/Indian comedy
✅ Multilingual Support - Process English, Hinglish, Hindi content
✅ Batch Processing - Handle multiple requests efficiently
✅ REST API - Production-ready web service
✅ Performance Monitoring - Track system performance
✅ Auto-Optimization - Adapts to your hardware automatically
    """)

    # Live Demo
    print_section("Live Demo")

    try:
        # Import platform
        from training.gcacu_unified_platform import (
            GCACUUnifiedPlatform, PlatformConfig, ProcessingMode
        )

        print("\n🔧 Initializing platform...")
        config = PlatformConfig(
            default_mode=ProcessingMode.AUTO,
            enable_cultural_intelligence=True,
            enable_multilingual_support=True
        )

        platform = GCACUUnifiedPlatform(config)
        print("✅ Platform initialized successfully!")

        # Demo predictions
        print_subsection("Example 1: US Comedy")
        us_text = "So I was at this restaurant in New York, right? And the waitress comes over, and I'm like, 'Can I get some extra napkins?' She looks at me like I just asked for her kidney!"

        result = platform.predict_laughter(us_text)
        print(f"Text: {us_text[:100]}...")
        print(f"Prediction: {result.prediction:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Language: {result.language_detected}")
        print(f"Domain: {result.content_analysis.domain.value}")

        print_subsection("Example 2: Indian Comedy")
        indian_text = "You know, when I first moved to America from India, I didn't understand the concept of 'roommate.' In India, we live with our parents until marriage!"

        result = platform.predict_laughter(indian_text)
        print(f"Text: {indian_text[:100]}...")
        print(f"Prediction: {result.prediction:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Language: {result.language_detected}")
        if result.cultural_context:
            print(f"Cultural Context: {result.cultural_context['culture']}")

        print_subsection("Example 3: Batch Processing")
        texts = [
            "Why did the chicken cross the road? To get to the other side!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Have you ever noticed how快递员always knock at the wrong time?"
        ]

        batch_result = platform.predict_batch(texts)
        print(f"Processed {len(batch_result.results)} items")
        print(f"Throughput: {batch_result.throughput_items_per_second:.2f} items/sec")
        print(f"Average time: {batch_result.average_time_per_item_ms:.2f}ms")
        print(f"Success rate: {batch_result.success_rate:.1%}")

        print_subsection("Example 4: Content Analysis")
        analysis_text = "British people are so polite. They'll apologize when you step on their foot!"

        analysis = platform.analyze_content(analysis_text)
        print(f"Text: {analysis_text}")
        print(f"Domain: {analysis.domain.value}")
        print(f"Culture: {analysis.culture.value if analysis.culture else 'N/A'}")
        print(f"Language: {analysis.language}")
        print(f"Complexity: {analysis.processing_complexity:.2f}")
        print(f"Recommended Architecture: {analysis.recommended_architecture.value}")

        print_subsection("Platform Metrics")
        metrics = platform.get_platform_metrics()
        print(f"Total Predictions: {metrics['total_predictions']}")
        print(f"Average Confidence: {metrics['average_confidence']:.3f}")
        print(f"Memory Usage: {metrics['memory_usage_mb']:.2f}MB")
        print(f"Cache Size: {metrics['cache_size']}")

        # Cleanup
        platform.shutdown()
        print("\n✅ Demo completed successfully!")

    except ImportError as e:
        print(f"\n⚠️ Some components are not available: {e}")
        print("The platform will run with limited functionality.")
        print("Please install the required dependencies for full functionality.")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        logger.exception("Demo failed")

    # Next Steps
    print_section("Next Steps")
    print("""
🎯 Explore More Features:

1. **Cultural Intelligence**
   from training.global_english_comedy_system import GlobalEnglishComedyProcessor
   processor = GlobalEnglishComedyProcessor()
   culture, confidence = processor.detect_cultural_context(text)

2. **REST API**
   python training/platform_api_layer.py --mode api --port 8080
   # Access at http://localhost:8080/docs

3. **Configuration Management**
   from training.platform_configuration import ConfigurationManager, DeploymentPreset
   manager = ConfigurationManager()
   config = manager.get_preset_config(DeploymentPreset.PRODUCTION)

4. **Benchmarking**
   python training/platform_benchmark_suite.py

5. **Deployment**
   python training/platform_deployment_guide.py

📚 Documentation:
- Full README: training/PLATFORM_README.md
- API Docs: http://localhost:8080/docs (when API is running)
- Code Examples: Look for example_*.py files

🤝 Support:
- GitHub Issues: https://github.com/your-org/gcacu-platform/issues
- Documentation: https://docs.gcacu-platform.com
    """)

    print_section("Quick Start Complete!")
    print("""
You're now ready to use the GCACU Unified Platform!

For more information, check out the comprehensive README:
    training/PLATFORM_README.md

Happy predicting! 🎭✨
    """)


def example_use_cases():
    """Show example use cases"""
    print_section("🎯 Example Use Cases")

    use_cases = {
        "Content Creation": {
            "description": "Analyze comedy content for audience prediction",
            "code": '''
# Analyze stand-up comedy material
platform = GCACUUnifiedPlatform(PlatformConfig())

joke = "Why did the comedian cross the road? To get to the punchline!"
result = platform.predict_laughter(joke)

if result.prediction > 0.7:
    print("This joke will likely get laughs!")
else:
    print("This joke might need work.")
'''
        },

        "Cross-Cultural Adaptation": {
            "description": "Adapt comedy content for different cultures",
            "code": '''
from training.global_english_comedy_system import ComedyCulture

processor = GlobalEnglishComedyProcessor()

# Adapt Indian joke for US audience
indian_joke = "In India, we live with our parents until marriage!"
adaptation = processor.adapt_joke_cross_cultural(indian_joke, ComedyCulture.US)

print(f"Adaptation score: {adaptation.cultural_adaptation_score:.2f}")
print(f"Suggestions: {adaptation.adaptation_suggestions}")
'''
        },

        "Batch Content Analysis": {
            "description": "Process large datasets efficiently",
            "code": '''
# Process YouTube comments dataset
comments = load_youtube_comments()  # Your data loading function

batch_result = platform.predict_batch(
    comments,
    mode=ProcessingMode.HIGH_SPEED
)

print(f"Processed {len(batch_result.results)} comments")
print(f"Throughput: {batch_result.throughput_items_per_second:.2f} items/sec")
print(f"Average laughter probability: {np.mean([r.prediction for r in batch_result.results]):.3f}")
'''
        },

        "Real-Time API": {
            "description": "Deploy as a real-time prediction service",
            "code": '''
# Start API server
from training.platform_api_layer import GCACUPythonAPI

api = GCACUPythonAPI()

# Or start REST API
# python training/platform_api_layer.py --mode api --port 8080

# Use API
result = api.predict("Your comedy text here")
print(f"Prediction: {result['prediction']:.3f}")
'''
        }
    }

    for use_case, details in use_cases.items():
        print_subsection(use_case)
        print(f"Description: {details['description']}")
        print(f"Code Example:")
        print(details['code'])
        print()


def troubleshooting_guide():
    """Show common issues and solutions"""
    print_section("🔧 Troubleshooting Guide")

    issues = {
        "Import Errors": {
            "problem": "Module not found errors",
            "solution": '''
# Install all required dependencies
pip install -r requirements.txt

# Or install core dependencies only
pip install torch transformers numpy pandas scikit-learn scipy matplotlib seaborn
'''
        },

        "Memory Issues": {
            "problem": "Out of memory errors",
            "solution": '''
# Use memory-optimized configuration
config = PlatformConfig(
    default_mode=ProcessingMode.MEMORY_OPTIMIZED,
    max_memory_gb=4.0,
    target_batch_size=2
)
'''
        },

        "Slow Performance": {
            "problem": "Predictions taking too long",
            "solution": '''
# Enable high-speed mode
result = platform.predict_laughter(text, mode=ProcessingMode.HIGH_SPEED)

# Or enable MLX optimization (Mac users)
config = PlatformConfig(
    enable_mlx_optimization=True
)
'''
        },

        "Cultural Intelligence Not Working": {
            "problem": "Cultural context not detected",
            "solution": '''
# Ensure cultural intelligence is enabled
config = PlatformConfig(
    enable_cultural_intelligence=True,
    enable_multilingual_support=True
)
'''
        },

        "API Server Not Starting": {
            "problem": "Cannot start REST API server",
            "solution": '''
# Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Then start the server
python training/platform_api_layer.py --mode api --port 8080
'''
        }
    }

    for issue, details in issues.items():
        print_subsection(issue)
        print(f"Problem: {details['problem']}")
        print(f"Solution:")
        print(details['solution'])
        print()


def performance_tips():
    """Show performance optimization tips"""
    print_section("⚡ Performance Tips")

    tips = [
        {
            "category": "Processing Mode Selection",
            "tips": [
                "Use AUTO for general purposes",
                "Use HIGH_SPEED for real-time applications",
                "Use HIGH_ACCURACY for critical predictions",
                "Use MEMORY_OPTIMIZED for resource-constrained environments"
            ]
        },
        {
            "category": "Batch Processing",
            "tips": [
                "Process multiple texts together for better throughput",
                "Use batch sizes of 16-32 for optimal performance",
                "Enable parallel processing for independent requests"
            ]
        },
        {
            "category": "Caching",
            "tips": [
                "Enable result caching for repeated queries",
                "Set appropriate cache TTL based on your use case",
                "Use distributed caching (Redis) for production deployments"
            ]
        },
        {
            "category": "Hardware Optimization",
            "tips": [
                "Enable MLX optimization on Mac M1/M2 systems",
                "Use GPU acceleration when available",
                "Allocate sufficient memory based on workload"
            ]
        },
        {
            "category": "Model Selection",
            "tips": [
                "Use baseline models for speed-critical applications",
                "Use ensemble models for accuracy-critical applications",
                "Let the platform auto-select based on content analysis"
            ]
        }
    ]

    for tip_group in tips:
        print_subsection(tip_group["category"])
        for i, tip in enumerate(tip_group["tips"], 1):
            print(f"{i}. {tip}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GCACU Platform Quick Start")
    parser.add_argument("--demo", action="store_true", help="Run live demo")
    parser.add_argument("--examples", action="store_true", help="Show use case examples")
    parser.add_argument("--troubleshoot", action="store_true", help="Show troubleshooting guide")
    parser.add_argument("--performance", action="store_true", help="Show performance tips")

    args = parser.parse_args()

    if args.demo:
        quick_start_demo()
    elif args.examples:
        example_use_cases()
    elif args.troubleshoot:
        troubleshooting_guide()
    elif args.performance:
        performance_tips()
    else:
        quick_start_demo()  # Default to demo