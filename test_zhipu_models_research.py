#!/usr/bin/env python3
"""
Research-based test for Zhipu AI GLM model names
Based on common patterns and research of Chinese AI models
"""

import requests
import json
import os

# Most likely Zhipu AI GLM model names based on research:
# Based on official documentation patterns and common usage
TEST_MODELS = [
    # Most common current format (based on research)
    "glm-4",                    # GLM-4 main model
    "glm-4-air",               # GLM-4 Air version
    "glm-4-airx",              # GLM-4 AirX version (your current attempt)
    "glm-4-plus",              # GLM-4 Plus version
    "glm-4-long",              # GLM-4 Long context version
    
    # Version specific formats
    "glm-4-0520",              # GLM-4 May 2024 version
    "glm-4-air-0520",          # GLM-4 Air May 2024
    "glm-4-airx-0520",         # GLM-4 AirX May 2024
    "glm-4-plus-0520",         # GLM-4 Plus May 2024
    
    # Previous generation
    "glm-3-turbo",             # GLM-3 Turbo (your current attempt)
    "glm-3-turbo-128k",        # GLM-3 Turbo with 128K context
    
    # ChatGLM series (if applicable)
    "chatglm3",                # ChatGLM3
    "chatglm3-6b",             # ChatGLM3 6B parameters
    "chatglm3-32b",            # ChatGLM3 32B parameters
    "chatglm-turbo",           # ChatGLM Turbo
    
    # Newer formats (researched)
    "glm-4v",                  # GLM-4 Vision
    "glm-4v-plus",             # GLM-4 Vision Plus
    
    # Alternative formats
    "glm4",                    # Without dash
    "glm4-air",
    "glm4-airx",
    "glm4-plus",
    "glm3-turbo",
    
    # Code specific models
    "glm-4-code",              # Code specialization
    "glm-4-codex",             # CodeX version
    
    # Latest models (2024 patterns)
    "glm-4-0620",              # June 2024 version
    "glm-4-air-0620",          # June 2024 Air version
    "glm-4-airx-0620",         # June 2024 AirX version
    "glm-4-plus-0620",         # June 2024 Plus version
    
    # Flash/speed optimized versions
    "glm-4-flash",             # Fast version
    "glm-4-flashx",            # FastX version
    
    # Legacy models
    "glm-130b",                # GLM 130B parameters
    "glm-4-9b",                # GLM-4 9B parameters
]

def test_model(api_key: str, model_name: str):
    """Test a specific model name"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "请回复'OK'"}
        ],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            return {"model": model_name, "status": "✅ SUCCESS", "details": "Model exists and works"}
        elif response.status_code == 404:
            return {"model": model_name, "status": "❌ NOT FOUND", "details": "Model does not exist"}
        elif response.status_code == 401:
            return {"model": model_name, "status": "❌ AUTH ERROR", "details": "API key invalid"}
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", str(response.text))
                return {"model": model_name, "status": f"❌ ERROR {response.status_code}", "details": error_msg}
            except:
                return {"model": model_name, "status": f"❌ ERROR {response.status_code}", "details": response.text}
                
    except Exception as e:
        return {"model": model_name, "status": "❌ FAILED", "details": str(e)}

def main():
    print("=== Zhipu AI GLM Model Name Research Test ===\n")
    
    api_key = os.getenv("ZHIPUAI_API_KEY")
    if not api_key:
        print("Error: Please set ZHIPUAI_API_KEY environment variable")
        print("Example: export ZHIPUAI_API_KEY='your_api_key_here'")
        return
    
    print(f"Testing {len(TEST_MODELS)} model name variations...\n")
    
    working_models = []
    not_found = []
    other_errors = []
    
    for i, model in enumerate(TEST_MODELS, 1):
        print(f"[{i:2d}/{len(TEST_MODELS)}] {model:<20} ", end="", flush=True)
        
        result = test_model(api_key, model)
        print(f"{result['status']}")
        
        if result['status'] == "✅ SUCCESS":
            working_models.append(result)
        elif "NOT FOUND" in result['status']:
            not_found.append(result)
        else:
            other_errors.append(result)
    
    print(f"\n=== RESULTS ===")
    print(f"✅ Working models: {len(working_models)}")
    for model in working_models:
        print(f"   - {model['model']}: {model['details']}")
    
    if not working_models:
        print("   No working models found!")
    
    print(f"\n❌ Models not found: {len(not_found)}")
    print("   (These model names don't exist)")
    
    print(f"\n⚠️  Other errors: {len(other_errors)}")
    for error in other_errors[:3]:  # Show first 3 errors
        print(f"   - {error['model']}: {error['details']}")
    
    if len(other_errors) > 3:
        print(f"   ... and {len(other_errors) - 3} more errors")
    
    # Try to get official model list
    print(f"\n=== ATTEMPTING TO GET OFFICIAL MODEL LIST ===")
    try:
        models_url = "https://open.bigmodel.cn/api/paas/v4/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(models_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            print("✅ Successfully retrieved official model list:")
            
            if "data" in models_data:
                for model_info in models_data["data"]:
                    model_id = model_info.get("id", "Unknown")
                    print(f"   - {model_id}")
            else:
                print("   Response structure:")
                print(json.dumps(models_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Failed to get model list: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting model list: {str(e)}")
    
    print(f"\n=== RECOMMENDATIONS ===")
    if working_models:
        print("Use these working model names:")
        for model in working_models:
            print(f"   - {model['model']}")
    else:
        print("No working models found. Check:")
        print("   1. API key is valid and has access to GLM models")
        print("   2. API endpoint is correct (https://open.bigmodel.cn/api/paas/v4)")
        print("   3. Account has the necessary permissions")
        print("   4. Try contacting Zhipu AI support for correct model names")

if __name__ == "__main__":
    main()