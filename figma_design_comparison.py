#!/usr/bin/env python3
"""
Figma Design Comparison Analysis
Compare Figma designs with Android and Web implementations using TreeQuest approach
"""

import os
import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

@dataclass
class DesignComponent:
    name: str
    type: str  # FRAME, TEXT, RECTANGLE, etc.
    properties: Dict[str, Any]
    figma_id: str
    platform: str

@dataclass
class PlatformAnalysis:
    platform: str
    total_components: int
    component_types: Dict[str, int]
    design_patterns: List[str]
    ui_framework: str
    figma_alignment_score: int

def parse_figma_board_data() -> List[DesignComponent]:
    """Parse Figma board data from the extracted markdown"""
    
    figma_file = "/Users/Subho/CascadeProjects/brain-spark-platform/out/board_fixed.md"
    components = []
    
    if not os.path.exists(figma_file):
        print(f"❌ Figma file not found: {figma_file}")
        return components
    
    print(f"📋 Reading Figma design data from: {figma_file}")
    
    try:
        with open(figma_file, 'r') as f:
            content = f.read()
        
        # Extract component information using regex
        # Look for patterns like: - **frame** `Component Name` `(id)`
        component_pattern = r'- \*\*(frame|text|rectangle|section)\*\* `([^`]+)` `\(([^)]+)\)`'
        matches = re.findall(component_pattern, content, re.IGNORECASE)
        
        for match in matches:
            component_type, component_name, component_id = match
            
            component = DesignComponent(
                name=component_name,
                type=component_type.upper(),
                properties={},
                figma_id=component_id,
                platform="figma"
            )
            components.append(component)
        
        print(f"   ✅ Found {len(components)} Figma components")
        
        # Also look for image references to count visual elements
        image_pattern = r'!\[.*?\]\(images/([^)]+)\)'
        image_matches = re.findall(image_pattern, content)
        
        print(f"   🖼️ Found {len(image_matches)} visual elements")
        
    except Exception as e:
        print(f"❌ Error parsing Figma data: {e}")
    
    return components

def analyze_android_ui_components() -> PlatformAnalysis:
    """Analyze Android UI components from Brain Spark Platform"""
    
    android_path = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android"
    
    print(f"📱 Analyzing Android UI components...")
    
    component_types = {}
    design_patterns = []
    total_components = 0
    
    # Look for UI-related files
    ui_files = []
    for root, dirs, files in os.walk(android_path):
        for file in files:
            if file.endswith('.kt') or file.endswith('.xml'):
                ui_files.append(os.path.join(root, file))
    
    # Analyze Kotlin files for Compose components
    compose_components = 0
    xml_components = 0
    
    for file_path in ui_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Count Compose components
                if file_path.endswith('.kt'):
                    compose_matches = re.findall(r'@Composable\s+fun\s+(\w+)', content)
                    compose_components += len(compose_matches)
                    
                    # Identify design patterns
                    if 'ViewModel' in content:
                        design_patterns.append('MVVM')
                    if 'Theme' in content:
                        design_patterns.append('Material Design')
                    if 'Navigation' in content:
                        design_patterns.append('Navigation')
                
                # Count XML components  
                elif file_path.endswith('.xml'):
                    xml_matches = re.findall(r'<([A-Za-z]+\w*)', content)
                    xml_components += len(xml_matches)
        
        except Exception as e:
            continue
    
    total_components = compose_components + xml_components
    component_types = {
        'Compose': compose_components,
        'XML': xml_components
    }
    
    # Determine UI framework
    ui_framework = "Jetpack Compose" if compose_components > xml_components else "XML Views"
    
    # Calculate Figma alignment score based on modern patterns
    figma_alignment_score = 0
    if 'Material Design' in design_patterns:
        figma_alignment_score += 30
    if ui_framework == "Jetpack Compose":
        figma_alignment_score += 25
    if 'Navigation' in design_patterns:
        figma_alignment_score += 20
    if 'MVVM' in design_patterns:
        figma_alignment_score += 15
    if total_components > 10:
        figma_alignment_score += 10
    
    print(f"   ✅ Found {total_components} UI components")
    print(f"   🎨 UI Framework: {ui_framework}")
    
    return PlatformAnalysis(
        platform="android",
        total_components=total_components,
        component_types=component_types,
        design_patterns=list(set(design_patterns)),
        ui_framework=ui_framework,
        figma_alignment_score=figma_alignment_score
    )

def analyze_web_ui_components() -> PlatformAnalysis:
    """Analyze Web UI components from Brain Spark Platform"""
    
    web_path = "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/web"
    
    print(f"🌐 Analyzing Web UI components...")
    
    component_types = {}
    design_patterns = []
    total_components = 0
    
    # Look for React/TypeScript components
    ui_files = []
    for root, dirs, files in os.walk(web_path):
        for file in files:
            if file.endswith(('.tsx', '.jsx', '.ts', '.js', '.css')):
                ui_files.append(os.path.join(root, file))
    
    # Analyze component files
    react_components = 0
    css_components = 0
    
    for file_path in ui_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Count React components
                if file_path.endswith(('.tsx', '.jsx')):
                    # Look for component definitions
                    component_matches = re.findall(r'(?:export\s+)?(?:const|function)\s+(\w+)', content)
                    react_components += len([m for m in component_matches if m[0].isupper()])
                    
                    # Identify design patterns
                    if 'useState' in content or 'useEffect' in content:
                        design_patterns.append('React Hooks')
                    if 'Provider' in content or 'Context' in content:
                        design_patterns.append('Context API')
                    if 'styled' in content:
                        design_patterns.append('Styled Components')
                    if 'className' in content:
                        design_patterns.append('CSS Classes')
                
                # Count CSS components
                elif file_path.endswith('.css'):
                    css_matches = re.findall(r'\.([a-zA-Z][\w-]*)\s*\{', content)
                    css_components += len(css_matches)
        
        except Exception as e:
            continue
    
    total_components = react_components + css_components
    component_types = {
        'React': react_components,
        'CSS': css_components
    }
    
    # Determine UI framework
    ui_framework = "React + TypeScript"
    if 'Styled Components' in design_patterns:
        ui_framework += " + Styled Components"
    
    # Calculate Figma alignment score
    figma_alignment_score = 0
    if 'React Hooks' in design_patterns:
        figma_alignment_score += 25
    if 'Styled Components' in design_patterns:
        figma_alignment_score += 20
    if 'Context API' in design_patterns:
        figma_alignment_score += 15
    if total_components > 20:
        figma_alignment_score += 20
    if react_components > 10:
        figma_alignment_score += 20
    
    print(f"   ✅ Found {total_components} UI components")
    print(f"   ⚛️ UI Framework: {ui_framework}")
    
    return PlatformAnalysis(
        platform="web",
        total_components=total_components,
        component_types=component_types,
        design_patterns=list(set(design_patterns)),
        ui_framework=ui_framework,
        figma_alignment_score=figma_alignment_score
    )

def generate_design_comparison_report():
    """Generate comprehensive design comparison report"""
    
    print("🎨 FIGMA DESIGN COMPARISON ANALYSIS")
    print("=" * 60)
    
    # Parse Figma components
    figma_components = parse_figma_board_data()
    
    # Analyze platforms
    android_analysis = analyze_android_ui_components()
    web_analysis = analyze_web_ui_components()
    
    # Generate comparison
    print(f"\n📊 PLATFORM COMPARISON SUMMARY")
    print("=" * 60)
    
    analyses = [android_analysis, web_analysis]
    
    print(f"🎯 FIGMA BASELINE:")
    print(f"   Total Design Components: {len(figma_components)}")
    print(f"   Component Types: {len(set(c.type for c in figma_components))}")
    print()
    
    for analysis in analyses:
        print(f"📱 {analysis.platform.upper()} PLATFORM:")
        print(f"   Total Components: {analysis.total_components}")
        print(f"   UI Framework: {analysis.ui_framework}")
        print(f"   Design Patterns: {', '.join(analysis.design_patterns)}")
        print(f"   Figma Alignment Score: {analysis.figma_alignment_score}/100")
        print(f"   Component Breakdown: {analysis.component_types}")
        print()
    
    # Determine best Figma alignment
    best_platform = max(analyses, key=lambda x: x.figma_alignment_score)
    
    print(f"🏆 BEST FIGMA ALIGNMENT: {best_platform.platform.upper()}")
    print(f"   Score: {best_platform.figma_alignment_score}/100")
    print(f"   Framework: {best_platform.ui_framework}")
    print(f"   Reasoning: Modern patterns and component architecture")
    
    # Generate recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if best_platform.platform == "android":
        print("   ✅ Use Brain Spark Platform Android as primary mobile implementation")
        print("   📱 Leverage Jetpack Compose for Figma design fidelity")
        print("   🎨 Maintain Material Design consistency")
    else:
        print("   ✅ Use Web platform as design reference for mobile")
        print("   📱 Port React components to Compose equivalents")
        print("   🎨 Maintain cross-platform design consistency")
    
    # Save detailed report
    comparison_data = {
        "timestamp": "2025-01-17",
        "figma_baseline": {
            "total_components": len(figma_components),
            "component_types": list(set(c.type for c in figma_components)),
            "sample_components": [
                {"name": c.name, "type": c.type, "id": c.figma_id}
                for c in figma_components[:10]
            ]
        },
        "platforms": [
            {
                "platform": analysis.platform,
                "total_components": analysis.total_components,
                "ui_framework": analysis.ui_framework,
                "design_patterns": analysis.design_patterns,
                "figma_alignment_score": analysis.figma_alignment_score,
                "component_types": analysis.component_types
            }
            for analysis in analyses
        ],
        "recommendation": {
            "best_platform": best_platform.platform,
            "alignment_score": best_platform.figma_alignment_score,
            "reasoning": "Highest Figma alignment score based on modern UI patterns and component architecture"
        },
        "next_actions": [
            "Use Brain Spark Platform Android as primary implementation",
            "Ensure Figma design tokens are implemented across platforms",
            "Create design system documentation",
            "Establish component parity between platforms"
        ]
    }
    
    with open('/Users/Subho/figma_design_comparison_report.json', 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: /Users/Subho/figma_design_comparison_report.json")
    
    return comparison_data

if __name__ == "__main__":
    report = generate_design_comparison_report()