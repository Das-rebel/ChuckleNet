#!/usr/bin/env python3

"""
Deep debug script to identify why the application is stuck loading
"""

import subprocess
import time
import sys

def deep_debug_loading():
    """Deep debug the loading issue"""

    print("🔍 DEEP DEBUG: STUCK LOADING ISSUE")
    print("=" * 50)

    # Test 1: Check if JavaScript is actually executing
    print("\n1. 🚀 Testing JavaScript Execution...")
    try:
        # Create a minimal test to check if any JavaScript runs
        test_js = '''
        console.log('TEST: JavaScript is running');
        document.addEventListener('DOMContentLoaded', function() {
            console.log('TEST: DOMContentLoaded fired');
            setTimeout(function() {
                console.log('TEST: setTimeout executed');
                const indicator = document.getElementById('loadingIndicator');
                if (indicator) {
                    indicator.style.display = 'none';
                    console.log('TEST: Loading indicator hidden');
                } else {
                    console.log('TEST: Loading indicator not found');
                }
            }, 1000);
        });
        '''

        # Add test script to HTML
        js_test_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>JS Test</title>
            <script src="http://localhost:8002/knowledge-graph-app.js"></script>
            <script>
                {test_js}
            </script>
        </head>
        <body>
            <div id="loadingIndicator" style="display: block; padding: 20px; background: red;">
                TEST LOADING INDICATOR
            </div>
            <div id="test-output">
                Testing JavaScript execution...
            </div>
        </body>
        </html>
        '''

        with open('/tmp/test_loading.html', 'w') as f:
            f.write(js_test_html)

        # Start test server
        subprocess.Popen(['python3', '-m', 'http.server', '8004'],
                        cwd='/tmp', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

        # Test if JavaScript class exists and can be instantiated
        print("   Testing KnowledgeGraphApp class...")

    except Exception as e:
        print(f"   ❌ JavaScript execution test failed: {e}")

    # Test 2: Check for JavaScript syntax errors
    print("\n2. 📝 Checking for JavaScript Syntax Errors...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        # Basic syntax checks
        syntax_checks = {
            'Class declaration': 'class KnowledgeGraphApp' in js_content,
            'Constructor method': 'constructor()' in js_content,
            'Init method': 'init()' in js_content,
            'Brace balance': js_content.count('{') == js_content.count('}'),
            'Parentheses balance': js_content.count('(') == js_content.count(')'),
            'Square brackets balance': js_content.count('[') == js_content.count(']'),
            'Unterminated strings': js_content.count('"') % 2 == 0 and js_content.count("'") % 2 == 0
        }

        syntax_passed = 0
        for check_name, passed in syntax_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'OK' if passed else 'ISSUE'}")
            if passed:
                syntax_passed += 1

        print(f"   📊 Syntax check: {syntax_passed}/{len(syntax_checks)} passed")

    except Exception as e:
        print(f"   ❌ Syntax check error: {e}")

    # Test 3: Check HTML structure for missing elements
    print("\n3. 🏗️ Checking HTML Structure for Missing Elements...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        required_elements = {
            'DOCTYPE declaration': '<!DOCTYPE html>' in html_content,
            'HTML tag': '<html' in html_content,
            'Head tag': '<head>' in html_content,
            'Body tag': '<body>' in html_content,
            'Knowledge Graph App script': 'knowledge-graph-app.js' in html_content,
            'D3.js library': 'd3@7' in html_content,
            'Chart.js library': 'chart.js' in html_content,
            'Main container': 'tab-content' in html_content,
            'Loading indicator': 'loadingIndicator' in html_content,
            'Tab panels': 'tab-panel' in html_content,
            'Graph panel': 'graph-panel' in html_content
        }

        html_passed = 0
        for element_name, found in required_elements.items():
            status = "✅" if found else "❌"
            print(f"   {status} {element_name}: {'Found' if found else 'Missing'}")
            if found:
                html_passed += 1

        print(f"   📊 HTML structure: {html_passed}/{len(required_elements)} elements found")

    except Exception as e:
        print(f"   ❌ HTML structure check error: {e}")

    # Test 4: Check initialization sequence
    print("\n4. 🔄 Checking Initialization Sequence...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        init_sequence = {
            'DOMContentLoaded listener': 'DOMContentLoaded' in js_content,
            'App instantiation': 'new KnowledgeGraphApp()' in js_content,
            'Constructor calls init': 'this.init()' in js_content,
            'Init is async': 'async init()' in js_content,
            'Load LinkedIn data': 'loadLinkedInData()' in js_content,
            'Error handling': 'try {' in js_content and 'catch' in js_content,
            'Show loading false': 'showLoading(false)' in js_content,
            'Console logging': 'console.log' in js_content
        }

        init_passed = 0
        for step_name, found in init_sequence.items():
            status = "✅" if found else "❌"
            print(f"   {status} {step_name}: {'Found' if found else 'Missing'}")
            if found:
                init_passed += 1

        print(f"   📊 Initialization: {init_passed}/{len(init_sequence)} steps found")

    except Exception as e:
        print(f"   ❌ Initialization check error: {e}")

    # Test 5: Check for common issues
    print("\n5. 🚨 Checking for Common Issues...")

    common_issues = {
        'Multiple app instances': js_content.count('new KnowledgeGraphApp()') if 'js_content' in locals() else 0,
        'Async/await issues': 'async' in js_content and 'await' in js_content if 'js_content' in locals() else False,
        'Missing error handling': js_content.count('catch') == 0 if 'js_content' in locals() else True,
        'DOM timing issues': 'DOMContentLoaded' in js_content if 'js_content' in locals() else False
    }

    print("   Common issue analysis:")
    for issue_name, value in common_issues.items():
        if issue_name == 'Multiple app instances':
            status = "⚠️" if value > 1 else "✅"
            print(f"   {status} {issue_name}: {value} instance(s)")
        elif issue_name == 'Async/await issues':
            status = "⚠️" if value else "✅"
            print(f"   {status} {issue_name}: {'Present' if value else 'None'}")
        elif issue_name == 'Missing error handling':
            status = "❌" if value else "✅"
            print(f"   {status} {issue_name}: {'Missing' if value else 'Present'}")
        elif issue_name == 'DOM timing issues':
            status = "⚠️" if value else "✅"
            print(f"   {status} {issue_name}: {'Uses DOMContentLoaded' if value else 'No DOM listener'}")

    print("\n" + "=" * 50)
    print("🎯 IMMEDIATE DEBUGGING STEPS")
    print("=" * 50)

    print("🔧 STEP 1: Check Browser Console")
    print("1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Console tab")
    print("4. Look for:")
    print("   ❌ Red error messages")
    print("   ❌ 'Failed to load resource' errors")
    print("   ❌ 'Uncaught SyntaxError'")
    print("   ❌ 'Cannot read property' errors")
    print("   ✅ Console messages from our app")

    print("\n🔧 STEP 2: Test Manual JavaScript Execution")
    print("In console, type:")
    print("   typeof KnowledgeGraphApp")
    print("   Expected: 'function'")
    print("")
    print("   const testApp = new KnowledgeGraphApp()")
    print("   Expected: Should create app object or show error")

    print("\n🔧 STEP 3: Check Network Tab")
    print("1. Go to Network tab in Developer Tools")
    print("2. Refresh the page")
    print("3. Check for:")
    print("   ❌ Failed requests (red status codes)")
    print("   ❌ 404 errors for JavaScript files")
    print("   ✅ All files should load with 200 status")

    print("\n🔧 STEP 4: Force Hide Loading")
    print("If everything else works, try:")
    print("   document.getElementById('loadingIndicator').style.display = 'none'")

    print("\n🚨 MOST LIKELY ISSUES:")
    print("1. JavaScript syntax error preventing execution")
    print("2. Missing external library (D3.js or Chart.js)")
    print("3. Console error stopping initialization")
    print("4. DOM element not found when script tries to hide loading")
    print("5. Async function never resolving")

    print(f"\n🚀 URL: http://localhost:8002/knowledge_graph_v2.html")

    return True

if __name__ == "__main__":
    try:
        success = deep_debug_loading()
        print(f"\n✅ Deep debug analysis completed")
        print(f"🔧 Follow the debugging steps above")
    except Exception as e:
        print(f"\n❌ Debug analysis failed: {e}")
        sys.exit(1)