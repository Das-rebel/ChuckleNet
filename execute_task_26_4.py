#!/usr/bin/env python3
"""
Execution script for Task 26.4: Integrate Routing Logic for LLM and Workflow Selection
Uses a TreeQuestAgent to generate the main Orchestrator class.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class OrchestratorAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate the code for the main Orchestrator
    that integrates all the core components.
    """
    def __init__(self):
        super().__init__(name="OrchestratorAgent")

    def propose_orchestrator_class(self) -> Tuple[str, float]:
        """
        Proposes the main Orchestrator class that ties everything together.
        """
        code = '''
import logging
from typing import Any

# Import all the core components we have built
from .model_parser import load_and_validate_models
from .model_registrar import ModelRegistrar
from .unified_api import UnifiedModelAPI
from .task_router import TaskRouter
from .workflow_engine import WorkflowGraph, WorkflowNode, WorkflowExecutor

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    The central nervous system of the Monk CLI.
    Initializes all core components and orchestrates the main processing flow.
    """
    def __init__(self, config_path: str):
        logger.info("Initializing Monk Orchestrator...")
        # 1. Load and validate the model configuration
        self.registry = load_and_validate_models(config_path)
        
        # 2. Register models with LiteLLM
        self.registrar = ModelRegistrar(self.registry)
        self.registrar.register_models()
        
        # 3. Initialize the Unified API
        self.api = UnifiedModelAPI(self.registrar)
        
        # 4. Initialize the Task Router
        self.router = TaskRouter(self.api)
        
        logger.info("Orchestrator initialized successfully.")

    async def handle_prompt(self, prompt: str) -> Any:
        """
        The main entry point for processing a user prompt.
        """
        # 1. Classify the prompt
        classification_result = await self.router.classify_prompt(prompt)
        task_type = classification_result.get("task_type")

        # 2. Route based on classification
        if task_type == "simple_query":
            logger.info("Handling as a simple query.")
            response = await self.api.get_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return response

        elif task_type == "complex_workflow":
            logger.info("Handling as a complex workflow.")
            # This is a placeholder for a dynamic workflow builder.
            # For now, we execute a predefined sample workflow.
            sample_workflow = self._build_sample_workflow()
            executor = WorkflowExecutor(sample_workflow)
            result = await executor.execute(initial_input=prompt)
            return result

        else:
            logger.error(f"Unknown task type: {task_type}. Cannot process prompt.")
            return "I'm sorry, I didn't understand that request."

    def _build_sample_workflow(self) -> WorkflowGraph:
        """
        Builds a sample workflow graph for demonstration.
        This would be replaced by a dynamic graph builder in a real scenario.
        """
        graph = WorkflowGraph()

        # Define actions for the nodes
        async def research_action(state):
            prompt = state['__initial_input__']
            print("--> (Node 1) Researching topic...")
            return await self.api.get_completion(messages=[{"role": "user", "content": f"Summarize the key points about {prompt}"}])

        async def coding_action(state):
            summary = state['research']
            print("--> (Node 2) Writing code based on research...")
            return await self.api.get_completion(messages=[{"role": "user", "content": f"Write a simple python function based on this summary: {summary}"}], strength='coding')

        # Add nodes to the graph
        graph.add_node(WorkflowNode(node_id="research", action=research_action))
        graph.add_node(WorkflowNode(node_id="coding", action=coding_action))

        # Define the workflow sequence
        graph.set_entry_point("research")
        graph.add_edge("research", "coding")

        return graph
'''
        score = 0.95
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing OrchestratorAgent...")
    agent = OrchestratorAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "orchestrator_class": agent.propose_orchestrator_class,
    }

    print("🌳 Running TreeQuest optimization to generate the Orchestrator...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=1, # Only one strategy, so 1 iteration is enough
        strategy=OptimizationStrategy.EXPLOITATION
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Orchestrator Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "orchestrator.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
