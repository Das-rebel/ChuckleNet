import requests
import json
import sys
import os

def diagnose():
    # Get API key from config file
    try:
        with open('../../.cline/config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get("providers", {}).get("openai", {}).get("apiKey")
            if not api_key:
                print("Error: OpenAI apiKey not found in config.json", file=sys.stderr)
                return 1
    except FileNotFoundError:
        print("Error: ../../.cline/config.json not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Error: Could not decode config.json", file=sys.stderr)
        return 1

    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    print(f"--- Starting OpenAI Connection Diagnosis ---")
    print(f"Attempting to connect to: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"Status Code: {response.status_code}")
        response.raise_for_status()
        print("Connection successful!")
        print("Response headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

    except requests.exceptions.RequestException as e:
        print("\n--- A request error occurred ---", file=sys.stderr)
        print(f"Error Type: {type(e).__name__}", file=sys.stderr)
        print(f"Error Details: {e}", file=sys.stderr)
        
        if e.__cause__:
            print("\n--- Underlying Cause ---", file=sys.stderr)
            print(f"Cause Type: {type(e.__cause__).__name__}", file=sys.stderr)
            print(f"Cause Details: {e.__cause__}", file=sys.stderr)

    print("\n--- Diagnosis Complete ---")
    return 0

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found. Please install it by running:", file=sys.stderr)
        print("python3.12 -m pip install requests", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(diagnose())
