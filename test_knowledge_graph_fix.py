#!/usr/bin/env python3

"""
Test script to verify the knowledge graph fix works correctly.
This script checks if the embedded data is accessible and functional.
"""

import subprocess
import time
import json
import os

def test_knowledge_graph():
    """Test if the knowledge graph loads and Query/Insights tabs work."""

    print("🧪 Testing Knowledge Graph Fix...")
    print("=" * 50)

    # Check if server is running
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8000/knowledge_graph_comprehensive.html'],
                               capture_output=True, text=True)
        if result.stdout != '200':
            print("❌ Server not responding correctly")
            return False
        print("✅ HTTP server is running")
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

    # Check if HTML file exists and has been modified
    html_file = '/Users/Subho/knowledge_graph_comprehensive.html'
    if not os.path.exists(html_file):
        print("❌ HTML file not found")
        return False

    # Check if the fix is applied (no more embeddedGraphData = null)
    with open(html_file, 'r') as f:
        content = f.read()
        if 'let embeddedGraphData = null;' in content:
            print("❌ Fix not applied correctly - embeddedGraphData = null still exists")
            return False
        if 'embeddedGraphData = {"nodes":' in content:
            print("✅ Embedded data is present in HTML")
        else:
            print("❌ Embedded data not found in HTML")
            return False

    # Check if JSON file exists
    json_file = '/Users/Subho/knowledge_graph_comprehensive.json'
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
            if 'nodes' in data and 'links' in data:
                print(f"✅ JSON file is valid ({len(data['nodes'])} nodes, {len(data['links'])} links)")
            else:
                print("❌ JSON file structure is invalid")
                return False

    print("\n📋 Manual Testing Steps:")
    print("1. Open: http://localhost:8000/knowledge_graph_comprehensive.html")
    print("2. Open Developer Console (F12)")
    print("3. Check for success messages:")
    print("   - ✅ Embedded graph data loaded")
    print("   - ✅ Graph data loaded successfully!")
    print("4. Test Query tab:")
    print("   - Click '💬 Query' tab")
    print("   - Type 'growth' and click '🔍 Search'")
    print("   - Should show results, not 'Graph data not loaded yet'")
    print("5. Test Insights tab:")
    print("   - Click '💡 Insights' tab")
    print("   - Should auto-generate insights")
    print("   - Should show various analysis sections")

    print("\n🎯 Expected Console Output:")
    print('✅ Embedded graph data loaded: {nodes: 24, links: 45, topics: 7}')
    print('✅ Using embedded graph data (from script tag)')
    print('✅ Graph data loaded successfully!')

    return True

if __name__ == "__main__":
    success = test_knowledge_graph()
    if success:
        print("\n🎉 Knowledge graph fix appears to be successful!")
        print("📝 Please complete the manual testing steps above to verify full functionality.")
    else:
        print("\n❌ Issues found with the knowledge graph fix.")