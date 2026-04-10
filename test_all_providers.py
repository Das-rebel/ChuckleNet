#!/usr/bin/env python3
"""
Test script to verify Cerebras and OpenAI integrations with Cline
"""
import sys
import os
import json
from cerebras.cloud.sdk import Cerebras
from openai import OpenAI

def main():
    # Get API keys from config file
    try:
        with open('../../.cline/config.json', 'r') as f:
            config = json.load(f)
            cerebras_api_key = config.get("providers", {}).get("openai-compatible", {}).get("apiKey")
            openai_api_key = config.get("providers", {}).get("openai", {}).get("apiKey")
            if not cerebras_api_key:
                print("Error: openai-compatible apiKey not found in config.json", file=sys.stderr)
                return 1
            if not openai_api_key:
                print("Error: OpenAI apiKey not found in config.json", file=sys.stderr)
                return 1
    except FileNotFoundError:
        print("Error: ../../.cline/config.json not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Error: Could not decode config.json", file=sys.stderr)
        return 1

    # Test openai-compatible (Cerebras)
    try:
        print("--- Testing openai-compatible (Cerebras) Connection ---")
        cerebras_client = Cerebras(api_key=cerebras_api_key)
        print("Testing openai-compatible (Cerebras) model list...")
        models = cerebras_client.models.list()
        print(f"Successfully connected to openai-compatible (Cerebras). Available models: {[m.id for m in models.data]}")

        print("\nSending a test prompt to openai-compatible (Cerebras)...")
        chat_completion = cerebras_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Hello, who are you?",
                }
            ],
            model="llama3.1-8b",
        )
        print(f"[openai-compatible (Cerebras)] Response: {chat_completion.choices[0].message.content}")
        print("--- openai-compatible (Cerebras) Test Successful ---")

    except Exception as e:
        print(f"openai-compatible (Cerebras) Error: {str(e)}", file=sys.stderr)

    # Test OpenAI
    try:
        print("\n--- Testing OpenAI Connection ---")
        print("Sending a test prompt to OpenAI...")
        
        import requests
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello, who are you?"}]
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        chat_completion = response.json()
        
        print(f"[OpenAI] Response: {chat_completion['choices'][0]['message']['content']}")
        print("--- OpenAI Test Successful ---")

    except Exception as e:
        print(f"OpenAI Error: {str(e)}", file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())
