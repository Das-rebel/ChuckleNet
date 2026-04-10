#!/usr/bin/env python3

"""
Test script to verify Graph Visualization functionality in the knowledge graph application
"""

import subprocess
import time
import sys
import json

def test_graph_visualization():
    """Test the Graph Visualization functionality of the knowledge graph application."""

    print("🕸️ Testing Graph Visualization Functionality")
    print("=" * 50)

    results = []

    # Test 1: Application Loads Correctly
    print("\n1. 🌐 Testing Application Accessibility...")
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge_graph_v2.html'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout.strip() == '200':
            print("   ✅ Application accessible")
            results.append(("Application Access", True, "HTTP 200"))
        else:
            print(f"   ❌ Server error: {result.stdout.strip()}")
            results.append(("Application Access", False, f"HTTP {result.stdout.strip()}"))
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("Application Access", False, str(e)))

    # Test 2: Graph Container Elements Present
    print("\n2. 🏗️ Checking Graph Container Elements...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        graph_containers = {
            'Main Graph Container': 'id="graphContainer"' in html_content,
            'Network Graph Container': 'id="networkGraph"' in html_content,
            'Graph Controls Panel': 'id="graphControls"' in html_content,
            'Graph Info Panel': 'id="graphInfo"' in html_content,
            'Graph Stats Panel': 'id="graphStats"' in html_content,
            'Zoom Controls': 'class="zoom-controls"' in html_content
        }

        passed_containers = 0
        for container_name, found in graph_containers.items():
            status = "✅" if found else "❌"
            print(f"   {status} {container_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_containers += 1
                results.append((f"Container: {container_name}", True, "Found"))
            else:
                results.append((f"Container: {container_name}", False, "Missing"))

        print(f"   📊 Graph containers: {passed_containers}/{len(graph_containers)} found")

    except Exception as e:
        print(f"   ❌ Container check error: {e}")
        results.append(("Graph Containers", False, str(e)))

    # Test 3: JavaScript Graph Implementation
    print("\n3. 📄 Verifying JavaScript Graph Implementation...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        graph_functions = {
            'D3.js Library Inclusion': 'd3' in js_content or 'd3.min.js' in js_content,
            'renderGraph Method': 'renderGraph(' in js_content,
            'initializeGraph Method': 'initializeGraph(' in js_content,
            'updateGraphStats Method': 'updateGraphStats(' in js_content,
            'setupGraphControls Method': 'setupGraphControls(' in js_content,
            'Network Graph Creation': 'networkGraph' in js_content,
            'Force Simulation': 'forceSimulation' in js_content or 'd3.forceSimulation' in js_content,
            'Node Creation': 'createNodes' in js_content or 'node.append' in js_content,
            'Link Creation': 'createLinks' in js_content or 'link.append' in js_content,
            'Zoom and Pan': 'zoom' in js_content and 'transform' in js_content
        }

        passed_functions = 0
        for function_name, found in graph_functions.items():
            status = "✅" if found else "❌"
            print(f"   {status} {function_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_functions += 1
                results.append((f"Function: {function_name}", True, "Found"))
            else:
                results.append((f"Function: {function_name}", False, "Missing"))

        print(f"   📊 Graph functions: {passed_functions}/{len(graph_functions)} implemented")

    except Exception as e:
        print(f"   ❌ Function check error: {e}")
        results.append(("Graph Functions", False, str(e)))

    # Test 4: Graph Data Structure
    print("\n4. 📊 Checking Graph Data Structure...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        # Look for sample data or data loading patterns
        data_indicators = {
            'Graph Data Variable': 'graphData' in html_content or 'nodes' in html_content,
            'Node Data Structure': 'nodes:' in html_content or '"nodes"' in html_content,
            'Link Data Structure': 'links:' in html_content or '"links"' in html_content,
            'Category Data': 'categories' in html_content,
            'Concept Data': 'concepts' in html_content,
            'Post Data': 'posts' in html_content
        }

        passed_data = 0
        for data_name, found in data_indicators.items():
            status = "✅" if found else "❌"
            print(f"   {status} {data_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_data += 1
                results.append((f"Data: {data_name}", True, "Found"))
            else:
                results.append((f"Data: {data_name}", False, "Missing"))

        print(f"   📊 Graph data: {passed_data}/{len(data_indicators)} structures found")

    except Exception as e:
        print(f"   ❌ Data check error: {e}")
        results.append(("Graph Data", False, str(e)))

    # Test 5: Graph Styling and CSS
    print("\n5. 🎨 Checking Graph Visualization Styling...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        graph_styles = {
            'Graph Container Styling': '.graph-container' in html_content,
            'Node Styling': '.node' in html_content,
            'Link Styling': '.link' in html_content,
            'Node Label Styling': '.node-label' in html_content,
            'Graph Tooltips': '.graph-tooltip' in html_content,
            'Zoom Button Styling': '.zoom-btn' in html_content,
            'Graph Stats Styling': '.graph-stats' in html_content,
            'Interactive Node Hover': ':hover' in html_content and 'node' in html_content
        }

        passed_styles = 0
        for style_name, found in graph_styles.items():
            status = "✅" if found else "❌"
            print(f"   {status} {style_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_styles += 1
                results.append((f"Style: {style_name}", True, "Found"))
            else:
                results.append((f"Style: {style_name}", False, "Missing"))

        print(f"   📊 Graph styling: {passed_styles}/{len(graph_styles)} styles found")

    except Exception as e:
        print(f"   ❌ Style check error: {e}")
        results.append(("Graph Styling", False, str(e)))

    # Test 6: Interactive Features
    print("\n6. 🎮 Checking Interactive Features...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        interactive_features = {
            'Node Click Events': 'onclick' in html_content or 'addEventListener' in html_content,
            'Drag and Drop': 'drag' in html_content,
            'Zoom Controls': 'zoom-in' in html_content or 'zoom-out' in html_content,
            'Pan Navigation': 'pan' in html_content,
            'Hover Tooltips': 'tooltip' in html_content,
            'Filter Controls': 'filter' in html_content,
            'Search Integration': 'search' in html_content and 'graph' in html_content
        }

        passed_features = 0
        for feature_name, found in interactive_features.items():
            status = "✅" if found else "❌"
            print(f"   {status} {feature_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_features += 1
                results.append((f"Feature: {feature_name}", True, "Found"))
            else:
                results.append((f"Feature: {feature_name}", False, "Missing"))

        print(f"   📊 Interactive features: {passed_features}/{len(interactive_features)} found")

    except Exception as e:
        print(f"   ❌ Feature check error: {e}")
        results.append(("Interactive Features", False, str(e)))

    # Generate Summary
    print("\n" + "=" * 50)
    print("📋 GRAPH VISUALIZATION TEST RESULTS")
    print("=" * 50)

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for test_name, status, details in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Graph visualization should work correctly!")
        success_rate = 100
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - Graph visualization should mostly work")
        success_rate = (passed / total) * 100
    else:
        print("❌ Multiple tests failed - Graph visualization needs attention")
        success_rate = (passed / total) * 100

    print(f"📈 Success Rate: {success_rate:.1f}%")

    # Test Instructions
    print(f"\n🌐 MANUAL TESTING INSTRUCTIONS:")
    print(f"1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print(f"2. Click on 'Graph Visualization' tab (1st tab)")
    print(f"3. Expected to see:")
    print(f"   • Interactive network graph with nodes and links")
    print(f"   • Colored nodes representing different content types")
    print(f"   • Zoom controls (+ / - buttons)")
    print(f"   • Graph statistics panel")
    print(f"4. Test interactions:")
    print(f"   • Click and drag nodes to reposition them")
    print(f"   • Use mouse wheel to zoom in/out")
    print(f"   • Click on nodes to see detailed information")
    print(f"   • Hover over nodes for tooltips")
    print(f"5. Check graph controls:")
    print(f"   • Reset zoom button")
    print(f"   • Fit to screen button")
    print(f"   • Filter options (if implemented)")

    print(f"\n🔧 EXPECTED BEHAVIOR:")
    print(f"• Graph should render with nodes representing posts, concepts, and categories")
    print(f"• Links should show relationships between content items")
    print(f"• Nodes should be color-coded by type")
    print(f"• Graph should be interactive with drag, zoom, and pan capabilities")
    print(f"• Graph statistics should show node count, link count, and other metrics")
    print(f"• Graph should load within 2-3 seconds on initial page load")

    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = test_graph_visualization()
        if success:
            print(f"\n✅ Graph visualization validation PASSED")
            print(f"🚀 Ready to test the graph visualization features in the browser")
        else:
            print(f"\n❌ Graph visualization validation FAILED")
            print(f"🔧 Please review and fix the issues above")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)