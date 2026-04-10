#!/usr/bin/env python3
import os

# Only fix the screens that are actually used in MainActivity
main_screens = [
    'SimpleBrainSparkDashboard.kt',  # Index 0
    'BookmarksScreen.kt',            # Index 1  
    'LearningPathsScreen.kt',        # Index 2
    'ActionablesScreen.kt',          # Index 3
    'SearchScreen.kt',               # Index 4
    'StatsScreen.kt',                # Index 5
    'SettingsScreenSimple.kt',       # Index 6 (we use Simple version)
]

screens_dir = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android/app/src/main/java/com/secondbrain/app/ui/screens/"

def fix_syntax_errors(content):
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix broken fontSize lines
        if 'fontSize = ' in line and 'fontWeight = ' in line and not line.strip().endswith(','):
            # Split the line properly
            if 'fontSize = ' in line and 'sp,' in line:
                parts = line.split('fontWeight = ')
                if len(parts) == 2:
                    font_size_part = parts[0].strip()
                    if not font_size_part.endswith(','):
                        font_size_part += ','
                    font_weight_part = 'fontWeight = ' + parts[1]
                    if not font_weight_part.endswith(','):
                        font_weight_part += ','
                    
                    fixed_lines.append(font_size_part)
                    fixed_lines.append('                ' + font_weight_part)  # Add proper indentation
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        # Fix lines ending with ),
        elif line.strip().endswith('),') and 'fontSize' in line:
            fixed_lines.append(line.replace('),', ','))
        # Fix malformed Color references 
        elif 'Color(0xFF' in line and not line.count('Color(0xFF') == line.count(')'):
            # Just skip malformed color lines for now or replace with a default
            if 'brush =' in line:
                fixed_lines.append(line.replace('brush = Color(0xFF', 'color = Color(0xFFF8F9FA)'))
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

for screen_file in main_screens:
    filepath = os.path.join(screens_dir, screen_file)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        
        original_content = content
        
        # Apply syntax fixes
        content = fix_syntax_errors(content)
        
        # Remove any remaining .copy() calls without proper closing
        content = content.replace('.copy(\nfontWeight = FontWeight.Medium,', ', fontWeight = FontWeight.Medium')
        content = content.replace('.copy(\nfontWeight = FontWeight.Bold,', ', fontWeight = FontWeight.Bold')
        content = content.replace('.copy(\nfontWeight = FontWeight.SemiBold,', ', fontWeight = FontWeight.SemiBold')
        
        # Remove any leftover SparkTheme references
        content = content.replace('typography.', '')
        
        if content != original_content:
            with open(filepath, 'w') as file:
                file.write(content)
            print(f"Fixed syntax errors in {screen_file}")
        else:
            print(f"No syntax fixes needed for {screen_file}")
    else:
        print(f"File not found: {screen_file}")