#!/usr/bin/env python3
"""
TreeQuest Deployment Orchestrator for Smart AI CLI Enhancement
Uses Claude Code as orchestrator with TreeQuest agents for rapid parallel implementation
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

# Add TreeQuest paths
sys.path.append('/Users/Subho/CascadeProjects/enhanced-treequest')
sys.path.append('/Users/Subho/CascadeProjects/multi-ai-treequest')

from enhanced_treequest_controller import (
    EnhancedTreeQuestController, TaskRequest, TaskComplexity, TaskType, ProviderStrength,
    smart_execution, frontend_execution, backend_execution, testing_execution,
    debugging_execution, documentation_execution
)

@dataclass
class DeploymentSubtask:
    """Individual deployment subtask"""
    id: str
    title: str
    description: str
    task_type: TaskType
    complexity: TaskComplexity
    priority: int  # 1 = highest
    dependencies: List[str] = None
    estimated_time: int = 30  # minutes
    output_file: str = None

class TreeQuestDeploymentOrchestrator:
    """Orchestrates rapid deployment using TreeQuest agents with Claude Code"""
    
    def __init__(self):
        self.treequest_controller = EnhancedTreeQuestController()
        self.base_dir = Path("/Users/Subho")
        self.deployment_results = {}
        
        print("🚀 TreeQuest Deployment Orchestrator initialized")
        print(f"🎯 Claude Code as orchestrator with TreeQuest agents")
        print(f"📊 Available providers: {list(self.treequest_controller.all_wrappers.keys())}")
        
    def define_deployment_subtasks(self) -> List[DeploymentSubtask]:
        """Define all subtasks for rapid deployment"""
        return [
            # Core File Analysis Components
            DeploymentSubtask(
                id="fa_001",
                title="FileAnalyzer Core Class",
                description="Create comprehensive FileAnalyzer class with multi-language support",
                task_type=TaskType.BACKEND,
                complexity=TaskComplexity.COMPLEX,
                priority=1,
                estimated_time=45,
                output_file="src/file_analyzer.py"
            ),
            
            DeploymentSubtask(
                id="pa_001",
                title="ProjectAnalyzer Core Class", 
                description="Create ProjectAnalyzer with project type detection and dependency analysis",
                task_type=TaskType.BACKEND,
                complexity=TaskComplexity.COMPLEX,
                priority=1,
                estimated_time=45,
                output_file="src/project_analyzer.py"
            ),
            
            DeploymentSubtask(
                id="pc_001",
                title="ProjectContext Manager",
                description="Create ProjectContext class for maintaining project state and context",
                task_type=TaskType.BACKEND,
                complexity=TaskComplexity.MEDIUM,
                priority=2,
                dependencies=["pa_001"],
                estimated_time=30,
                output_file="src/project_context.py"
            ),
            
            # CLI Integration Components
            DeploymentSubtask(
                id="cli_001",
                title="File Subcommands Integration",
                description="Integrate file analyze/explain/optimize/test/diff commands into unified CLI",
                task_type=TaskType.FRONTEND,
                complexity=TaskComplexity.MEDIUM,
                priority=1,
                dependencies=["fa_001"],
                estimated_time=35,
                output_file="src/file_commands.py"
            ),
            
            DeploymentSubtask(
                id="cli_002",
                title="Project Subcommands Integration",
                description="Integrate project analyze/structure/dependencies/readme commands into CLI",
                task_type=TaskType.FRONTEND,
                complexity=TaskComplexity.MEDIUM,
                priority=1,
                dependencies=["pa_001", "pc_001"],
                estimated_time=35,
                output_file="src/project_commands.py"
            ),
            
            # Advanced Features
            DeploymentSubtask(
                id="ai_001",
                title="AI-Powered Code Analysis",
                description="Create intelligent code analysis using SmartAI backend with provider routing",
                task_type=TaskType.BACKEND,
                complexity=TaskComplexity.EXPERT,
                priority=2,
                dependencies=["fa_001"],
                estimated_time=50,
                output_file="src/ai_code_analyzer.py"
            ),
            
            DeploymentSubtask(
                id="ai_002",
                title="Smart Test Generation",
                description="Implement AI-powered test case generation for multiple languages",
                task_type=TaskType.TESTING,
                complexity=TaskComplexity.COMPLEX,
                priority=3,
                dependencies=["ai_001"],
                estimated_time=40,
                output_file="src/smart_test_generator.py"
            ),
            
            DeploymentSubtask(
                id="ai_003",
                title="README Generation Engine",
                description="Create AI-powered README generation with project analysis",
                task_type=TaskType.DOCUMENTATION,
                complexity=TaskComplexity.MEDIUM,
                priority=3,
                dependencies=["pa_001", "ai_001"],
                estimated_time=35,
                output_file="src/readme_generator.py"
            ),
            
            # Integration and Testing
            DeploymentSubtask(
                id="int_001",
                title="Unified CLI Integration",
                description="Merge all components into smart-ai-unified-v2.py with full functionality",
                task_type=TaskType.BACKEND,
                complexity=TaskComplexity.EXPERT,
                priority=1,
                dependencies=["cli_001", "cli_002", "ai_001"],
                estimated_time=60,
                output_file="smart-ai-unified-v2.py"
            ),
            
            DeploymentSubtask(
                id="test_001",
                title="Comprehensive Testing Suite",
                description="Create complete test suite for all file and project features",
                task_type=TaskType.TESTING,
                complexity=TaskComplexity.COMPLEX,
                priority=2,
                dependencies=["int_001"],
                estimated_time=45,
                output_file="tests/test_smart_ai_v2.py"
            ),
            
            # Documentation and Examples
            DeploymentSubtask(
                id="doc_001",
                title="Enhanced Documentation",
                description="Create comprehensive documentation with examples and usage guides",
                task_type=TaskType.DOCUMENTATION,
                complexity=TaskComplexity.MEDIUM,
                priority=4,
                dependencies=["int_001"],
                estimated_time=30,
                output_file="docs/SMART_AI_V2_GUIDE.md"
            ),
            
            DeploymentSubtask(
                id="demo_001",
                title="Demo Scripts and Examples",
                description="Create demonstration scripts showing file and project features",
                task_type=TaskType.FRONTEND,
                complexity=TaskComplexity.SIMPLE,
                priority=4,
                dependencies=["int_001"],
                estimated_time=25,
                output_file="examples/smart_ai_demos.py"
            )
        ]
    
    async def execute_subtask_with_treequest(self, subtask: DeploymentSubtask) -> Dict[str, Any]:
        """Execute a single subtask using TreeQuest agents"""
        print(f"\n🔄 Executing: {subtask.title}")
        print(f"📝 Description: {subtask.description}")
        print(f"⏱️  Estimated time: {subtask.estimated_time} minutes")
        print(f"🎯 Task type: {subtask.task_type.value}")
        
        # Create detailed context for the subtask
        context = f"""
Smart AI CLI Enhancement Project - Subtask {subtask.id}
Task: {subtask.title}
Description: {subtask.description}
Output File: {subtask.output_file}
Dependencies: {subtask.dependencies or "None"}

Project Context:
- Base implementation: /Users/Subho/smart-ai-unified.py (working CLI)
- Target: Add file and project awareness to achieve Claude Code parity
- Architecture: Modular components that integrate with existing SmartAIBackend
- Requirements: Python 3.8+, clean code, comprehensive error handling

Technical Requirements:
- Use existing SmartAIBackend for AI processing
- Support multiple file types and project structures
- Provide intelligent analysis and suggestions
- Maintain compatibility with existing CLI interface
- Follow established patterns from unified CLI

Specific Implementation Needs:
{self._get_specific_requirements(subtask)}
"""
        
        try:
            # Select optimal execution strategy based on task type
            if subtask.task_type == TaskType.FRONTEND:
                result = await frontend_execution(subtask.description, context)
            elif subtask.task_type == TaskType.BACKEND:
                result = await backend_execution(subtask.description, context)
            elif subtask.task_type == TaskType.TESTING:
                result = await testing_execution(subtask.description, context)
            elif subtask.task_type == TaskType.DOCUMENTATION:
                result = await documentation_execution(subtask.description, context)
            else:
                result = await smart_execution(subtask.description, context, subtask.task_type)
            
            if result.success:
                print(f"   ✅ Completed: {subtask.title}")
                print(f"   🔧 Provider: {result.provider}")
                print(f"   ⏱️  Time: {result.execution_time:.1f}s")
                print(f"   📊 Quality: {result.quality_score:.2f}")
                
                # Save result to file if it contains code
                if subtask.output_file and "```" in result.content:
                    await self._save_component_result(subtask, result.content)
                
                return {
                    "subtask_id": subtask.id,
                    "title": subtask.title,
                    "success": True,
                    "provider": result.provider,
                    "execution_time": result.execution_time,
                    "quality_score": result.quality_score,
                    "content_length": len(result.content),
                    "output_file": subtask.output_file
                }
            else:
                print(f"   ❌ Failed: {subtask.title}")
                print(f"   Error: {result.error_message}")
                return {
                    "subtask_id": subtask.id,
                    "title": subtask.title,
                    "success": False,
                    "error": result.error_message
                }
                
        except Exception as e:
            print(f"   ❌ Exception in subtask: {e}")
            return {
                "subtask_id": subtask.id,
                "title": subtask.title,
                "success": False,
                "error": str(e)
            }
    
    def _get_specific_requirements(self, subtask: DeploymentSubtask) -> str:
        """Get specific requirements based on subtask type"""
        requirements_map = {
            "fa_001": """
FileAnalyzer Requirements:
- Support 30+ file extensions (.py, .js, .ts, .java, .cpp, .go, .rs, etc.)
- Language detection and syntax analysis
- Import/dependency extraction
- Code complexity metrics
- Security vulnerability detection
- Performance optimization suggestions
            """,
            "pa_001": """
ProjectAnalyzer Requirements:
- Project type detection (Python, Node.js, React, Django, etc.)
- Directory structure analysis
- Dependency management file parsing (requirements.txt, package.json, etc.)
- Architecture pattern detection
- Build system identification
- Configuration file analysis
            """,
            "cli_001": """
File Commands Requirements:
- `smart-ai file analyze <file>` - Comprehensive file analysis
- `smart-ai file explain <file>` - AI-powered code explanation
- `smart-ai file optimize <file>` - Performance suggestions
- `smart-ai file test <file>` - Generate test cases
- `smart-ai file diff <file1> <file2>` - Intelligent file comparison
- Support for --format json|markdown|plain
            """,
            "cli_002": """
Project Commands Requirements:
- `smart-ai project analyze` - Full project analysis
- `smart-ai project structure` - Project tree visualization
- `smart-ai project dependencies` - Dependency analysis
- `smart-ai project readme` - README generation
- `smart-ai project summarize` - Project summary
- Support for all output formats and verbosity levels
            """,
            "ai_001": """
AI Code Analysis Requirements:
- Integration with SmartAIBackend for provider routing
- Context-aware code analysis with project understanding
- Multi-language support with language-specific insights
- Performance bottleneck detection
- Code quality assessment
- Refactoring suggestions
            """,
            "int_001": """
Integration Requirements:
- Merge all components into unified CLI
- Maintain backward compatibility with existing interface
- Add new subcommands without breaking changes
- Comprehensive error handling and user feedback
- Support for all existing features plus new file/project capabilities
            """
        }
        return requirements_map.get(subtask.id, "Standard implementation requirements apply.")
    
    async def _save_component_result(self, subtask: DeploymentSubtask, content: str):
        """Save subtask result to appropriate file"""
        if not subtask.output_file:
            return
            
        # Create output directory structure
        output_path = self.base_dir / "smart-ai-enhanced" / subtask.output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract code from content if present
        if "```python" in content:
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
                
                # Add header
                header = f'''"""
{subtask.title}
{subtask.description}
Generated by TreeQuest Deployment Orchestrator
"""

'''
                
                with open(output_path, 'w') as f:
                    f.write(header + code_content)
                
                print(f"   💾 Saved: {output_path}")
        else:
            # Save as markdown or text
            with open(output_path.with_suffix('.md'), 'w') as f:
                f.write(f"# {subtask.title}\n\n{content}")
            print(f"   💾 Saved: {output_path.with_suffix('.md')}")
    
    async def execute_parallel_deployment(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Execute deployment with parallel processing"""
        subtasks = self.define_deployment_subtasks()
        
        print(f"🚀 Starting TreeQuest parallel deployment")
        print(f"📊 Total subtasks: {len(subtasks)}")
        print(f"⚡ Max concurrent: {max_concurrent}")
        print("=" * 60)
        
        deployment_start_time = asyncio.get_event_loop().time()
        completed_subtasks = []
        pending_subtasks = subtasks.copy()
        
        while pending_subtasks:
            # Find subtasks ready to execute (no unmet dependencies)
            ready_subtasks = []
            for subtask in pending_subtasks:
                if not subtask.dependencies:
                    ready_subtasks.append(subtask)
                else:
                    # Check if all dependencies are completed
                    deps_met = all(
                        any(completed.get("subtask_id") == dep_id and completed.get("success") 
                            for completed in completed_subtasks)
                        for dep_id in subtask.dependencies
                    )
                    if deps_met:
                        ready_subtasks.append(subtask)
            
            if not ready_subtasks:
                print("⚠️  No subtasks ready - checking for dependency issues")
                remaining_deps = set()
                for subtask in pending_subtasks:
                    if subtask.dependencies:
                        remaining_deps.update(subtask.dependencies)
                completed_ids = {s.get("subtask_id") for s in completed_subtasks if s.get("success")}
                unmet_deps = remaining_deps - completed_ids
                print(f"❌ Unmet dependencies: {unmet_deps}")
                break
            
            # Execute ready subtasks in parallel (limited by max_concurrent)
            batch_size = min(max_concurrent, len(ready_subtasks))
            current_batch = ready_subtasks[:batch_size]
            
            print(f"\n🔄 Executing batch of {len(current_batch)} subtasks:")
            for subtask in current_batch:
                print(f"   📋 {subtask.id}: {subtask.title}")
            
            # Execute batch in parallel
            batch_tasks = [
                self.execute_subtask_with_treequest(subtask) 
                for subtask in current_batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    result = {
                        "subtask_id": current_batch[i].id,
                        "title": current_batch[i].title,
                        "success": False,
                        "error": str(result)
                    }
                completed_subtasks.append(result)
                pending_subtasks.remove(current_batch[i])
            
            # Short pause between batches
            await asyncio.sleep(1)
        
        total_deployment_time = asyncio.get_event_loop().time() - deployment_start_time
        successful_subtasks = sum(1 for s in completed_subtasks if s.get("success"))
        
        deployment_summary = {
            "total_subtasks": len(subtasks),
            "completed_subtasks": len(completed_subtasks),
            "successful_subtasks": successful_subtasks,
            "success_rate": successful_subtasks / len(subtasks) if subtasks else 0,
            "total_time": total_deployment_time,
            "subtask_results": completed_subtasks
        }
        
        print("\n" + "=" * 60)
        print("🎉 TREEQUEST DEPLOYMENT SUMMARY")
        print("=" * 60)
        print(f"📊 Subtasks Completed: {successful_subtasks}/{len(subtasks)}")
        print(f"✅ Success Rate: {deployment_summary['success_rate']:.1%}")
        print(f"⏱️  Total Time: {total_deployment_time/60:.1f} minutes")
        print(f"📁 Output Directory: {self.base_dir}/smart-ai-enhanced/")
        
        # Show results by category
        categories = {"Core": [], "CLI": [], "AI": [], "Integration": [], "Testing": [], "Documentation": []}
        for result in completed_subtasks:
            subtask_id = result.get("subtask_id", "")
            if subtask_id.startswith("fa_") or subtask_id.startswith("pa_") or subtask_id.startswith("pc_"):
                categories["Core"].append(result)
            elif subtask_id.startswith("cli_"):
                categories["CLI"].append(result)
            elif subtask_id.startswith("ai_"):
                categories["AI"].append(result)
            elif subtask_id.startswith("int_"):
                categories["Integration"].append(result)
            elif subtask_id.startswith("test_"):
                categories["Testing"].append(result)
            elif subtask_id.startswith("doc_") or subtask_id.startswith("demo_"):
                categories["Documentation"].append(result)
        
        print("\n📋 Results by Category:")
        for category, results in categories.items():
            if results:
                successful = sum(1 for r in results if r.get("success"))
                print(f"   {category}: {successful}/{len(results)} ({'✅' if successful == len(results) else '⚠️'})")
        
        return deployment_summary

# Main execution functions
async def deploy_file_awareness():
    """Deploy file awareness features using TreeQuest"""
    orchestrator = TreeQuestDeploymentOrchestrator()
    return await orchestrator.execute_parallel_deployment(max_concurrent=2)

async def deploy_project_awareness():
    """Deploy project awareness features using TreeQuest"""
    orchestrator = TreeQuestDeploymentOrchestrator()
    # Filter to project-related subtasks only
    orchestrator.define_deployment_subtasks = lambda: [
        s for s in orchestrator.define_deployment_subtasks() 
        if s.id.startswith("pa_") or s.id.startswith("pc_") or s.id.startswith("cli_002")
    ]
    return await orchestrator.execute_parallel_deployment(max_concurrent=3)

async def deploy_all_enhancements():
    """Deploy all Smart AI CLI enhancements using TreeQuest"""
    orchestrator = TreeQuestDeploymentOrchestrator()
    return await orchestrator.execute_parallel_deployment(max_concurrent=3)

# Main entry point
async def main():
    """Main deployment orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TreeQuest Deployment Orchestrator")
    parser.add_argument("--mode", choices=["file", "project", "all"], default="all", 
                       help="Deployment mode")
    parser.add_argument("--concurrent", type=int, default=3, 
                       help="Max concurrent subtasks")
    
    args = parser.parse_args()
    
    if args.mode == "file":
        result = await deploy_file_awareness()
    elif args.mode == "project":
        result = await deploy_project_awareness()
    else:
        result = await deploy_all_enhancements()
    
    return result

if __name__ == "__main__":
    asyncio.run(main())