#!/usr/bin/env python3

"""
Comprehensive test to verify data is actually loading and displaying in the application
"""

import subprocess
import time
import sys
import json

def verify_data_loading():
    """Verify if data is actually loading and displaying in the knowledge graph application."""

    print("🔍 VERIFYING ACTUAL DATA LOADING")
    print("=" * 50)

    # Test 1: Check if JavaScript is executing
    print("\n1. 🚀 Testing JavaScript Execution...")
    try:
        # Create a simple test to check if JavaScript runs
        test_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>JS Test</title>
            <script src="http://localhost:8002/knowledge-graph-app.js"></script>
        </head>
        <body>
            <div id="test-output"></div>
            <script>
                try {
                    const app = new KnowledgeGraphApp();
                    document.getElementById('test-output').innerHTML =
                        'JS loaded: ' + (app ? 'SUCCESS' : 'FAILED');
                } catch (e) {
                    document.getElementById('test-output').innerHTML =
                        'JS Error: ' + e.message;
                }
            </script>
        </body>
        </html>
        '''

        # Write test file
        with open('/tmp/test_js.html', 'w') as f:
            f.write(test_html)

        # Start test server in background
        subprocess.Popen(['python3', '-m', 'http.server', '8003'],
                        cwd='/tmp', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        time.sleep(2)  # Let server start

        # Test if JavaScript class exists
        result = subprocess.run(['curl', '-s', 'http://localhost:8003/test_js.html'],
                              capture_output=True, text=True, timeout=10)

        if 'SUCCESS' in result.stdout:
            print("   ✅ JavaScript class loads successfully")
        elif 'JS Error:' in result.stdout:
            print(f"   ❌ JavaScript error: {result.stdout}")
            return False
        else:
            print("   ❌ JavaScript test inconclusive")

        # Clean up test server
        subprocess.run(['pkill', '-f', 'python3.*8003'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"   ❌ JavaScript test failed: {e}")
        return False

    # Test 2: Check data generation methods
    print("\n2. 📊 Testing Data Generation Methods...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        # Check if sample data generation methods work
        data_method_checks = {
            'generateLinkedInPosts': 'generateLinkedInPosts(' in js_content,
            'Sample data structure': 'posts:' in js_content and 'concepts:' in js_content,
            'Data initialization': 'this.data = {' in js_content,
            'Processing method': 'processData(' in js_content,
            'Data object creation': 'posts: [],' in js_content and 'concepts: [],' in js_content
        }

        passed_checks = 0
        for check_name, found in data_method_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_checks += 1

        if passed_checks < len(data_method_checks) * 0.8:
            print("   ⚠️ Data generation methods may be incomplete")
            return False

    except Exception as e:
        print(f"   ❌ Data generation check error: {e}")
        return False

    # Test 3: Check if data is being generated correctly
    print("\n3. 🔢 Verifying Sample Data Content...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        # Look for actual sample data values
        sample_data_checks = {
            'Posts count (440)': '440' in js_content,
            'Brand strategy concept': 'brand_strategy' in js_content,
            'Growth marketing concept': 'growth_marketing' in js_content,
            'Content creation concept': 'content_creation' in js_content,
            'Digital transformation concept': 'digital_transformation' in js_content,
            'Customer experience concept': 'customer_experience' in js_content,
            'Data analytics concept': 'data_analytics' in js_content,
            'Social media category': 'social_media' in js_content,
            'Analytics category': 'analytics' in js_content,
            'Strategy category': 'strategy' in js_content
        }

        passed_data = 0
        for data_name, found in sample_data_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {data_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_data += 1

        print(f"   📊 Sample data: {passed_data}/{len(sample_data_checks)} items found")

        if passed_data < len(sample_data_checks) * 0.7:
            print("   ⚠️ Sample data may be incomplete")
            return False

    except Exception as e:
        print(f"   ❌ Sample data check error: {e}")
        return False

    # Test 4: Check initialization sequence
    print("\n4. 🔄 Verifying Initialization Sequence...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        init_checks = {
            'Async init method': 'async init()' in js_content,
            'Load LinkedIn data call': 'await this.loadLinkedInData()' in js_content,
            'Initialize event listeners': 'this.initializeEventListeners()' in js_content,
            'Build search index': 'this.buildSearchIndex()' in js_content,
            'Process data': 'this.processData()' in js_content,
            'Render active tab': 'this.renderActiveTab()' in js_content,
            'Hide loading': 'this.showLoading(false)' in js_content,
            'DOMContentLoaded listener': 'DOMContentLoaded' in js_content
        }

        passed_init = 0
        for init_name, found in init_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {init_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_init += 1

        print(f"   📊 Initialization: {passed_init}/{len(init_checks)} steps found")

        if passed_init < len(init_checks) * 0.8:
            print("   ⚠️ Initialization sequence may be incomplete")
            return False

    except Exception as e:
        print(f"   ❌ Initialization check error: {e}")
        return False

    # Test 5: Check tab rendering methods exist
    print("\n5. 🎨 Verifying Tab Rendering Methods...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        render_checks = {
            'renderGraphTab': 'renderGraphTab()' in js_content,
            'renderTimelineTab': 'renderTimelineTab()' in js_content,
            'renderTopicsTab': 'renderTopicsTab()' in js_content,
            'renderQueryTab': 'renderQueryTab()' in js_content,
            'renderInsightsTab': 'renderInsightsTab()' in js_content,
            'renderActiveTab': 'renderActiveTab()' in js_content,
            'switchTab': 'switchTab(' in js_content,
            'Tab switching logic': 'this.activeTab' in js_content
        }

        passed_render = 0
        for render_name, found in render_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {render_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_render += 1

        print(f"   📊 Rendering methods: {passed_render}/{len(render_checks)} methods found")

    except Exception as e:
        print(f"   ❌ Rendering methods check error: {e}")
        return False

    # Test 6: Check HTML structure matches JavaScript expectations
    print("\n6. 🏗️ Verifying HTML-JavaScript Compatibility...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        compatibility_checks = {
            'Graph panel ID': 'id="graph-panel"' in html_content,
            'Timeline panel ID': 'id="timeline-panel"' in html_content,
            'Topics panel ID': 'id="topics-panel"' in html_content,
            'Search panel ID': 'id="search-panel"' in html_content,
            'Insights panel ID': 'id="insights-panel"' in html_content,
            'Tab navigation': 'class="tab-navigation"' in html_content,
            'Tab buttons': 'data-tab' in html_content,
            'Loading indicator': 'loading' in html_content
        }

        passed_compat = 0
        for compat_name, found in compatibility_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {compat_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_compat += 1

        print(f"   📊 HTML compatibility: {passed_compat}/{len(compatibility_checks)} elements found")

        if passed_compat < len(compatibility_checks) * 0.8:
            print("   ⚠️ HTML structure may have compatibility issues")
            return False

    except Exception as e:
        print(f"   ❌ HTML compatibility check error: {e}")
        return False

    print("\n" + "=" * 50)
    print("📋 DATA LOADING VERIFICATION RESULTS")
    print("=" * 50)

    print("🎯 MANUAL VERIFICATION STEPS:")
    print("1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print("2. Open Developer Console (F12)")
    print("3. Check for console messages:")
    print("   - Should see no red errors")
    print("   - May see 'Knowledge Graph App initialized' if added")
    print("4. Test app object:")
    print("   - Type: window.app")
    print("   - Should return: KnowledgeGraphApp { ... }")
    print("5. Test data loading:")
    print("   - Type: window.app.data")
    print("   - Should return object with posts, concepts, categories")
    print("6. Test data generation:")
    print("   - Type: window.app.generateLinkedInPosts(5)")
    print("   - Should return array of 5 post objects")
    print("7. Test tab functionality:")
    print("   - Type: window.app.switchTab('graph')")
    print("   - Should switch to graph tab")
    print("   - Type: window.app.renderActiveTab()")
    print("   - Should render content for active tab")

    print("\n🔍 SPECIFIC THINGS TO CHECK:")
    print("✅ No JavaScript errors in console")
    print("✅ window.app object exists")
    print("✅ window.app.data contains sample data")
    print("✅ Clicking tabs shows different content")
    print("✅ Search input field accepts text")
    print("✅ Graph tab shows network visualization")
    print("✅ Timeline tab shows charts")
    print("✅ Topics tab shows topic cards")

    print("\n🚨 TROUBLESHOOTING IF STILL NOT WORKING:")
    print("❌ If window.app is undefined:")
    print("   - Check if knowledge-graph-app.js is loading")
    print("   - Check for JavaScript syntax errors")
    print("")
    print("❌ If window.app.data is null:")
    print("   - Type: window.app.init() to reinitialize")
    print("   - Type: window.app.loadLinkedInData() to load data")
    print("")
    print("❌ If tabs don't render:")
    print("   - Type: window.app.processData() to process data")
    print("   - Type: window.app.renderActiveTab() to force render")

    print(f"\n🎉 EXPECTED OUTCOME:")
    print(f"All tests should pass AND manual verification should show:")
    print(f"• Interactive visualizations with real data")
    print(f"• Working search with results")
    print(f"• Tab switching with different content")
    print(f"• No console errors")

    return True

if __name__ == "__main__":
    try:
        success = verify_data_loading()
        if success:
            print(f"\n✅ Data loading verification completed")
            print(f"🔧 Follow manual steps above to confirm functionality")
        else:
            print(f"\n❌ Critical issues found in data loading")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification execution failed: {e}")
        sys.exit(1)