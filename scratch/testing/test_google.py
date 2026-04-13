import requests
import json
import os
from dotenv import load_dotenv

# Путь к конфигу
dotenv_path = os.path.join(os.path.dirname(__file__), '../../Credentials.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")
# Модели из вашего списка
MODELS_TO_TEST = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite-preview"]

def test_gemini():
    print("--- Testing Google AI Studio (Checking models from your list) ---")
    
    for model in MODELS_TO_TEST:
        print(f"\n>> Trying model: {model}...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": "Hello, are you working? Respond with 'YES' if you are."}]
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"[OK] {model}: ACCESS GRANTED")
                print("Response JSON:")
                print(json.dumps(response.json(), indent=2, ensure_ascii=False))
                return # Останавливаемся на первой работающей
            else:
                print(f"[FAIL] {model}: Status {response.status_code}")
                # Выводим тело ошибки для диагностики биллинга
                try:
                    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
                except:
                    print(response.text)
        except Exception as e:
            print(f"Error testing {model}: {str(e)}")
            
    print("\n[CRITICAL] None of the models worked.")

if __name__ == "__main__":
    test_gemini()
