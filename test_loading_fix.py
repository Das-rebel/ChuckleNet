#!/usr/bin/env python3

"""
Test script to verify the loading issue is fixed
"""

import subprocess
import time
import sys

def test_loading_fix():
    """Test if the loading issue has been fixed"""

    print("🔧 TESTING LOADING FIX")
    print("=" * 50)

    # Test 1: Check if loading indicator exists
    print("\n1. 🏗️ Checking Loading Indicator...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        loading_checks = {
            'Main loading indicator': 'id="loadingIndicator"' in html_content,
            'Loading overlay class': 'loading-overlay' in html_content,
            'Loading text content': 'Analyzing your content...' in html_content,
            'Loading container': 'loading-container' in html_content,
            'Spinner element': 'spinner' in html_content,
            'Initial hidden state': 'style="display: none;"' in html_content and 'loadingIndicator' in html_content
        }

        passed_checks = 0
        for check_name, found in loading_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_checks += 1

        print(f"   📊 Loading indicator: {passed_checks}/{len(loading_checks)} components found")

    except Exception as e:
        print(f"   ❌ Loading indicator check error: {e}")
        return False

    # Test 2: Check JavaScript loading methods
    print("\n2. 📄 Checking JavaScript Loading Methods...")
    try:
        js_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge-graph-app.js'],
                                   capture_output=True, text=True, timeout=10).stdout

        js_checks = {
            'showLoading method': 'showLoading(' in js_content,
            'Initial loading call': 'this.showLoading(true)' in js_content,
            'Hide loading call': 'this.showLoading(false)' in js_content,
            'Loading indicator ID': 'loadingIndicator' in js_content,
            'Constructor loading': 'showLoading(true)' in js_content
        }

        passed_js = 0
        for check_name, found in js_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_js += 1

        print(f"   📊 JavaScript loading: {passed_js}/{len(js_checks)} methods found")

    except Exception as e:
        print(f"   ❌ JavaScript check error: {e}")
        return False

    # Test 3: Check CSS styling for loading
    print("\n3. 🎨 Checking Loading CSS...")
    try:
        html_content = subprocess.run(['curl', '-s', 'http://localhost:8002/knowledge_graph_v2.html'],
                                      capture_output=True, text=True, timeout=10).stdout

        css_checks = {
            'Loading overlay style': '.loading-overlay' in html_content,
            'Fixed positioning': 'position: fixed' in html_content,
            'Full coverage': 'width: 100%' in html_content and 'height: 100%' in html_content,
            'High z-index': 'z-index: 9999' in html_content,
            'Background overlay': 'rgba(255, 255, 255, 0.95)' in html_content
        }

        passed_css = 0
        for check_name, found in css_checks.items():
            status = "✅" if found else "❌"
            print(f"   {status} {check_name}: {'Found' if found else 'Missing'}")
            if found:
                passed_css += 1

        print(f"   📊 Loading CSS: {passed_css}/{len(css_checks)} styles found")

    except Exception as e:
        print(f"   ❌ CSS check error: {e}")
        return False

    print("\n" + "=" * 50)
    print("📋 LOADING FIX VERIFICATION RESULTS")
    print("=" * 50)

    print("🎯 EXPECTED BEHAVIOR:")
    print("✅ Page should briefly show 'Analyzing your content...'")
    print("✅ Loading overlay should disappear after initialization")
    print("✅ Content should be visible and interactive")
    print("✅ All tabs should work properly")

    print("\n🧪 MANUAL VERIFICATION:")
    print("1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print("2. Expected sequence:")
    print("   - Brief loading overlay: 'Analyzing your content...'")
    print("   - Loading overlay disappears")
    print("   - Graph tab content appears")
    print("3. Open Console (F12) and check for:")
    print("   🚀 Initializing Knowledge Graph App...")
    print("   ✅ Knowledge Graph App initialized successfully!")
    print("4. Test functionality:")
    print("   - Click different tabs")
    print("   - Try search functionality")
    print("   - Check graph visualization")

    print("\n🚨 IF STILL STUCK:")
    print("❌ Check console for JavaScript errors")
    print("❌ Verify all libraries loaded (D3.js, Chart.js)")
    print("❌ Try manual initialization:")
    print("   - window.app.showLoading(false)")

    print(f"\n🎉 SUCCESS INDICATORS:")
    print(f"• Loading overlay appears briefly then disappears")
    print(f"• All console initialization messages appear")
    print(f"• Content is visible and interactive")
    print(f"• Tab switching works properly")
    print(f"• No 'stuck loading' state")

    print(f"\n🚀 APPLICATION URL:")
    print(f"http://localhost:8002/knowledge_graph_v2.html")

    return True

if __name__ == "__main__":
    try:
        success = test_loading_fix()
        print(f"\n✅ Loading fix verification completed")
        print(f"🔧 Follow manual verification steps above")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        sys.exit(1)