import os
import requests
import json
from dotenv import load_dotenv

# Загружаем ключи
# Путь относительно корня проекта
dotenv_path = os.path.join(os.path.dirname(__file__), '../../Credentials.env')
load_dotenv(dotenv_path)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Тестовые данные
# Рукопись Эйнштейна
IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Einstein_handwriting.png"
MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-31b-it"
]

def test_model(model_id):
    print(f"\n--- Testing Model: {model_id} ---")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/aicubik/Telegram_Voice_Bot",
        "X-Title": "OCR Benchmark Bot",
        "Content-Type": "json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Пожалуйста, распознай текст на этом изображении. Это рукопись. Ответь на русском языке."},
                    {"type": "image_url", "image_url": {"url": IMAGE_URL}}
                ]
            }
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            actual_model = result.get('model', 'unknown')
            print(f"[OK] SUCCESS")
            print(f"Actual Model Used: {actual_model}")
            print(f"Result Preview: {content[:200]}...")
            return True, content, actual_model
        else:
            print(f"[FAIL] FAILED (Status: {response.status_code})")
            print(f"Error: {response.text}")
            return False, response.text, None
    except Exception as e:
        print(f"[ERROR] ERROR: {e}")
        return False, str(e), None

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found in Credentials.env")
    else:
        results = {}
        for mid in MODELS:
            results[mid] = test_model(mid)
        
        print("\n" + "="*50)
        print("BENCHMARK SUMMARY")
        print("="*50)
        for mid, (success, out, actual) in results.items():
            status = "WORKING" if success else "NOT WORKING (or fallback)"
            print(f"{mid}: {status} (Actual: {actual})")
