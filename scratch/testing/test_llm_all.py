import os
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем ключи из разных возможных путей
load_dotenv('Credentials.env')
load_dotenv('../Credentials.env')

def test_pollinations():
    print("\n--- Testing Pollinations Text (GPT-OSS 20B) ---")
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [{"role": "user", "content": "Say 'OK'"}],
            "model": "openai-fast"
        }
        response = requests.post(url, json=payload, timeout=20)
        if response.status_code == 200:
            print(f"[OK] Response: {response.text.strip()}")
            return True
        else:
            print(f"[FAIL] Status code: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
    return False

def test_openai_style(name, client_args, model):
    print(f"\n--- Testing {name} ({model}) ---")
    try:
        client = OpenAI(**client_args)
        if not client.api_key:
            print(f"[SKIP] API key for {name} is missing.")
            return False
            
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=20
        )
        response = completion.choices[0].message.content.strip()
        print(f"[OK] Response: {response}")
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

if __name__ == "__main__":
    results = {}
    
    # 1. Groq - Llama 4 Scout
    results["Groq (Llama 4 Scout)"] = test_openai_style(
        "Groq", 
        {"api_key": os.getenv('GROQ_API_KEY'), "base_url": "https://api.groq.com/openai/v1"}, 
        "meta-llama/llama-4-scout-17b-16e-instruct"
    )
    
    # 2. OpenRouter - Qwen3 Coder
    results["OpenRouter (Qwen3 Coder)"] = test_openai_style(
        "OpenRouter", 
        {"api_key": os.getenv('OPENROUTER_API_KEY'), "base_url": "https://openrouter.ai/api/v1"}, 
        "qwen/qwen3-coder:free"
    )
    
    # 3. OpenRouter - Llama 3.3
    results["OpenRouter (Llama 3.3)"] = test_openai_style(
        "OpenRouter", 
        {"api_key": os.getenv('OPENROUTER_API_KEY'), "base_url": "https://openrouter.ai/api/v1"}, 
        "meta-llama/llama-3.3-70b-instruct:free"
    )
    
    # 4. OpenRouter - Gemma 4
    results["OpenRouter (Gemma 4)"] = test_openai_style(
        "OpenRouter", 
        {"api_key": os.getenv('OPENROUTER_API_KEY'), "base_url": "https://openrouter.ai/api/v1"}, 
        "google/gemma-4-31b-it:free"
    )
    
    # 5. Pollinations - GPT-OSS
    results["Pollinations (GPT-OSS)"] = test_pollinations()

    print("\n" + "="*40)
    for name, status in results.items():
        status_str = "ACTIVE" if status else "FAILED"
        print(f"{name:25}: {status_str}")
