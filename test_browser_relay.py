#!/usr/bin/env python3
"""
Quick test script for OpenClaw Browser Relay
"""

import asyncio
import websockets
import json
import requests
import subprocess

async def test_websocket():
    """Test WebSocket connection"""
    print("\n1️⃣ Testing WebSocket Connection...")
    try:
        async with websockets.connect('ws://127.0.0.1:18792/extension') as ws:
            print("   ✅ WebSocket connected")

            # Send ping
            await ws.send(json.dumps({'method': 'test', 'params': {}}))
            print("   📤 Sent test message")

            # Receive response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"   📥 Received: {response}")

            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_http():
    """Test HTTP endpoint"""
    print("\n2️⃣ Testing HTTP Endpoint...")
    try:
        response = requests.get('http://127.0.0.1:18792/', timeout=2)
        print(f"   ✅ HTTP Status: {response.status_code}")
        print(f"   ✅ Response: {response.text.strip()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_relay_process():
    """Check if relay process is running"""
    print("\n3️⃣ Checking Relay Process...")
    try:
        result = subprocess.run(
            ['lsof', '-i', ':18792'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Relay server is running on port 18792")
            print(f"   📊 Process info:\n{result.stdout}")
            return True
        else:
            print("   ❌ No process found on port 18792")
            return False
    except Exception as e:
        print(f"   ❌ Failed to check: {e}")
        return False

def test_tmlpd():
    """Test TMLPD service"""
    print("\n4️⃣ Testing TMLPD Service...")
    try:
        response = requests.get('http://127.0.0.1:8765/', timeout=2)
        print(f"   ✅ TMLPD Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

async def main():
    print("="*70)
    print("🧪 OPENCLAW BROWSER RELAY - COMPREHENSIVE TEST")
    print("="*70)

    results = []

    # Test relay process
    results.append(("Relay Process", test_relay_process()))

    # Test HTTP endpoint
    results.append(("HTTP Endpoint", test_http()))

    # Test WebSocket connection
    results.append(("WebSocket Connection", await test_websocket()))

    # Test TMLPD
    results.append(("TMLPD Service", test_tmlpd()))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(result for _, result in results)
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Browser relay is ready to use.")
        print("\n📝 Next Step: Load extension in Brave and click to connect")
    else:
        print("⚠️  SOME TESTS FAILED. Check troubleshooting section.")
    print("="*70)

if __name__ == '__main__':
    asyncio.run(main())
