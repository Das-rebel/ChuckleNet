#!/usr/bin/env python3
"""
Feature Comparator for Second Brain Web vs Android Analysis
Phase 2: Web Reference Mapping - Feature-by-feature comparison
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class FeatureComparator:
    def __init__(self, web_root: str, android_root: str):
        self.web_root = Path(web_root)
        self.android_root = Path(android_root)
        self.results = {
            'comparison_timestamp': datetime.now().isoformat(),
            'web_root': str(self.web_root),
            'android_root': str(self.android_root),
            'feature_matrix': {},
            'missing_features': [],
            'implemented_features': [],
            'partial_features': [],
            'web_components': {},
            'android_components': {},
            'gap_analysis': {},
            'implementation_priority': {}
        }
    
    def analyze_web_components(self) -> Dict[str, Any]:
        """Analyze all web components and features"""
        print("🌐 Analyzing web components...")
        
        web_components = {}
        
        # Analyze pages
        pages_dir = self.web_root / "src" / "pages"
        if pages_dir.exists():
            for page_file in pages_dir.glob("*.tsx"):
                component_analysis = self._analyze_web_component(page_file, 'page')
                if component_analysis:
                    web_components[f"pages/{page_file.name}"] = component_analysis
        
        # Analyze components
        components_dir = self.web_root / "src" / "components"
        if components_dir.exists():
            for component_file in components_dir.rglob("*.tsx"):
                relative_path = component_file.relative_to(self.web_root / "src")
                component_analysis = self._analyze_web_component(component_file, 'component')
                if component_analysis:
                    web_components[str(relative_path)] = component_analysis
        
        self.results['web_components'] = web_components
        return web_components
    
    def _analyze_web_component(self, file_path: Path, component_type: str) -> Optional[Dict[str, Any]]:
        """Analyze individual web component"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'type': component_type,
                'name': self._extract_component_name(content),
                'features': self._extract_features(content),
                'props': self._extract_props(content),
                'hooks': self._extract_hooks(content),
                'imports': self._extract_imports(content),
                'complexity': self._calculate_complexity(content),
                'ui_elements': self._extract_ui_elements(content),
                'functionality': self._extract_functionality(content),
                'dependencies': self._extract_dependencies(content),
                'lines_of_code': len(content.split('\n'))
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing web component {file_path}: {e}")
            return None
    
    def _extract_features(self, content: str) -> List[str]:
        """Extract features from component content"""
        features = []
        
        # Look for feature indicators
        feature_patterns = [
            r'// Feature:\s*(.+)',
            r'/\*\s*Feature:\s*(.+?)\s*\*/',
            r'className="([^"]*feature[^"]*)"',
            r'data-feature="([^"]*)"'
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            features.extend(matches)
        
        # Look for component-specific features
        if 'UniversalCapture' in content:
            features.extend(['smart_capture', 'url_capture', 'voice_capture', 'visual_capture'])
        if 'AIChat' in content:
            features.extend(['ai_chat', 'conversation', 'context_aware'])
        if 'Search' in content:
            features.extend(['search', 'filters', 'semantic_search'])
        if 'Review' in content:
            features.extend(['spaced_repetition', 'review_system', 'learning'])
        if 'Twitter' in content:
            features.extend(['social', 'tweets', 'threads', 'messaging'])
        
        return list(set(features))
    
    def _extract_ui_elements(self, content: str) -> List[str]:
        """Extract UI elements used in component"""
        ui_elements = []
        
        # Common UI elements
        ui_patterns = [
            r'<(\w+Button)',
            r'<(\w+Card)',
            r'<(\w+Input)',
            r'<(\w+Modal)',
            r'<(\w+Dialog)',
            r'<(\w+Dropdown)',
            r'<(\w+Tab)',
            r'<(\w+Accordion)',
            r'<(\w+Progress)',
            r'<(\w+Badge)',
            r'<(\w+Avatar)',
            r'<(\w+Tooltip)'
        ]
        
        for pattern in ui_patterns:
            matches = re.findall(pattern, content)
            ui_elements.extend(matches)
        
        return list(set(ui_elements))
    
    def _extract_functionality(self, content: str) -> List[str]:
        """Extract functionality from component"""
        functionality = []
        
        # Look for function definitions
        functions = re.findall(r'const (\w+)\s*=', content)
        functionality.extend(functions)
        
        # Look for event handlers
        handlers = re.findall(r'on(\w+)\s*=', content)
        functionality.extend([f"handle_{handler.lower()}" for handler in handlers])
        
        # Look for API calls
        if 'fetch(' in content or 'axios.' in content:
            functionality.append('api_integration')
        
        # Look for state management
        if 'useState' in content:
            functionality.append('state_management')
        if 'useEffect' in content:
            functionality.append('side_effects')
        if 'useContext' in content:
            functionality.append('context_management')
        
        return list(set(functionality))
    
    def analyze_android_components(self) -> Dict[str, Any]:
        """Analyze all Android components and features"""
        print("📱 Analyzing Android components...")
        
        android_components = {}
        
        # Analyze screens
        screens_dir = self.android_root / "src" / "screens"
        if screens_dir.exists():
            for screen_file in screens_dir.glob("*.tsx"):
                component_analysis = self._analyze_android_component(screen_file, 'screen')
                if component_analysis:
                    android_components[f"screens/{screen_file.name}"] = component_analysis
        
        # Analyze UI components
        ui_dir = self.android_root / "src" / "ui"
        if ui_dir.exists():
            for ui_file in ui_dir.glob("*.tsx"):
                component_analysis = self._analyze_android_component(ui_file, 'ui_component')
                if component_analysis:
                    android_components[f"ui/{ui_file.name}"] = component_analysis
        
        # Analyze other components
        components_dir = self.android_root / "src"
        for component_file in components_dir.rglob("*.tsx"):
            if component_file.parent.name not in ['screens', 'ui']:
                relative_path = component_file.relative_to(self.android_root / "src")
                component_analysis = self._analyze_android_component(component_file, 'component')
                if component_analysis:
                    android_components[str(relative_path)] = component_analysis
        
        self.results['android_components'] = android_components
        return android_components
    
    def _analyze_android_component(self, file_path: Path, component_type: str) -> Optional[Dict[str, Any]]:
        """Analyze individual Android component"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'type': component_type,
                'name': self._extract_component_name(content),
                'features': self._extract_features(content),
                'props': self._extract_props(content),
                'hooks': self._extract_hooks(content),
                'imports': self._extract_imports(content),
                'complexity': self._calculate_complexity(content),
                'ui_elements': self._extract_ui_elements(content),
                'functionality': self._extract_functionality(content),
                'dependencies': self._extract_dependencies(content),
                'lines_of_code': len(content.split('\n')),
                'mobile_specific': self._extract_mobile_features(content)
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing Android component {file_path}: {e}")
            return None
    
    def _extract_mobile_features(self, content: str) -> List[str]:
        """Extract mobile-specific features"""
        mobile_features = []
        
        if 'TouchableOpacity' in content:
            mobile_features.append('touch_interaction')
        if 'ScrollView' in content:
            mobile_features.append('scrolling')
        if 'Dimensions' in content:
            mobile_features.append('responsive_design')
        if 'Platform' in content:
            mobile_features.append('platform_specific')
        if 'Vibration' in content:
            mobile_features.append('haptic_feedback')
        if 'Alert' in content:
            mobile_features.append('native_alerts')
        if 'Share' in content:
            mobile_features.append('native_sharing')
        
        return mobile_features
    
    def create_feature_matrix(self) -> Dict[str, Any]:
        """Create comprehensive feature comparison matrix"""
        print("📊 Creating feature comparison matrix...")
        
        web_features = self._extract_all_features(self.results['web_components'])
        android_features = self._extract_all_features(self.results['android_components'])
        
        feature_matrix = {}
        
        # Compare each web feature against Android implementation
        for feature in web_features:
            feature_matrix[feature] = {
                'web_implementation': self._find_web_implementations(feature),
                'android_implementation': self._find_android_implementations(feature),
                'status': self._determine_feature_status(feature),
                'completeness': self._calculate_feature_completeness(feature),
                'priority': self._calculate_feature_priority(feature)
            }
        
        self.results['feature_matrix'] = feature_matrix
        return feature_matrix
    
    def _extract_all_features(self, components: Dict[str, Any]) -> List[str]:
        """Extract all unique features from components"""
        all_features = set()
        
        for component in components.values():
            features = component.get('features', [])
            functionality = component.get('functionality', [])
            ui_elements = component.get('ui_elements', [])
            
            all_features.update(features)
            all_features.update(functionality)
            all_features.update(ui_elements)
        
        return list(all_features)
    
    def _find_web_implementations(self, feature: str) -> List[str]:
        """Find web components that implement a feature"""
        implementations = []
        
        for path, component in self.results['web_components'].items():
            if feature in component.get('features', []) or feature in component.get('functionality', []):
                implementations.append(path)
        
        return implementations
    
    def _find_android_implementations(self, feature: str) -> List[str]:
        """Find Android components that implement a feature"""
        implementations = []
        
        for path, component in self.results['android_components'].items():
            if feature in component.get('features', []) or feature in component.get('functionality', []):
                implementations.append(path)
        
        return implementations
    
    def _determine_feature_status(self, feature: str) -> str:
        """Determine implementation status of a feature"""
        web_impl = self._find_web_implementations(feature)
        android_impl = self._find_android_implementations(feature)
        
        if web_impl and android_impl:
            return 'implemented'
        elif web_impl and not android_impl:
            return 'missing'
        elif not web_impl and android_impl:
            return 'android_only'
        else:
            return 'not_found'
    
    def _calculate_feature_completeness(self, feature: str) -> float:
        """Calculate completeness percentage for a feature"""
        web_impl = self._find_web_implementations(feature)
        android_impl = self._find_android_implementations(feature)
        
        if not web_impl:
            return 0.0
        
        # Simple completeness calculation
        if android_impl:
            return 1.0
        else:
            return 0.0
    
    def _calculate_feature_priority(self, feature: str) -> str:
        """Calculate priority level for implementing a feature"""
        # Core features get high priority
        core_features = ['universal_capture', 'ai_chat', 'search', 'review_system', 'knowledge_management']
        
        if feature in core_features:
            return 'high'
        elif 'social' in feature or 'twitter' in feature:
            return 'medium'
        else:
            return 'low'
    
    def generate_gap_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive gap analysis"""
        print("🔍 Generating gap analysis...")
        
        gap_analysis = {
            'missing_features': [],
            'implemented_features': [],
            'partial_features': [],
            'android_only_features': [],
            'implementation_roadmap': {},
            'effort_estimation': {}
        }
        
        for feature, matrix in self.results['feature_matrix'].items():
            status = matrix['status']
            completeness = matrix['completeness']
            
            if status == 'missing':
                gap_analysis['missing_features'].append({
                    'feature': feature,
                    'priority': matrix['priority'],
                    'web_implementations': matrix['web_implementation'],
                    'effort_estimate': self._estimate_implementation_effort(feature)
                })
            elif status == 'implemented':
                gap_analysis['implemented_features'].append(feature)
            elif completeness > 0 and completeness < 1:
                gap_analysis['partial_features'].append({
                    'feature': feature,
                    'completeness': completeness,
                    'android_implementations': matrix['android_implementation']
                })
            elif status == 'android_only':
                gap_analysis['android_only_features'].append(feature)
        
        # Sort by priority
        gap_analysis['missing_features'].sort(key=lambda x: x['priority'], reverse=True)
        
        self.results['gap_analysis'] = gap_analysis
        return gap_analysis
    
    def _estimate_implementation_effort(self, feature: str) -> str:
        """Estimate implementation effort for a feature"""
        # Simple effort estimation based on feature complexity
        complex_features = ['knowledge_graph_3d', 'workflow_automation', 'ai_processing_pipeline']
        medium_features = ['twitter_integration', 'social_features', 'advanced_search']
        
        if feature in complex_features:
            return 'high (2-4 weeks)'
        elif feature in medium_features:
            return 'medium (1-2 weeks)'
        else:
            return 'low (3-5 days)'
    
    def generate_implementation_roadmap(self) -> Dict[str, Any]:
        """Generate implementation roadmap"""
        print("🗺️ Generating implementation roadmap...")
        
        roadmap = {
            'phase_1_core': [],
            'phase_2_enhancement': [],
            'phase_3_advanced': [],
            'phase_4_polish': [],
            'timeline_estimate': {},
            'resource_requirements': {}
        }
        
        gap_analysis = self.results['gap_analysis']
        
        # Phase 1: Core missing features (high priority)
        roadmap['phase_1_core'] = [
            feature for feature in gap_analysis['missing_features']
            if feature['priority'] == 'high'
        ]
        
        # Phase 2: Enhancement features (medium priority)
        roadmap['phase_2_enhancement'] = [
            feature for feature in gap_analysis['missing_features']
            if feature['priority'] == 'medium'
        ]
        
        # Phase 3: Advanced features (low priority)
        roadmap['phase_3_advanced'] = [
            feature for feature in gap_analysis['missing_features']
            if feature['priority'] == 'low'
        ]
        
        # Phase 4: Polish and optimization
        roadmap['phase_4_polish'] = gap_analysis['partial_features']
        
        # Timeline estimation
        total_effort = 0
        for phase_features in [roadmap['phase_1_core'], roadmap['phase_2_enhancement'], roadmap['phase_3_advanced']]:
            phase_effort = 0
            for feature in phase_features:
                effort_str = feature.get('effort_estimate', 'low (3-5 days)')
                if 'high' in effort_str:
                    phase_effort += 3  # weeks
                elif 'medium' in effort_str:
                    phase_effort += 1.5  # weeks
                else:
                    phase_effort += 0.5  # weeks
            total_effort += phase_effort
        
        roadmap['timeline_estimate'] = {
            'total_weeks': total_effort,
            'phase_1_weeks': sum(3 if 'high' in f.get('effort_estimate', '') else 1.5 if 'medium' in f.get('effort_estimate', '') else 0.5 for f in roadmap['phase_1_core']),
            'phase_2_weeks': sum(3 if 'high' in f.get('effort_estimate', '') else 1.5 if 'medium' in f.get('effort_estimate', '') else 0.5 for f in roadmap['phase_2_enhancement']),
            'phase_3_weeks': sum(3 if 'high' in f.get('effort_estimate', '') else 1.5 if 'medium' in f.get('effort_estimate', '') else 0.5 for f in roadmap['phase_3_advanced'])
        }
        
        self.results['implementation_priority'] = roadmap
        return roadmap
    
    def save_results(self, output_path: str = None) -> str:
        """Save comparison results to JSON file"""
        if not output_path:
            output_path = Path(self.android_root).parent / 'feature_comparison_results.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Comparison results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print comparison summary"""
        gap_analysis = self.results['gap_analysis']
        roadmap = self.results['implementation_priority']
        
        print("\n" + "="*60)
        print("📊 FEATURE COMPARISON SUMMARY")
        print("="*60)
        print(f"Total Features Analyzed: {len(self.results['feature_matrix'])}")
        print(f"Implemented Features: {len(gap_analysis['implemented_features'])}")
        print(f"Missing Features: {len(gap_analysis['missing_features'])}")
        print(f"Partial Features: {len(gap_analysis['partial_features'])}")
        print(f"Android-Only Features: {len(gap_analysis['android_only_features'])}")
        
        print("\n🚫 Missing Features (High Priority):")
        for feature in gap_analysis['missing_features'][:10]:  # Show top 10
            if feature['priority'] == 'high':
                print(f"  • {feature['feature']} ({feature['effort_estimate']})")
        
        print("\n📅 Implementation Timeline:")
        timeline = roadmap['timeline_estimate']
        print(f"  Phase 1 (Core): {timeline['phase_1_weeks']:.1f} weeks")
        print(f"  Phase 2 (Enhancement): {timeline['phase_2_weeks']:.1f} weeks")
        print(f"  Phase 3 (Advanced): {timeline['phase_3_weeks']:.1f} weeks")
        print(f"  Total Estimated: {timeline['total_weeks']:.1f} weeks")

def main():
    """Main execution function"""
    web_root = "/Users/Subho/spark-thread-stationery-ui-99/monorepo/apps/web"
    android_root = "/Users/Subho/spark-thread-stationery-ui-99/monorepo/apps/mobile"
    
    print("🚀 Starting Feature Comparison Analysis")
    print(f"🌐 Web Root: {web_root}")
    print(f"📱 Android Root: {android_root}")
    
    comparator = FeatureComparator(web_root, android_root)
    
    # Analyze web components
    print("\n🌐 Phase 1: Analyzing Web Components")
    comparator.analyze_web_components()
    
    # Analyze Android components
    print("\n📱 Phase 2: Analyzing Android Components")
    comparator.analyze_android_components()
    
    # Create feature matrix
    print("\n📊 Phase 3: Creating Feature Matrix")
    comparator.create_feature_matrix()
    
    # Generate gap analysis
    print("\n🔍 Phase 4: Generating Gap Analysis")
    comparator.generate_gap_analysis()
    
    # Generate implementation roadmap
    print("\n🗺️ Phase 5: Generating Implementation Roadmap")
    comparator.generate_implementation_roadmap()
    
    # Save and display results
    output_file = comparator.save_results()
    comparator.print_summary()
    
    print(f"\n✅ Feature comparison complete! Results saved to: {output_file}")
    
    return comparator.results

if __name__ == "__main__":
    results = main()