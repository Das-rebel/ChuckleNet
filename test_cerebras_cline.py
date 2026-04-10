#!/usr/bin/env python3
"""
Test script to verify Cerebras integration with Cline
"""
import sys
import os
from cerebras.cloud.sdk import Cerebras

def main():
    # Get API key from environment
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("Error: CEREBRAS_API_KEY environment variable not set", file=sys.stderr)
        return 1
    
    try:
        # Initialize Cerebras client
        client = Cerebras(api_key=api_key)
        
        # Test listing available models
        print("Testing Cerebras connection...")
        models = client.models.list()
        print(f"Successfully connected to Cerebras. Available models: {[m.id for m in models.data]}")
        
        # Simple chat loop
        print("\nEnter your prompt (or 'quit' to exit):")
        while True:
            user_input = input("> ")
            if user_input.lower() in ('quit', 'exit'):
                break
                
            # Here you would normally send the prompt to Cerebras
            # For now, we'll just echo the input
            print(f"[Cerebras] You said: {user_input}")
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
