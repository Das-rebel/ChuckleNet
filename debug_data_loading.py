#!/usr/bin/env python3

"""
Debug script to check data loading and initialization in the knowledge graph application
"""

import subprocess
import time
import sys
import json

def debug_data_loading():
    """Debug data loading issues in the knowledge graph application."""

    print("🐛 Debugging Data Loading Issues")
    print("=" * 50)

    # Test 1: Check Application Loads
    print("\n1. 🌐 Testing Application Accessibility...")
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge_graph_v2.html'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout.strip() == '200':
            print("   ✅ Application accessible")
        else:
            print(f"   ❌ Server error: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

    # Test 2: Check JavaScript File Loads
    print("\n2. 📄 Checking JavaScript File Loading...")
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge-graph-app.js'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout.strip() == '200':
            print("   ✅ JavaScript file accessible")
        else:
            print(f"   ❌ JavaScript file error: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ JavaScript file error: {e}")
        return False

    # Test 3: Check for Sample Data Generation
    print("\n3. 📊 Checking Sample Data Generation...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        data_checks = {
            'generateLinkedInPosts Method': 'generateLinkedInPosts(' in js_content,
            'Sample Posts Count': '440' in js_content,
            'Sample Concepts Data': 'brand_strategy' in js_content,
            'Sample Categories Data': 'categories:' in js_content,
            'Data Processing Method': 'processData(' in js_content,
            'Init Method Called': 'this.init()' in js_content
        }

        passed_checks = 0
        for check_name, found in data_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_checks += 1

        print(f"   📊 Data generation: {passed_checks}/{len(data_checks)} checks passed")

        if passed_checks < len(data_checks) * 0.8:
            print("   ⚠️ Data generation may have issues")
            return False

    except Exception as e:
        print(f"   ❌ Data generation check error: {e}")
        return False

    # Test 4: Check Tab Rendering Methods
    print("\n4. 🎨 Checking Tab Rendering Methods...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        render_methods = {
            'renderGraphTab Method': 'renderGraphTab()' in js_content,
            'renderTimelineTab Method': 'renderTimelineTab()' in js_content,
            'renderTopicsTab Method': 'renderTopicsTab()' in js_content,
            'renderQueryTab Method': 'renderQueryTab()' in js_content,
            'renderInsightsTab Method': 'renderInsightsTab()' in js_content,
            'renderActiveTab Method': 'renderActiveTab()' in js_content
        }

        passed_methods = 0
        for method_name, found in render_methods.items():
            status = "✅" if found else "❌"
            print(f"   {status} {method_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_methods += 1

        print(f"   📊 Render methods: {passed_methods}/{len(render_methods)} methods found")

        if passed_methods < len(render_methods) * 0.8:
            print("   ⚠️ Some render methods may be missing")
            return False

    except Exception as e:
        print(f"   ❌ Render methods check error: {e}")
        return False

    # Test 5: Check Event Listener Setup
    print("\n5. 🎮 Checking Event Listener Setup...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        event_checks = {
            'DOMContentLoaded Event': 'DOMContentLoaded' in js_content,
            'Tab Click Events': 'addEventListener' in js_content and 'click' in js_content,
            'Tab Switching Logic': 'switchTab(' in js_content,
            'Initialization Call': 'new KnowledgeGraphApp()' in js_content
        }

        passed_events = 0
        for event_name, found in event_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {event_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_events += 1

        print(f"   📊 Event setup: {passed_events}/{len(event_checks)} events found")

    except Exception as e:
        print(f"   ❌ Event setup check error: {e}")
        return False

    # Test 6: Check HTML Structure
    print("\n6. 🏗️ Checking HTML Structure...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        html_checks = {
            'Tab Navigation': 'class="tab-navigation"' in html_content,
            'Tab Panels': 'class="tab-panel"' in html_content,
            'Graph Tab': 'id="graph-panel"' in html_content,
            'Timeline Tab': 'id="timeline-panel"' in html_content,
            'Topics Tab': 'id="topics-panel"' in html_content,
            'Query Tab': 'id="search-panel"' in html_content,
            'Insights Tab': 'id="insights-panel"' in html_content,
            'JavaScript Include': '<script src="knowledge-graph-app.js">' in html_content
        }

        passed_html = 0
        for check_name, found in html_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_html += 1

        print(f"   📊 HTML structure: {passed_html}/{len(html_checks)} elements found")

        if passed_html < len(html_checks) * 0.8:
            print("   ⚠️ HTML structure may have issues")
            return False

    except Exception as e:
        print(f"   ❌ HTML structure check error: {e}")
        return False

    # Generate Debug Summary
    print("\n" + "=" * 50)
    print("📋 DEBUG SUMMARY")
    print("=" * 50)

    print("🔍 POTENTIAL ISSUES IDENTIFIED:")
    print("1. JavaScript may not be executing properly")
    print("2. DOM ready event may not be firing")
    print("3. Tab click events may not be connected")
    print("4. Data may be generated but not rendered")
    print("5. Console errors may be preventing execution")

    print("\n🌐 MANUAL DEBUGGING STEPS:")
    print("1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print("2. Open Developer Console (F12)")
    print("3. Check for JavaScript errors:")
    print("   - Look for red error messages")
    print("   - Check for 'undefined' errors")
    print("   - Verify app object exists: type 'window.app' in console")
    print("4. Test data loading:")
    print("   - Type 'window.app.data' in console")
    print("   - Type 'window.app.generateLinkedInPosts(10)' in console")
    print("5. Test tab switching:")
    print("   - Type 'window.app.switchTab(\"graph\")' in console")
    print("   - Type 'window.app.renderActiveTab()' in console")

    print("\n🔧 EXPECTED BEHAVIOR:")
    print("• Application should load sample data automatically")
    print("• Console should show 'Knowledge Graph App initialized' message")
    print("• Clicking tabs should render different visualizations")
    print("• Data should appear in graphs, charts, and search results")

    return True

if __name__ == "__main__":
    try:
        success = debug_data_loading()
        if success:
            print(f"\n✅ Debug completed - Check manual steps above")
        else:
            print(f"\n❌ Critical issues found")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️ Debug interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Debug execution failed: {e}")
        sys.exit(1)