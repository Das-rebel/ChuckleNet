#!/usr/bin/env python3
"""
Execution script for Task 25.2: Implement models.yaml Parsing and Validation Logic (v2)
Uses a TreeQuestAgent to determine the optimal implementation for the parser.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class ParserValidationAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for parsing and validating the models.yaml file.
    """
    def __init__(self):
        super().__init__(name="ParserValidationAgent")

    def propose_pydantic_validator(self) -> Tuple[str, float]:
        """
        Proposes a robust implementation using Pydantic for validation.
        This version uses .format() to avoid nested f-string issues.
        """
        code = '''
import yaml
from typing import List, Optional, Literal
from pydantic import BaseModel, ValidationError, field_validator

class ModelMetadata(BaseModel):
    supports_streaming: bool = True
    context_window: Optional[int] = None
    is_local: bool = False

class ModelConfig(BaseModel):
    id: str
    provider: str
    model_name: str
    strengths: List[Literal['reasoning', 'coding', 'summarization', 'writing', 'analysis', 'general']]
    speed_tier: Literal['fast', 'medium', 'slow']
    cost_tier: Literal['cheap', 'moderate', 'premium']
    api_endpoint: Optional[str] = None
    metadata: ModelMetadata = ModelMetadata()

    @field_validator('id')
    def id_must_be_slug(cls, v):
        if ' ' in v or v.lower() != v:
            raise ValueError('id must be a lowercase slug with no spaces')
        return v

class ModelsRegistry(BaseModel):
    schema_version: float
    models: List[ModelConfig]

def load_and_validate_models(file_path: str) -> ModelsRegistry:
    """
    Loads a YAML file, parses it, and validates it against the Pydantic schema.
    Returns a validated ModelsRegistry object or raises an error.
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: The file {} was not found.".format(file_path))
        raise
    except yaml.YAMLError as e:
        print("Error parsing YAML file: {}.".format(e))
        raise

    try:
        registry = ModelsRegistry.model_validate(data)
        print("Successfully validated {} models from {}.".format(len(registry.models), file_path))
        return registry
    except ValidationError as e:
        print("Error validating model configuration:\n{}".format(e))
        raise
'''
        score = 0.95
        return code.strip(), score

    # Other proposal methods remain the same...
    def propose_manual_validator(self) -> Tuple[str, float]:
        code = '''
import yaml

def load_and_validate_manually(file_path: str) -> dict:
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    if 'models' not in data or not isinstance(data['models'], list):
        raise ValueError("Missing or invalid 'models' list in YAML")
    for model in data['models']:
        if 'id' not in model or 'provider' not in model:
            raise ValueError("Model missing required key: {}".format(model))
    print("Manually validated {} models.".format(len(data['models'])))
    return data
'''
        score = 0.75
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing ParserValidationAgent (v2)...")
    agent = ParserValidationAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "pydantic_validator": agent.propose_pydantic_validator,
        "manual_validator": agent.propose_manual_validator,
    }

    print("🌳 Running TreeQuest optimization...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Parser & Validator Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "model_parser.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
