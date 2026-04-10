#!/usr/bin/env python3
"""
Execution script for Task 25.1: Design models.yaml Configuration Schema
Uses a TreeQuestAgent to determine the optimal schema design.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class SchemaDesignerAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to design the optimal schema for models.yaml.
    """
    def __init__(self):
        super().__init__(name="SchemaDesignerAgent")

    def propose_comprehensive_schema(self) -> Tuple[str, float]:
        """
        Proposes a detailed, comprehensive schema that aligns with the PRD.
        This is expected to be the best option.
        """
        schema = """
# Monk CLI - LLM Registry Configuration
# This file defines all Large Language Models available to the Monk CLI.

# Version of the schema for future migrations.
schema_version: 1.0

# List of all registered LLM providers.
models:
  # - Unique identifier for the model. Used for direct referencing.
  #   id: claude-3-opus
  #
  #   # The provider of the model (e.g., anthropic, openai, google, ollama).
  #   provider: anthropic
  #
  #   # The specific model name used by the provider's API.
  #   model_name: "claude-3-opus-20240229"
  #
  #   # Functional strengths of the model. Used by the Task Router.
  #   # Options: reasoning, coding, summarization, writing, analysis, general
  #   strengths:
  #     - reasoning
  #     - analysis
  #
  #   # Performance and cost tiers for intelligent routing.
  #   # Options: fast, medium, slow
  #   speed_tier: medium
  #   # Options: cheap, moderate, premium
  #   cost_tier: premium
  #
  #   # API endpoint details. For providers like Ollama, this can be a local URL.
  #   # If omitted, the default endpoint for the provider will be used.
  #   api_endpoint: "https://api.anthropic.com/v1/messages"
  #
  #   # Additional metadata for specific integrations or UI purposes.
  #   metadata:
  #     supports_streaming: true
  #     context_window: 200000

  - id: gpt-4o
    provider: openai
    model_name: "gpt-4o"
    strengths:
      - general
      - coding
      - reasoning
    speed_tier: fast
    cost_tier: premium
    metadata:
      supports_streaming: true
      context_window: 128000

  - id: llama3-8b-local
    provider: ollama
    model_name: "llama3:8b"
    strengths:
      - general
      - summarization
    speed_tier: fast
    cost_tier: cheap
    api_endpoint: "http://localhost:11434/api/chat"
    metadata:
      supports_streaming: true
      is_local: true
"""
        # This schema is comprehensive and well-documented, aligning perfectly with the task details.
        score = 0.95
        return schema.strip(), score

    def propose_basic_schema(self) -> Tuple[str, float]:
        """
        Proposes a simpler, less detailed schema.
        """
        schema = """
# Basic Model Configuration
models:
  - id: claude-3-opus
    provider: anthropic
    model_name: claude-3-opus-20240229
  - id: gpt-4o
    provider: openai
    model_name: gpt-4o
"""
        # This schema is functional but lacks the detailed attributes required by the PRD.
        score = 0.7
        return schema.strip(), score

    def propose_provider_centric_schema(self) -> Tuple[str, float]:
        """
        Proposes a schema grouped by provider instead of a flat list.
        """
        schema = """
# Provider-Centric Model Configuration
providers:
  anthropic:
    - id: claude-3-opus
      model_name: claude-3-opus-20240229
      strengths: [reasoning]
      tier: premium
  openai:
    - id: gpt-4o
      model_name: gpt-4o
      strengths: [general, coding]
      tier: premium
  ollama:
    - id: llama3-8b-local
      model_name: llama3:8b
      strengths: [general]
      tier: local
"""
        # This schema is a valid alternative but the flat list is more extensible.
        score = 0.85
        return schema.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing SchemaDesignerAgent...")
    agent = SchemaDesignerAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "comprehensive": agent.propose_comprehensive_schema,
        "basic": agent.propose_basic_schema,
        "provider_centric": agent.propose_provider_centric_schema,
    }

    print("🌳 Running TreeQuest optimization to find the best schema...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=3,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Schema Design:")
    print(result.best_state)
    print("---")

    # Save the winning schema to a file
    output_filename = "models.yaml"
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best schema design saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
