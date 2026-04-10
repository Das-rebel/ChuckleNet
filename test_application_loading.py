#!/usr/bin/env python3

"""
Test script to verify the knowledge graph application loads correctly
"""

import subprocess
import time
import json
import sys

def test_application_loading():
    """Test that the application loads without errors and main components work."""

    print("🧪 Testing Knowledge Graph Application Loading")
    print("=" * 60)

    results = []

    # Test 1: Basic Server Response
    print("\n1. 🌐 Testing Server Response...")
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge_graph_v2.html'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout.strip() == '200':
            print("   ✅ Server responding correctly")
            results.append(("Server Response", True, "HTTP 200"))
        else:
            print(f"   ❌ Server error: {result.stdout.strip()}")
            results.append(("Server Response", False, f"HTTP {result.stdout.strip()}"))
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("Server Response", False, str(e)))

    # Test 2: HTML Content Validation
    print("\n2. 📄 Validating HTML Content...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        critical_elements = {
            'Main Application Class': 'class KnowledgeGraphApp' in html_content,
            'D3.js Library': 'd3@7' in html_content,
            'Chart.js Library': 'chart.js' in html_content,
            'Graph Container': 'id="graphContainer"' in html_content,
            'Network Graph': 'id="networkGraph"' in html_content,
            'Timeline Panel': 'id="timeline-panel"' in html_content,
            'Search Panel': 'id="search-panel"' in html_content,
            'Insights Panel': 'id="insights-panel"' in html_content,
            'Enhanced Features Container': 'enhancedSearchContainer' in html_content
        }

        passed_elements = 0
        for element_name, found in critical_elements.items():
            status = "✅" if found else "❌"
            print(f"   {status} {element_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_elements += 1
                results.append((f"HTML: {element_name}", True, "Found"))
            else:
                results.append((f"HTML: {element_name}", False, "Missing"))

        print(f"   📊 HTML validation: {passed_elements}/{len(critical_elements)} elements found")

    except Exception as e:
        print(f"   ❌ HTML validation error: {e}")
        results.append(("HTML Content", False, str(e)))

    # Test 3: JavaScript Files Accessibility
    print("\n3. 🔧 Testing JavaScript Files...")
    try:
        # Test main JavaScript file
        js_result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                                   'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10)

        # Test enhanced features file
        enhanced_js_result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                                           'http://localhost:8002/enhanced_knowledge_graph_features.js'],
                                           capture_output=True, text=True, timeout=10)

        # Test CSS file
        css_result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                                   'http://localhost:8002/enhanced_knowledge_graph_styles.css'],
                                   capture_output=True, text=True, timeout=10)

        js_files = {
            'Main JavaScript': js_result.stdout.strip() == '200',
            'Enhanced Features JavaScript': enhanced_js_result.stdout.strip() == '200',
            'Enhanced Styles CSS': css_result.stdout.strip() == '200'
        }

        passed_files = 0
        for file_name, accessible in js_files.items():
            status = "✅" if accessible else "❌"
            print(f"   {status} {file_name}: {'Accessible' if accessible else 'Not Found'}")
            if accessible:
                passed_files += 1
                results.append((f"Files: {file_name}", True, "Accessible"))
            else:
                results.append((f"Files: {file_name}", False, "Not Found"))

        print(f"   📊 JavaScript files: {passed_files}/{len(js_files)} files accessible")

    except Exception as e:
        print(f"   ❌ JavaScript files test error: {e}")
        results.append(("JavaScript Files", False, str(e)))

    # Test 4: Performance Check
    print("\n4. ⚡ Checking Application Performance...")
    try:
        start_time = time.time()
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{time_total}',
                               'http://localhost:8002/knowledge_graph_v2.html'],
                               capture_output=True, text=True, timeout=10)
        load_time = float(result.stdout.strip())

        if load_time < 1.0:
            print(f"   ✅ Load time: {load_time:.3f}s (excellent)")
            results.append(("Performance", True, f"{load_time:.3f}s (excellent)"))
        elif load_time < 3.0:
            print(f"   ✅ Load time: {load_time:.3f}s (good)")
            results.append(("Performance", True, f"{load_time:.3f}s (good)"))
        elif load_time < 5.0:
            print(f"   ⚠️ Load time: {load_time:.3f}s (acceptable)")
            results.append(("Performance", True, f"{load_time:.3f}s (acceptable)"))
        else:
            print(f"   ❌ Load time: {load_time:.3f}s (slow)")
            results.append(("Performance", False, f"{load_time:.3f}s (slow)"))

    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        results.append(("Performance", False, str(e)))

    # Generate Summary
    print("\n" + "=" * 60)
    print("📋 APPLICATION LOADING TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for test_name, status, details in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Application should load correctly!")
        success_rate = 100
        print("\n🌐 Next Steps:")
        print("1. Open http://localhost:8002/knowledge_graph_v2.html in your browser")
        print("2. Check browser console for any JavaScript errors")
        print("3. Test each tab: Graph, Timeline, Topics, Search, Insights")
        print("4. Verify enhanced features are working (if enabled)")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - Application should mostly work")
        success_rate = (passed / total) * 100
        print("\n⚠️ Check the failed tests above for potential issues")
    else:
        print("❌ Multiple tests failed - Application may have loading issues")
        success_rate = (passed / total) * 100
        print("\n❌ Review failed tests and fix critical issues")

    print(f"\n📈 Success Rate: {success_rate:.1f}%")

    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = test_application_loading()
        if success:
            print(f"\n✅ Application loading validation PASSED")
            print(f"🚀 Ready to test the knowledge graph functionality")
        else:
            print(f"\n❌ Application loading validation FAILED")
            print(f"🔧 Please review and fix the issues above")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)