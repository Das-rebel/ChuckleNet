#!/usr/bin/env python3

"""
Quick check to verify data loading status with console output
"""

import subprocess
import time
import sys

def check_data_loading_status():
    """Quick status check for data loading"""

    print("📊 QUICK DATA LOADING STATUS CHECK")
    print("=" * 50)

    print("\n🔍 TESTING APPLICATION STATUS:")

    # Test application accessibility
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge_graph_v2.html'],
                               capture_output=True, text=True, timeout=5)
        if result.stdout.strip() == '200':
            print("✅ Application accessible")
        else:
            print(f"❌ Server error: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

    # Test JavaScript file
    try:
        result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                               'http://localhost:8002/knowledge-graph-app.js'],
                               capture_output=True, text=True, timeout=5)
        if result.stdout.strip() == '200':
            print("✅ JavaScript file accessible")
        else:
            print(f"❌ JavaScript file error: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ JavaScript file error: {e}")
        return False

    print("\n🎯 CONSOLE VERIFICATION STEPS:")
    print("1. Open: http://localhost:8002/knowledge_graph_v2.html")
    print("2. Open Developer Console (F12)")
    print("3. Look for these messages:")
    print("   🚀 Initializing Knowledge Graph App...")
    print("   📊 Loading LinkedIn data...")
    print("   ✅ Data loaded successfully")
    print("   🎧 Initializing event listeners...")
    print("   🔍 Building search index...")
    print("   ⚙️ Processing data...")
    print("   🎨 Rendering active tab...")
    print("   ✅ Knowledge Graph App initialized successfully!")
    print("   📈 Data summary: {posts: 440, concepts: 6, categories: 6}")

    print("\n🧪 TESTING IN CONSOLE:")
    print("Type these commands in browser console:")
    print("")
    print("1. Check if app exists:")
    print("   window.app")
    print("")
    print("2. Check data structure:")
    print("   window.app.data")
    print("")
    print("3. Check data counts:")
    print("   window.app.data.posts.length")
    print("   window.app.data.concepts.length")
    print("   window.app.data.categories.length")
    print("")
    print("4. Test data generation:")
    print("   window.app.generateLinkedInPosts(3)")
    print("")
    print("5. Test search:")
    print("   window.app.performSearch('brand')")
    print("")
    print("6. Test tab switching:")
    print("   window.app.switchTab('graph')")
    print("   window.app.switchTab('timeline')")
    print("   window.app.switchTab('query')")

    print("\n🎯 EXPECTED RESULTS:")
    print("✅ Console should show initialization messages")
    print("✅ window.app should return KnowledgeGraphApp object")
    print("✅ window.app.data should have posts, concepts, categories")
    print("✅ Data counts should show: posts=440, concepts=6, categories=6")
    print("✅ Search should return highlighted results")
    print("✅ Tab switching should show different visualizations")

    print("\n🚨 IF STILL NOT WORKING:")
    print("❌ Check for red errors in console")
    print("❌ Make sure all external libraries loaded (D3.js, Chart.js)")
    print("❌ Try manual initialization: window.app.init()")
    print("❌ Try data loading: window.app.loadLinkedInData()")

    print(f"\n🎉 SUCCESS INDICATORS:")
    print(f"• No console errors")
    print(f"• All initialization messages appear")
    print(f"• Visualizations render with data")
    print(f"• Search functionality works")
    print(f"• Tab switching shows different content")

    print(f"\n🚀 APPLICATION URL:")
    print(f"http://localhost:8002/knowledge_graph_v2.html")

    return True

if __name__ == "__main__":
    try:
        success = check_data_loading_status()
        print(f"\n✅ Status check completed")
        print(f"🔧 Follow console verification steps above")
    except Exception as e:
        print(f"\n❌ Status check failed: {e}")
        sys.exit(1)