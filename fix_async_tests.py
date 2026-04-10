#!/usr/bin/env python3
"""
Automated script to fix async/await patterns in test files
"""

import re
import os
from pathlib import Path

def fix_test_file(file_path):
    """Fix async/await issues in a test file"""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern 1: Add async to tests that use fireEvent but aren't async
    # Find test functions with fireEvent but without async keyword
    pattern1 = r"it\('([^']+)',\s*\(\)\s*=>\s*\{[^}]*fireEvent\("
    matches1 = re.finditer(pattern1, content)

    for match in matches1:
        test_content = content[match.start():match.end()+500]  # Get some context
        if 'async' not in test_content[:test_content.find('fireEvent')]:
            # Replace it('...', () => { with it('...', async () => {
            old = "it('{}', () => {{".format(match.group(1))
            new = "it('{}', async () => {{".format(match.group(1))
            content = content.replace(old, new, 1)

    # Pattern 2: Wrap fireEvent calls in act()
    # Find fireEvent calls not wrapped in act/await act
    pattern2 = r"(?<!await act\(\(async \) => \{\s*)fireEvent\("
    # This is complex, so we'll do a simpler replacement

    # Pattern 3: Add await to Promise.then() chains
    content = re.sub(r'\.then\(\([^)]*\) => \{', 'await (async () => {', content)
    content = re.sub(r'\)\}\)', '; })()', content)  # Close the async IIFE

    # Pattern 4: Add await before mockResolvedValue calls
    content = re.sub(r'(\w+)\.mockResolvedValue\(', 'await \\1.mockResolvedValue(', content)

    # Save the file if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Main function to fix all test files"""
    project_dir = Path('/Users/Subho/brain-spark-analysis-project/src/__tests__')

    # Find all test files
    test_files = list(project_dir.rglob('*.test.ts')) + list(project_dir.rglob('*.test.tsx'))

    fixed_count = 0
    for test_file in test_files:
        if fix_test_file(test_file):
            print(f"Fixed: {test_file}")
            fixed_count += 1

    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == '__main__':
    main()
