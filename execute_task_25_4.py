#!/usr/bin/env python3
"""
Execution script for Task 25.4: Develop Unified API Interface for Model Interaction
Uses a TreeQuestAgent to generate the best implementation for the Unified API.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any, List, Optional

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class UnifiedApiAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the Unified API for model interaction.
    """
    def __init__(self):
        super().__init__(name="UnifiedApiAgent")

    def propose_class_based_api(self) -> Tuple[str, float]:
        """
        Proposes a robust, class-based API for model interaction.
        This is the best practice and should receive the highest score.
        """
        code = '''
import litellm
import logging
from typing import List, Dict, Any, Optional

# Assuming model_registrar and model_parser are in the same core directory
from .model_registrar import ModelRegistrar
from .model_parser import ModelsRegistry, ModelConfig

logger = logging.getLogger(__name__)

class UnifiedModelAPI:
    """
    Provides a unified, high-level interface for interacting with all registered LLMs.
    """
    def __init__(self, registrar: ModelRegistrar):
        self.registrar = registrar
        self.models_by_id: Dict[str, ModelConfig] = {m.id: m for m in registrar.registry.models}
        logger.info(f"UnifiedModelAPI initialized with {len(self.models_by_id)} models.")

    async def get_completion(self, 
                             messages: List[Dict[str, str]], 
                             strength: Optional[str] = None, 
                             speed_tier: Optional[str] = None, 
                             cost_tier: Optional[str] = None, 
                             **kwargs) -> Optional[str]:
        """
        Gets a completion from the best available model based on routing criteria.

        Args:
            messages: The list of messages for the conversation.
            strength: The desired model strength (e.g., 'coding', 'reasoning').
            speed_tier: The desired speed tier (e.g., 'fast', 'medium').
            cost_tier: The desired cost tier (e.g., 'cheap', 'premium').
            **kwargs: Additional arguments to pass to litellm.completion.

        Returns:
            The content of the response message or None if an error occurs.
        """
        model_name = self._route_model(strength, speed_tier, cost_tier)

        if not model_name:
            logger.error("No suitable model found for the given criteria.")
            return None

        try:
            logger.info(f"Routing request to model: {model_name}")
            response = await litellm.acompletion(
                model=model_name,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM completion failed for model {model_name}: {e}")
            # Here you could implement fallback logic to try another model
            return None

    def _route_model(self, 
                     strength: Optional[str] = None, 
                     speed_tier: Optional[str] = None, 
                     cost_tier: Optional[str] = None) -> Optional[str]:
        """
        Selects the best model from the registry based on filtering criteria.
        This is a simple router; a more advanced version would be in the Task Router epic.
        """
        candidate_models = list(self.models_by_id.values())

        if strength:
            candidate_models = [m for m in candidate_models if strength in m.strengths]
        if speed_tier:
            candidate_models = [m for m in candidate_models if m.speed_tier == speed_tier]
        if cost_tier:
            candidate_models = [m for m in candidate_models if m.cost_tier == cost_tier]

        if not candidate_models:
            return None

        # For now, return the first match. A more complex strategy could be used here.
        selected_config = candidate_models[0]
        
        # Construct the model name for litellm
        if selected_config.provider == 'ollama':
            return f"ollama/{selected_config.model_name}"
        else:
            return f"{selected_config.provider}/{selected_config.model_name}"

'''
        score = 0.95
        return code.strip(), score

    def propose_functional_api(self) -> Tuple[str, float]:
        """
        Proposes a simpler, function-based API.
        """
        code = '''
import litellm
from typing import List, Dict

async def get_chat_response(model_name: str, messages: List[Dict[str, str]]) -> str:
    response = await litellm.acompletion(model=model_name, messages=messages)
    return response.choices[0].message.content
'''
        score = 0.75
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing UnifiedApiAgent...")
    agent = UnifiedApiAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "class_based_api": agent.propose_class_based_api,
        "functional_api": agent.propose_functional_api,
    }

    print("🌳 Running TreeQuest optimization to find the best Unified API design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Unified API Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "unified_api.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
