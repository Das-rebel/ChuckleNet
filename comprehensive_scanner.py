#!/usr/bin/env python3
"""
Comprehensive Project Scanner for Second Brain Android Analysis
Phase 1: Complete Project Inventory - Systematic file categorization
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class ProjectScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            'scan_timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'file_inventory': {},
            'component_analysis': {},
            'disabled_files': [],
            'missing_files': [],
            'integration_points': {},
            'summary': {}
        }
    
    def scan_project_structure(self) -> Dict[str, Any]:
        """Scan entire project structure and categorize files"""
        print("🔍 Scanning project structure...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip node_modules and other irrelevant directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                # Categorize file
                category = self._categorize_file(file_path)
                
                self.results['file_inventory'][str(relative_path)] = {
                    'absolute_path': str(file_path),
                    'relative_path': str(relative_path),
                    'category': category,
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if file_path.exists() else None,
                    'status': self._determine_file_status(file_path)
                }
        
        return self.results['file_inventory']
    
    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on path and extension"""
        path_str = str(file_path)
        
        if 'src/screens' in path_str:
            return 'screen'
        elif 'src/components' in path_str:
            return 'component'
        elif 'src/ui' in path_str:
            return 'ui_component'
        elif 'src/lib' in path_str:
            return 'library'
        elif 'src/hooks' in path_str:
            return 'hook'
        elif 'src/types' in path_str:
            return 'type_definition'
        elif 'android' in path_str and file_path.suffix == '.kt':
            return 'android_native'
        elif file_path.suffix == '.tsx':
            return 'react_component'
        elif file_path.suffix == '.ts':
            return 'typescript'
        elif file_path.suffix == '.json':
            return 'configuration'
        elif file_path.suffix == '.md':
            return 'documentation'
        else:
            return 'other'
    
    def _determine_file_status(self, file_path: Path) -> str:
        """Determine if file is active, disabled, or missing"""
        if not file_path.exists():
            return 'missing'
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for disabled indicators
            if any(indicator in content.lower() for indicator in [
                'disabled', 'commented out', '// todo', '// fixme', 
                'placeholder', 'mock', 'temporary'
            ]):
                return 'disabled'
            
            # Check for empty or minimal content
            if len(content.strip()) < 50:
                return 'minimal'
                
            return 'active'
            
        except Exception as e:
            return f'error: {str(e)}'
    
    def analyze_react_components(self) -> Dict[str, Any]:
        """Deep analysis of React components"""
        print("⚛️ Analyzing React components...")
        
        components = {}
        
        for file_path, file_info in self.results['file_inventory'].items():
            if file_info['category'] in ['screen', 'component', 'ui_component'] and file_path.endswith('.tsx'):
                component_analysis = self._analyze_component(Path(self.project_root) / file_path)
                if component_analysis:
                    components[file_path] = component_analysis
        
        self.results['component_analysis'] = components
        return components
    
    def _analyze_component(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze individual React component"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                'name': self._extract_component_name(content),
                'props': self._extract_props(content),
                'imports': self._extract_imports(content),
                'exports': self._extract_exports(content),
                'hooks_used': self._extract_hooks(content),
                'complexity_score': self._calculate_complexity(content),
                'dependencies': self._extract_dependencies(content),
                'status': self._determine_file_status(file_path)
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_component_name(self, content: str) -> str:
        """Extract component name from content"""
        # Look for default export
        default_export_match = re.search(r'export default function (\w+)', content)
        if default_export_match:
            return default_export_match.group(1)
        
        # Look for named export
        named_export_match = re.search(r'export function (\w+)', content)
        if named_export_match:
            return named_export_match.group(1)
        
        return 'Unknown'
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract component props"""
        props_match = re.search(r'interface (\w+)Props\s*\{([^}]+)\}', content, re.DOTALL)
        if props_match:
            props_content = props_match.group(2)
            return [prop.strip().split(':')[0].strip() for prop in props_content.split('\n') if ':' in prop]
        return []
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = re.findall(r'import .+ from [\'"]([^\'"]+)[\'"]', content)
        return imports
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract export statements"""
        exports = re.findall(r'export (?:default )?(?:function|const|class) (\w+)', content)
        return exports
    
    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used"""
        hooks = re.findall(r'use(\w+)', content)
        return list(set(hooks))
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate component complexity score"""
        score = 0
        score += len(re.findall(r'useState|useEffect|useCallback|useMemo', content)) * 2
        score += len(re.findall(r'if\s*\(|for\s*\(|while\s*\(', content)) * 1
        score += len(re.findall(r'<[A-Z]\w+', content)) * 1  # JSX components
        return score
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract component dependencies"""
        dependencies = []
        
        # Look for component imports
        component_imports = re.findall(r'import (\w+) from [\'"]\.\./', content)
        dependencies.extend(component_imports)
        
        # Look for hook imports
        hook_imports = re.findall(r'import \{([^}]+)\} from [\'"]react', content)
        if hook_imports:
            dependencies.extend([hook.strip() for hook in hook_imports[0].split(',')])
        
        return dependencies
    
    def identify_disabled_files(self) -> List[str]:
        """Identify files that are disabled or incomplete"""
        print("🚫 Identifying disabled files...")
        
        disabled_files = []
        
        for file_path, file_info in self.results['file_inventory'].items():
            if file_info['status'] in ['disabled', 'minimal']:
                disabled_files.append(file_path)
        
        self.results['disabled_files'] = disabled_files
        return disabled_files
    
    def map_integration_points(self) -> Dict[str, Any]:
        """Map integration points and dependencies"""
        print("🔗 Mapping integration points...")
        
        integration_map = {
            'screen_dependencies': {},
            'component_dependencies': {},
            'external_dependencies': {},
            'missing_integrations': []
        }
        
        # Analyze screen dependencies
        for file_path, file_info in self.results['file_inventory'].items():
            if file_info['category'] == 'screen':
                screen_deps = self._analyze_screen_dependencies(Path(self.project_root) / file_path)
                integration_map['screen_dependencies'][file_path] = screen_deps
        
        # Analyze component dependencies
        for file_path, file_info in self.results['file_inventory'].items():
            if file_info['category'] in ['component', 'ui_component']:
                comp_deps = self._analyze_component_dependencies(Path(self.project_root) / file_path)
                integration_map['component_dependencies'][file_path] = comp_deps
        
        self.results['integration_points'] = integration_map
        return integration_map
    
    def _analyze_screen_dependencies(self, file_path: Path) -> Dict[str, Any]:
        """Analyze dependencies for a screen"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {
                'imports': self._extract_imports(content),
                'components_used': re.findall(r'<(\w+)', content),
                'hooks_used': self._extract_hooks(content),
                'navigation': 'navigation' in content.lower(),
                'api_calls': len(re.findall(r'fetch\(|axios\.|api\.', content))
            }
            
            return dependencies
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_component_dependencies(self, file_path: Path) -> Dict[str, Any]:
        """Analyze dependencies for a component"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = {
                'imports': self._extract_imports(content),
                'props_interface': 'Props' in content,
                'state_management': len(re.findall(r'useState|useReducer', content)),
                'side_effects': len(re.findall(r'useEffect', content)),
                'external_libs': [imp for imp in self._extract_imports(content) if not imp.startswith('.')]
            }
            
            return dependencies
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive project summary"""
        print("📊 Generating project summary...")
        
        total_files = len(self.results['file_inventory'])
        active_files = len([f for f in self.results['file_inventory'].values() if f['status'] == 'active'])
        disabled_files = len(self.results['disabled_files'])
        missing_files = len([f for f in self.results['file_inventory'].values() if f['status'] == 'missing'])
        
        category_counts = {}
        for file_info in self.results['file_inventory'].values():
            category = file_info['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        self.results['summary'] = {
            'total_files': total_files,
            'active_files': active_files,
            'disabled_files': disabled_files,
            'missing_files': missing_files,
            'completion_percentage': round((active_files / total_files) * 100, 2) if total_files > 0 else 0,
            'category_breakdown': category_counts,
            'complexity_distribution': self._analyze_complexity_distribution(),
            'integration_readiness': self._assess_integration_readiness()
        }
        
        return self.results['summary']
    
    def _analyze_complexity_distribution(self) -> Dict[str, int]:
        """Analyze complexity distribution of components"""
        complexity_dist = {'low': 0, 'medium': 0, 'high': 0}
        
        for comp_analysis in self.results['component_analysis'].values():
            score = comp_analysis.get('complexity_score', 0)
            if score < 5:
                complexity_dist['low'] += 1
            elif score < 15:
                complexity_dist['medium'] += 1
            else:
                complexity_dist['high'] += 1
        
        return complexity_dist
    
    def _assess_integration_readiness(self) -> Dict[str, Any]:
        """Assess integration readiness"""
        readiness = {
            'screens_ready': 0,
            'components_ready': 0,
            'apis_integrated': 0,
            'navigation_setup': 0,
            'state_management': 0
        }
        
        for file_path, file_info in self.results['file_inventory'].items():
            if file_info['category'] == 'screen' and file_info['status'] == 'active':
                readiness['screens_ready'] += 1
            
            if file_info['category'] in ['component', 'ui_component'] and file_info['status'] == 'active':
                readiness['components_ready'] += 1
        
        return readiness
    
    def save_results(self, output_path: str = None) -> str:
        """Save analysis results to JSON file"""
        if not output_path:
            output_path = self.project_root / 'project_analysis_results.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print analysis summary"""
        summary = self.results['summary']
        
        print("\n" + "="*60)
        print("📊 PROJECT ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Files: {summary['total_files']}")
        print(f"Active Files: {summary['active_files']}")
        print(f"Disabled Files: {summary['disabled_files']}")
        print(f"Missing Files: {summary['missing_files']}")
        print(f"Completion: {summary['completion_percentage']}%")
        
        print("\n📁 Category Breakdown:")
        for category, count in summary['category_breakdown'].items():
            print(f"  {category}: {count}")
        
        print("\n🧩 Complexity Distribution:")
        for level, count in summary['complexity_distribution'].items():
            print(f"  {level}: {count}")
        
        print("\n🔗 Integration Readiness:")
        for aspect, count in summary['integration_readiness'].items():
            print(f"  {aspect}: {count}")

def main():
    """Main execution function"""
    project_root = "/Users/Subho/spark-thread-stationery-ui-99/monorepo/apps/mobile"
    
    print("🚀 Starting Comprehensive Project Analysis")
    print(f"📁 Project Root: {project_root}")
    
    scanner = ProjectScanner(project_root)
    
    # Phase 1: Complete Project Inventory
    print("\n📋 Phase 1: Complete Project Inventory")
    scanner.scan_project_structure()
    
    # Phase 2: Component Analysis
    print("\n⚛️ Phase 2: React Component Analysis")
    scanner.analyze_react_components()
    
    # Phase 3: Disabled Files Identification
    print("\n🚫 Phase 3: Disabled Files Identification")
    scanner.identify_disabled_files()
    
    # Phase 4: Integration Mapping
    print("\n🔗 Phase 4: Integration Points Mapping")
    scanner.map_integration_points()
    
    # Phase 5: Summary Generation
    print("\n📊 Phase 5: Summary Generation")
    scanner.generate_summary()
    
    # Save and display results
    output_file = scanner.save_results()
    scanner.print_summary()
    
    print(f"\n✅ Analysis complete! Results saved to: {output_file}")
    
    return scanner.results

if __name__ == "__main__":
    results = main()