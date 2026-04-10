#!/usr/bin/env python3
"""
Test script to find correct Zhipu AI GLM model names
"""

import requests
import json
import os
from typing import List, Dict, Any

# Common Zhipu AI GLM model name variations to test
TEST_MODELS = [
    # Current format (not working)
    "glm-4",
    "glm-3-turbo", 
    "glm-4-airx",
    
    # Alternative formats
    "glm4",
    "glm3-turbo",
    "glm4-airx",
    
    # Other variations
    "glm-4-air",
    "glm-4-plus",
    "glm-4v",
    "glm-4-airx",
    "glm-4-airx-0414",
    "glm-4-airx-0520",
    
    # ChatGLM format
    "chatglm3-6b",
    "chatglm3-32b",
    "chatglm3",
    
    # Newer variations
    "glm-4-0520",
    "glm-4-airx-0520",
    "glm-4-air-0520",
    "glm-4-plus-0520",
    
    # Legacy format
    "chatglm_turbo",
    "chatglm_pro",
    "chatglm_6b",
    "chatglm_32b",
    
    # Versioned format
    "glm-4v",
    "glm-4-0620",
    "glm-4-air-0620",
]

def test_model(api_key: str, model_name: str) -> Dict[str, Any]:
    """Test if a specific model name works with Zhipu AI API"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Hello, please respond with just 'OK'"}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        result = {
            "model": model_name,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "error": None,
            "response": None
        }
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                result["error"] = error_data.get("error", {}).get("message", str(response.text))
            except:
                result["error"] = response.text
        else:
            try:
                response_data = response.json()
                result["response"] = response_data
            except:
                result["error"] = "Failed to parse response"
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "model": model_name,
            "status_code": None,
            "success": False,
            "error": f"Request failed: {str(e)}",
            "response": None
        }

def main():
    """Main function to test all model names"""
    print("=== Zhipu AI GLM Model Name Testing ===\n")
    
    # Get API key from environment
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("Error: ZHIPU_API_KEY environment variable not set")
        print("Please set it with: export ZHIPU_API_KEY='your_api_key_here'")
        return
    
    print(f"Testing {len(TEST_MODELS)} model name variations...\n")
    
    working_models = []
    failed_models = []
    
    for i, model in enumerate(TEST_MODELS, 1):
        print(f"[{i:2d}/{len(TEST_MODELS)}] Testing: {model:<20} ", end="", flush=True)
        
        result = test_model(api_key, model)
        
        if result["success"]:
            print("✅ SUCCESS")
            working_models.append(model)
        else:
            print(f"❌ FAILED ({result.get('status_code', 'N/A')})")
            failed_models.append(result)
    
    print(f"\n=== RESULTS ===")
    print(f"✅ Working models: {len(working_models)}")
    for model in working_models:
        print(f"   - {model}")
    
    print(f"\n❌ Failed models: {len(failed_models)}")
    for result in failed_models[:5]:  # Show first 5 failures
        print(f"   - {result['model']}: {result['error']}")
    
    if len(failed_models) > 5:
        print(f"   ... and {len(failed_models) - 5} more")
    
    # Also try to get available models from the API
    print(f"\n=== FETCHING AVAILABLE MODELS FROM API ===")
    try:
        models_url = "https://open.bigmodel.cn/api/paas/v4/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(models_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            print("✅ Successfully fetched models list:")
            
            if "data" in models_data:
                for model_info in models_data["data"]:
                    model_id = model_info.get("id", "Unknown")
                    print(f"   - {model_id}")
            else:
                print("   Response structure:")
                print(json.dumps(models_data, indent=2))
        else:
            print(f"❌ Failed to fetch models list: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error fetching models list: {str(e)}")

if __name__ == "__main__":
    main()