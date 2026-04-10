#!/usr/bin/env python3
"""
Parallel Testing Executor using TMLPD

Implements a parallel task distribution system with 5 specialized agents
to speed up testing and implementation tasks.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import json
import time
import logging
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# TMLPD imports
TMLPD_PATH = Path.home() / "tmlpd-clean"
if TMLPD_PATH.exists():
    sys.path.insert(0, str(TMLPD_PATH))

try:
    from workflows.dynamic_parallel_executor import DynamicParallelExecutor
except ImportError:
    print("Warning: TMLPD DynamicParallelExecutor not found. Creating mock...")
    DynamicParallelExecutor = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Specialized agent types"""
    PERFORMANCE = "performance"
    CONVERSATION = "conversation"
    LANGUAGE = "language"
    CODE_ANALYSIS = "code_analysis"
    INTEGRATION = "integration"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Task definition for parallel execution"""
    id: str
    title: str
    description: str
    agent_type: AgentType
    priority: int = 5  # 1-10, lower is higher priority
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 60.0  # seconds
    difficulty: str = "medium"
    required_capabilities: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None  # Agent ID
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Agent:
    """Parallel execution agent"""
    id: int
    name: str
    agent_type: AgentType
    current_task: Optional[Task] = None
    completed_tasks: List[Task] = field(default_factory=list)
    total_time: float = 0.0
    success_rate: float = 1.0


class ParallelTestingExecutor:
    """
    Parallel Testing Executor with 5 specialized agents.

    Features:
    - 5 specialized agents for different testing types
    - Dynamic task assignment and dependency management
    - Progress tracking and coordination
    - Result merging and conflict resolution
    - Real-time monitoring and reporting
    """

    def __init__(
        self,
        project_root: Path = PROJECT_ROOT,
        pool_size: int = 5,
        enable_learning: bool = True
    ):
        """
        Initialize parallel testing executor.

        Args:
            project_root: Root directory of the project
            pool_size: Number of parallel agents (default: 5)
            enable_learning: Enable learning from executions
        """
        self.project_root = project_root
        self.pool_size = pool_size
        self.enable_learning = enable_learning

        # Initialize TMLPD executor if available
        self.tmlpd_executor = None
        if DynamicParallelExecutor:
            self._init_tmlpd_executor()

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self.task_dependencies: Dict[str, List[str]] = {}

        # Agent pool
        self.agents: Dict[int, Agent] = {}
        self._init_agents()

        # Progress tracking
        self.progress = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "blocked_tasks": 0,
            "in_progress_tasks": 0,
            "start_time": None,
            "end_time": None,
            "current_agent_status": {}
        }

        # Results storage
        self.results: Dict[str, Dict[str, Any]] = {}
        self.execution_log: List[Dict[str, Any]] = []

        # Learning data
        self.learning_data: List[Dict[str, Any]] = []

    def _init_tmlpd_executor(self):
        """Initialize TMLPD executor for LLM-based task execution"""
        try:
            # Create a mock provider executor for demonstration
            # In real implementation, this would connect to actual LLM providers
            self.tmlpd_executor = DynamicParallelExecutor(
                pool_size=self.pool_size,
                enable_learning=self.enable_learning
            )
            logger.info("TMLPD executor initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize TMLPD executor: {e}")

    def _init_agents(self):
        """Initialize specialized agents"""
        agent_configs = [
            {
                "id": 1,
                "name": "Performance Agent",
                "type": AgentType.PERFORMANCE,
                "description": "Specialized in performance testing, optimization, and benchmarking"
            },
            {
                "id": 2,
                "name": "Conversation Agent",
                "type": AgentType.CONVERSATION,
                "description": "Specialized in conversation flow testing and user experience validation"
            },
            {
                "id": 3,
                "name": "Language Agent",
                "type": AgentType.LANGUAGE,
                "description": "Specialized in language preference testing and localization"
            },
            {
                "id": 4,
                "name": "Code Analysis Agent",
                "type": AgentType.CODE_ANALYSIS,
                "description": "Specialized in code analysis, bug detection, and code quality"
            },
            {
                "id": 5,
                "name": "Integration Agent",
                "type": AgentType.INTEGRATION,
                "description": "Specialized in integration testing and end-to-end validation"
            }
        ]

        for config in agent_configs:
            agent = Agent(
                id=config["id"],
                name=config["name"],
                agent_type=config["type"]
            )
            self.agents[config["id"]] = agent

    def create_testing_tasks(self) -> List[Task]:
        """
        Create comprehensive testing task breakdown.

        Returns:
            List of testing tasks with dependencies
        """
        tasks = []

        # Performance Testing Tasks
        performance_tasks = [
            Task(
                id="perf_1",
                title="Baseline Performance Metrics",
                description="Collect baseline performance metrics for all major functions",
                agent_type=AgentType.PERFORMANCE,
                priority=1,
                difficulty="easy",
                estimated_time=30.0
            ),
            Task(
                id="perf_2",
                title="Load Testing Implementation",
                description="Implement load testing for concurrent user scenarios",
                agent_type=AgentType.PERFORMANCE,
                priority=2,
                difficulty="medium",
                dependencies=["perf_1"],
                estimated_time=45.0
            ),
            Task(
                id="perf_3",
                title="Memory Usage Analysis",
                description="Analyze memory usage patterns and identify leaks",
                agent_type=AgentType.PERFORMANCE,
                priority=3,
                difficulty="medium",
                estimated_time=40.0
            ),
            Task(
                id="perf_4",
                title="Performance Optimization",
                description="Implement performance optimizations based on testing results",
                agent_type=AgentType.PERFORMANCE,
                priority=4,
                difficulty="hard",
                dependencies=["perf_2", "perf_3"],
                estimated_time=60.0
            )
        ]

        # Conversation Flow Testing Tasks
        conversation_tasks = [
            Task(
                id="conv_1",
                title="Happy Path Testing",
                description="Test all happy path conversation flows",
                agent_type=AgentType.CONVERSATION,
                priority=1,
                difficulty="easy",
                estimated_time=35.0
            ),
            Task(
                id="conv_2",
                title="Edge Case Testing",
                description="Test edge cases and error handling in conversations",
                agent_type=AgentType.CONVERSATION,
                priority=2,
                difficulty="medium",
                estimated_time=45.0
            ),
            Task(
                id="conv_3",
                title="Multi-turn Conversation Testing",
                description="Test multi-turn conversation state management",
                agent_type=AgentType.CONVERSATION,
                priority=3,
                difficulty="medium",
                dependencies=["conv_1"],
                estimated_time=50.0
            ),
            Task(
                id="conv_4",
                title="Conversation Flow Analysis",
                description="Analyze conversation flow patterns and identify issues",
                agent_type=AgentType.CONVERSATION,
                priority=4,
                difficulty="medium",
                dependencies=["conv_2", "conv_3"],
                estimated_time=40.0
            )
        ]

        # Language Preference Testing Tasks
        language_tasks = [
            Task(
                id="lang_1",
                title="English Language Testing",
                description="Test all functionality with English language preference",
                agent_type=AgentType.LANGUAGE,
                priority=1,
                difficulty="easy",
                estimated_time=30.0
            ),
            Task(
                id="lang_2",
                title="Multi-language Support Testing",
                description="Test multi-language support and switching",
                agent_type=AgentType.LANGUAGE,
                priority=2,
                difficulty="medium",
                dependencies=["lang_1"],
                estimated_time=45.0
            ),
            Task(
                id="lang_3",
                title="Language Detection Testing",
                description="Test automatic language detection capabilities",
                agent_type=AgentType.LANGUAGE,
                priority=3,
                difficulty="medium",
                estimated_time=35.0
            ),
            Task(
                id="lang_4",
                title="RTL Language Testing",
                description="Test right-to-left language support if applicable",
                agent_type=AgentType.LANGUAGE,
                priority=4,
                difficulty="medium",
                dependencies=["lang_2"],
                estimated_time=40.0
            )
        ]

        # Code Analysis Tasks
        code_analysis_tasks = [
            Task(
                id="code_1",
                title="Static Code Analysis",
                description="Perform static code analysis using linters and analyzers",
                agent_type=AgentType.CODE_ANALYSIS,
                priority=1,
                difficulty="easy",
                estimated_time=25.0
            ),
            Task(
                id="code_2",
                title="Security Analysis",
                description="Conduct security analysis and vulnerability scanning",
                agent_type=AgentType.CODE_ANALYSIS,
                priority=2,
                difficulty="hard",
                dependencies=["code_1"],
                estimated_time=50.0
            ),
            Task(
                id="code_3",
                title="Bug Detection and Reporting",
                description="Detect and report potential bugs and issues",
                agent_type=AgentType.CODE_ANALYSIS,
                priority=3,
                difficulty="medium",
                dependencies=["code_1"],
                estimated_time=45.0
            ),
            Task(
                id="code_4",
                title="Code Quality Assessment",
                description="Assess overall code quality and suggest improvements",
                agent_type=AgentType.CODE_ANALYSIS,
                priority=4,
                difficulty="medium",
                dependencies=["code_2", "code_3"],
                estimated_time=40.0
            )
        ]

        # Integration Testing Tasks
        integration_tasks = [
            Task(
                id="int_1",
                title="Component Integration Testing",
                description="Test integration between major components",
                agent_type=AgentType.INTEGRATION,
                priority=1,
                difficulty="medium",
                estimated_time=45.0
            ),
            Task(
                id="int_2",
                title="API Integration Testing",
                description="Test API integrations and endpoints",
                agent_type=AgentType.INTEGRATION,
                priority=2,
                difficulty="medium",
                dependencies=["int_1"],
                estimated_time=50.0
            ),
            Task(
                id="int_3",
                title="End-to-End Testing",
                description="Perform end-to-end system testing",
                agent_type=AgentType.INTEGRATION,
                priority=3,
                difficulty="hard",
                dependencies=["int_2"],
                estimated_time=60.0
            ),
            Task(
                id="int_4",
                title="Test Report Generation",
                description="Generate comprehensive test reports",
                agent_type=AgentType.INTEGRATION,
                priority=4,
                difficulty="medium",
                dependencies=["int_3"],
                estimated_time=30.0
            )
        ]

        # Combine all tasks
        tasks.extend(performance_tasks)
        tasks.extend(conversation_tasks)
        tasks.extend(language_tasks)
        tasks.extend(code_analysis_tasks)
        tasks.extend(integration_tasks)

        return tasks

    async def execute_parallel_tasks(
        self,
        tasks: List[Task] = None,
        fail_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Execute tasks in parallel with specialized agents.

        Args:
            tasks: List of tasks to execute (default: auto-generate testing tasks)
            fail_on_error: Stop execution on first error

        Returns:
            Execution results with detailed statistics
        """
        if tasks is None:
            tasks = self.create_testing_tasks()

        # Initialize task management
        for task in tasks:
            self.tasks[task.id] = task

        self.progress["total_tasks"] = len(tasks)
        self.progress["start_time"] = datetime.now()

        logger.info(f"Starting parallel execution with {len(tasks)} tasks")
        logger.info(f"Agent pool size: {self.pool_size}")

        # Build dependency graph and queue
        await self._build_task_queue()

        # Create worker tasks for each agent
        agent_workers = [
            asyncio.create_task(self._agent_worker(agent_id))
            for agent_id in self.agents.keys()
        ]

        # Monitor progress
        monitor_task = asyncio.create_task(self._progress_monitor())

        # Wait for all agents to complete
        await asyncio.gather(*agent_workers)
        monitor_task.cancel()

        self.progress["end_time"] = datetime.now()

        # Generate final results
        results = await self._generate_results()

        return results

    async def _build_task_queue(self):
        """Build task queue respecting dependencies"""
        # Initialize all tasks as pending
        for task_id, task in self.tasks.items():
            self.task_dependencies[task_id] = task.dependencies.copy()

        # Add ready tasks to queue
        await self._update_task_queue()

    async def _update_task_queue(self):
        """Update task queue with tasks whose dependencies are satisfied"""
        for task_id, task in self.tasks.items():
            if (task.status == TaskStatus.PENDING and
                self._are_dependencies_satisfied(task_id)):

                task.status = TaskStatus.READY
                await self.task_queue.put(task_id)
                logger.info(f"Added task {task_id} to queue")

    def _are_dependencies_satisfied(self, task_id: str) -> bool:
        """Check if all task dependencies are satisfied"""
        dependencies = self.tasks[task_id].dependencies

        for dep_id in dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _agent_worker(self, agent_id: int):
        """
        Agent worker that processes tasks from the queue.

        Each agent:
        1. Pulls a task from the queue
        2. Executes it with specialized capabilities
        3. Updates task status
        4. Immediately pulls the next available task
        """
        agent = self.agents[agent_id]
        logger.info(f"Agent {agent_id} ({agent.name}) started")

        while True:
            try:
                # Get next task (blocks until available)
                task_id = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )

                # Check for shutdown signal
                if task_id is None:
                    logger.info(f"Agent {agent_id} shutting down")
                    self.task_queue.task_done()
                    break

                task = self.tasks[task_id]

                # Verify agent type matches task type
                if task.agent_type != agent.agent_type:
                    # Put back and try different agent
                    await self.task_queue.put(task_id)
                    await asyncio.sleep(0.1)
                    continue

                # Execute task
                await self._execute_task(agent, task)

                # Update queue with newly available tasks
                await self._update_task_queue()

                self.task_queue.task_done()

            except asyncio.TimeoutError:
                # No tasks available, check if we should stop
                if self._all_tasks_completed():
                    break
                continue
            except Exception as e:
                logger.error(f"Agent {agent_id} error: {e}")
                continue

    async def _execute_task(self, agent: Agent, task: Task):
        """Execute a single task"""
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = agent.id
        task.started_at = datetime.now()

        logger.info(f"Agent {agent.id} starting task {task.id}: {task.title}")

        # Update progress
        self.progress["in_progress_tasks"] += 1
        self.progress["current_agent_status"][agent.id] = {
            "task_id": task.id,
            "status": "in_progress",
            "started_at": task.started_at.isoformat()
        }

        try:
            # Execute task based on type
            result = await self._execute_task_by_type(agent, task)

            # Store result
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            # Update agent statistics
            agent.completed_tasks.append(task)
            execution_time = (task.completed_at - task.started_at).total_seconds()
            agent.total_time += execution_time

            # Update progress
            self.progress["completed_tasks"] += 1
            self.progress["in_progress_tasks"] -= 1

            self.progress["current_agent_status"][agent.id] = {
                "task_id": task.id,
                "status": "completed",
                "completed_at": task.completed_at.isoformat()
            }

            logger.info(f"Agent {agent.id} completed task {task.id} in {execution_time:.2f}s")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = {
                "success": False,
                "error": str(e),
                "traceback": str(e)
            }

            # Update progress
            self.progress["failed_tasks"] += 1
            self.progress["in_progress_tasks"] -= 1

            agent.success_rate = (
                len([t for t in agent.completed_tasks if t.status == TaskStatus.COMPLETED]) /
                len(agent.completed_tasks) if agent.completed_tasks else 0
            )

            logger.error(f"Agent {agent.id} failed task {task.id}: {e}")

    async def _execute_task_by_type(self, agent: Agent, task: Task) -> Dict[str, Any]:
        """
        Execute task based on agent specialization.

        This is a mock implementation - in real use, this would call
        actual testing frameworks and tools.
        """
        start_time = time.time()

        # Simulate task execution based on type
        if agent.agent_type == AgentType.PERFORMANCE:
            result = await self._execute_performance_task(task)
        elif agent.agent_type == AgentType.CONVERSATION:
            result = await self._execute_conversation_task(task)
        elif agent.agent_type == AgentType.LANGUAGE:
            result = await self._execute_language_task(task)
        elif agent.agent_type == AgentType.CODE_ANALYSIS:
            result = await self._execute_code_analysis_task(task)
        elif agent.agent_type == AgentType.INTEGRATION:
            result = await self._execute_integration_task(task)
        else:
            raise ValueError(f"Unknown agent type: {agent.agent_type}")

        execution_time = time.time() - start_time
        result["execution_time"] = execution_time
        result["agent_id"] = agent.id
        result["success"] = True

        return result

    async def _execute_performance_task(self, task: Task) -> Dict[str, Any]:
        """Execute performance testing task"""
        # Mock implementation - replace with actual performance testing
        await asyncio.sleep(task.estimated_time / 10)  # Simulate work

        return {
            "task_type": "performance",
            "metrics": {
                "response_time": 150.5,
                "throughput": 1000,
                "memory_usage": 512,
                "cpu_usage": 45.2
            },
            "findings": [
                "Function X shows good performance",
                "Module Y could benefit from caching"
            ],
            "recommendations": [
                "Implement caching for frequently accessed data",
                "Optimize database queries"
            ]
        }

    async def _execute_conversation_task(self, task: Task) -> Dict[str, Any]:
        """Execute conversation flow testing task"""
        await asyncio.sleep(task.estimated_time / 10)

        return {
            "task_type": "conversation",
            "tested_flows": [
                "Happy path: User greeting → Response",
                "Edge case: Invalid input → Error handling",
                "Multi-turn: Extended conversation"
            ],
            "issues_found": [
                "Missing validation in flow Z",
                "Unclear error message in scenario Y"
            ],
            "success_rate": 0.95
        }

    async def _execute_language_task(self, task: Task) -> Dict[str, Any]:
        """Execute language preference testing task"""
        await asyncio.sleep(task.estimated_time / 10)

        return {
            "task_type": "language",
            "tested_languages": ["English", "Spanish", "French", "German"],
            "coverage": 0.92,
            "issues_found": [
                "Missing translations for feature X",
                "Date formatting inconsistent in locale Y"
            ],
            "recommendations": [
                "Add missing translations",
                "Standardize date formatting"
            ]
        }

    async def _execute_code_analysis_task(self, task: Task) -> Dict[str, Any]:
        """Execute code analysis task"""
        await asyncio.sleep(task.estimated_time / 10)

        return {
            "task_type": "code_analysis",
            "files_analyzed": 150,
            "issues_found": {
                "critical": 2,
                "high": 5,
                "medium": 15,
                "low": 30
            },
            "code_quality": {
                "maintainability": 75,
                "complexity": 68,
                "duplication": 82
            },
            "recommendations": [
                "Refactor function X (high complexity)",
                "Extract duplicate code in module Y"
            ]
        }

    async def _execute_integration_task(self, task: Task) -> Dict[str, Any]:
        """Execute integration testing task"""
        await asyncio.sleep(task.estimated_time / 10)

        return {
            "task_type": "integration",
            "test_suites_run": 25,
            "tests_passed": 240,
            "tests_failed": 3,
            "coverage": 0.88,
            "integration_points": [
                "API integration: PASS",
                "Database integration: PASS",
                "External service: FAIL (timeout)"
            ],
            "issues_found": [
                "External service timeout after 30s",
                "Data consistency issue in edge case"
            ]
        }

    async def _progress_monitor(self):
        """Monitor and report progress"""
        try:
            while True:
                await asyncio.sleep(5.0)  # Report every 5 seconds

                if self.progress["start_time"]:
                    elapsed = (datetime.now() - self.progress["start_time"]).total_seconds()
                    completion_rate = (
                        self.progress["completed_tasks"] / self.progress["total_tasks"]
                        if self.progress["total_tasks"] > 0 else 0
                    )

                    logger.info(
                        f"Progress: {self.progress['completed_tasks']}/"
                        f"{self.progress['total_tasks']} tasks "
                        f"({completion_rate:.1%}) - "
                        f"Elapsed: {elapsed:.1f}s"
                    )

        except asyncio.CancelledError:
            logger.info("Progress monitor stopped")

    def _all_tasks_completed(self) -> bool:
        """Check if all tasks are completed"""
        completed_statuses = {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.BLOCKED
        }

        return all(
            task.status in completed_statuses
            for task in self.tasks.values()
        )

    async def _generate_results(self) -> Dict[str, Any]:
        """Generate comprehensive execution results"""
        total_time = (
            (self.progress["end_time"] - self.progress["start_time"]).total_seconds()
            if self.progress["end_time"] and self.progress["start_time"]
            else 0
        )

        # Calculate sequential time (sum of all task estimates)
        sequential_time = sum(task.estimated_time for task in self.tasks.values())
        speedup = sequential_time / total_time if total_time > 0 else 1.0

        # Gather results by agent type
        results_by_type = {}
        for agent in self.agents.values():
            agent_type = agent.agent_type.value
            if agent_type not in results_by_type:
                results_by_type[agent_type] = {
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                    "total_time": 0,
                    "success_rate": 1.0,
                    "findings": [],
                    "recommendations": []
                }

            for task in agent.completed_tasks:
                if task.status == TaskStatus.COMPLETED:
                    results_by_type[agent_type]["tasks_completed"] += 1
                    results_by_type[agent_type]["total_time"] += task.result.get("execution_time", 0)

                    if task.result:
                        findings = task.result.get("findings", [])
                        recommendations = task.result.get("recommendations", [])
                        results_by_type[agent_type]["findings"].extend(findings)
                        results_by_type[agent_type]["recommendations"].extend(recommendations)

        return {
            "success": self.progress["failed_tasks"] == 0,
            "total_tasks": self.progress["total_tasks"],
            "tasks_completed": self.progress["completed_tasks"],
            "tasks_failed": self.progress["failed_tasks"],
            "tasks_blocked": self.progress["blocked_tasks"],
            "total_time": total_time,
            "sequential_time": sequential_time,
            "speedup": speedup,
            "started_at": self.progress["start_time"].isoformat() if self.progress["start_time"] else None,
            "completed_at": self.progress["end_time"].isoformat() if self.progress["end_time"] else None,
            "results_by_type": results_by_type,
            "agent_performance": {
                agent_id: {
                    "name": agent.name,
                    "type": agent.agent_type.value,
                    "tasks_completed": len(agent.completed_tasks),
                    "total_time": agent.total_time,
                    "success_rate": agent.success_rate
                }
                for agent_id, agent in self.agents.items()
            },
            "all_task_results": {
                task_id: {
                    "title": task.title,
                    "status": task.status.value,
                    "result": task.result,
                    "execution_time": (
                        (task.completed_at - task.started_at).total_seconds()
                        if task.completed_at and task.started_at
                        else None
                    ),
                    "assigned_to": task.assigned_to
                }
                for task_id, task in self.tasks.items()
            }
        }

    def print_summary(self, results: Dict[str, Any]):
        """Print execution summary"""
        print("\n" + "=" * 80)
        print("📊 PARALLEL TESTING EXECUTION SUMMARY")
        print("=" * 80)

        print(f"\n✅ Success: {results['success']}")
        print(f"📝 Total Tasks: {results['total_tasks']}")
        print(f"✓ Completed: {results['tasks_completed']}")
        print(f"✗ Failed: {results['tasks_failed']}")
        print(f"🚫 Blocked: {results['tasks_blocked']}")
        print(f"⏱️  Total Time: {results['total_time']:.2f}s")
        print(f"📊 Sequential Time: {results['sequential_time']:.2f}s")
        print(f"🚀 Speedup: {results['speedup']:.2f}x")

        # Print results by type
        print("\n" + "-" * 80)
        print("📋 RESULTS BY AGENT TYPE")
        print("-" * 80)

        for agent_type, type_results in results["results_by_type"].items():
            print(f"\n🤖 {agent_type.upper()} AGENT:")
            print(f"   Tasks Completed: {type_results['tasks_completed']}")
            print(f"   Total Time: {type_results['total_time']:.2f}s")

            if type_results["findings"]:
                print(f"   Key Findings:")
                for finding in type_results["findings"][:3]:
                    print(f"      • {finding}")

            if type_results["recommendations"]:
                print(f"   Recommendations:")
                for rec in type_results["recommendations"][:2]:
                    print(f"      • {rec}")

        # Print agent performance
        print("\n" + "-" * 80)
        print("🏆 AGENT PERFORMANCE")
        print("-" * 80)

        for agent_id, perf in results["agent_performance"].items():
            print(f"\n   Agent {agent_id} ({perf['name']}):")
            print(f"      Tasks: {perf['tasks_completed']}")
            print(f"      Time: {perf['total_time']:.2f}s")
            print(f"      Success Rate: {perf['success_rate']:.1%}")

        print("\n" + "=" * 80)

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parallel_testing_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {filename}")
        return filename


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parallel Testing Executor using TMLPD"
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Task IDs to execute"
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate task breakdown without executing"
    )
    parser.add_argument(
        "--output",
        help="Output file for results"
    )

    args = parser.parse_args()

    executor = ParallelTestingExecutor()

    if args.generate_only:
        # Generate and display task breakdown
        tasks = executor.create_testing_tasks()
        print("\n📋 GENERATED TESTING TASKS")
        print("=" * 80)

        for task in tasks:
            print(f"\n{task.id}: {task.title}")
            print(f"   Description: {task.description}")
            print(f"   Agent: {task.agent_type.value}")
            print(f"   Priority: {task.priority}")
            print(f"   Difficulty: {task.difficulty}")
            print(f"   Estimated Time: {task.estimated_time}s")
            if task.dependencies:
                print(f"   Dependencies: {', '.join(task.dependencies)}")

        return

    # Execute tasks
    results = await executor.execute_parallel_tasks(
        fail_on_error=False
    )

    # Print summary
    executor.print_summary(results)

    # Save results
    output_file = args.output
    if output_file:
        executor.save_results(results, output_file)


if __name__ == "__main__":
    asyncio.run(main())