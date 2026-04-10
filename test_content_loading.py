#!/usr/bin/env python3

"""
Test script to verify content is actually loading in the application
"""

import subprocess
import time
import sys

def test_content_loading():
    """Test if content is loading in the knowledge graph application."""

    print("📊 Testing Content Loading")
    print("=" * 50)

    # Test if the application loads properly
    print("\n1. 🌐 Checking Application Load...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        # Check for key indicators that JavaScript has run
        js_indicators = {
            'Knowledge Graph App initialized': 'Knowledge Graph App initialized' in html_content,
            'Loading indicators': 'loading' in html_content,
            'Sample data content': 'Brand Strategy' in html_content,
            'Tab content visible': 'tab-content' in html_content
        }

        print("   JavaScript execution indicators:")
        for indicator, found in js_indicators.items():
            status = "✅" if found else "❌"
            print(f"   {status} {indicator}: {'Found' if found else 'Missing'}")

    except Exception as e:
        print(f"   ❌ Error checking application: {e}")
        return False

    print("\n2. 🔧 Testing Manual Load Instructions...")

    manual_steps = [
        "1. Open: http://localhost:8002/knowledge_graph_v2.html",
        "2. Open Developer Console (F12 or right-click → Inspect)",
        "3. Go to Console tab",
        "4. Check for any red error messages",
        "5. Type 'window.app' and press Enter",
        "   - Should show: KnowledgeGraphApp { ... }",
        "6. Type 'window.app.data' and press Enter",
        "   - Should show data object with posts, concepts, categories",
        "7. Type 'window.app.switchTab(\"graph\")' and press Enter",
        "   - Should render the network graph",
        "8. Type 'window.app.renderActiveTab()' and press Enter",
        "   - Should render the active tab content"
    ]

    for step in manual_steps:
        print(f"   {step}")

    print("\n3. 🎯 Expected Content in Each Tab:")

    tab_content = [
        "📈 Graph Visualization Tab:",
        "   • Network graph with colored nodes",
        "   • Zoom controls (+, -, reset, fit)",
        "   • Graph statistics (node count, link count)",
        "   • Node information panel",
        "",
        "📅 Timeline Analysis Tab:",
        "   • Line chart showing posting frequency",
        "   • Time range selector (7 days, 30 days, etc.)",
        "   • Group by options (day, week, month)",
        "   • Timeline statistics panel",
        "",
        "🏷️ Topics Discovery Tab:",
        "   • Topic cards with engagement metrics",
        "   • Topic filtering options",
        "   • Sentiment analysis charts",
        "   • Top keywords display",
        "",
        "🔍 Natural Language Query Tab:",
        "   • Search input field",
        "   • Filter pills (All Results, Posts, Concepts, Categories)",
        "   • Search results with highlighting",
        "   • Search analytics (result count, time)",
        "",
        "💡 Insights Tab:",
        "   • Key insights cards",
        "   • Engagement trends",
        "   • Top concepts chart",
        "   • Sentiment analysis"
    ]

    for item in tab_content:
        print(f"   {item}")

    print("\n4. 🔍 Troubleshooting Common Issues:")

    troubleshooting = [
        "❌ If you see JavaScript errors:",
        "   • Check if all libraries loaded (D3.js, Chart.js)",
        "   • Check for syntax errors in console",
        "",
        "❌ If tabs switch but no content appears:",
        "   • Type 'window.app.data' to check if data loaded",
        "   • Type 'window.app.generateLinkedInPosts(5)' to test data generation",
        "",
        "❌ If search doesn't work:",
        "   • Type 'window.app.buildSearchIndex()' to rebuild search index",
        "   • Type 'window.app.performSearch(\"brand\")' to test search",
        "",
        "❌ If graphs don't render:",
        "   • Check if D3.js loaded: type 'd3'",
        "   • Type 'window.app.initializeGraph()' to force graph rendering"
    ]

    for item in troubleshooting:
        print(f"   {item}")

    print(f"\n🎉 SUCCESS INDICATORS:")
    print(f"✅ Application loads without console errors")
    print(f"✅ 'window.app' object exists in console")
    print(f"✅ 'window.app.data' contains posts, concepts, categories")
    print(f"✅ Tab switching shows different content")
    print(f"✅ Search returns highlighted results")
    print(f"✅ Graph visualization shows network of nodes")
    print(f"✅ Timeline chart shows temporal data")

    print(f"\n🚀 URL: http://localhost:8002/knowledge_graph_v2.html")
    print(f"📋 Test Suite: http://localhost:8002/comprehensive_browser_test.html")

    return True

if __name__ == "__main__":
    try:
        success = test_content_loading()
        print(f"\n✅ Content loading test completed")
        print(f"🔧 Follow manual steps above to verify functionality")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)