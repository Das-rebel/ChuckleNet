#!/usr/bin/env python3
"""
Test script for Smart AI Unified CLI
Validates both legacy and modern interfaces
"""

import subprocess
import sys
import json

def run_command(args, timeout=10):
    """Run command and return result"""
    try:
        result = subprocess.run(
            [sys.executable, '/Users/Subho/smart-ai-unified.py'] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)

def test_interface():
    """Test interface detection and basic commands"""
    tests = [
        # Modern interface tests
        {
            'name': 'Modern help',
            'args': ['ask', '--help'],
            'expect_success': False,  # Help exits with 0 but we capture as error
            'expect_in_output': 'Question to ask'
        },
        {
            'name': 'Providers list',
            'args': ['providers', 'list'],
            'expect_success': True,
            'expect_in_output': 'Available providers'
        },
        {
            'name': 'Status command',
            'args': ['status'],
            'expect_success': True,
            'expect_in_output': 'System Status'
        },
        {
            'name': 'Config list',
            'args': ['config', 'list'],
            'expect_success': True,
            'expect_in_output': ''  # May be empty
        },
        
        # Legacy interface tests
        {
            'name': 'Legacy help',
            'args': ['--help'],
            'expect_success': True,
            'expect_in_output': 'MODERN INTERFACE'
        },
        {
            'name': 'Legacy status (no args)',
            'args': [],
            'expect_success': True,
            'expect_in_output': 'Interactive Mode',
            'input_response': '/quit\n'
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"Testing: {test['name']}")
        
        if 'input_response' in test:
            # For interactive tests, we need to send input
            try:
                proc = subprocess.Popen(
                    [sys.executable, '/Users/Subho/smart-ai-unified.py'] + test['args'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(input=test['input_response'], timeout=5)
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                returncode, stdout, stderr = -1, "", "Timeout"
        else:
            returncode, stdout, stderr = run_command(test['args'], timeout=5)
        
        # Check results
        success = True
        if test['expect_success'] and returncode != 0:
            success = False
        elif not test['expect_success'] and returncode == 0:
            # For help commands that exit with error code but produce output
            success = test['expect_in_output'] in (stdout + stderr)
        
        if success and test['expect_in_output']:
            success = test['expect_in_output'] in (stdout + stderr)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}")
        
        if not success or '--verbose' in sys.argv:
            print(f"    Return code: {returncode}")
            print(f"    Stdout: {stdout[:200]}...")
            print(f"    Stderr: {stderr[:200]}...")
        
        results.append({
            'name': test['name'],
            'success': success,
            'returncode': returncode,
            'stdout': stdout[:500],
            'stderr': stderr[:500]
        })
    
    return results

def test_format_options():
    """Test different output formats"""
    print("\nTesting output formats...")
    
    format_tests = [
        ('plain', 'providers list'),
        ('json', '--format json providers list'), 
        ('markdown', '--format markdown providers list')
    ]
    
    for format_name, args_str in format_tests:
        args = args_str.split()
        returncode, stdout, stderr = run_command(args)
        
        if returncode == 0:
            print(f"✅ {format_name} format working")
            if format_name == 'json':
                try:
                    # Validate JSON format if output looks like JSON
                    if stdout.strip().startswith('{') or stdout.strip().startswith('['):
                        json.loads(stdout)
                        print("  ✅ Valid JSON output")
                except json.JSONDecodeError:
                    print("  ❌ Invalid JSON output")
        else:
            print(f"❌ {format_name} format failed")

def main():
    """Run all tests"""
    print("🧪 Testing Smart AI Unified CLI")
    print("=" * 50)
    
    # Test basic interface
    results = test_interface()
    
    # Test format options
    test_format_options()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        for r in results:
            if not r['success']:
                print(f"  ❌ {r['name']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())