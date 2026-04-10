#!/usr/bin/env python3
"""
Test script to verify Cerebras integration with Cline
"""
import sys
import os
import json
from cerebras.cloud.sdk import Cerebras

def main():
    # Get API key from config file
    try:
        with open('../../.cline/config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get("providers", {}).get("cerebras", {}).get("apiKey")
            if not api_key:
                print("Error: apiKey not found in config.json", file=sys.stderr)
                return 1
    except FileNotFoundError:
        print("Error: ../../.cline/config.json not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Error: Could not decode config.json", file=sys.stderr)
        return 1

    try:
        # Initialize Cerebras client
        client = Cerebras(api_key=api_key)

        # Test listing available models
        print("Testing Cerebras connection...")
        models = client.models.list()
        print(f"Successfully connected to Cerebras. Available models: {[m.id for m in models.data]}")

        # Test a chat completion
        print("\nSending a test prompt to Cerebras...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Hello, who are you?",
                }
            ],
            model="llama3.1-8b",
        )
        print(f"[Cerebras] Response: {chat_completion.choices[0].message.content}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
