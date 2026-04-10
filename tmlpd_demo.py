#!/usr/bin/env python3
"""
Enhanced TMLPD Multi-Agent Deployment Demo
Shows different ways to deploy multiple AI agents using your existing TMLPD setup
"""

import subprocess
import sys
from pathlib import Path

class TMLPDDeploymentDemo:
    def __init__(self):
        self.tmlpd_dir = Path("~/tmlpd-clean").expanduser()
        self.treequest_bin = "/Users/Subho/.local/bin/treequest"

    def show_available_options(self):
        """Show all available TMLPD deployment options"""
        print("🚀 AVAILABLE TMLPD MULTI-AGENT DEPLOYMENT OPTIONS")
        print("=" * 60)

        options = [
            {
                "name": "TreeQuest Parallel",
                "command": "treequest-parallel",
                "description": "Deploy multiple TreeQuest agents in parallel using different providers",
                "status": self.check_command("treequest-parallel")
            },
            {
                "name": "TMLPD Codex CLI",
                "command": "tmlpd-codex",
                "description": "Use TMLPD with Codex integration for complex task orchestration",
                "status": self.check_file("~/tmlpd-clean/tmlpd_codex.py")
            },
            {
                "name": "TreeQuest Status",
                "command": "treequest status",
                "description": "Check available providers and system status",
                "status": "checked"
            },
            {
                "name": "TMLPD Service",
                "file": "~/tmlpd-clean/tmlpd_service.py",
                "description": "Run TMLPD as a service for agent orchestration",
                "status": self.check_file("~/tmlpd-clean/tmlpd_service.py")
            },
            {
                "name": "MCP Server",
                "file": "~/tmlpd-clean/mcp_server.py",
                "description": "Start TMLPD MCP server for advanced agent management",
                "status": self.check_file("~/tmlpd-clean/mcp_server.py")
            }
        ]

        for i, option in enumerate(options, 1):
            status_icon = "✅" if option["status"] else "❌"
            print(f"{i}. {status_icon} **{option['name']}**")
            print(f"   Description: {option['description']}")
            if option.get("command"):
                print(f"   Command: {option['command']}")
            if option.get("file"):
                print(f"   File: {option['file']}")
            print()

    def check_command(self, cmd):
        """Check if a command is available"""
        try:
            result = subprocess.run(["which", cmd], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_file(self, file_path):
        """Check if a file exists"""
        return Path(file_path).expanduser().exists()

    def demo_treequery_parallel(self):
        """Demonstrate TreeQuest parallel execution"""
        print("🔄 DEMONSTRATING TREEQUEST PARALLEL EXECUTION")
        print("=" * 50)

        # Check current TreeQuest status
        print("📊 Current TreeQuest Status:")
        try:
            result = subprocess.run(
                [self.treequest_bin, "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout)
        except Exception as e:
            print(f"❌ Error checking status: {e}")

    def demo_provider_diversification(self):
        """Show provider diversification strategy"""
        print("🤖 MULTI-PROVIDER STRATEGY")
        print("=" * 40)

        providers = [
            {"name": "Anthropic (Claude)", "use": "Complex reasoning, code generation", "speed": "medium"},
            {"name": "Cerebras (Qwen)", "use": "235B params, complex tasks", "speed": "fast"},
            {"name": "Groq (Llama)", "use": "Ultra-fast responses (0.14s)", "speed": "ultra-fast"},
            {"name": "Mistral", "use": "Balanced speed/quality", "speed": "fast"},
            {"name": "Ollama (Local)", "use": "Privacy, local processing", "speed": "variable"}
        ]

        for provider in providers:
            print(f"• **{provider['name']}**")
            print(f"  Use Case: {provider['use']}")
            print(f"  Speed: {provider['speed']}")
            print()

    def create_parallel_deployment_example(self):
        """Create a practical example of parallel deployment"""
        print("💡 PRACTICAL PARALLEL DEPLOYMENT EXAMPLE")
        print("=" * 50)

        example_tasks = [
            {
                "task": "Code Analysis",
                "provider": "anthropic",
                "reason": "Requires deep reasoning and code understanding"
            },
            {
                "task": "Quick API Testing",
                "provider": "groq",
                "reason": "Needs ultra-fast iteration (0.14s response)"
            },
            {
                "task": "Documentation Generation",
                "provider": "cerebras",
                "reason": "Large language model for comprehensive docs"
            },
            {
                "task": "Performance Optimization",
                "provider": "mistral",
                "reason": "Good balance of speed and quality"
            },
            {
                "task": "Local Data Processing",
                "provider": "ollama",
                "reason": "Privacy and local control"
            }
        ]

        print("🚀 **Parallel Task Allocation Strategy:**")
        for i, task in enumerate(example_tasks, 1):
            print(f"{i}. **{task['task']}** → {task['provider'].upper()}")
            print(f"   Reason: {task['reason']}")
            print()

    def show_deployment_commands(self):
        """Show actual deployment commands"""
        print("🔧 **DEPLOYMENT COMMANDS**")
        print("=" * 40)

        commands = [
            {
                "title": "Quick Status Check",
                "code": "treequest status"
            },
            {
                "title": "Test All Providers",
                "code": "treequest test"
            },
            {
                "title": "Query with Specific Provider",
                "code": 'treequest query --provider groq "Analyze this code quickly"'
            },
            {
                "title": "Start TMLPD MCP Server",
                "code": "python3 ~/tmlpd-clean/mcp_server.py"
            },
            {
                "title": "Run TMLPD Codex Integration",
                "code": "tmlpd-codex --help"
            }
        ]

        for cmd in commands:
            print(f"**{cmd['title']}**:")
            print(f"```bash")
            print(f"{cmd['code']}")
            print(f"```")
            print()


def main():
    demo = TMLPDDeploymentDemo()

    # Show all available options
    demo.show_available_options()

    # Demonstrate TreeQuest capabilities
    demo.demo_treequery_parallel()

    # Show provider strategy
    demo.demo_provider_diversification()

    # Show practical example
    demo.create_parallel_deployment_example()

    # Show deployment commands
    demo.show_deployment_commands()

    print("🎉 **TMLPD MULTI-AGENT SYSTEM READY!**")
    print()
    print("📋 **Next Steps:**")
    print("1. Check system status: `treequest status`")
    print("2. Test providers: `treequest test`")
    print("3. Deploy parallel agents: `treequest-parallel`")
    print("4. Or use the Python script: `python3 ~/deploy_tmlpd_agents.py`")


if __name__ == "__main__":
    main()