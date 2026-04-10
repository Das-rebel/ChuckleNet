#!/usr/bin/env python3
"""
TMLPD Agent Executor for OpenClow
Routes queries to appropriate model based on difficulty classification
"""

import asyncio
import json
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
TMLPD_MCP_PORT = 18790
TMLPD_THRESHOLD = 40  # Use TMLPD for score >= 40
OPENCLAW_DEFAULT_AGENT = "main"
LOG_FILE = "/tmp/openclaw/tmlpd-agent.log"

class TMLPDAgent:
    """TMLPD routing agent for OpenClow"""

    def __init__(self):
        self.log_file = Path(LOG_FILE)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log to file and stderr"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_line)
        
        if level in ["ERROR", "WARN"]:
            print(log_line.strip(), file=sys.stderr)

    def classify(self, prompt: str) -> Dict[str, Any]:
        """Classify query difficulty"""
        prompt_lower = prompt.lower()
        
        # Quick classification (8-factor scoring simplified)
        score = 10  # Base score
        
        # Length factor
        if len(prompt) > 100: score += 5
        if len(prompt) > 300: score += 10
        if len(prompt) > 500: score += 15
        
        # Word count
        words = prompt.split()
        if len(words) > 20: score += 5
        if len(words) > 50: score += 10
        
        # Keywords
        reasoning = ['why', 'how', 'explain', 'analyze', 'compare', 'evaluate', 'design', 'optimize']
        creative = ['write', 'create', 'design', 'generate', 'compose']
        technical = ['api', 'function', 'class', 'async', 'database', 'algorithm']
        complex = ['architecture', 'scalability', 'system', 'infrastructure', 'distributed']
        
        for kw in reasoning:
            if kw in prompt_lower: score += 8
        for kw in creative:
            if kw in prompt_lower: score += 8
        for kw in technical:
            if kw in prompt_lower: score += 6
        for kw in complex:
            if kw in prompt_lower: score += 12
        
        score = min(100, score)
        
        # Determine level and route
        if score < 30:
            level, route, model = "TRIVIAL", "direct", "haiku"
        elif score < 50:
            level, route, model = "EASY", "direct", "gemini-flash"
        elif score < 70:
            level, route, model = "MEDIUM", "tmlpd", "sonnet"
        elif score < 85:
            level, route, model = "HARD", "tmlpd-parallel", "multi-model"
        else:
            level, route, model = "EXPERT", "tmlpd-parallel", "multi-model"
        
        return {
            "score": score,
            "level": level,
            "route": route,
            "model": model
        }

    async def execute_via_tmlpd(self, prompt: str, timeout: int = 60000) -> Dict[str, Any]:
        """Execute via TMLPD MCP server"""
        self.log(f"Executing via TMLPD MCP server", "INFO")
        
        try:
            # Use MCP client
            mcp_client = Path("/Users/Subho/projects/openclaw-voice-chat/server/mcp_client_ws.py")
            
            if not mcp_client.exists():
                self.log(f"MCP client not found: {mcp_client}", "ERROR")
                return {"success": False, "error": "MCP client not found"}
            
            proc = await asyncio.create_subprocess_exec(
                sys.executable, str(mcp_client),
                "--execute", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout / 1000
            )
            
            if proc.returncode == 0:
                content = stdout.decode().strip()
                self.log(f"TMLPD execution succeeded: {len(content)} chars", "SUCCESS")
                return {"success": True, "content": content, "source": "tmlpd"}
            else:
                error = stderr.decode().strip()
                self.log(f"TMLPD execution failed: {error[:100]}", "ERROR")
                return {"success": False, "error": error}
                
        except asyncio.TimeoutError:
            self.log(f"TMLPD execution timed out", "WARN")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            self.log(f"TMLPD execution error: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    async def execute_direct(self, prompt: str, timeout: int = 60000) -> Dict[str, Any]:
        """Execute directly via OpenClow"""
        self.log(f"Executing directly via OpenClow", "INFO")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                'openclaw', 'agent', '--local', '--agent', OPENCLAW_DEFAULT_AGENT,
                '--message', prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(os.environ), 'PATH': os.environ.get('PATH', '')}
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout / 1000
            )
            
            if proc.returncode == 0:
                response = stdout.decode().strip()
                # Clean response
                lines = [l for l in response.split('\n') if l.strip() and not l.startswith('│')]
                content = '\n'.join(lines) if lines else response
                self.log(f"Direct execution succeeded: {len(content)} chars", "SUCCESS")
                return {"success": True, "content": content, "source": "openclaw"}
            else:
                error = stderr.decode().strip()
                self.log(f"Direct execution failed: {error[:100]}", "ERROR")
                return {"success": False, "error": error}
                
        except asyncio.TimeoutError:
            self.log(f"Direct execution timed out", "WARN")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            self.log(f"Direct execution error: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    async def execute(self, prompt: str) -> Dict[str, Any]:
        """Main execution entry point"""
        start_time = datetime.now()
        
        self.log(f"=" * 60, "INFO")
        self.log(f"TMLPD Agent execution started", "INFO")
        self.log(f"Prompt: {prompt[:100]}...", "INFO")
        
        # Classify the query
        classification = self.classify(prompt)
        self.log(f"Classification: {classification['level']} (score: {classification['score']})", "INFO")
        self.log(f"Route: {classification['route']} → {classification['model']}", "INFO")
        
        # Execute based on route
        if classification['route'] == 'direct':
            result = await self.execute_direct(prompt)
        else:
            # Try TMLPD first, fallback to direct
            result = await self.execute_via_tmlpd(prompt)
            
            if not result['success']:
                self.log(f"Falling back to direct execution", "WARN")
                result = await self.execute_direct(prompt)
        
        # Record duration
        duration = (datetime.now() - start_time).total_seconds()
        result['duration'] = duration
        result['classification'] = classification
        
        self.log(f"Execution completed in {duration:.1f}s", "INFO")
        self.log(f"=" * 60, "INFO")
        
        return result


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: openclaw_tmlpd_agent.py <prompt>", file=sys.stderr)
        sys.exit(1)
    
    prompt = sys.argv[1]
    agent = TMLPDAgent()
    
    result = await agent.execute(prompt)
    
    if result['success']:
        print(result['content'])
        sys.exit(0)
    else:
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
