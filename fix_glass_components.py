#!/usr/bin/env python3
import os
import re

screens_dir = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android/app/src/main/java/com/secondbrain/app/ui/screens/"

glass_replacements = {
    'GlassHeader(': 'Card(',
    'GlassCard(': 'Card(',
    'GlassButton(': 'Button(',
}

# These are the files that need Glass component replacements
problematic_files = ['StatsScreen.kt', 'QuickActionsScreen.kt', 'LearningPathBuilderScreen.kt']

for filename in problematic_files:
    filepath = os.path.join(screens_dir, filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        
        original_content = content
        
        # Replace Glass components with standard Material components
        for old_comp, new_comp in glass_replacements.items():
            content = content.replace(old_comp, new_comp)
        
        # Fix Card component properties that differ from GlassCard
        content = re.sub(r'backgroundColor\s*=\s*([^,)]+)', r'colors = CardDefaults.cardColors(containerColor = \1)', content)
        content = re.sub(r'glassmorphismColor\s*=\s*([^,)]+)', r'colors = CardDefaults.cardColors(containerColor = \1)', content)
        
        # Add shape and elevation for Cards
        content = re.sub(r'Card\(\s*\n\s*modifier', r'Card(\n    shape = RoundedCornerShape(12.dp),\n    colors = CardDefaults.cardColors(containerColor = Color.White),\n    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),\n    modifier', content)
        
        if content != original_content:
            with open(filepath, 'w') as file:
                file.write(content)
            print(f"Fixed Glass components in {filename}")
        else:
            print(f"No Glass component changes needed for {filename}")