#!/usr/bin/env python3
"""
Smart AI CLI Deployment Orchestrator
Uses Claude Code as orchestrator with TreeQuest agents to deploy CLI improvements
Leverages local Gemma and other models for fast, cost-effective implementation
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add TreeQuest paths
sys.path.append('/Users/Subho/CascadeProjects/enhanced-treequest')
sys.path.append('/Users/Subho/CascadeProjects/multi-ai-treequest')

from enhanced_treequest_controller import (
    EnhancedTreeQuestController, TaskRequest, TaskComplexity, TaskType, ProviderStrength,
    smart_execution, frontend_execution, backend_execution, testing_execution,
    local_execution, llama33_execution
)

@dataclass
class DeploymentTask:
    """Deployment task definition"""
    id: str
    title: str
    description: str
    subtasks: List[str]
    priority: int  # 1 = high, 5 = low
    task_type: TaskType
    estimated_time: int  # minutes
    dependencies: List[str] = None
    provider_preference: str = "local"  # local, fast, accurate
    
class SmartAIDeploymentOrchestrator:
    """Orchestrates CLI improvement deployment using TreeQuest agents"""
    
    def __init__(self):
        self.base_dir = Path("/Users/Subho")
        self.project_dir = self.base_dir / "smart-ai-enhanced"
        self.treequest_controller = EnhancedTreeQuestController()
        
        # Create project structure
        self.setup_project_structure()
        
        # Define deployment tasks
        self.deployment_tasks = self.define_deployment_tasks()
        
        print("🚀 Smart AI CLI Deployment Orchestrator initialized")
        print(f"📁 Project directory: {self.project_dir}")
        print(f"🎯 {len(self.deployment_tasks)} deployment tasks defined")
        
    def setup_project_structure(self):
        """Create enhanced project structure"""
        directories = [
            "smart-ai-enhanced",
            "smart-ai-enhanced/src",
            "smart-ai-enhanced/src/commands",
            "smart-ai-enhanced/src/config",
            "smart-ai-enhanced/src/providers",
            "smart-ai-enhanced/src/utils",
            "smart-ai-enhanced/tests",
            "smart-ai-enhanced/docs",
            "smart-ai-enhanced/examples",
        ]
        
        for dir_path in directories:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created: {full_path}")
    
    def define_deployment_tasks(self) -> List[DeploymentTask]:
        """Define all deployment tasks for CLI improvements"""
        return [
            # Phase 1: Core Infrastructure (High Priority)
            DeploymentTask(
                id="task_001",
                title="Enhanced Command Structure",
                description="Implement subcommand-based CLI with argparse hierarchy",
                subtasks=[
                    "Create main CLI entry point with subcommands",
                    "Implement 'ask', 'chat', 'providers', 'config' commands",
                    "Add command completion for bash/zsh",
                    "Create help system with examples"
                ],
                priority=1,
                task_type=TaskType.BACKEND,
                estimated_time=120,
                provider_preference="local"
            ),
            
            DeploymentTask(
                id="task_002", 
                title="Configuration Management System",
                description="Build unified config hierarchy with secure credential storage",
                subtasks=[
                    "Create ConfigManager class with hierarchy support",
                    "Implement environment variable integration", 
                    "Add secure credential storage using keyring",
                    "Create profile/preset management"
                ],
                priority=1,
                task_type=TaskType.BACKEND,
                estimated_time=90,
                dependencies=["task_001"],
                provider_preference="local"
            ),
            
            DeploymentTask(
                id="task_003",
                title="Enhanced Provider Selection",
                description="Implement intelligent provider selection with fallback",
                subtasks=[
                    "Create ProviderSelector class with ML-like scoring",
                    "Implement historical performance tracking",
                    "Add task-specific provider routing",
                    "Create provider health monitoring"
                ],
                priority=2,
                task_type=TaskType.BACKEND,
                estimated_time=75,
                dependencies=["task_002"],
                provider_preference="fast"
            ),
            
            # Phase 2: Performance & Caching (Medium Priority)
            DeploymentTask(
                id="task_004",
                title="Response Caching System", 
                description="Implement semantic caching with TTL",
                subtasks=[
                    "Create ResponseCache class with vector similarity",
                    "Implement TTL-based cache expiration",
                    "Add cache warming and preloading",
                    "Create cache management CLI commands"
                ],
                priority=2,
                task_type=TaskType.PERFORMANCE,
                estimated_time=60,
                dependencies=["task_003"],
                provider_preference="local"
            ),
            
            DeploymentTask(
                id="task_005",
                title="Output Formatting System",
                description="Add multiple output formats with filtering",
                subtasks=[
                    "Create OutputFormatter class",
                    "Implement JSON, table, markdown formatters",
                    "Add response filtering and truncation",
                    "Create structured data extraction"
                ],
                priority=3,
                task_type=TaskType.FRONTEND,
                estimated_time=45,
                dependencies=["task_001"],
                provider_preference="local"
            ),
            
            # Phase 3: Security & Validation (High Priority)
            DeploymentTask(
                id="task_006",
                title="Input Validation & Security",
                description="Implement comprehensive input validation and security",
                subtasks=[
                    "Create InputValidator class with pydantic",
                    "Add prompt sanitization and injection prevention",
                    "Implement rate limiting per provider",
                    "Add audit logging and monitoring"
                ],
                priority=1,
                task_type=TaskType.SECURITY,
                estimated_time=90,
                dependencies=["task_002"],
                provider_preference="accurate"
            ),
            
            DeploymentTask(
                id="task_007",
                title="Enhanced Error Handling",
                description="Implement comprehensive error handling with suggestions",
                subtasks=[
                    "Create ErrorHandler class with context",
                    "Add error categorization and recovery",
                    "Implement suggestion system for common errors",
                    "Create debugging and trace functionality"
                ],
                priority=2,
                task_type=TaskType.DEBUGGING,
                estimated_time=60,
                dependencies=["task_001"],
                provider_preference="local"
            ),
            
            # Phase 4: Testing & Documentation (Medium Priority)
            DeploymentTask(
                id="task_008",
                title="Comprehensive Testing Framework",
                description="Build complete test suite with mocking",
                subtasks=[
                    "Create test infrastructure with pytest",
                    "Implement provider mocking for testing",
                    "Add integration tests for CLI commands",
                    "Create performance benchmarking tests"
                ],
                priority=3,
                task_type=TaskType.TESTING,
                estimated_time=75,
                dependencies=["task_001", "task_002"],
                provider_preference="local"
            ),
            
            DeploymentTask(
                id="task_009",
                title="Documentation & Examples",
                description="Create comprehensive documentation and examples",
                subtasks=[
                    "Write installation and setup guide",
                    "Create API documentation with examples",
                    "Add troubleshooting guide",
                    "Create video tutorials and demos"
                ],
                priority=4,
                task_type=TaskType.DOCUMENTATION,
                estimated_time=90,
                dependencies=["task_008"],
                provider_preference="accurate"
            ),
            
            # Phase 5: Advanced Features (Low Priority)
            DeploymentTask(
                id="task_010", 
                title="Plugin Architecture",
                description="Implement extensible plugin system",
                subtasks=[
                    "Create PluginManager class",
                    "Define plugin interface and lifecycle",
                    "Add plugin discovery and loading",
                    "Create example plugins"
                ],
                priority=5,
                task_type=TaskType.ARCHITECTURE,
                estimated_time=120,
                dependencies=["task_003"],
                provider_preference="accurate"
            )
        ]
    
    async def execute_deployment_task(self, task: DeploymentTask) -> Dict[str, Any]:
        """Execute a single deployment task using TreeQuest agents"""
        print(f"\n🚀 Executing Task: {task.title}")
        print(f"📝 Description: {task.description}")
        print(f"⏱️  Estimated time: {task.estimated_time} minutes")
        print(f"🎯 Provider preference: {task.provider_preference}")
        
        results = []
        total_start_time = time.time()
        
        for i, subtask in enumerate(task.subtasks, 1):
            print(f"\n   🔄 Subtask {i}/{len(task.subtasks)}: {subtask}")
            
            # Create context for the subtask
            context = f"""
Smart AI CLI Enhancement Project
Task: {task.title}
Description: {task.description}
Current Subtask: {subtask}
Project Directory: {self.project_dir}
Task Type: {task.task_type.value}

Requirements:
- Use existing smart-ai CLI as base
- Implement with Python 3.8+ compatibility
- Follow PEP 8 coding standards
- Include error handling and logging
- Create modular, testable code
- Use local/offline capabilities when possible

Context: We are enhancing the existing Smart AI CLI that orchestrates between Claude Code, TreeQuest, Gemma, and OpenDia providers.
"""
            
            # Select execution strategy based on preference
            try:
                if task.provider_preference == "local":
                    result = await local_execution(subtask, context)
                elif task.provider_preference == "fast": 
                    result = await llama33_execution(subtask, context, "groq")
                else:  # accurate
                    result = await smart_execution(subtask, context, task.task_type)
                
                if result.success:
                    print(f"   ✅ Completed: {subtask}")
                    print(f"   🔧 Provider: {result.provider}")
                    print(f"   ⏱️  Time: {result.execution_time:.1f}s")
                    
                    # Save result to file if it contains code
                    if "```" in result.content and len(result.content) > 100:
                        await self.save_subtask_result(task, i, subtask, result.content)
                    
                    results.append({
                        "subtask": subtask,
                        "success": True,
                        "provider": result.provider,
                        "execution_time": result.execution_time,
                        "content_length": len(result.content)
                    })
                else:
                    print(f"   ❌ Failed: {subtask}")
                    print(f"   Error: {result.error_message}")
                    results.append({
                        "subtask": subtask,
                        "success": False,
                        "error": result.error_message
                    })
                    
            except Exception as e:
                print(f"   ❌ Exception in subtask: {e}")
                results.append({
                    "subtask": subtask,
                    "success": False,
                    "error": str(e)
                })
        
        total_time = time.time() - total_start_time
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        task_summary = {
            "task_id": task.id,
            "title": task.title,
            "success_rate": success_rate,
            "total_time": total_time,
            "results": results,
            "completed": success_rate >= 0.8  # 80% success rate required
        }
        
        print(f"\n📊 Task Summary: {task.title}")
        print(f"   ✅ Success Rate: {success_rate:.1%}")
        print(f"   ⏱️  Total Time: {total_time/60:.1f} minutes")
        print(f"   🎯 Status: {'COMPLETED' if task_summary['completed'] else 'NEEDS RETRY'}")
        
        return task_summary
    
    async def save_subtask_result(self, task: DeploymentTask, subtask_num: int, subtask: str, content: str):
        """Save subtask result to appropriate file"""
        # Determine file type and location based on content and task
        file_mapping = {
            "CLI entry point": "src/main.py",
            "ConfigManager": "src/config/config_manager.py", 
            "ProviderSelector": "src/providers/provider_selector.py",
            "ResponseCache": "src/utils/response_cache.py",
            "OutputFormatter": "src/utils/output_formatter.py",
            "InputValidator": "src/utils/input_validator.py",
            "ErrorHandler": "src/utils/error_handler.py",
            "test": f"tests/test_{task.id}_{subtask_num}.py",
            "documentation": f"docs/{task.id}_{subtask_num}.md"
        }
        
        # Determine filename
        filename = None
        for key, path in file_mapping.items():
            if key.lower() in subtask.lower():
                filename = path
                break
        
        if not filename:
            filename = f"src/generated_{task.id}_{subtask_num}.py"
        
        file_path = self.project_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract code from content if present
        if "```python" in content:
            # Extract Python code blocks
            lines = content.split('\n')
            code_lines = []
            in_code_block = False
            
            for line in lines:
                if line.strip().startswith("```python"):
                    in_code_block = True
                    continue
                elif line.strip() == "```" and in_code_block:
                    in_code_block = False
                    continue
                elif in_code_block:
                    code_lines.append(line)
            
            if code_lines:
                code_content = '\n'.join(code_lines)
                with open(file_path, 'w') as f:
                    f.write(f"# {subtask}\n# Generated by Smart AI CLI Deployment Orchestrator\n\n")
                    f.write(code_content)
                print(f"   💾 Saved code to: {file_path}")
        else:
            # Save as markdown or text
            with open(file_path.with_suffix('.md'), 'w') as f:
                f.write(f"# {subtask}\n\n{content}")
            print(f"   💾 Saved content to: {file_path.with_suffix('.md')}")
    
    async def execute_deployment_plan(self, task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute full deployment plan or specific tasks"""
        
        # Filter tasks if specific IDs provided
        if task_ids:
            tasks_to_execute = [t for t in self.deployment_tasks if t.id in task_ids]
        else:
            # Sort by priority and dependencies
            tasks_to_execute = sorted(self.deployment_tasks, key=lambda t: t.priority)
        
        print(f"🚀 Starting deployment of {len(tasks_to_execute)} tasks")
        print("=" * 60)
        
        deployment_start_time = time.time()
        task_results = []
        
        for task in tasks_to_execute:
            # Check dependencies
            if task.dependencies:
                unmet_deps = []
                for dep_id in task.dependencies:
                    dep_completed = any(
                        r.get("task_id") == dep_id and r.get("completed") 
                        for r in task_results
                    )
                    if not dep_completed:
                        unmet_deps.append(dep_id)
                
                if unmet_deps:
                    print(f"⏸️  Skipping {task.title} - unmet dependencies: {unmet_deps}")
                    continue
            
            # Execute task
            result = await self.execute_deployment_task(task)
            task_results.append(result)
            
            # Short pause between tasks
            await asyncio.sleep(2)
        
        total_deployment_time = time.time() - deployment_start_time
        completed_tasks = sum(1 for r in task_results if r["completed"])
        
        deployment_summary = {
            "total_tasks": len(task_results),
            "completed_tasks": completed_tasks,
            "success_rate": completed_tasks / len(task_results) if task_results else 0,
            "total_time": total_deployment_time,
            "task_results": task_results
        }
        
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"📊 Tasks Completed: {completed_tasks}/{len(task_results)}")
        print(f"✅ Success Rate: {deployment_summary['success_rate']:.1%}")
        print(f"⏱️  Total Time: {total_deployment_time/60:.1f} minutes")
        print(f"📁 Project Location: {self.project_dir}")
        
        # Save deployment report
        report_path = self.project_dir / "deployment_report.json"
        with open(report_path, 'w') as f:
            json.dump(deployment_summary, f, indent=2, default=str)
        
        print(f"📄 Deployment report saved: {report_path}")
        
        return deployment_summary
    
    async def create_integration_script(self):
        """Create script to integrate enhanced CLI with existing smart-ai"""
        integration_script = f'''#!/usr/bin/env python3
"""
Smart AI Enhanced Integration Script
Integrates the enhanced CLI with existing smart-ai installation
"""

import os
import shutil
import sys
from pathlib import Path

def integrate_enhanced_cli():
    """Integrate enhanced CLI with existing installation"""
    
    # Paths
    enhanced_dir = Path("{self.project_dir}")
    existing_smart_ai = Path("/Users/Subho/smart-ai")
    backup_dir = Path("/Users/Subho/smart-ai-backup")
    
    print("🔄 Starting Smart AI CLI integration...")
    
    # Create backup
    if existing_smart_ai.exists():
        print(f"💾 Creating backup at {{backup_dir}}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(existing_smart_ai, backup_dir)
    
    # Copy enhanced files
    if enhanced_dir.exists():
        print("📁 Copying enhanced CLI files...")
        
        # Copy Python files
        for py_file in enhanced_dir.rglob("*.py"):
            rel_path = py_file.relative_to(enhanced_dir)
            dest_path = existing_smart_ai / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py_file, dest_path)
            print(f"   ✅ Copied: {{rel_path}}")
    
    # Update permissions
    if existing_smart_ai.exists():
        os.chmod(existing_smart_ai / "smart-ai", 0o755)
    
    print("✅ Integration completed!")
    print(f"🔧 Enhanced CLI available at: {{existing_smart_ai}}")
    print(f"💾 Backup available at: {{backup_dir}}")

if __name__ == "__main__":
    integrate_enhanced_cli()
'''
        
        script_path = self.project_dir / "integrate.py"
        with open(script_path, 'w') as f:
            f.write(integration_script)
        
        os.chmod(script_path, 0o755)
        print(f"🔧 Integration script created: {script_path}")
        
        return script_path

# Quick deployment functions for specific phases
async def deploy_core_infrastructure():
    """Deploy Phase 1: Core Infrastructure"""
    orchestrator = SmartAIDeploymentOrchestrator()
    return await orchestrator.execute_deployment_plan(["task_001", "task_002", "task_003"])

async def deploy_performance_features():
    """Deploy Phase 2: Performance & Caching"""
    orchestrator = SmartAIDeploymentOrchestrator()
    return await orchestrator.execute_deployment_plan(["task_004", "task_005"])

async def deploy_security_features():
    """Deploy Phase 3: Security & Validation"""
    orchestrator = SmartAIDeploymentOrchestrator()
    return await orchestrator.execute_deployment_plan(["task_006", "task_007"])

async def deploy_testing_docs():
    """Deploy Phase 4: Testing & Documentation"""
    orchestrator = SmartAIDeploymentOrchestrator()
    return await orchestrator.execute_deployment_plan(["task_008", "task_009"])

async def deploy_advanced_features():
    """Deploy Phase 5: Advanced Features"""
    orchestrator = SmartAIDeploymentOrchestrator()
    return await orchestrator.execute_deployment_plan(["task_010"])

async def deploy_everything():
    """Deploy all phases"""
    orchestrator = SmartAIDeploymentOrchestrator()
    result = await orchestrator.execute_deployment_plan()
    
    # Create integration script
    await orchestrator.create_integration_script()
    
    return result

# Main execution
async def main():
    """Main deployment entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart AI CLI Deployment Orchestrator")
    parser.add_argument("--phase", choices=["core", "performance", "security", "testing", "advanced", "all"], 
                       default="all", help="Deployment phase to execute")
    parser.add_argument("--tasks", nargs="+", help="Specific task IDs to execute")
    
    args = parser.parse_args()
    
    if args.tasks:
        orchestrator = SmartAIDeploymentOrchestrator()
        result = await orchestrator.execute_deployment_plan(args.tasks)
    elif args.phase == "core":
        result = await deploy_core_infrastructure()
    elif args.phase == "performance":
        result = await deploy_performance_features()
    elif args.phase == "security":
        result = await deploy_security_features()
    elif args.phase == "testing":
        result = await deploy_testing_docs()
    elif args.phase == "advanced":
        result = await deploy_advanced_features()
    else:  # all
        result = await deploy_everything()
    
    return result

if __name__ == "__main__":
    asyncio.run(main())