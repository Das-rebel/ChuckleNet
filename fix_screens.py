#!/usr/bin/env python3
import os
import re

# Define replacements for SparkTheme typography
typography_replacements = {
    'style = SparkTheme.typography.displayLarge.copy(': 'fontSize = 48.sp,',
    'style = SparkTheme.typography.displayMedium.copy(': 'fontSize = 36.sp,',
    'style = SparkTheme.typography.displaySmall.copy(': 'fontSize = 30.sp,',
    'style = SparkTheme.typography.headlineLarge.copy(': 'fontSize = 28.sp,',
    'style = SparkTheme.typography.headlineMedium.copy(': 'fontSize = 24.sp,',
    'style = SparkTheme.typography.headlineSmall.copy(': 'fontSize = 20.sp,',
    'style = SparkTheme.typography.titleLarge.copy(': 'fontSize = 18.sp,',
    'style = SparkTheme.typography.titleMedium.copy(': 'fontSize = 16.sp,',
    'style = SparkTheme.typography.titleSmall.copy(': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.bodyLarge.copy(': 'fontSize = 16.sp,',
    'style = SparkTheme.typography.bodyMedium.copy(': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.bodySmall.copy(': 'fontSize = 12.sp,',
    'style = SparkTheme.typography.labelLarge.copy(': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.labelMedium.copy(': 'fontSize = 12.sp,',
    'style = SparkTheme.typography.labelSmall.copy(': 'fontSize = 10.sp,',
    # Non-copy variants
    'style = SparkTheme.typography.displayLarge,': 'fontSize = 48.sp,',
    'style = SparkTheme.typography.displayMedium,': 'fontSize = 36.sp,',
    'style = SparkTheme.typography.displaySmall,': 'fontSize = 30.sp,',
    'style = SparkTheme.typography.headlineLarge,': 'fontSize = 28.sp,',
    'style = SparkTheme.typography.headlineMedium,': 'fontSize = 24.sp,',
    'style = SparkTheme.typography.headlineSmall,': 'fontSize = 20.sp,',
    'style = SparkTheme.typography.titleLarge,': 'fontSize = 18.sp,',
    'style = SparkTheme.typography.titleMedium,': 'fontSize = 16.sp,',
    'style = SparkTheme.typography.titleSmall,': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.bodyLarge,': 'fontSize = 16.sp,',
    'style = SparkTheme.typography.bodyMedium,': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.bodySmall,': 'fontSize = 12.sp,',
    'style = SparkTheme.typography.labelLarge,': 'fontSize = 14.sp,',
    'style = SparkTheme.typography.labelMedium,': 'fontSize = 12.sp,',
    'style = SparkTheme.typography.labelSmall,': 'fontSize = 10.sp,'
}

screens_dir = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android/app/src/main/java/com/secondbrain/app/ui/screens/"

for filename in os.listdir(screens_dir):
    if filename.endswith('.kt'):
        filepath = os.path.join(screens_dir, filename)
        
        with open(filepath, 'r') as file:
            content = file.read()
        
        original_content = content
        
        # Replace all typography references
        for old_pattern, new_text in typography_replacements.items():
            content = content.replace(old_pattern, new_text)
        
        # Handle multi-line style patterns with fontWeight
        content = re.sub(r'fontSize = (\d+)\.sp,\s*\n\s*fontWeight = FontWeight\.\w+\s*\n\s*\),', 
                        r'fontSize = \1.sp,\nfontWeight = FontWeight.Medium,', 
                        content, flags=re.MULTILINE)
        
        # Remove any leftover closing parentheses from .copy()
        content = re.sub(r'fontSize = (\d+)\.sp,\s*\n\s*\),', r'fontSize = \1.sp,', content, flags=re.MULTILINE)
        
        # Replace any remaining SparkTheme color or gradient references
        content = content.replace('SparkTheme.colorScheme.', 'Color(0xFF')
        content = content.replace('SparkTheme.', '')
        
        if content != original_content:
            with open(filepath, 'w') as file:
                file.write(content)
            print(f"Fixed {filename}")
        else:
            print(f"No changes needed for {filename}")