#!/usr/bin/env python3
"""
Android Implementation Comparison Analysis
Using TreeQuest task classification approach to compare Android implementations
"""

import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AndroidImplementation:
    name: str
    path: str
    features: List[str]
    build_files: List[str]
    ui_components: List[str]
    last_modified: str
    size_mb: float
    advancement_score: int

def analyze_android_implementation(base_path: str, name: str) -> AndroidImplementation:
    """Analyze an Android implementation using TreeQuest-style analysis"""
    
    features = []
    build_files = []
    ui_components = []
    
    # Walk through the Android directory
    for root, dirs, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)
            
            # Identify build files
            if file.endswith(('.gradle', 'build.gradle', 'settings.gradle')):
                build_files.append(rel_path)
            
            # Identify UI components
            if file.endswith('.kt') and any(ui_term in file.lower() for ui_term in ['activity', 'fragment', 'ui', 'view']):
                ui_components.append(rel_path)
            
            # Identify features
            if file.endswith('.kt'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'Compose' in content:
                            features.append('Jetpack Compose')
                        if 'ViewModel' in content:
                            features.append('MVVM Architecture')
                        if 'Room' in content:
                            features.append('Room Database')
                        if 'Navigation' in content:
                            features.append('Navigation Component')
                        if 'Hilt' in content or 'Dagger' in content:
                            features.append('Dependency Injection')
                except:
                    pass
    
    # Remove duplicates
    features = list(set(features))
    
    # Calculate advancement score based on modern Android features
    advancement_score = 0
    if 'Jetpack Compose' in features:
        advancement_score += 30
    if 'MVVM Architecture' in features:
        advancement_score += 20
    if 'Room Database' in features:
        advancement_score += 15
    if 'Navigation Component' in features:
        advancement_score += 15
    if 'Dependency Injection' in features:
        advancement_score += 20
    
    # Get directory size
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(base_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    
    size_mb = total_size / (1024 * 1024)
    
    # Get last modified time
    try:
        last_modified = str(os.path.getmtime(base_path))
    except:
        last_modified = "unknown"
    
    return AndroidImplementation(
        name=name,
        path=base_path,
        features=features,
        build_files=build_files,
        ui_components=ui_components,
        last_modified=last_modified,
        size_mb=size_mb,
        advancement_score=advancement_score
    )

def compare_android_implementations():
    """Compare Android implementations using TreeQuest classification approach"""
    
    print("🔍 Android Implementation Comparison Analysis")
    print("=" * 60)
    
    # Define Android implementations to analyze
    implementations = [
        {
            "name": "Brain Spark Platform Android",
            "path": "/Users/Subho/CascadeProjects/brain-spark-platform/platforms/android"
        },
        {
            "name": "Second Brain Android (Main)",
            "path": "/Users/Subho/second-brain-android"
        },
        {
            "name": "Second Brain Android (Resumetailor)",
            "path": "/Users/Subho/second-brain-android/resumetailor-app"
        }
    ]
    
    analysis_results = []
    
    for impl in implementations:
        if os.path.exists(impl["path"]):
            print(f"\n📱 Analyzing: {impl['name']}")
            print(f"   Path: {impl['path']}")
            
            result = analyze_android_implementation(impl["path"], impl["name"])
            analysis_results.append(result)
            
            print(f"   ✅ Features found: {len(result.features)}")
            print(f"   📁 Build files: {len(result.build_files)}")
            print(f"   🎨 UI components: {len(result.ui_components)}")
            print(f"   📊 Advancement score: {result.advancement_score}/100")
            print(f"   💾 Size: {result.size_mb:.1f} MB")
        else:
            print(f"\n❌ Path not found: {impl['path']}")
    
    # Generate comparison report
    print("\n📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    if analysis_results:
        # Sort by advancement score
        sorted_results = sorted(analysis_results, key=lambda x: x.advancement_score, reverse=True)
        
        print("🏆 RANKING BY ADVANCEMENT:")
        for i, result in enumerate(sorted_results, 1):
            print(f"   {i}. {result.name}")
            print(f"      Score: {result.advancement_score}/100")
            print(f"      Key Features: {', '.join(result.features[:3])}")
            print(f"      Size: {result.size_mb:.1f} MB")
            print()
        
        # Most advanced implementation
        most_advanced = sorted_results[0]
        print(f"🚀 MOST ADVANCED: {most_advanced.name}")
        print(f"   Advancement Score: {most_advanced.advancement_score}/100")
        print(f"   Features: {', '.join(most_advanced.features)}")
        print(f"   Path: {most_advanced.path}")
        
        # Save detailed analysis
        analysis_data = {
            "timestamp": "2025-01-17",
            "implementations": [
                {
                    "name": result.name,
                    "path": result.path,
                    "features": result.features,
                    "advancement_score": result.advancement_score,
                    "size_mb": result.size_mb,
                    "build_files_count": len(result.build_files),
                    "ui_components_count": len(result.ui_components)
                }
                for result in analysis_results
            ],
            "recommendation": {
                "most_advanced": most_advanced.name,
                "score": most_advanced.advancement_score,
                "reasoning": "Highest advancement score based on modern Android features"
            }
        }
        
        with open('/Users/Subho/android_comparison_report.json', 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: /Users/Subho/android_comparison_report.json")
    
    return analysis_results

if __name__ == "__main__":
    results = compare_android_implementations()