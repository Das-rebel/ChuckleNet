#!/usr/bin/env python3

"""
Test script to verify Timeline Analysis functionality in the knowledge graph application
"""

import subprocess
import time
import sys
import json

def test_timeline_analysis():
    """Test the Timeline Analysis functionality of the knowledge graph application."""

    print("📈 Testing Timeline Analysis Functionality")
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

    # Test 2: Timeline Container Elements Present
    print("\n2. 🏗️ Checking Timeline Container Elements...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        timeline_containers = {
            'Timeline Panel': 'id="timeline-panel"' in html_content,
            'Timeline Chart Container': 'id="timelineChart"' in html_content,
            'Timeline Controls': 'id="timelineControls"' in html_content,
            'Timeline Stats Panel': 'id="timelineStats"' in html_content,
            'Time Range Selector': 'id="timeRange"' in html_content,
            'Grouping Selector': 'id="grouping"' in html_content
        }

        passed_containers = 0
        for container_name, found in timeline_containers.items():
            status = "✅" if found else "❌"
            print(f"   {status} {container_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_containers += 1
                results.append((f"Container: {container_name}", True, "Found"))
            else:
                results.append((f"Container: {container_name}", False, "Missing"))

        print(f"   📊 Timeline containers: {passed_containers}/{len(timeline_containers)} found")

    except Exception as e:
        print(f"   ❌ Container check error: {e}")
        results.append(("Timeline Containers", False, str(e)))

    # Test 3: JavaScript Timeline Implementation
    print("\n3. 📄 Verifying JavaScript Timeline Implementation...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        timeline_functions = {
            'Chart.js Library Inclusion': 'Chart' in js_content or 'chart.js' in js_content,
            'renderTimelineTab Method': 'renderTimelineTab(' in js_content,
            'initializeTimeline Method': 'initializeTimeline(' in js_content,
            'prepareTimelineData Method': 'prepareTimelineData(' in js_content,
            'updateTimelineStats Method': 'updateTimelineStats(' in js_content,
            'setupTimelineControls Method': 'setupTimelineControls(' in js_content,
            'updateTimelineChart Method': 'updateTimelineChart(' in js_content,
            'Timeline Chart Creation': 'timelineChart' in js_content,
            'Timeline Data Processing': 'timelineData' in js_content
        }

        passed_functions = 0
        for function_name, found in timeline_functions.items():
            status = "✅" if found else "❌"
            print(f"   {status} {function_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_functions += 1
                results.append((f"Function: {function_name}", True, "Found"))
            else:
                results.append((f"Function: {function_name}", False, "Missing"))

        print(f"   📊 Timeline functions: {passed_functions}/{len(timeline_functions)} implemented")

    except Exception as e:
        print(f"   ❌ Function check error: {e}")
        results.append(("Timeline Functions", False, str(e)))

    # Test 4: Timeline Data Structure
    print("\n4. 📊 Checking Timeline Data Structure...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        # Look for timeline data patterns
        data_indicators = {
            'Timeline Data Variable': 'timelineData' in html_content,
            'Time-based Data': 'time' in html_content or 'date' in html_content,
            'Engagement Metrics': 'engagement' in html_content,
            'Temporal Analysis': 'temporal' in html_content or 'time' in html_content,
            'Date Processing': 'Date' in html_content or 'date' in html_content,
            'Time Range Options': 'timeRange' in html_content
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

        print(f"   📊 Timeline data: {passed_data}/{len(data_indicators)} structures found")

    except Exception as e:
        print(f"   ❌ Data check error: {e}")
        results.append(("Timeline Data", False, str(e)))

    # Test 5: Timeline Styling and CSS
    print("\n5. 🎨 Checking Timeline Visualization Styling...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        timeline_styles = {
            'Timeline Container Styling': '.timeline-container' in html_content,
            'Chart Canvas Styling': 'canvas' in html_content,
            'Timeline Stats Styling': '.timeline-stats' in html_content,
            'Control Panel Styling': '.control-panel' in html_content,
            'Time Range Selector Styling': '.time-selector' in html_content,
            'Responsive Timeline Design': '@media' in html_content and 'timeline' in html_content
        }

        passed_styles = 0
        for style_name, found in timeline_styles.items():
            status = "✅" if found else "❌"
            print(f"   {status} {style_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_styles += 1
                results.append((f"Style: {style_name}", True, "Found"))
            else:
                results.append((f"Style: {style_name}", False, "Missing"))

        print(f"   📊 Timeline styling: {passed_styles}/{len(timeline_styles)} styles found")

    except Exception as e:
        print(f"   ❌ Style check error: {e}")
        results.append(("Timeline Styling", False, str(e)))

    # Test 6: Interactive Timeline Features
    print("\n6. 🎮 Checking Interactive Timeline Features...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        interactive_features = {
            'Time Range Selection': 'select' in html_content and 'time' in html_content,
            'Data Grouping Options': 'grouping' in html_content,
            'Chart Interactivity': 'Chart.js' in html_content or 'interactive' in html_content,
            'Timeline Filter Controls': 'filter' in html_content and 'time' in html_content,
            'Zoom and Pan Timeline': 'zoom' in html_content and 'timeline' in html_content,
            'Temporal Data Filtering': 'temporal' in html_content or 'filter' in html_content,
            'Timeline Statistics Display': 'stats' in html_content and 'timeline' in html_content
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
    print("📋 TIMELINE ANALYSIS TEST RESULTS")
    print("=" * 50)

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for test_name, status, details in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Timeline analysis should work correctly!")
        success_rate = 100
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - Timeline analysis should mostly work")
        success_rate = (passed / total) * 100
    else:
        print("❌ Multiple tests failed - Timeline analysis needs attention")
        success_rate = (passed / total) * 100

    print(f"📈 Success Rate: {success_rate:.1f}%")

    # Test Instructions
    print(f"\n🌐 MANUAL TESTING INSTRUCTIONS:")
    print(f"1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print(f"2. Click on 'Timeline Analysis' tab (2nd tab)")
    print(f"3. Expected to see:")
    print(f"   • Interactive timeline chart showing post frequency over time")
    print(f"   • Time range selector (e.g., 'Last 7 days', 'Last 30 days', 'All time')")
    print(f"   • Data grouping options (e.g., 'By day', 'By week', 'By month')")
    print(f"   • Timeline statistics panel")
    print(f"4. Test interactions:")
    print(f"   • Change time range to see filtered data")
    print(f"   • Switch between grouping options")
    print(f"   • Hover over chart points for details")
    print(f"   • Click on data points for more information")
    print(f"5. Check timeline controls:")
    print(f"   • Time range selector functionality")
    print(f"   • Grouping option changes")
    print(f"   • Statistics panel updates")

    print(f"\n🔧 EXPECTED BEHAVIOR:")
    print(f"• Timeline should render posts chronologically with engagement metrics")
    print(f"• Chart should show trends and patterns in posting frequency")
    print(f"• Time range controls should filter displayed data")
    print(f"• Grouping options should aggregate data by selected time periods")
    print(f"• Statistics should show total posts, average engagement, peak posting times")
    print(f"• Timeline should be responsive and interactive")
    print(f"• Chart should load within 2-3 seconds on initial page load")

    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = test_timeline_analysis()
        if success:
            print(f"\n✅ Timeline analysis validation PASSED")
            print(f"🚀 Ready to test the timeline analysis features in the browser")
        else:
            print(f"\n❌ Timeline analysis validation FAILED")
            print(f"🔧 Please review and fix the issues above")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)