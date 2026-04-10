#!/usr/bin/env python3
"""
TMLPD Python Wrapper
Calls TMLPD MCP server and returns classification + routing decisions
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, Optional
from pathlib import Path

class TMLPDWrapper:
    """Python wrapper for TMLPD MCP server"""

    def __init__(self, mcp_url: str = "ws://localhost:18790"):
        self.mcp_url = mcp_url
        self.skill_path = Path.home() / ".openclaw/skills/tmlpd-skill"

    def classify(self, prompt: str) -> Dict[str, Any]:
        """
        Classify query difficulty using TMLPD skill

        Returns:
            {
                "score": 0-100,
                "level": "trivial|easy|medium|hard|expert",
                "recommended": "haiku|gemini-flash|sonnet|tmlpd-parallel|tmlpd-halo",
                "confidence": 0.0-1.0
            }
        """
        try:
            # Use Node.js to call the skill directly
            result = subprocess.run(
                ["node", "-e", f"""
                const skill = require('{self.skill_path}/dist/index.js');
                const result = skill.tmlpd_classify_sync({json.dumps(prompt)});
                console.log(JSON.stringify(result));
                """],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return json.loads(result.stdout.strip())
            else:
                # Fallback: simple heuristic classification
                return self._simple_classify(prompt)

        except Exception as e:
            print(f"[TMLPD] Classification error: {e}", file=sys.stderr)
            return self._simple_classify(prompt)

    def _simple_classify(self, prompt: str) -> Dict[str, Any]:
        """Simple fallback classification"""
        prompt_lower = prompt.lower()
        length = len(prompt)
        words = prompt.split()

        # Basic scoring
        score = 10  # Base score

        # Length factor
        if length > 100: score += 10
        if length > 300: score += 15
        if length > 500: score += 15

        # Reasoning indicators
        reasoning_words = ['why', 'how', 'explain', 'analyze', 'compare', 'design']
        for word in reasoning_words:
            if word in prompt_lower:
                score += 10

        # Creativity indicators
        creative_words = ['write', 'create', 'design', 'generate']
        for word in creative_words:
            if word in prompt_lower:
                score += 10

        # Technical indicators
        tech_words = ['api', 'function', 'class', 'async', 'database', 'algorithm']
        for word in tech_words:
            if word in prompt_lower:
                score += 8

        score = min(100, score)

        # Determine level
        if score < 20:
            level, recommended = "trivial", "haiku"
        elif score < 40:
            level, recommended = "easy", "gemini-flash"
        elif score < 60:
            level, recommended = "medium", "sonnet"
        elif score < 80:
            level, recommended = "hard", "tmlpd-parallel"
        else:
            level, recommended = "expert", "tmlpd-halo"

        return {
            "score": score,
            "level": level,
            "recommended": recommended,
            "confidence": 0.7
        }

    async def execute_via_mcp(self, prompt: str, timeout: int = 60000) -> Dict[str, Any]:
        """
        Execute query via TMLPD MCP server

        Returns:
            {
                "success": bool,
                "content": str,
                "error": str (if failed),
                "duration": int
            }
        """
        try:
            # Call mcp_client.py which handles WebSocket communication
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "/Users/Subho/projects/openclaw-voice-chat/server/mcp_client_ws.py",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout / 1000
            )

            if proc.returncode == 0:
                return {
                    "success": True,
                    "content": stdout.decode().strip(),
                    "duration": 0
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode().strip(),
                    "duration": 0
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Timeout after {timeout}ms",
                "duration": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": 0
            }

    def should_use_tmlpd(self, prompt: str) -> bool:
        """
        Determine if query should use TMLPD (vs direct OpenClow)

        Returns True if:
        - Score >= 40 (medium or higher complexity)
        - AND TMLPD server is available
        """
        classification = self.classify(prompt)
        return classification["score"] >= 40


# Singleton instance
_tmlpd_wrapper: Optional[TMLPDWrapper] = None

def get_tmlpd_wrapper() -> TMLPDWrapper:
    global _tmlpd_wrapper
    if _tmlpd_wrapper is None:
        _tmlpd_wrapper = TMLPDWrapper()
    return _tmlpd_wrapper


if __name__ == "__main__":
    # Test classification
    wrapper = TMLPDWrapper()

    test_prompts = [
        "What is 2+2?",
        "Explain async/await in Python",
        "Design a REST API with JWT authentication",
        "Create a scalable microservices architecture for e-commerce"
    ]

    print("=== TMLPD Classification Test ===\n")
    for prompt in test_prompts:
        result = wrapper.classify(prompt)
        print(f"Prompt: {prompt}")
        print(f"  Score: {result['score']}")
        print(f"  Level: {result['level']}")
        print(f"  Recommended: {result['recommended']}")
        print(f"  Use TMLPD: {wrapper.should_use_tmlpd(prompt)}")
        print()
