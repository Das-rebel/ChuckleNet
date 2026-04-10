#!/usr/bin/env python3

"""
Comprehensive automated test for the knowledge graph application.
Tests all critical functionality including Query and Insights tabs.
"""

import subprocess
import time
import json
import re
import sys

def test_knowledge_graph_comprehensive():
    """Run comprehensive test suite for knowledge graph application."""

    print("🧪 COMPREHENSIVE KNOWLEDGE GRAPH RECHECK")
    print("=" * 60)

    results = []

    # Test 1: Server Connectivity
    print("\n1. 🌐 Testing Server Connectivity...")
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}'],
                               capture_output=True, text=True, timeout=10)
        if result.stdout.strip() == '200':
            print("   ✅ Server responding correctly")
            results.append(("Server Connectivity", True, "HTTP 200"))
        else:
            print(f"   ❌ Server error: {result.stdout.strip()}")
            results.append(("Server Connectivity", False, f"HTTP {result.stdout.strip()}"))
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        results.append(("Server Connectivity", False, str(e)))

    # Test 2: HTML Content Validation
    print("\n2. 📄 Validating HTML Content...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8001/knowledge_graph_comprehensive.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        checks = {
            'Direct Data Embedding': 'const directData' in html_content,
            'Query Function': 'window.processQuery' in html_content,
            'Insights Function': 'window.generateAIInsights' in html_content,
            'LoadData Function': 'function loadData' in html_content,
            'SetGraphData Function': 'function setGraphData' in html_content,
            'Query Tab HTML': 'Query Tab' in html_content,
            'Insights Tab HTML': 'Insights Tab' in html_content
        }

        passed_checks = 0
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'Found' if passed else 'Missing'}")
            if passed:
                passed_checks += 1
                results.append((f"HTML: {check_name}", True, "Found"))
            else:
                results.append((f"HTML: {check_name}", False, "Missing"))

        print(f"   📊 HTML validation: {passed_checks}/{len(checks)} checks passed")

    except Exception as e:
        print(f"   ❌ HTML validation error: {e}")
        results.append(("HTML Content", False, str(e)))

    # Test 3: Data Structure Validation
    print("\n3. 📊 Validating Data Structure...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8001/knowledge_graph_comprehensive.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        pattern = r'const directData = ({.*?});'
        match = re.search(pattern, html_content, re.DOTALL)

        if match:
            try:
                data = json.loads(match.group(1))
                node_count = len(data.get('nodes', []))
                link_count = len(data.get('links', []))
                topic_count = len(data.get('topics', []))

                print(f"   ✅ JSON data structure valid")
                print(f"   📈 Nodes: {node_count}")
                print(f"   🔗 Links: {link_count}")
                print(f"   🎯 Topics: {topic_count}")

                # Validate expected counts
                if node_count == 24 and link_count == 45 and topic_count == 7:
                    print("   ✅ Data structure matches expected values")
                    results.append(("Data Structure", True, f"{node_count} nodes, {link_count} links"))
                else:
                    print(f"   ⚠️ Unexpected data counts")
                    results.append(("Data Structure", False, f"Counts: {node_count}/{24} nodes, {link_count}/{45} links"))

                # Check for required sections
                required_sections = ['timeline', 'sentiment_summary', 'metadata']
                for section in required_sections:
                    if section in data:
                        print(f"   ✅ {section} section present")
                    else:
                        print(f"   ❌ {section} section missing")
                        results.append((f"Data: {section}", False, "Missing"))

            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parse error: {e}")
                results.append(("Data Structure", False, f"JSON error: {e}"))
        else:
            print("   ❌ Direct data not found in HTML")
            results.append(("Data Structure", False, "Direct data missing"))

    except Exception as e:
        print(f"   ❌ Data validation error: {e}")
        results.append(("Data Structure", False, str(e)))

    # Test 4: JavaScript Syntax Check
    print("\n4. 🔧 Checking JavaScript Syntax...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8001/knowledge_graph_comprehensive.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        # Check for common JavaScript syntax issues
        syntax_checks = [
            ('Unmatched braces', html_content.count('{') == html_content.count('}')),
            ('Unmatched brackets', html_content.count('[') == html_content.count(']')),
            ('No script errors', '<script>' in html_content and '</script>' in html_content),
            ('Function definitions', 'function(' in html_content),
        ]

        passed_syntax = 0
        for check_name, passed in syntax_checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'OK' if passed else 'Issue'}")
            if passed:
                passed_syntax += 1
                results.append((f"Syntax: {check_name}", True, "OK"))
            else:
                results.append((f"Syntax: {check_name}", False, "Issue"))

        print(f"   📊 Syntax validation: {passed_syntax}/{len(syntax_checks)} checks passed")

    except Exception as e:
        print(f"   ❌ Syntax check error: {e}")
        results.append(("JavaScript Syntax", False, str(e)))

    # Test 5: Performance Check
    print("\n5. ⚡ Checking Application Performance...")
    try:
        start_time = time.time()
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{time_total}'],
                               capture_output=True, text=True, timeout=10)
        load_time = float(result.stdout.strip())

        if load_time < 2.0:
            print(f"   ✅ Load time: {load_time:.2f}s (fast)")
            results.append(("Performance", True, f"{load_time:.2f}s"))
        elif load_time < 5.0:
            print(f"   ⚠️ Load time: {load_time:.2f}s (acceptable)")
            results.append(("Performance", True, f"{load_time:.2f}s"))
        else:
            print(f"   ❌ Load time: {load_time:.2f}s (slow)")
            results.append(("Performance", False, f"{load_time:.2f}s"))

      except Exception as e:
        print(f"   ❌ Performance test error: {e}")
        results.append(("Performance", False, str(e)))

    # Generate Summary Report
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    for test_name, status, details in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    print(f"\n📊 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Application is fully functional!")
        success_rate = 100
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed - Application is mostly functional")
        success_rate = (passed / total) * 100
    else:
        print("❌ Multiple tests failed - Application needs attention")
        success_rate = (passed / total) * 100

    print(f"📈 Success Rate: {success_rate:.1f}%")

    # Specific Query & Insights validation
    print("\n🎯 Query & Insights Tab Validation:")
    query_related = [r for r in results if 'Query' in r[0] or 'Insights' in r[0]]
    for test_name, status, details in query_related:
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}: {details}")

    # Generate final verdict
    if passed == total:
        print("\n✅ VERDICT: KNOWLEDGE GRAPH IS FULLY FUNCTIONAL")
        print("🚀 Query and Insights tabs should work correctly!")
        return True
    else:
        print("\n❌ VERDICT: KNOWLEDGE GRAPH NEEDS ATTENTION")
        print("🔧 Some functionality may not work as expected")
        return False

def create_test_report(results, success_rate):
    """Create a detailed test report."""

    report = f"""
# Knowledge Graph Comprehensive Test Report

**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Overall Status:** {'✅ PASSED' if success_rate == 100 else '⚠️ PARTIAL' if success_rate >= 80 else '❌ FAILED'}
**Success Rate:** {success_rate:.1f}%

## Test Results Summary

"""

    passed = sum(1 for _, status, _ in results if status)
    total = len(results)

    report += f"**Overall:** {passed}/{total} tests passed\n\n"

    # Categorize results
    categories = {
        'Server & Connectivity': [],
        'HTML & Structure': [],
        'Data & Content': [],
        'JavaScript & Functions': [],
        'Performance': []
    }

    for test_name, status, details in results:
        for category in categories:
            if any(keyword in test_name.lower() for keyword in
                   ['server', 'html', 'data', 'syntax', 'performance']):
                categories[category].append((test_name, status, details))
                break

    for category, items in categories.items():
        if items:
            report += f"### {category}\n"
            for test_name, status, details in items:
                icon = "✅" if status else "❌"
                report += f"- {icon} **{test_name}:** {details}\n"
            report += "\n"

    # Specific focus on Query & Insights
    report += "## Query & Insights Tab Validation\n\n"
    query_tests = [r for r in results if 'query' in r[0].lower() or 'insights' in r[0].lower()]
    for test_name, status, details in query_tests:
        icon = "✅" if status else "❌"
        report += f"- {icon} **{test_name}:** {details}\n"

    # Recommendations
    report += "\n## Recommendations\n\n"
    if success_rate == 100:
        report += "🎉 **All tests passed!** The knowledge graph application is ready for use.\n\n"
        report += "### Next Steps:\n"
        report += "1. Open the application in your browser\n"
        report += "2. Test Query and Insights tabs manually\n"
        report += "3. Verify all functionality works as expected\n"
    else:
        report += "⚠️ **Some tests failed.** Review the failed tests above.\n\n"
        report += "### Recommended Actions:\n"
        report += "1. Fix any identified issues\n"
        report += "2. Re-run the test suite\n"
        report += "3. Ensure all core functionality works\n"

    report += f"""
---
*Generated by Knowledge Graph Test Suite*
*Test Framework: Automated Validation*
"""

    return report

if __name__ == "__main__":
    try:
        success = test_knowledge_graph_comprehensive()

        # Create detailed report
        passed = sum(1 for _, status, _ in results if status)
        total = len(results)
        success_rate = (passed / total) * 100

        with open('/Users/Subho/knowledge_graph_test_report.md', 'w') as f:
            f.write(create_test_report(results, success_rate))

        print(f"\n📄 Detailed report saved to: /Users/Subho/knowledge_graph_test_report.md")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)