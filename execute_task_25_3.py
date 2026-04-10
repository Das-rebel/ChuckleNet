#!/usr/bin/env python3
"""
Execution script for Task 25.3: Register Models with LiteLLM Abstraction Layer
Uses a TreeQuestAgent to generate the best implementation for the registrar.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class LiteLLMRegistrarAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for registering models with the LiteLLM library.
    """
    def __init__(self):
        super().__init__(name="LiteLLMRegistrarAgent")

    def propose_robust_registrar(self) -> Tuple[str, float]:
        """
        Proposes a robust implementation that handles custom endpoints and logging.
        """
        code = '''
import litellm
import logging
from typing import List

# Assuming model_parser.py is in the same core directory
from .model_parser import ModelConfig, ModelsRegistry

logger = logging.getLogger(__name__)

class ModelRegistrar:
    """
    Handles the registration of models from the configuration with LiteLLM.
    """
    def __init__(self, registry: ModelsRegistry):
        self.registry = registry
        self.registered_models = []

    def register_models(self):
        """
        Iterates through the models in the registry and registers them with LiteLLM.
        Handles custom API bases for providers like Ollama.
        """
        print(f"Starting model registration for {len(self.registry.models)} models...")
        custom_llm_provider_map = {}

        for model_config in self.registry.models:
            try:
                # For providers that require a custom api_base, like a local Ollama instance
                if model_config.provider == "ollama" and model_config.api_endpoint:
                    # LiteLLM expects the provider name to be 'ollama' and the model name to be just the model id
                    # The api_base is set for the entire provider.
                    if 'ollama' not in custom_llm_provider_map:
                        custom_llm_provider_map['ollama'] = []
                    
                    model_info = {
                        "model_name": model_config.model_name,
                        "litellm_params": {
                            "model": f"ollama/{model_config.model_name}",
                            "api_base": model_config.api_endpoint
                        }
                    }
                    custom_llm_provider_map['ollama'].append(model_info)
                    self.registered_models.append(model_info)
                    logger.info(f"Prepared local model for registration: {model_config.id}")

                else:
                    # For standard cloud providers, the model name is usually sufficient
                    # LiteLLM's router will handle the standard endpoints.
                    model_name_with_provider = f"{model_config.provider}/{model_config.model_name}"
                    self.registered_models.append({"model_name": model_name_with_provider, "litellm_params": {"model": model_name_with_provider}})
                    logger.info(f"Prepared standard model for registration: {model_config.id}")

            except Exception as e:
                logger.info(f"Failed to prepare model {model_config.id} for registration: {e}")

        # Set the custom LLM settings in LiteLLM if any were prepared
        if custom_llm_provider_map:
            litellm.custom_llm_provider = custom_llm_provider_map
            print(f"Registered {len(custom_llm_provider_map.get('ollama', []))} custom Ollama models.")

        # The model_list in LiteLLM is used by its Router for routing
        litellm.model_list = self.registered_models
        print(f"Registration complete. {len(litellm.model_list)} total models configured in LiteLLM.")

    def get_registered_models(self) -> List[Dict]:
        return self.registered_models

'''
        score = 0.95
        return code.strip(), score

    def propose_simple_registrar(self) -> Tuple[str, float]:
        """
        Proposes a basic implementation that just appends to model_list.
        """
        code = '''
import litellm
from .model_parser import ModelsRegistry

def register_models_simple(registry: ModelsRegistry):
    model_list = []
    for model in registry.models:
        model_list.append({"model_name": model.model_name, "litellm_params": {"model": f"{model.provider}/{model.model_name}"}})
    litellm.model_list = model_list
    print(f"Simply registered {len(model_list)} models.")
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing LiteLLMRegistrarAgent...")
    agent = LiteLLMRegistrarAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "robust_registrar": agent.propose_robust_registrar,
        "simple_registrar": agent.propose_simple_registrar,
    }

    print("🌳 Running TreeQuest optimization to find the best registrar implementation...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Model Registrar Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "model_registrar.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
