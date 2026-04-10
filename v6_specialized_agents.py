"""
Specialized LLM Agents for V6 Parallel Task Execution

This module implements specialized agents designed to work on specific categories
of V6 tasks in parallel, leveraging the existing TreeQuest and TaskMaster infrastructure.

Author: Claude AI Assistant
Date: 2025-09-23
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pathlib import Path

# Import existing monk infrastructure
import sys
sys.path.append('/Users/Subho/monk')

from core.treequest_cli import TreeQuestAgent
from core.intelligent_router import IntelligentRouter
from core.performance_monitor import PerformanceMonitor
from agents.task_specialized_agents import SpecializedAgentBase

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class TaskResult:
    task_id: str
    status: str
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    quality_score: float = 0.0
    dependencies_completed: List[str] = field(default_factory=list)

@dataclass
class AgentCapabilities:
    primary_skills: List[str]
    secondary_skills: List[str]
    max_concurrent_tasks: int = 3
    quality_threshold: float = 0.85
    preferred_providers: List[str] = field(default_factory=lambda: ["anthropic", "openai"])

class V6SpecializedAgent(SpecializedAgentBase):
    """Base class for V6 specialized agents with enhanced parallel capabilities"""

    def __init__(self, agent_id: str, capabilities: AgentCapabilities, work_dir: str = "/Users/Subho"):
        super().__init__(agent_id)
        self.capabilities = capabilities
        self.work_dir = Path(work_dir)
        self.status = AgentStatus.IDLE
        self.current_tasks: Dict[str, Dict] = {}
        self.completed_tasks: List[TaskResult] = []
        self.performance_monitor = PerformanceMonitor()
        self.router = IntelligentRouter()

        # Enhanced parallel execution
        self.task_semaphore = asyncio.Semaphore(capabilities.max_concurrent_tasks)
        self.task_queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None

        # Agent specialization metrics
        self.specialization_score = 0.0
        self.success_rate = 0.0
        self.average_quality = 0.0

    async def initialize(self) -> bool:
        """Initialize agent with TreeQuest and required systems"""
        try:
            await self.router.initialize()
            self.performance_monitor.start_monitoring()

            # Start worker task for parallel execution
            self.worker_task = asyncio.create_task(self._task_worker())

            logging.info(f"Agent {self.agent_id} initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize agent {self.agent_id}: {e}")
            return False

    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a single task with performance monitoring"""
        task_id = task.get('id', 'unknown')
        start_time = time.time()

        try:
            async with self.task_semaphore:
                self.status = AgentStatus.WORKING
                self.current_tasks[task_id] = task

                # Route to appropriate LLM provider
                provider = await self._select_provider(task)

                # Execute with quality monitoring
                result = await self._execute_with_quality_check(task, provider)

                execution_time = time.time() - start_time
                quality_score = await self._calculate_quality_score(task, result)

                task_result = TaskResult(
                    task_id=task_id,
                    status="completed",
                    result=result,
                    execution_time=execution_time,
                    quality_score=quality_score
                )

                # Update metrics
                self._update_metrics(task_result)

                return task_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = TaskResult(
                task_id=task_id,
                status="failed",
                error=str(e),
                execution_time=execution_time
            )

            logging.error(f"Task {task_id} failed: {e}")
            return error_result

        finally:
            self.current_tasks.pop(task_id, None)
            if not self.current_tasks:
                self.status = AgentStatus.IDLE

    async def execute_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[TaskResult]:
        """Execute multiple tasks in parallel with dependency management"""
        # Group tasks by dependencies
        task_groups = await self._group_tasks_by_dependencies(tasks)

        all_results = []

        # Execute groups sequentially, tasks within groups in parallel
        for group in task_groups:
            group_tasks = [tasks[i] for i in group]
            group_futures = [self.execute_task(task) for task in group_tasks]
            group_results = await asyncio.gather(*group_futures, return_exceptions=True)

            # Process results and handle exceptions
            for i, result in enumerate(group_results):
                if isinstance(result, Exception):
                    task_id = group_tasks[i].get('id', 'unknown')
                    error_result = TaskResult(
                        task_id=task_id,
                        status="failed",
                        error=str(result)
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)

        return all_results

    async def _task_worker(self):
        """Background worker for processing queued tasks"""
        while True:
            try:
                task = await self.task_queue.get()
                await self.execute_task(task)
                self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Worker error: {e}")

    async def _select_provider(self, task: Dict[str, Any]) -> str:
        """Select optimal provider based on task characteristics"""
        task_type = task.get('type', 'general')
        complexity = task.get('complexity', 'medium')

        # Use intelligent router for provider selection
        provider_selection = await self.router.route_task(
            task_description=task.get('description', ''),
            task_type=task_type,
            complexity=complexity,
            preferred_providers=self.capabilities.preferred_providers
        )

        return provider_selection.get('provider', 'anthropic')

    async def _execute_with_quality_check(self, task: Dict[str, Any], provider: str) -> Any:
        """Execute task with quality validation"""
        # This would integrate with TreeQuest for actual execution
        # For now, placeholder implementation
        task_description = task.get('description', '')

        # Execute with TreeQuest
        result = await self.router.execute_with_provider(
            prompt=task_description,
            provider=provider,
            context=task.get('context', {})
        )

        return result

    async def _calculate_quality_score(self, task: Dict[str, Any], result: Any) -> float:
        """Calculate quality score for task execution"""
        # Implement quality scoring based on task type and results
        base_score = 0.8

        # Adjust based on execution time and completeness
        if result and isinstance(result, dict):
            completeness = result.get('completeness', 0.8)
            accuracy = result.get('accuracy', 0.8)
            base_score = (completeness + accuracy) / 2

        return min(base_score, 1.0)

    async def _group_tasks_by_dependencies(self, tasks: List[Dict[str, Any]]) -> List[List[int]]:
        """Group tasks by dependencies for parallel execution"""
        # Simple dependency grouping - can be enhanced
        task_groups = []
        processed = set()

        for i, task in enumerate(tasks):
            if i in processed:
                continue

            dependencies = task.get('dependencies', [])
            if not dependencies or all(dep in processed for dep in dependencies):
                # Can execute in parallel
                parallel_group = [i]

                # Find other tasks that can run in parallel
                for j, other_task in enumerate(tasks[i+1:], i+1):
                    if j in processed:
                        continue

                    other_deps = other_task.get('dependencies', [])
                    if not other_deps or all(dep in processed for dep in other_deps):
                        parallel_group.append(j)

                task_groups.append(parallel_group)
                processed.update(parallel_group)
            else:
                # Task has unmet dependencies, handle in next iteration
                pass

        return task_groups

    def _update_metrics(self, result: TaskResult):
        """Update agent performance metrics"""
        if result.status == "completed":
            self.completed_tasks.append(result)

            # Update specialization score
            if len(self.completed_tasks) > 0:
                recent_quality = sum(t.quality_score for t in self.completed_tasks[-10:]) / min(10, len(self.completed_tasks))
                self.average_quality = recent_quality

                # Calculate success rate
                successful_tasks = sum(1 for t in self.completed_tasks if t.status == "completed")
                self.success_rate = successful_tasks / len(self.completed_tasks)

                # Update specialization score
                self.specialization_score = (self.average_quality * 0.7) + (self.success_rate * 0.3)

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "specialization_score": self.specialization_score,
            "success_rate": self.success_rate,
            "average_quality": self.average_quality,
            "capabilities": self.capabilities.__dict__
        }

    async def shutdown(self):
        """Shutdown agent gracefully"""
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        self.performance_monitor.stop_monitoring()
        logging.info(f"Agent {self.agent_id} shutdown complete")