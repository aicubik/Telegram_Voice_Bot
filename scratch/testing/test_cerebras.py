import requests
import json
import os
from dotenv import load_dotenv

# Загружаем ключи
dotenv_path = os.path.join(os.path.dirname(__file__), '../../Credentials.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv("CEREBRAS_API_KEY", "csk-dummy-if-not-available")
MODEL = "llama3.3-70b"

def test_cerebras():
    print(f"--- Testing Cerebras (Model: {MODEL}) ---")
    url = "https://api.cerebras.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "How fast are you?"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ CEREBRAS: ACCESS GRANTED")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ CEREBRAS: ACCESS FAILED ({response.status_code})")
            print(response.text)
            
    except Exception as e:
        print(f"\nПрерывание: {str(e)}")

if __name__ == "__main__":
    test_cerebras()
