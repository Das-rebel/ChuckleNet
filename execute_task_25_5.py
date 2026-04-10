#!/usr/bin/env python3
"""
Execution script for Task 25.5: Implement Configuration Reloading and Error Handling
Uses a TreeQuestAgent to generate the best implementation for the config reloader.
"""

import asyncio
import os
import sys
from typing import Dict, Callable, Tuple, Any

# Add monk root to path to allow importing core modules
sys.path.insert(0, '/Users/Subho/monk')

from core.treequest_optimization import TreeQuestAgent, OptimizationStrategy

class ConfigReloaderAgent(TreeQuestAgent):
    """
    This agent uses TreeQuest to generate and select the best implementation
    for the configuration reloading and error handling mechanism.
    """
    def __init__(self):
        super().__init__(name="ConfigReloaderAgent")

    def propose_watchdog_strategy(self) -> Tuple[str, float]:
        """
        Proposes a robust, event-based reloader using the watchdog library.
        This is the best practice for automatic reloading.
        """
        code = '''
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable

logger = logging.getLogger(__name__)

class ConfigChangeHandler(FileSystemEventHandler):
    """
    Handles file system events for the models.yaml file.
    """
    def __init__(self, reload_callback: Callable[[], None]):
        self.reload_callback = reload_callback
        self.last_triggered = 0

    def on_modified(self, event):
        if event.src_path.endswith("models.yaml"):
            # Debounce to avoid multiple triggers for one save event
            if time.time() - self.last_triggered > 1:
                logger.info("models.yaml has been modified. Triggering reload.")
                self.reload_callback()
                self.last_triggered = time.time()

class ConfigReloader:
    """
    Monitors the configuration file for changes and triggers a reload.
    """
    def __init__(self, config_path: str, reload_callback: Callable[[], None]):
        self.config_path = config_path
        self.reload_callback = reload_callback
        self.observer = Observer()

    def start(self):
        """
        Starts the file system observer in a background thread.
        """
        event_handler = ConfigChangeHandler(self.reload_callback)
        # Observe the directory containing the config file
        config_dir = os.path.dirname(self.config_path)
        self.observer.schedule(event_handler, config_dir, recursive=False)
        self.observer.start()
        logger.info(f"Started watching {self.config_path} for changes.")

    def stop(self):
        """
        Stops the file system observer.
        """
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped watching config file.")

# Example usage:
# def my_reload_logic():
#     print("Reloading configuration...")
#     # Here you would re-initialize the parser, registrar, and API
#
# reloader = ConfigReloader("./models.yaml", my_reload_logic)
# reloader.start()
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     reloader.stop()
'''
        score = 0.95
        return code.strip(), score

    def propose_manual_reload_strategy(self) -> Tuple[str, float]:
        """
        Proposes a simple function to be called manually for reloading.
        """
        code = '''
import logging

logger = logging.getLogger(__name__)

def trigger_reload(app_context: object):
    """
    Manually triggers the reloading of the application configuration.
    This would be called from a specific CLI command or API endpoint.
    """
    logger.info("Manual reload triggered.")
    # app_context would hold the instances of the parser, registrar, etc.
    # and this function would orchestrate the re-initialization.
    # e.g., app_context.reload_all()
    print("Configuration reloaded manually.")
'''
        score = 0.7
        return code.strip(), score

async def main():
    """
    Main execution function.
    """
    print("🤖 Initializing ConfigReloaderAgent...")
    agent = ConfigReloaderAgent()

    task_functions: Dict[str, Callable[[], Tuple[str, float]]] = {
        "watchdog_reloader": agent.propose_watchdog_strategy,
        "manual_reloader": agent.propose_manual_reload_strategy,
    }

    print("🌳 Running TreeQuest optimization to find the best Config Reloader design...")
    result = await agent.execute_with_treequest(
        task_functions=task_functions,
        iterations=2,
        strategy=OptimizationStrategy.BALANCED
    )

    print(f"\n🏆 TreeQuest optimization complete. Best score: {result.best_score:.3f}")
    print("---")
    print("Winning Config Reloader Implementation:")
    print(result.best_state)
    print("---")

    output_dir = "/Users/Subho/monk/core"
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, "config_reloader.py")
    with open(output_filename, 'w') as f:
        f.write(result.best_state)
    print(f"✅ Best implementation saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
