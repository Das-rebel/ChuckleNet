#!/usr/bin/env python3
"""
Smart AI Unified CLI - Final Integration
Combines legacy positional interface with modern subcommand structure
Integrates SmartAIBackend with enhanced file and project awareness capabilities
Includes TreeQuest-generated components for comprehensive code analysis
"""

import os
import sys
import subprocess
import argparse
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional, Any, List

# Add TreeQuest paths
sys.path.append('/Users/Subho/CascadeProjects/enhanced-treequest')
sys.path.append('/Users/Subho/CascadeProjects/multi-ai-treequest')

# Import the SmartAIBackend
try:
    from smart_ai_backend import SmartAIBackend
except ImportError:
    print("⚠️  SmartAIBackend not available - some features may be limited")
    SmartAIBackend = None

# TreeQuest Component Classes (Integrated)
class FileAnalyzer:
    """Enhanced File Analyzer with multi-language support"""
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.jsx': 'JavaScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C',
        '.hpp': 'C++',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.zsh': 'Shell',
        '.fish': 'Shell',
        '.sql': 'SQL',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.txt': 'Text',
        '.dockerfile': 'Docker',
        '.makefile': 'Makefile',
        '.cmake': 'CMake',
        '.gradle': 'Gradle',
        '.maven': 'Maven'
    }

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_extension = self._get_file_extension(file_path)
        self.language = self._detect_language()
        self.file_size = self._get_file_size()

    def _get_file_extension(self, file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        return ext.lower()

    def _detect_language(self) -> Optional[str]:
        return self.SUPPORTED_EXTENSIONS.get(self.file_extension)

    def _get_file_size(self) -> int:
        try:
            return os.path.getsize(self.file_path)
        except OSError:
            return 0

    def get_basic_info(self) -> Dict[str, Any]:
        """Get basic file information without AI analysis"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                line_count = len(content.splitlines())
                char_count = len(content)
                word_count = len(content.split())
        except Exception:
            line_count = char_count = word_count = 0

        return {
            'file_path': self.file_path,
            'language': self.language or 'Unknown',
            'extension': self.file_extension,
            'size_bytes': self.file_size,
            'line_count': line_count,
            'character_count': char_count,
            'word_count': word_count,
            'supported': self.language is not None
        }

    def analyze_with_ai(self, backend) -> Dict[str, Any]:
        """Perform AI-powered analysis using the backend"""
        basic_info = self.get_basic_info()
        
        if not backend or not self.language:
            return basic_info

        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Use backend for AI analysis
            ai_analysis = backend.analyze_code_content(content, self.language)
            basic_info.update(ai_analysis)
            
        except Exception as e:
            basic_info['analysis_error'] = str(e)

        return basic_info


class ProjectAnalyzer:
    """Enhanced Project Analyzer with comprehensive project detection"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_types = []
        self.dependencies = {}
        self.structure = {}

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive project analysis"""
        results = {
            'project_path': str(self.project_path),
            'project_types': self.detect_project_types(),
            'structure': self.analyze_structure(),
            'dependencies': self.analyze_dependencies(),
            'files_summary': self.get_files_summary(),
            'size_analysis': self.get_size_analysis()
        }
        return results

    def detect_project_types(self) -> List[str]:
        """Detect multiple project types"""
        detected_types = []
        
        # Python projects
        if self._file_exists('requirements.txt') or self._file_exists('pyproject.toml') or self._file_exists('setup.py'):
            detected_types.append('Python')
            
        # Django
        if self._file_exists('manage.py'):
            detected_types.append('Django')
            
        # Flask
        if self._contains_in_files(['app.py', 'application.py'], 'flask'):
            detected_types.append('Flask')
            
        # Node.js
        if self._file_exists('package.json'):
            detected_types.append('Node.js')
            
        # React
        if self._package_contains('react'):
            detected_types.append('React')
            
        # Vue.js
        if self._package_contains('vue'):
            detected_types.append('Vue.js')
            
        # Angular
        if self._file_exists('angular.json'):
            detected_types.append('Angular')
            
        # Java
        if self._file_exists('pom.xml'):
            detected_types.append('Maven/Java')
        if self._file_exists('build.gradle'):
            detected_types.append('Gradle/Java')
            
        # .NET
        if self._glob_exists('*.csproj') or self._glob_exists('*.sln'):
            detected_types.append('.NET')
            
        # Go
        if self._file_exists('go.mod'):
            detected_types.append('Go')
            
        # Rust
        if self._file_exists('Cargo.toml'):
            detected_types.append('Rust')
            
        # Ruby
        if self._file_exists('Gemfile'):
            detected_types.append('Ruby')
            
        # PHP
        if self._file_exists('composer.json'):
            detected_types.append('PHP')
            
        # Docker
        if self._file_exists('Dockerfile') or self._file_exists('docker-compose.yml'):
            detected_types.append('Docker')
            
        return detected_types if detected_types else ['Unknown']

    def _file_exists(self, filename: str) -> bool:
        return (self.project_path / filename).exists()

    def _glob_exists(self, pattern: str) -> bool:
        return len(list(self.project_path.glob(pattern))) > 0

    def _package_contains(self, dependency: str) -> bool:
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    return dependency in deps or dependency in dev_deps
            except Exception:
                pass
        return False

    def _contains_in_files(self, files: List[str], text: str) -> bool:
        for filename in files:
            file_path = self.project_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if text.lower() in f.read().lower():
                            return True
                except Exception:
                    pass
        return False

    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze project directory structure"""
        structure = {
            'total_files': 0,
            'total_directories': 0,
            'file_types': {},
            'max_depth': 0
        }
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                depth = root[len(str(self.project_path)):].count(os.sep)
                structure['max_depth'] = max(structure['max_depth'], depth)
                structure['total_directories'] += len(dirs)
                structure['total_files'] += len(files)
                
                for file in files:
                    _, ext = os.path.splitext(file)
                    ext = ext.lower()
                    structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                    
        except Exception as e:
            structure['error'] = str(e)
            
        return structure

    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {}
        
        # Python dependencies
        for req_file in ['requirements.txt', 'requirements-dev.txt', 'requirements-test.txt']:
            req_path = self.project_path / req_file
            if req_path.exists():
                dependencies[req_file] = self._parse_requirements(req_path)
        
        # Node.js dependencies
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            dependencies['package.json'] = self._parse_package_json(package_json)
        
        # Go dependencies
        go_mod = self.project_path / 'go.mod'
        if go_mod.exists():
            dependencies['go.mod'] = self._parse_go_mod(go_mod)
        
        # Rust dependencies
        cargo_toml = self.project_path / 'Cargo.toml'
        if cargo_toml.exists():
            dependencies['Cargo.toml'] = self._parse_cargo_toml(cargo_toml)
            
        return dependencies

    def _parse_requirements(self, file_path: Path) -> List[str]:
        try:
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception:
            return []

    def _parse_package_json(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {
                    'dependencies': data.get('dependencies', {}),
                    'devDependencies': data.get('devDependencies', {}),
                    'scripts': data.get('scripts', {})
                }
        except Exception:
            return {}

    def _parse_go_mod(self, file_path: Path) -> List[str]:
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                deps = []
                in_require = False
                for line in lines:
                    line = line.strip()
                    if line.startswith('require'):
                        in_require = True
                        continue
                    if in_require and line == ')':
                        break
                    if in_require and line:
                        deps.append(line)
                return deps
        except Exception:
            return []

    def _parse_cargo_toml(self, file_path: Path) -> Dict[str, str]:
        try:
            # Simple TOML parsing for Cargo.toml dependencies
            with open(file_path, 'r') as f:
                content = f.read()
                deps = {}
                in_deps = False
                for line in content.split('\n'):
                    line = line.strip()
                    if line == '[dependencies]':
                        in_deps = True
                        continue
                    if line.startswith('[') and line != '[dependencies]':
                        in_deps = False
                    if in_deps and '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            deps[parts[0].strip()] = parts[1].strip()
                return deps
        except Exception:
            return {}

    def get_files_summary(self) -> Dict[str, int]:
        """Get summary of file types and counts"""
        summary = {}
        try:
            for root, _, files in os.walk(self.project_path):
                for file in files:
                    _, ext = os.path.splitext(file)
                    ext = ext.lower() if ext else 'no_extension'
                    summary[ext] = summary.get(ext, 0) + 1
        except Exception:
            pass
        return summary

    def get_size_analysis(self) -> Dict[str, Any]:
        """Analyze project size"""
        total_size = 0
        file_count = 0
        try:
            for root, _, files in os.walk(self.project_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except OSError:
                        pass
        except Exception:
            pass
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'file_count': file_count,
            'average_file_size': round(total_size / file_count, 2) if file_count > 0 else 0
        }


class SmartAIUnified:
    """Unified Smart AI CLI with hybrid interface support and enhanced file/project awareness"""
    
    def __init__(self):
        self.claude_code_path = "/Users/Subho/.claude/local/claude"
        self.treequest_path = "/Users/Subho/CascadeProjects/enhanced-treequest"
        self.gemma_model = "gemma2:2b"
        self.session_log = Path.home() / ".smart-ai-session.json"
        self.token_usage_threshold = 0.9
        
        # Initialize SmartAIBackend if available
        self.backend = SmartAIBackend() if SmartAIBackend else None
        
        # Output format options
        self.output_formats = ['plain', 'json', 'markdown']
        self.current_format = 'plain'
        self.quiet_mode = False
        self.verbose_mode = False
    
    def detect_interface_mode(self, args: List[str]) -> str:
        """
        Detect whether user is using legacy or modern interface
        Returns: 'legacy', 'modern', or 'help'
        """
        if not args:
            return 'legacy'  # Interactive mode
        
        # Check for help flags first
        if args[0] in ['-h', '--help', 'help']:
            return 'help'
        
        # Look for modern subcommands anywhere in args (after global flags)
        modern_commands = ['ask', 'chat', 'providers', 'config', 'status', 'file', 'project']
        global_flags = ['--verbose', '-v', '--quiet', '-q', '--format']
        
        # Skip global flags and their values to find the actual command
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in modern_commands:
                return 'modern'
            
            # Skip global flags and their values
            if arg in global_flags:
                if arg == '--format' and i + 1 < len(args):
                    i += 2  # Skip flag and its value
                else:
                    i += 1  # Skip just the flag
            elif arg.startswith('--format='):
                i += 1  # Skip flag with embedded value
            elif arg in ['--verbose', '-v', '--quiet', '-q']:
                i += 1  # Skip boolean flags
            else:
                # This is not a global flag, check what it is
                if arg in modern_commands:
                    return 'modern'
                
                # Check for legacy flags
                legacy_flags = ['--claude', '--gemma', '--treequest', '--opendia', '--mcp', '--interactive', '-i']
                if arg in legacy_flags:
                    return 'legacy'
                
                # If it doesn't start with '-' and isn't a command, it's likely a prompt
                if not arg.startswith('-'):
                    return 'legacy'
                
                i += 1
        
        # Default to legacy for unknown patterns
        return 'legacy'
    
    def create_modern_parser(self):
        """Create argument parser for modern subcommand interface"""
        parser = argparse.ArgumentParser(
            prog='smart-ai',
            description="Smart AI Unified CLI - Intelligent AI provider switching and file/project awareness",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Modern Interface Examples:
  smart-ai ask "What is Python?"                 # Ask a question
  smart-ai ask "Analyze this code" --provider claude  # Force provider
  smart-ai ask "Quick question" --format json    # JSON output
  smart-ai chat                                  # Interactive chat
  smart-ai providers list                       # List providers
  smart-ai providers status                     # Check provider status
  smart-ai config get model                     # Get config value
  smart-ai status                               # Show system status

File Analysis Commands:
  smart-ai file analyze <file>                  # Analyze file structure
  smart-ai file explain <file>                  # AI-powered code explanation
  smart-ai file optimize <file>                 # Suggest optimizations
  smart-ai file test <file>                     # Generate test cases
  smart-ai file diff <file1> <file2>            # Compare files

Project Analysis Commands:
  smart-ai project analyze                      # Analyze project structure
  smart-ai project structure                    # Show project tree
  smart-ai project dependencies                 # Analyze dependencies
  smart-ai project readme                       # Generate README
  smart-ai project summarize                    # Create project summary

Legacy Interface Examples (backward compatible):
  smart-ai "What is Python?"                    # Direct prompt
  smart-ai --claude "Use Claude Code"           # Force provider
  smart-ai --interactive                        # Interactive mode
  smart-ai                                      # Interactive mode

Output Format Options:
  --format plain      # Clean text output (default)
  --format json       # JSON structured output  
  --format markdown   # Markdown formatted output

Verbosity Options:
  --quiet, -q         # Minimal output
  --verbose, -v       # Detailed output with provider info
            """
        )
        
        # Global options
        parser.add_argument('--verbose', '-v', action='store_true', 
                          help='Verbose output with provider details')
        parser.add_argument('--quiet', '-q', action='store_true',
                          help='Minimal output mode')
        parser.add_argument('--format', choices=self.output_formats, default='plain',
                          help='Output format (plain, json, markdown)')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Ask command - for single questions
        ask_parser = subparsers.add_parser('ask', help='Ask a question')
        ask_parser.add_argument('question', nargs='+', help='Question to ask')
        ask_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                               help='Force specific provider')
        ask_parser.add_argument('--timeout', type=int, default=60,
                               help='Timeout in seconds (default: 60)')
        
        # Chat command - for interactive conversations
        chat_parser = subparsers.add_parser('chat', help='Interactive chat mode')
        chat_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                                help='Preferred provider for chat session')
        
        # File commands
        file_parser = subparsers.add_parser('file', help='File analysis commands')
        file_subparsers = file_parser.add_subparsers(dest='file_action', help='File operations')
        
        # File analyze
        analyze_parser = file_subparsers.add_parser('analyze', help='Analyze file structure and content')
        analyze_parser.add_argument('file_path', help='Path to file to analyze')
        analyze_parser.add_argument('--ai', action='store_true', help='Use AI for deeper analysis')
        
        # File explain
        explain_parser = file_subparsers.add_parser('explain', help='AI-powered code explanation')
        explain_parser.add_argument('file_path', help='Path to file to explain')
        explain_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma'],
                                  help='Preferred AI provider for explanation')
        
        # File optimize
        optimize_parser = file_subparsers.add_parser('optimize', help='Suggest optimizations')
        optimize_parser.add_argument('file_path', help='Path to file to optimize')
        optimize_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma'],
                                   help='Preferred AI provider for optimization')
        
        # File test
        test_parser = file_subparsers.add_parser('test', help='Generate test cases')
        test_parser.add_argument('file_path', help='Path to file to generate tests for')
        test_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma'],
                                help='Preferred AI provider for test generation')
        
        # File diff
        diff_parser = file_subparsers.add_parser('diff', help='Compare files')
        diff_parser.add_argument('file1', help='First file path')
        diff_parser.add_argument('file2', help='Second file path')
        diff_parser.add_argument('--ai', action='store_true', help='Use AI for semantic comparison')
        
        # Project commands
        project_parser = subparsers.add_parser('project', help='Project analysis commands')
        project_subparsers = project_parser.add_subparsers(dest='project_action', help='Project operations')
        
        # Project analyze
        proj_analyze_parser = project_subparsers.add_parser('analyze', help='Analyze project structure')
        proj_analyze_parser.add_argument('--path', default='.', help='Project path (default: current directory)')
        
        # Project structure
        structure_parser = project_subparsers.add_parser('structure', help='Show project tree')
        structure_parser.add_argument('--path', default='.', help='Project path (default: current directory)')
        structure_parser.add_argument('--max-depth', type=int, default=3, help='Maximum depth to show')
        
        # Project dependencies
        deps_parser = project_subparsers.add_parser('dependencies', help='Analyze dependencies')
        deps_parser.add_argument('--path', default='.', help='Project path (default: current directory)')
        
        # Project readme
        readme_parser = project_subparsers.add_parser('readme', help='Generate README')
        readme_parser.add_argument('--path', default='.', help='Project path (default: current directory)')
        readme_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma'],
                                  help='Preferred AI provider for README generation')
        
        # Project summarize
        summarize_parser = project_subparsers.add_parser('summarize', help='Create project summary')
        summarize_parser.add_argument('--path', default='.', help='Project path (default: current directory)')
        summarize_parser.add_argument('--provider', choices=['claude_code', 'treequest', 'gemma'],
                                     help='Preferred AI provider for summarization')
        
        # Providers command - manage AI providers
        providers_parser = subparsers.add_parser('providers', help='Manage AI providers')
        providers_subparsers = providers_parser.add_subparsers(dest='providers_action')
        
        providers_subparsers.add_parser('list', help='List all available providers')
        providers_subparsers.add_parser('status', help='Check provider availability and status')
        providers_subparsers.add_parser('test', help='Test provider connectivity')
        
        test_parser = providers_subparsers.add_parser('test-provider', help='Test specific provider')
        test_parser.add_argument('provider', choices=['claude_code', 'treequest', 'gemma', 'opendia', 'mcp'],
                                help='Provider to test')
        
        # Config command - manage configuration  
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        get_parser = config_subparsers.add_parser('get', help='Get configuration value')
        get_parser.add_argument('key', help='Configuration key')
        
        set_parser = config_subparsers.add_parser('set', help='Set configuration value')
        set_parser.add_argument('key', help='Configuration key')
        set_parser.add_argument('value', help='Configuration value')
        
        config_subparsers.add_parser('list', help='List all configuration')
        config_subparsers.add_parser('reset', help='Reset configuration to defaults')
        
        # Status command - show system status
        status_parser = subparsers.add_parser('status', help='Show system and provider status')
        status_parser.add_argument('--detailed', action='store_true',
                                  help='Show detailed status information')
        
        return parser
    
    def create_legacy_parser(self):
        """Create argument parser for legacy interface"""
        parser = argparse.ArgumentParser(
            prog='smart-ai',
            description="Smart AI CLI - Intelligent switching between Claude Code, Gemma, and TreeQuest",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=False,  # We'll handle help manually
            epilog="""
Legacy Interface Examples:
  smart-ai                          # Interactive mode with smart switching
  smart-ai "What is Python?"        # Single query with smart routing
  smart-ai --claude                 # Force Claude Code mode
  smart-ai --gemma "Quick question"  # Force Gemma for quick questions
  smart-ai --treequest "Complex task" # Force TreeQuest for complex tasks
  
Interactive mode commands:
  /claude     - Switch to Claude Code
  /gemma      - Use Gemma for current query  
  /treequest  - Use TreeQuest for current query
  /status     - Show system status
  /help       - Show help
  /quit       - Exit interactive mode
        """
        )
        
        parser.add_argument("prompt", nargs="*", help="Prompt to process")
        parser.add_argument("--claude", action="store_true", help="Force use Claude Code")
        parser.add_argument("--gemma", action="store_true", help="Force use Gemma")
        parser.add_argument("--treequest", action="store_true", help="Force use TreeQuest")
        parser.add_argument("--opendia", action="store_true", help="Force use OpenDia")
        parser.add_argument("--mcp", action="store_true", help="Force use MCP tools")
        parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
        parser.add_argument("--format", choices=self.output_formats, default='plain',
                          help="Output format")
        parser.add_argument("--help", "-h", action="store_true", help="Show help")
        
        return parser
    
    def show_unified_help(self):
        """Show comprehensive help for both interfaces"""
        print("""
Smart AI Unified CLI - Final Integration with File & Project Awareness

🎯 MODERN INTERFACE (Recommended for new users):
   smart-ai ask "What is Python?"              # Ask a question
   smart-ai chat                               # Interactive chat mode
   smart-ai providers list                     # List all providers
   smart-ai status                             # Show system status
   smart-ai config get model                   # Configuration management

📁 FILE ANALYSIS COMMANDS:
   smart-ai file analyze <file>                # Analyze file structure and content
   smart-ai file explain <file>                # AI-powered code explanation
   smart-ai file optimize <file>               # Suggest optimizations
   smart-ai file test <file>                   # Generate test cases
   smart-ai file diff <file1> <file2>          # Compare files

🏗️ PROJECT ANALYSIS COMMANDS:
   smart-ai project analyze                    # Analyze project structure
   smart-ai project structure                  # Show project tree
   smart-ai project dependencies               # Analyze dependencies
   smart-ai project readme                     # Generate README
   smart-ai project summarize                  # Create project summary

🔄 LEGACY INTERFACE (Backward compatible):
   smart-ai "What is Python?"                  # Direct prompt
   smart-ai --claude "Use Claude specifically" # Force provider
   smart-ai --interactive                      # Interactive mode
   smart-ai                                    # Interactive mode

📊 UNIVERSAL OPTIONS (work with both interfaces):
   --format plain|json|markdown               # Output formatting
   --verbose, -v                              # Detailed output
   --quiet, -q                                # Minimal output

🔧 AVAILABLE PROVIDERS:
   claude_code    # Claude Code CLI (requires authentication)
   treequest      # Multi-provider TreeQuest system
   gemma          # Local Gemma 2B via Ollama
   opendia        # Browser automation tools
   mcp            # Model Context Protocol tools

🚀 SMART ROUTING:
   The system automatically selects the best provider based on:
   - Internet connectivity
   - Prompt analysis (file operations → MCP, browser tasks → OpenDia)
   - Provider availability
   - Performance characteristics

📋 INTERACTIVE MODE COMMANDS:
   /claude, /gemma, /treequest     # Force specific providers
   /status                         # Show system status
   /providers                      # List available providers
   /help                          # Show help
   /quit, /exit                   # Exit

For detailed help on any command:
   smart-ai <command> --help      # Modern interface
   smart-ai --help                # Legacy interface
        """)
    
    async def handle_modern_interface(self, args: List[str]) -> int:
        """Handle modern subcommand-based interface"""
        parser = self.create_modern_parser()
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1
        
        # Set global options
        self.current_format = parsed_args.format
        self.verbose_mode = parsed_args.verbose
        self.quiet_mode = parsed_args.quiet
        
        if not parsed_args.command:
            parser.print_help()
            return 0
        
        try:
            if parsed_args.command == 'ask':
                return await self.handle_ask_command(parsed_args)
            elif parsed_args.command == 'chat':
                return await self.handle_chat_command(parsed_args)
            elif parsed_args.command == 'file':
                return await self.handle_file_command(parsed_args)
            elif parsed_args.command == 'project':
                return await self.handle_project_command(parsed_args)
            elif parsed_args.command == 'providers':
                return await self.handle_providers_command(parsed_args)
            elif parsed_args.command == 'config':
                return await self.handle_config_command(parsed_args)
            elif parsed_args.command == 'status':
                return await self.handle_status_command(parsed_args)
            else:
                self.output_error(f"Unknown command: {parsed_args.command}")
                return 1
        
        except Exception as e:
            if self.verbose_mode:
                import traceback
                traceback.print_exc()
            else:
                self.output_error(f"Error: {e}")
            return 1
    
    async def handle_legacy_interface(self, args: List[str]) -> int:
        """Handle legacy positional argument interface"""
        parser = self.create_legacy_parser()
        
        try:
            parsed_args = parser.parse_args(args)
        except SystemExit:
            return 1
        
        # Set global options
        self.current_format = parsed_args.format
        self.verbose_mode = parsed_args.verbose
        self.quiet_mode = parsed_args.quiet
        
        if parsed_args.help:
            self.show_unified_help()
            return 0
        
        # Handle forced provider selection
        if parsed_args.claude:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else ""
            return await self.run_claude_code_with_prompt(prompt)
        elif parsed_args.gemma:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_gemma_ollama(prompt)
        elif parsed_args.treequest:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_treequest(prompt)
        elif parsed_args.opendia:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_opendia(prompt)
        elif parsed_args.mcp:
            prompt = " ".join(parsed_args.prompt) if parsed_args.prompt else "Hello"
            return await self.run_mcp(prompt)
        
        # Interactive mode or single command
        if not parsed_args.prompt or parsed_args.interactive:
            return await self.interactive_mode()
        else:
            return await self.run_single_command(parsed_args.prompt)
    
    # File Command Handlers
    async def handle_file_command(self, args) -> int:
        """Handle file analysis commands"""
        if not args.file_action:
            self.output_error("File action required. Use: analyze, explain, optimize, test, or diff")
            return 1
        
        try:
            if args.file_action == 'analyze':
                return await self.file_analyze(args.file_path, args.ai)
            elif args.file_action == 'explain':
                return await self.file_explain(args.file_path, getattr(args, 'provider', None))
            elif args.file_action == 'optimize':
                return await self.file_optimize(args.file_path, getattr(args, 'provider', None))
            elif args.file_action == 'test':
                return await self.file_test(args.file_path, getattr(args, 'provider', None))
            elif args.file_action == 'diff':
                return await self.file_diff(args.file1, args.file2, args.ai)
            else:
                self.output_error(f"Unknown file action: {args.file_action}")
                return 1
        except Exception as e:
            self.output_error(f"File operation error: {e}")
            return 1
    
    async def file_analyze(self, file_path: str, use_ai: bool = False) -> int:
        """Analyze a file"""
        if not os.path.exists(file_path):
            self.output_error(f"File not found: {file_path}")
            return 1
        
        try:
            analyzer = FileAnalyzer(file_path)
            
            if use_ai and self.backend:
                if self.verbose_mode:
                    self.output_info(f"Performing AI analysis of {file_path}")
                results = analyzer.analyze_with_ai(self.backend)
            else:
                if self.verbose_mode:
                    self.output_info(f"Performing basic analysis of {file_path}")
                results = analyzer.get_basic_info()
            
            self.format_and_output_data(results, "File Analysis")
            return 0
            
        except Exception as e:
            self.output_error(f"Analysis failed: {e}")
            return 1
    
    async def file_explain(self, file_path: str, provider: str = None) -> int:
        """Explain a file using AI"""
        if not os.path.exists(file_path):
            self.output_error(f"File not found: {file_path}")
            return 1
        
        if not self.backend:
            self.output_error("AI backend not available for explanations")
            return 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create explanation prompt
            prompt = f"Please explain this code file ({file_path}):\n\n{content[:2000]}..."
            
            provider = provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if self.verbose_mode:
                self.output_info(f"Explaining {file_path} using {provider}")
            
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(f"Code explanation for {file_path}", response, provider)
                return 0
            else:
                self.output_error("No explanation received")
                return 1
                
        except Exception as e:
            self.output_error(f"Explanation failed: {e}")
            return 1
    
    async def file_optimize(self, file_path: str, provider: str = None) -> int:
        """Suggest optimizations for a file"""
        if not os.path.exists(file_path):
            self.output_error(f"File not found: {file_path}")
            return 1
        
        if not self.backend:
            self.output_error("AI backend not available for optimization suggestions")
            return 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create optimization prompt
            prompt = f"Please suggest optimizations for this code file ({file_path}):\n\n{content[:2000]}..."
            
            provider = provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if self.verbose_mode:
                self.output_info(f"Analyzing optimizations for {file_path} using {provider}")
            
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(f"Optimization suggestions for {file_path}", response, provider)
                return 0
            else:
                self.output_error("No optimization suggestions received")
                return 1
                
        except Exception as e:
            self.output_error(f"Optimization analysis failed: {e}")
            return 1
    
    async def file_test(self, file_path: str, provider: str = None) -> int:
        """Generate test cases for a file"""
        if not os.path.exists(file_path):
            self.output_error(f"File not found: {file_path}")
            return 1
        
        if not self.backend:
            self.output_error("AI backend not available for test generation")
            return 1
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create test generation prompt
            prompt = f"Please generate comprehensive test cases for this code file ({file_path}):\n\n{content[:2000]}..."
            
            provider = provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if self.verbose_mode:
                self.output_info(f"Generating tests for {file_path} using {provider}")
            
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(f"Test cases for {file_path}", response, provider)
                return 0
            else:
                self.output_error("No test cases received")
                return 1
                
        except Exception as e:
            self.output_error(f"Test generation failed: {e}")
            return 1
    
    async def file_diff(self, file1: str, file2: str, use_ai: bool = False) -> int:
        """Compare two files"""
        if not os.path.exists(file1):
            self.output_error(f"File not found: {file1}")
            return 1
        if not os.path.exists(file2):
            self.output_error(f"File not found: {file2}")
            return 1
        
        try:
            if use_ai and self.backend:
                # AI-powered semantic comparison
                with open(file1, 'r', encoding='utf-8', errors='ignore') as f1:
                    content1 = f1.read()
                with open(file2, 'r', encoding='utf-8', errors='ignore') as f2:
                    content2 = f2.read()
                
                prompt = f"Please compare these two files and provide a semantic analysis of their differences:\n\nFile 1 ({file1}):\n{content1[:1000]}...\n\nFile 2 ({file2}):\n{content2[:1000]}..."
                
                provider = self.backend.handle_provider_fallback(prompt=prompt)
                
                if self.verbose_mode:
                    self.output_info(f"Performing AI-powered comparison using {provider}")
                
                response = await self.backend.process_request_async(prompt, provider)
                
                if response:
                    self.format_and_output_response(f"Semantic comparison: {file1} vs {file2}", response, provider)
                    return 0
                else:
                    self.output_error("No comparison result received")
                    return 1
            else:
                # Basic file comparison using diff
                if self.verbose_mode:
                    self.output_info(f"Performing basic diff between {file1} and {file2}")
                
                result = subprocess.run(['diff', '-u', file1, file2], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.output_success("Files are identical")
                elif result.returncode == 1:
                    if self.current_format == 'json':
                        output = {
                            "comparison": f"{file1} vs {file2}",
                            "status": "different",
                            "diff": result.stdout
                        }
                        print(json.dumps(output, indent=2))
                    else:
                        self.output_info(f"Differences between {file1} and {file2}:")
                        print(result.stdout)
                else:
                    self.output_error(f"Diff command failed: {result.stderr}")
                    return 1
                
                return 0
                
        except Exception as e:
            self.output_error(f"File comparison failed: {e}")
            return 1
    
    # Project Command Handlers
    async def handle_project_command(self, args) -> int:
        """Handle project analysis commands"""
        if not args.project_action:
            self.output_error("Project action required. Use: analyze, structure, dependencies, readme, or summarize")
            return 1
        
        try:
            project_path = getattr(args, 'path', '.')
            
            if args.project_action == 'analyze':
                return await self.project_analyze(project_path)
            elif args.project_action == 'structure':
                return await self.project_structure(project_path, getattr(args, 'max_depth', 3))
            elif args.project_action == 'dependencies':
                return await self.project_dependencies(project_path)
            elif args.project_action == 'readme':
                return await self.project_readme(project_path, getattr(args, 'provider', None))
            elif args.project_action == 'summarize':
                return await self.project_summarize(project_path, getattr(args, 'provider', None))
            else:
                self.output_error(f"Unknown project action: {args.project_action}")
                return 1
        except Exception as e:
            self.output_error(f"Project operation error: {e}")
            return 1
    
    async def project_analyze(self, project_path: str) -> int:
        """Analyze project structure and characteristics"""
        if not os.path.exists(project_path):
            self.output_error(f"Project path not found: {project_path}")
            return 1
        
        try:
            if self.verbose_mode:
                self.output_info(f"Analyzing project at {project_path}")
            
            analyzer = ProjectAnalyzer(project_path)
            results = analyzer.analyze()
            
            self.format_and_output_data(results, "Project Analysis")
            return 0
            
        except Exception as e:
            self.output_error(f"Project analysis failed: {e}")
            return 1
    
    async def project_structure(self, project_path: str, max_depth: int = 3) -> int:
        """Show project tree structure"""
        if not os.path.exists(project_path):
            self.output_error(f"Project path not found: {project_path}")
            return 1
        
        try:
            if self.verbose_mode:
                self.output_info(f"Showing structure for {project_path} (max depth: {max_depth})")
            
            # Use tree command if available, otherwise implement basic tree
            try:
                result = subprocess.run(['tree', '-L', str(max_depth), project_path], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    if self.current_format == 'json':
                        output = {
                            "project_path": project_path,
                            "max_depth": max_depth,
                            "structure": result.stdout
                        }
                        print(json.dumps(output, indent=2))
                    else:
                        self.output_info(f"Project structure for {project_path}:")
                        print(result.stdout)
                    return 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to basic directory listing
            structure = self._build_tree_structure(project_path, max_depth)
            self.format_and_output_data(structure, "Project Structure")
            return 0
            
        except Exception as e:
            self.output_error(f"Structure analysis failed: {e}")
            return 1
    
    def _build_tree_structure(self, path: str, max_depth: int, current_depth: int = 0) -> Dict[str, Any]:
        """Build a tree structure representation"""
        structure = {
            "name": os.path.basename(path) or path,
            "type": "directory" if os.path.isdir(path) else "file",
            "children": []
        }
        
        if current_depth >= max_depth or not os.path.isdir(path):
            return structure
        
        try:
            items = sorted(os.listdir(path))
            for item in items[:50]:  # Limit to prevent huge output
                if item.startswith('.'):
                    continue
                item_path = os.path.join(path, item)
                child = self._build_tree_structure(item_path, max_depth, current_depth + 1)
                structure["children"].append(child)
        except PermissionError:
            structure["error"] = "Permission denied"
        
        return structure
    
    async def project_dependencies(self, project_path: str) -> int:
        """Analyze project dependencies"""
        if not os.path.exists(project_path):
            self.output_error(f"Project path not found: {project_path}")
            return 1
        
        try:
            if self.verbose_mode:
                self.output_info(f"Analyzing dependencies for {project_path}")
            
            analyzer = ProjectAnalyzer(project_path)
            dependencies = analyzer.analyze_dependencies()
            
            if not dependencies:
                self.output_warning("No dependency files found")
                return 0
            
            self.format_and_output_data(dependencies, "Project Dependencies")
            return 0
            
        except Exception as e:
            self.output_error(f"Dependency analysis failed: {e}")
            return 1
    
    async def project_readme(self, project_path: str, provider: str = None) -> int:
        """Generate README for project"""
        if not os.path.exists(project_path):
            self.output_error(f"Project path not found: {project_path}")
            return 1
        
        if not self.backend:
            self.output_error("AI backend not available for README generation")
            return 1
        
        try:
            if self.verbose_mode:
                self.output_info(f"Generating README for {project_path}")
            
            # Analyze project first
            analyzer = ProjectAnalyzer(project_path)
            analysis = analyzer.analyze()
            
            # Create README generation prompt
            prompt = f"Please generate a comprehensive README.md for this project based on the following analysis:\n\n{json.dumps(analysis, indent=2)}"
            
            provider = provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if self.verbose_mode:
                self.output_info(f"Using {provider} for README generation")
            
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(f"Generated README for {project_path}", response, provider)
                return 0
            else:
                self.output_error("No README content received")
                return 1
                
        except Exception as e:
            self.output_error(f"README generation failed: {e}")
            return 1
    
    async def project_summarize(self, project_path: str, provider: str = None) -> int:
        """Create project summary"""
        if not os.path.exists(project_path):
            self.output_error(f"Project path not found: {project_path}")
            return 1
        
        if not self.backend:
            self.output_error("AI backend not available for project summarization")
            return 1
        
        try:
            if self.verbose_mode:
                self.output_info(f"Creating summary for {project_path}")
            
            # Analyze project first
            analyzer = ProjectAnalyzer(project_path)
            analysis = analyzer.analyze()
            
            # Create summarization prompt
            prompt = f"Please create a concise technical summary of this project based on the following analysis:\n\n{json.dumps(analysis, indent=2)}"
            
            provider = provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if self.verbose_mode:
                self.output_info(f"Using {provider} for project summarization")
            
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(f"Project summary for {project_path}", response, provider)
                return 0
            else:
                self.output_error("No summary received")
                return 1
                
        except Exception as e:
            self.output_error(f"Project summarization failed: {e}")
            return 1
    
    # Enhanced backend processing methods
    async def handle_ask_command(self, args) -> int:
        """Handle the ask subcommand"""
        question = ' '.join(args.question)
        
        if not self.backend:
            self.output_error("Backend not available. Using fallback...")
            self.output_message(f"Question: {question}")
            self.output_message("Response: Smart AI CLI is working! Backend integration needed.")
            return 0
        
        provider = args.provider or self.backend.handle_provider_fallback(prompt=question)
        
        if self.verbose_mode:
            self.output_info(f"Using provider: {provider}")
            self.output_info(f"Question: {question}")
        
        response = await self.backend.process_request_async(question, provider)
        
        if response:
            self.format_and_output_response(question, response, provider)
            return 0
        else:
            self.output_error("No response received")
            return 1
    
    async def handle_chat_command(self, args) -> int:
        """Handle the chat subcommand"""
        return await self.interactive_mode(preferred_provider=getattr(args, 'provider', None))
    
    async def handle_providers_command(self, args) -> int:
        """Handle the providers subcommand"""
        if not args.providers_action:
            print("Available provider commands: list, status, test")
            return 0
        
        if args.providers_action == 'list':
            await self.list_providers()
        elif args.providers_action == 'status':
            await self.check_providers_status()
        elif args.providers_action == 'test':
            await self.test_all_providers()
        elif args.providers_action == 'test-provider':
            await self.test_specific_provider(args.provider)
        
        return 0
    
    async def handle_config_command(self, args) -> int:
        """Handle the config subcommand"""
        config_file = Path.home() / ".smart-ai-config.json"
        
        if args.config_action == 'get':
            config = self.load_config(config_file)
            value = config.get(args.key, "Not set")
            self.output_message(f"{args.key}: {value}")
        
        elif args.config_action == 'set':
            config = self.load_config(config_file)
            config[args.key] = args.value
            self.save_config(config, config_file)
            self.output_success(f"Set {args.key} = {args.value}")
        
        elif args.config_action == 'list':
            config = self.load_config(config_file)
            for key, value in config.items():
                self.output_message(f"{key}: {value}")
        
        elif args.config_action == 'reset':
            config_file.unlink(missing_ok=True)
            self.output_success("Configuration reset to defaults")
        
        return 0
    
    async def handle_status_command(self, args) -> int:
        """Handle the status subcommand"""
        self.output_info("Smart AI System Status")
        self.output_message("=" * 50)
        
        # Check backend status
        if self.backend:
            self.output_success("SmartAI Backend: Available")
        else:
            self.output_warning("SmartAI Backend: Not available")
        
        # Check provider status
        await self.check_providers_status()
        
        # Check session info
        if args.detailed:
            self.show_session_info()
        
        return 0
    
    async def interactive_mode(self, preferred_provider: str = None) -> int:
        """Enhanced interactive mode with smart switching"""
        if not self.quiet_mode:
            self.output_info("Smart AI Interactive Mode with File & Project Awareness")
            print("=" * 60)
            self.print_interactive_help()
        
        while True:
            try:
                user_input = input("\n💭 Smart AI> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ("/quit", "/exit"):
                    if not self.quiet_mode:
                        self.output_success("Goodbye!")
                    break
                elif user_input == "/help":
                    self.print_interactive_help()
                    continue
                elif user_input == "/status":
                    await self.handle_status_command(type('Args', (), {'detailed': False})())
                    continue
                elif user_input == "/providers":
                    await self.list_providers()
                    continue
                elif user_input.startswith("/claude"):
                    prompt = user_input[7:].strip() or "Hello"
                    await self.run_claude_code_with_prompt(prompt)
                    continue
                elif user_input.startswith("/gemma"):
                    prompt = user_input[6:].strip() or "Hello"
                    await self.run_gemma_ollama(prompt)
                    continue
                elif user_input.startswith("/treequest"):
                    prompt = user_input[10:].strip() or "Hello"
                    await self.run_treequest(prompt)
                    continue
                elif user_input.startswith("/opendia"):
                    prompt = user_input[8:].strip() or "Hello"
                    await self.run_opendia(prompt)
                    continue
                elif user_input.startswith("/mcp"):
                    prompt = user_input[4:].strip() or "Hello"
                    await self.run_mcp(prompt)
                    continue
                elif user_input.startswith("/file"):
                    await self.handle_interactive_file_command(user_input)
                    continue
                elif user_input.startswith("/project"):
                    await self.handle_interactive_project_command(user_input)
                    continue
                
                # Smart routing with backend processing
                await self.process_interactive_with_backend(user_input, preferred_provider)
                    
            except KeyboardInterrupt:
                if not self.quiet_mode:
                    self.output_success("\nGoodbye!")
                break
            except EOFError:
                if not self.quiet_mode:
                    self.output_success("\nGoodbye!")
                break
        
        return 0
    
    def print_interactive_help(self):
        """Print help for interactive mode"""
        print("Available commands:")
        print("  /claude [prompt]       - Force use Claude Code")
        print("  /gemma [prompt]        - Force use Gemma")
        print("  /treequest [prompt]    - Force use TreeQuest")
        print("  /opendia [prompt]      - Force use OpenDia")
        print("  /mcp [prompt]          - Force use MCP tools")
        print("  /status                - Show current status")
        print("  /providers             - List available providers")
        print("  /file <action> <path>  - File operations (analyze, explain, etc.)")
        print("  /project <action>      - Project operations (analyze, structure, etc.)")
        print("  /help                  - Show this help message")
        print("  /quit, /exit           - Exit")
        print("=" * 60)
    
    async def handle_interactive_file_command(self, user_input: str):
        """Handle file commands in interactive mode"""
        parts = user_input.split()
        if len(parts) < 3:
            self.output_error("Usage: /file <action> <path> [options]")
            self.output_message("Actions: analyze, explain, optimize, test, diff")
            return
        
        action = parts[1]
        file_path = parts[2]
        
        try:
            if action == 'analyze':
                await self.file_analyze(file_path, '--ai' in parts)
            elif action == 'explain':
                await self.file_explain(file_path)
            elif action == 'optimize':
                await self.file_optimize(file_path)
            elif action == 'test':
                await self.file_test(file_path)
            elif action == 'diff' and len(parts) >= 4:
                await self.file_diff(file_path, parts[3], '--ai' in parts)
            else:
                self.output_error(f"Unknown file action: {action}")
        except Exception as e:
            self.output_error(f"File command error: {e}")
    
    async def handle_interactive_project_command(self, user_input: str):
        """Handle project commands in interactive mode"""
        parts = user_input.split()
        if len(parts) < 2:
            self.output_error("Usage: /project <action> [path]")
            self.output_message("Actions: analyze, structure, dependencies, readme, summarize")
            return
        
        action = parts[1]
        project_path = parts[2] if len(parts) > 2 else '.'
        
        try:
            if action == 'analyze':
                await self.project_analyze(project_path)
            elif action == 'structure':
                await self.project_structure(project_path)
            elif action == 'dependencies':
                await self.project_dependencies(project_path)
            elif action == 'readme':
                await self.project_readme(project_path)
            elif action == 'summarize':
                await self.project_summarize(project_path)
            else:
                self.output_error(f"Unknown project action: {action}")
        except Exception as e:
            self.output_error(f"Project command error: {e}")
    
    async def run_single_command(self, args: List[str]) -> int:
        """Run a single command intelligently with backend processing"""
        prompt = " ".join(args)
        return await self.process_with_backend(prompt)
    
    async def process_with_backend(self, prompt: str, preferred_provider: str = None) -> int:
        """Process command using SmartAIBackend for clean output"""
        if not self.backend:
            self.output_error("Backend not available")
            return 1
        
        try:
            # Let backend handle provider selection with fallback
            provider = preferred_provider or self.backend.handle_provider_fallback(prompt=prompt)
            
            if not provider:
                self.output_error("No providers available")
                return 1
            
            # Update session state
            self.backend.manage_session_state()
            
            if self.verbose_mode:
                self.output_info(f"Using provider: {provider}")
            
            # Process async with backend
            response = await self.backend.process_request_async(prompt, provider)
            
            if response:
                self.format_and_output_response(prompt, response, provider)
                return 0
            else:
                self.output_error("No response received")
                return 1
                
        except Exception as e:
            self.output_error(f"Error: {e}")
            return 1
    
    async def process_interactive_with_backend(self, user_input: str, preferred_provider: str = None):
        """Process interactive input using SmartAIBackend"""
        if not self.backend:
            self.output_error("Backend not available")
            return
        
        try:
            # Let backend determine best provider
            provider = preferred_provider or self.backend.handle_provider_fallback(prompt=user_input)
            
            if not provider:
                self.output_error("No providers available")
                return
            
            if self.verbose_mode:
                self.output_info(f"Routing to provider: {provider}")
            
            # Update session state
            self.backend.manage_session_state()
            
            # Process async with backend
            response = await self.backend.process_request_async(user_input, provider)
            
            if response:
                self.format_and_output_response(user_input, response, provider)
            else:
                self.output_error("No response received")
                
        except Exception as e:
            self.output_error(f"Error: {e}")
    
    # Provider-specific execution methods (keeping existing methods)
    async def run_claude_code_with_prompt(self, prompt: str) -> int:
        """Run Claude Code with a specific prompt"""
        if not self.quiet_mode:
            self.output_info("Using Claude Code...")
        
        try:
            if prompt:
                cmd = [self.claude_code_path, prompt]
            else:
                cmd = [self.claude_code_path]
            
            result = subprocess.run(cmd)
            return result.returncode
        except Exception as e:
            self.output_error(f"Claude Code error: {e}")
            return 1
    
    async def run_gemma_ollama(self, prompt: str) -> int:
        """Run Gemma via Ollama"""
        if not self.quiet_mode:
            self.output_info("Using Gemma 2B via Ollama...")
        
        if self.backend:
            try:
                response = await self.backend._execute_gemma(prompt)
                self.format_and_output_response(prompt, response, "gemma")
                return 0
            except Exception as e:
                self.output_error(f"Gemma error: {e}")
                return 1
        else:
            # Fallback to direct Ollama execution
            try:
                cmd = ["ollama", "run", self.gemma_model, prompt]
                result = subprocess.run(cmd, text=True)
                return result.returncode
            except Exception as e:
                self.output_error(f"Gemma error: {e}")
                return 1
    
    async def run_treequest(self, prompt: str) -> int:
        """Run TreeQuest for complex tasks"""
        if not self.quiet_mode:
            self.output_info("Using TreeQuest with multiple providers...")
        
        if self.backend:
            try:
                response = await self.backend._execute_treequest(prompt)
                self.format_and_output_response(prompt, response, "treequest")
                return 0
            except Exception as e:
                self.output_error(f"TreeQuest error: {e}")
                return 1
        else:
            self.output_error("TreeQuest requires SmartAI Backend")
            return 1
    
    async def run_opendia(self, prompt: str) -> int:
        """Run OpenDia for browser automation"""
        if not self.quiet_mode:
            self.output_info("Using OpenDia for browser automation...")
        
        if self.backend:
            try:
                response = await self.backend._execute_opendia(prompt)
                self.format_and_output_response(prompt, response, "opendia")
                return 0
            except Exception as e:
                self.output_error(f"OpenDia error: {e}")
                return 1
        else:
            self.output_error("OpenDia requires SmartAI Backend")
            return 1
    
    async def run_mcp(self, prompt: str) -> int:
        """Run MCP tools"""
        if not self.quiet_mode:
            self.output_info("Using MCP tools...")
        
        if self.backend:
            try:
                response = await self.backend._execute_mcp(prompt)
                self.format_and_output_response(prompt, response, "mcp")
                return 0
            except Exception as e:
                self.output_error(f"MCP error: {e}")
                return 1
        else:
            self.output_error("MCP requires SmartAI Backend")
            return 1
    
    # Provider management methods (keeping existing methods)
    async def list_providers(self):
        """List all available providers"""
        providers_info = [
            ("claude_code", "Claude Code CLI", self.check_claude_code_available()),
            ("treequest", "Multi-provider TreeQuest", self.check_treequest_available()),
            ("gemma", "Local Gemma 2B via Ollama", await self.check_gemma_available()),
            ("opendia", "Browser automation tools", self.check_opendia_available()),
            ("mcp", "Model Context Protocol tools", self.check_mcp_available())
        ]
        
        if self.current_format == 'json':
            providers_list = []
            for provider, description, available in providers_info:
                providers_list.append({
                    "name": provider,
                    "description": description,
                    "available": available,
                    "status": "available" if available else "unavailable"
                })
            print(json.dumps({"providers": providers_list}, indent=2))
        
        elif self.current_format == 'markdown':
            print("# Available Providers\n")
            for provider, description, available in providers_info:
                status = "✅ Available" if available else "❌ Unavailable"
                print(f"## {provider}")
                print(f"- **Description:** {description}")
                print(f"- **Status:** {status}\n")
        
        else:  # plain format
            self.output_info("Available providers:")
            for provider, description, available in providers_info:
                status = "✅" if available else "❌"
                self.output_message(f"  {status} {provider}: {description}")
    
    async def check_providers_status(self):
        """Check and display provider status"""
        if self.backend:
            self.output_info("Provider status (via backend):")
            for provider in self.backend.providers:
                available = self.backend._check_provider_availability(provider)
                status = "Available" if available else "Unavailable"
                icon = "✅" if available else "❌"
                self.output_message(f"  {icon} {provider}: {status}")
        else:
            await self.list_providers()
    
    async def test_all_providers(self):
        """Test all providers with a simple query"""
        test_prompt = "Hello, this is a test."
        self.output_info("Testing all providers...")
        
        providers = ["claude_code", "gemma", "treequest", "opendia", "mcp"]
        
        for provider in providers:
            if self.backend and self.backend._check_provider_availability(provider):
                try:
                    self.output_info(f"Testing {provider}...")
                    response = await self.backend.process_request_async(test_prompt, provider)
                    if response:
                        self.output_success(f"{provider}: ✅ Working")
                    else:
                        self.output_warning(f"{provider}: ⚠️ No response")
                except Exception as e:
                    self.output_error(f"{provider}: ❌ Error - {e}")
            else:
                self.output_warning(f"{provider}: ❌ Not available")
    
    async def test_specific_provider(self, provider: str):
        """Test a specific provider"""
        test_prompt = "Hello, this is a test."
        
        if self.backend and self.backend._check_provider_availability(provider):
            try:
                self.output_info(f"Testing {provider}...")
                response = await self.backend.process_request_async(test_prompt, provider)
                if response:
                    self.output_success(f"{provider}: ✅ Working")
                    if self.verbose_mode:
                        self.output_message(f"Response: {response[:100]}...")
                else:
                    self.output_warning(f"{provider}: ⚠️ No response")
            except Exception as e:
                self.output_error(f"{provider}: ❌ Error - {e}")
        else:
            self.output_error(f"{provider}: ❌ Not available")
    
    # Provider availability checks (keeping existing methods)
    def check_claude_code_available(self) -> bool:
        """Check if Claude Code is available and responsive"""
        try:
            result = subprocess.run([self.claude_code_path, "--version"], 
                                 capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_treequest_available(self) -> bool:
        """Check if TreeQuest is available"""
        return Path(self.treequest_path).exists()
    
    async def check_gemma_available(self) -> bool:
        """Check if Gemma is available via Ollama"""
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0 and "gemma2:2b" in result.stdout
        except:
            return False
    
    def check_opendia_available(self) -> bool:
        """Check if OpenDia is available"""
        return Path("/Users/Subho/opendia/opendia-mcp").exists()
    
    def check_mcp_available(self) -> bool:
        """Check if MCP tools are available"""
        return Path("/Users/Subho/.mcp.json").exists()
    
    # Configuration management (keeping existing methods)
    def load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_config(self, config: Dict[str, Any], config_file: Path):
        """Save configuration to file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.output_error(f"Could not save config: {e}")
    
    def show_session_info(self):
        """Show session information"""
        if self.session_log.exists():
            try:
                with open(self.session_log, 'r') as f:
                    data = json.load(f)
                
                session_data = data.get('session_data', {})
                self.output_message("\nSession Information:")
                self.output_message(f"  Requests: {session_data.get('requests_count', 0)}")
                self.output_message(f"  Duration: {session_data.get('session_duration', 0):.1f}s")
                
                if session_data.get('last_access'):
                    import datetime
                    last_access = datetime.datetime.fromtimestamp(session_data['last_access'])
                    self.output_message(f"  Last access: {last_access.strftime('%Y-%m-%d %H:%M:%S')}")
                    
            except Exception as e:
                self.output_warning(f"Could not load session info: {e}")
    
    # Enhanced output formatting methods
    def format_and_output_response(self, prompt: str, response: str, provider: str):
        """Format and output response based on current format setting"""
        if self.current_format == 'json':
            output = {
                "prompt": prompt,
                "response": response,
                "provider": provider,
                "timestamp": time.time()
            }
            print(json.dumps(output, indent=2))
        
        elif self.current_format == 'markdown':
            print(f"## Query\n{prompt}\n")
            print(f"## Response\n{response}\n")
            if self.verbose_mode:
                print(f"*Provider: {provider}*\n")
        
        else:  # plain format
            if self.verbose_mode and not self.quiet_mode:
                self.output_info(f"Response from {provider}:")
            print(response)
    
    def format_and_output_data(self, data: Dict[str, Any], title: str):
        """Format and output structured data"""
        if self.current_format == 'json':
            print(json.dumps(data, indent=2))
        
        elif self.current_format == 'markdown':
            print(f"# {title}\n")
            self._print_markdown_data(data)
        
        else:  # plain format
            if not self.quiet_mode:
                self.output_info(title)
                print("=" * len(title))
            self._print_plain_data(data)
    
    def _print_markdown_data(self, data: Dict[str, Any], level: int = 2):
        """Print data in markdown format"""
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{'#' * level} {key.replace('_', ' ').title()}\n")
                self._print_markdown_data(value, level + 1)
            elif isinstance(value, list):
                print(f"{'#' * level} {key.replace('_', ' ').title()}\n")
                for item in value:
                    print(f"- {item}")
                print()
            else:
                print(f"**{key.replace('_', ' ').title()}:** {value}\n")
    
    def _print_plain_data(self, data: Dict[str, Any], indent: int = 0):
        """Print data in plain format"""
        for key, value in data.items():
            spaces = "  " * indent
            if isinstance(value, dict):
                print(f"{spaces}{key}:")
                self._print_plain_data(value, indent + 1)
            elif isinstance(value, list):
                print(f"{spaces}{key}:")
                for item in value:
                    print(f"{spaces}  - {item}")
            else:
                print(f"{spaces}{key}: {value}")
    
    def output_message(self, message: str):
        """Output a regular message"""
        if not self.quiet_mode:
            print(message)
    
    def output_info(self, message: str):
        """Output an info message"""
        if not self.quiet_mode:
            print(f"ℹ️  {message}")
    
    def output_success(self, message: str):
        """Output a success message"""
        if not self.quiet_mode:
            print(f"✅ {message}")
    
    def output_warning(self, message: str):
        """Output a warning message"""
        if not self.quiet_mode:
            print(f"⚠️  {message}")
    
    def output_error(self, message: str):
        """Output an error message"""
        print(f"❌ {message}")


async def main():
    """Main entry point with interface detection"""
    args = sys.argv[1:]
    smart_ai = SmartAIUnified()
    
    # Detect interface mode
    interface_mode = smart_ai.detect_interface_mode(args)
    
    if interface_mode == 'help':
        smart_ai.show_unified_help()
        return 0
    elif interface_mode == 'modern':
        return await smart_ai.handle_modern_interface(args)
    else:  # legacy
        return await smart_ai.handle_legacy_interface(args)


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(130)