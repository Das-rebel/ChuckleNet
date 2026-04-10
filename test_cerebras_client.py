import sys
import os
from cerebras.cloud.sdk import Cerebras

def main():
    try:
        # Initialize the client with your API key
        api_key = os.getenv('CEREBRAS_API_KEY', 'csk-59h9m9vpjrwxpew26eek6myk39xcenrpw35ye8ndy5vme4nm')
        client = Cerebras(api_key=api_key)
        
        # Test connection by listing available models
        print("Testing connection to Cerebras API...")
        models = client.models.list()
        
        if models:
            print("\nSuccess! Available models:")
            for model in models.data:
                print(f"- {model.id}")
            return 0
        else:
            print("No models found. Check your API key and network connection.")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
