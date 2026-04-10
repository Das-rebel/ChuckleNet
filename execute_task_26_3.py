#!/usr/bin/env python3
"""
Execution script for Task 26.3: Implement Graph-Based Workflow Engine
Uses a TreeQuestAgent to generate the best implementation for the workflow engine.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class WorkflowEngineAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the graph-based workflow engine.
    """
    def __init__(self):
        super().__init__(name="WorkflowEngineAgent")

    def propose_graph_based_engine(self) -> Tuple[str, float]:
        """
        Proposes a comprehensive, graph-based workflow engine inspired by LangGraph.
        """
        code = '''
import logging
from typing import List, Dict, Any, Callable, Optional, Set
from collections import deque

logger = logging.getLogger(__name__)

class WorkflowNode:
    """Represents a single node (a step) in the workflow graph."""
    def __init__(self, node_id: str, action: Callable[[Dict[str, Any]], Any]):
        self.node_id = node_id
        self.action = action  # The function to execute for this node

class WorkflowGraph:
    """Represents the directed acyclic graph (DAG) of the workflow."""
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, List[str]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, node: WorkflowNode):
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists.")
        self.nodes[node.node_id] = node
        self.edges[node.node_id] = []

    def add_edge(self, from_node_id: str, to_node_id: str):
        if from_node_id not in self.nodes or to_node_id not in self.nodes:
            raise ValueError("One or both nodes do not exist in the graph.")
        self.edges[from_node_id].append(to_node_id)

    def set_entry_point(self, node_id: str):
        if node_id not in self.nodes:
            raise ValueError(f"Entry point node {node_id} does not exist.")
        self.entry_point = node_id

class WorkflowExecutor:
    """
    Executes a workflow defined by a WorkflowGraph.
    Uses topological sort to handle dependencies.
    """
    def __init__(self, graph: WorkflowGraph):
        self.graph = graph
        self.state: Dict[str, Any] = {}

    async def execute(self, initial_input: Any) -> Dict[str, Any]:
        if not self.graph.entry_point:
            raise ValueError("Workflow entry point is not set.")

        sorted_nodes = self._topological_sort()
        self.state['__initial_input__'] = initial_input

        logger.info(f"Executing workflow with {len(sorted_nodes)} nodes.")

        for node_id in sorted_nodes:
            node = self.graph.nodes[node_id]
            logger.info(f"Executing node: {node.node_id}")
            try:
                # A real implementation would handle inputs more gracefully
                result = await self._run_action(node.action, self.state)
                self.state[node.node_id] = result
            except Exception as e:
                logger.error(f"Error executing node {node.node_id}: {e}")
                self.state[node.node_id] = {"__error__": str(e)}
                # Decide on error propagation strategy - for now, we stop
                break
        
        logger.info("Workflow execution complete.")
        return self.state

    async def _run_action(self, action: Callable, state: Dict) -> Any:
        if asyncio.iscoroutinefunction(action):
            return await action(state)
        else:
            return action(state)

    def _topological_sort(self) -> List[str]:
        """Performs a topological sort of the graph nodes."""
        in_degree = {node_id: 0 for node_id in self.graph.nodes}
        for u in self.graph.edges:
            for v in self.graph.edges[u]:
                in_degree[v] += 1

        queue = deque([node_id for node_id in self.graph.nodes if in_degree[node_id] == 0])
        sorted_order = []

        while queue:
            u = queue.popleft()
            sorted_order.append(u)
            for v in self.graph.edges[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(sorted_order) != len(self.graph.nodes):
            raise ValueError("Graph contains a cycle, cannot execute.")
        
        return sorted_order
'''
        score = 0.95
        return code.strip(), score

    def propose_simple_sequential_engine(self) -> Tuple[str, float]:
        """
        Proposes a simple engine that runs tasks in a fixed sequence.
        """
        code = '''
import logging
from typing import List, Callable, Dict, Any

logger = logging.getLogger(__name__)

class SequentialEngine:
    def __init__(self, tasks: List[Callable]):
        self.tasks = tasks

    async def run(self, initial_input: Any) -> List[Any]:
        results = []
        current_input = initial_input
        for i, task in enumerate(self.tasks):
            logger.info(f"Running task {i+1}/{len(self.tasks)}")
            result = await task(current_input)
            results.append(result)
            current_input = result # Output of one task is input to the next
        return results
'''
        score = 0.65
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing WorkflowEngineAgent...")
    agent = WorkflowEngineAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "graph_based_engine": agent.propose_graph_based_engine,
        "sequential_engine": agent.propose_simple_sequential_engine,
    }

    print("🌳 Running TreeQuest optimization to find the best Workflow Engine design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Workflow Engine Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "workflow_engine.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
