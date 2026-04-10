#!/usr/bin/env python3

"""
Test script to verify search functionality in the knowledge graph application
"""

import subprocess
import time
import sys

def test_search_functionality():
    """Test the search functionality of the knowledge graph application."""

    print("🔍 Testing Search Functionality")
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

    # Test 2: Search Components Present
    print("\n2. 🔧 Checking Search Components...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        search_components = {
            'Search Input': 'id="nl-query"' in html_content,
            'Search Button': 'id="search-posts"' in html_content,
            'Search Results Container': 'id="search-results"' in html_content,
            'Filter Pills': 'data-search-type' in html_content,
            'Search Loading': 'id="search-loading"' in html_content
        }

        passed_components = 0
        for component_name, found in search_components.items():
            status = "✅" if found else "❌"
            print(f"   {status} {component_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_components += 1
                results.append((f"Component: {component_name}", True, "Found"))
            else:
                results.append((f"Component: {component_name}", False, "Missing"))

        print(f"   📊 Search components: {passed_components}/{len(search_components)} found")

    except Exception as e:
        print(f"   ❌ Component check error: {e}")
        results.append(("Search Components", False, str(e)))

    # Test 3: JavaScript Search Implementation
    print("\n3. 📄 Verifying JavaScript Search Implementation...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        search_functions = {
            'performSearch Method': 'performSearch(' in js_content,
            'buildSearchIndex Method': 'buildSearchIndex(' in js_content,
            'displaySearchResults Method': 'displaySearchResults(' in js_content,
            'setupSearchControls Method': 'setupSearchControls(' in js_content,
            'Search Index Creation': 'searchIndex' in js_content,
            'Search Relevance Calculation': 'calculateRelevance(' in js_content,
            'Query Highlighting': 'highlightSearchTerms(' in js_content
        }

        passed_functions = 0
        for function_name, found in search_functions.items():
            status = "✅" if found else "❌"
            print(f"   {status} {function_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_functions += 1
                results.append((f"Function: {function_name}", True, "Found"))
            else:
                results.append((f"Function: {function_name}", False, "Missing"))

        print(f"   📊 Search functions: {passed_functions}/{len(search_functions)} implemented")

    except Exception as e:
        print(f"   ❌ Function check error: {e}")
        results.append(("Search Functions", False, str(e)))

    # Test 4: CSS Styling for Search Results
    print("\n4. 🎨 Checking Search Result Styling...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        search_styles = {
            'Result Item Styling': '.result-item' in html_content,
            'Result Header Styling': '.result-header' in html_content,
            'Search Badges': '.badge-category' in html_content,
            'Search Highlighting': 'mark {' in html_content,
            'No Results Styling': '.no-results' in html_content,
            'Color Swatches': '.color-swatch' in html_content
        }

        passed_styles = 0
        for style_name, found in search_styles.items():
            status = "✅" if found else "❌"
            print(f"   {status} {style_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_styles += 1
                results.append((f"Style: {style_name}", True, "Found"))
            else:
                results.append((f"Style: {style_name}", False, "Missing"))

        print(f"   📊 Search styling: {passed_styles}/{len(search_styles)} styles found")

    except Exception as e:
        print(f"   ❌ Style check error: {e}")
        results.append(("Search Styling", False, str(e)))

    # Generate Summary
    print("\n" + "=" * 50)
    print("📋 SEARCH FUNCTIONALITY TEST RESULTS")
    print("=" * 50)

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for test_name, status, details in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Search functionality should work correctly!")
        success_rate = 100
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - Search functionality should mostly work")
        success_rate = (passed / total) * 100
    else:
        print("❌ Multiple tests failed - Search functionality needs attention")
        success_rate = (passed / total) * 100

    print(f"📈 Success Rate: {success_rate:.1f}%")

    # Test Instructions
    print(f"\n🌐 MANUAL TESTING INSTRUCTIONS:")
    print(f"1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print(f"2. Click on 'Natural Language Query' tab")
    print(f"3. Try these search queries:")
    print(f"   - 'brand strategy'")
    print(f"   - 'digital marketing'")
    print(f"   - 'customer experience'")
    print(f"   - 'high engagement'")
    print(f"4. Test the filter pills: All Results, Posts, Concepts, Categories")
    print(f"5. Check that search results display with highlighting")
    print(f"6. Verify search analytics show result counts and timing")

    print(f"\n🔧 EXPECTED BEHAVIOR:")
    print(f"• Search input should accept text and show suggestions")
    print(f"• Search button should trigger search when clicked")
    print(f"• Results should appear grouped by type (Categories, Concepts, Posts)")
    print(f"• Search terms should be highlighted in results")
    print(f"• Filter pills should limit search to specific content types")
    print(f"• Analytics should show search performance metrics")

    return success_rate >= 80

if __name__ == "__main__":
    try:
        success = test_search_functionality()
        if success:
            print(f"\n✅ Search functionality validation PASSED")
            print(f"🚀 Ready to test the search features in the browser")
        else:
            print(f"\n❌ Search functionality validation FAILED")
            print(f"🔧 Please review and fix the issues above")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)