#!/usr/bin/env python3
"""
TreeQuest Tool Ecosystem Deployment Orchestrator
Rapidly deploy GitHub, Docker, npm, and git integration tools using TreeQuest agents
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

class TreeQuestEcosystemDeployer:
    def __init__(self):
        self.base_dir = Path("/Users/Subho/smart-ai-enhanced/src")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Tool ecosystem components to deploy
        self.ecosystem_components = {
            "github_analyzer": {
                "description": "Analyze GitHub repositories, PRs, issues, and provide insights",
                "file": "github_analyzer.py",
                "dependencies": ["file_analyzer.py", "project_analyzer.py"],
                "priority": "high"
            },
            "docker_optimizer": {
                "description": "Analyze Dockerfiles, suggest optimizations, security improvements",
                "file": "docker_optimizer.py", 
                "dependencies": ["file_analyzer.py"],
                "priority": "high"
            },
            "npm_manager": {
                "description": "Analyze package.json, suggest updates, security audits, dependency analysis",
                "file": "npm_manager.py",
                "dependencies": ["project_analyzer.py"],
                "priority": "high"
            },
            "git_workflow": {
                "description": "Analyze git history, suggest workflow improvements, branch strategies",
                "file": "git_workflow.py",
                "dependencies": ["project_analyzer.py"],
                "priority": "high"
            },
            "ecosystem_commands": {
                "description": "CLI subcommands for ecosystem tools integration", 
                "file": "ecosystem_commands.py",
                "dependencies": ["github_analyzer.py", "docker_optimizer.py", "npm_manager.py", "git_workflow.py"],
                "priority": "medium"
            },
            "tool_integration": {
                "description": "Unified interface for all ecosystem tools with smart routing",
                "file": "tool_integration.py",
                "dependencies": ["ecosystem_commands.py"],
                "priority": "medium"
            }
        }
        
    def generate_ecosystem_prompts(self):
        """Generate TreeQuest prompts for each ecosystem component"""
        prompts = {}
        
        for component, config in self.ecosystem_components.items():
            prompt = f"""
Create a {component} Python module for Smart AI CLI enhancement.

Requirements:
- Class name: {component.title().replace('_', '')}
- File: {config['file']}
- Purpose: {config['description']}
- Dependencies: {', '.join(config['dependencies'])}

Technical Specifications:
1. Follow the established pattern from existing Smart AI components
2. Use SmartAIBackend for AI processing
3. Implement error handling and logging
4. Support multiple output formats (JSON, markdown, plain)
5. Include comprehensive docstrings and type hints
6. Handle file/project context appropriately

Specific Features for {component}:
"""
            
            if component == "github_analyzer":
                prompt += """
- Repository analysis: README, structure, activity
- PR/Issue analysis with AI insights
- Contributor analysis and project health metrics
- Security vulnerability scanning
- Code quality assessment
- GitHub API integration (with fallback for rate limits)
"""
            elif component == "docker_optimizer":
                prompt += """
- Dockerfile analysis and optimization suggestions
- Multi-stage build recommendations
- Security best practices validation
- Image size optimization
- Base image vulnerability scanning
- Performance tuning suggestions
"""
            elif component == "npm_manager":
                prompt += """
- package.json analysis and dependency audit
- Security vulnerability detection
- Outdated package identification
- License compatibility checking
- Bundle size analysis
- Performance impact assessment
"""
            elif component == "git_workflow":
                prompt += """
- Git history analysis and insights
- Branch strategy recommendations
- Commit message quality assessment
- Merge vs rebase recommendations
- Git hooks suggestions
- Repository health metrics
"""
            elif component == "ecosystem_commands":
                prompt += """
- CLI subcommands: github, docker, npm, git
- Argument parsing for each tool
- Integration with existing CLI structure
- Help text and usage examples
- Command routing and validation
"""
            elif component == "tool_integration":
                prompt += """
- Unified interface for all ecosystem tools
- Smart routing based on project context
- Configuration management
- Cross-tool insights and recommendations
- Workflow orchestration capabilities
"""
            
            prompt += """

Implementation Pattern:
```python
class {ClassName}:
    def __init__(self, backend=None):
        self.backend = backend or SmartAIBackend()
        
    def analyze(self, context):
        # Main analysis method
        pass
        
    def get_insights(self, data):
        # AI-powered insights
        pass
        
    def format_output(self, data, format='plain'):
        # Format output for different modes
        pass
```

Generate complete, production-ready code following Smart AI CLI patterns.
""".replace("{ClassName}", component.title().replace('_', ''))
            
            prompts[component] = prompt
            
        return prompts
    
    async def deploy_component(self, component, prompt):
        """Deploy a single component using TreeQuest"""
        print(f"🚀 Deploying {component}...")
        
        try:
            # Use TreeQuest to generate the component
            result = subprocess.run([
                'python3', '/Users/Subho/gemini-treequest/treequest_enhanced.py',
                '--task', prompt,
                '--output', str(self.base_dir / self.ecosystem_components[component]['file']),
                '--model', 'gemma2:2b',
                '--provider', 'ollama'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {component} deployed successfully")
                return True
            else:
                print(f"❌ {component} deployment failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {component} deployment timed out")
            return False
        except Exception as e:
            print(f"💥 {component} deployment error: {e}")
            return False
    
    async def deploy_all_components(self):
        """Deploy all ecosystem components in parallel"""
        print("🎯 Starting Tool Ecosystem Deployment...")
        start_time = time.time()
        
        prompts = self.generate_ecosystem_prompts()
        
        # Deploy high priority components first
        high_priority = [k for k, v in self.ecosystem_components.items() if v['priority'] == 'high']
        medium_priority = [k for k, v in self.ecosystem_components.items() if v['priority'] == 'medium']
        
        # Deploy high priority components in parallel
        high_tasks = [self.deploy_component(comp, prompts[comp]) for comp in high_priority]
        high_results = await asyncio.gather(*high_tasks, return_exceptions=True)
        
        # Deploy medium priority components after high priority
        medium_tasks = [self.deploy_component(comp, prompts[comp]) for comp in medium_priority]
        medium_results = await asyncio.gather(*medium_tasks, return_exceptions=True)
        
        # Calculate results
        total_components = len(self.ecosystem_components)
        successful = sum(1 for r in high_results + medium_results if r is True)
        duration = time.time() - start_time
        
        print(f"\n📊 Deployment Results:")
        print(f"   Components: {successful}/{total_components} successful")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Success Rate: {(successful/total_components)*100:.1f}%")
        
        return successful == total_components
    
    def integrate_with_main_cli(self):
        """Integrate ecosystem tools with main Smart AI CLI"""
        print("🔗 Integrating ecosystem tools with main CLI...")
        
        # Read the current unified CLI
        cli_path = "/Users/Subho/smart-ai-unified-final.py"
        
        try:
            with open(cli_path, 'r') as f:
                cli_content = f.read()
            
            # Add ecosystem imports
            ecosystem_imports = """
# Ecosystem tool imports
try:
    from smart_ai_enhanced.src.github_analyzer import GithubAnalyzer
    from smart_ai_enhanced.src.docker_optimizer import DockerOptimizer  
    from smart_ai_enhanced.src.npm_manager import NpmManager
    from smart_ai_enhanced.src.git_workflow import GitWorkflow
    from smart_ai_enhanced.src.ecosystem_commands import EcosystemCommands
    from smart_ai_enhanced.src.tool_integration import ToolIntegration
    ECOSYSTEM_AVAILABLE = True
except ImportError as e:
    ECOSYSTEM_AVAILABLE = False
    print(f"Ecosystem tools not available: {e}")
"""
            
            # Add ecosystem commands to CLI
            ecosystem_commands = """
        # Ecosystem tool commands
        elif args.command == 'github':
            if ECOSYSTEM_AVAILABLE:
                github = GithubAnalyzer(backend)
                result = github.analyze(args.target if hasattr(args, 'target') else '.')
                print(format_output(result, args.format))
            else:
                print("GitHub analyzer not available")
                
        elif args.command == 'docker':
            if ECOSYSTEM_AVAILABLE:
                docker = DockerOptimizer(backend)
                result = docker.analyze(args.target if hasattr(args, 'target') else 'Dockerfile')
                print(format_output(result, args.format))
            else:
                print("Docker optimizer not available")
                
        elif args.command == 'npm':
            if ECOSYSTEM_AVAILABLE:
                npm = NpmManager(backend)
                result = npm.analyze(args.target if hasattr(args, 'target') else 'package.json')
                print(format_output(result, args.format))
            else:
                print("NPM manager not available")
                
        elif args.command == 'git':
            if ECOSYSTEM_AVAILABLE:
                git = GitWorkflow(backend)
                result = git.analyze(args.target if hasattr(args, 'target') else '.')
                print(format_output(result, args.format))
            else:
                print("Git workflow analyzer not available")
"""
            
            # Check if ecosystem tools are already integrated
            if "GithubAnalyzer" not in cli_content:
                # Add imports after existing imports
                import_pos = cli_content.find("# Main CLI")
                if import_pos != -1:
                    cli_content = cli_content[:import_pos] + ecosystem_imports + "\n" + cli_content[import_pos:]
                
                # Add commands before the final else
                command_pos = cli_content.find("else:\n            print(f\"Unknown command: {args.command}\")")
                if command_pos != -1:
                    cli_content = cli_content[:command_pos] + ecosystem_commands + "\n        " + cli_content[command_pos:]
                
                # Write updated CLI
                with open(cli_path, 'w') as f:
                    f.write(cli_content)
                    
                print("✅ Ecosystem tools integrated with main CLI")
            else:
                print("✅ Ecosystem tools already integrated")
                
        except Exception as e:
            print(f"❌ Integration failed: {e}")

async def main():
    deployer = TreeQuestEcosystemDeployer()
    
    print("🎯 Smart AI CLI Tool Ecosystem Deployment")
    print("=" * 50)
    
    # Deploy all components
    success = await deployer.deploy_all_components()
    
    if success:
        # Integrate with main CLI
        deployer.integrate_with_main_cli()
        print("\n🎉 Tool Ecosystem Deployment Complete!")
        print("📝 New commands available:")
        print("   smart-ai github <repo>     # Analyze GitHub repository")
        print("   smart-ai docker <file>     # Optimize Dockerfile")  
        print("   smart-ai npm <package>     # Analyze npm package")
        print("   smart-ai git <project>     # Analyze git workflow")
    else:
        print("\n❌ Deployment failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())