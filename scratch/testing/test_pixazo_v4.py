import os
import requests
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv('Credentials.env')
load_dotenv('../Credentials.env')

PIXAZO_KEY = os.getenv('PIXAZO_API_KEY')

def test_pixazo_v4_final():
    """Финальный тест API Pixazo 2026: Синхронное получение URL."""
    print("--- Testing Pixazo 2026 FINAL API ---")
    if not PIXAZO_KEY:
        print("[SKIP] PIXAZO_API_KEY is missing.")
        return False

    url = "https://gateway.pixazo.ai/flux-1-schnell/v1/getData"
    headers = {
        "Ocp-Apim-Subscription-Key": PIXAZO_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": "Futuristic city with neon lights, 8k, detailed",
        "width": 1024,
        "height": 1024
    }

    try:
        print(f"Sending request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            # В 2026 году Pixazo возвращает URL в поле 'output'
            media_url = data.get("output")
            if media_url and media_url.startswith("http"):
                print(f"[OK] Got image URL: {media_url}")
                # Проверяем скачивание
                img_res = requests.get(media_url, timeout=30)
                if img_res.status_code == 200:
                    print(f"[OK] Image downloaded successfully! ({len(img_res.content)} bytes)")
                    return True
                else:
                    print(f"[FAIL] Could not download image from URL. Status: {img_res.status_code}")
            else:
                print(f"[FAIL] Unexpected response structure (no output URL): {data}")
        else:
            print(f"[FAIL] Request failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    return False

if __name__ == "__main__":
    if test_pixazo_v4_final():
        print("\n=== PIXAZO V2 (2026) WORKING PERFECTLY! ===")
    else:
        print("\n=== PIXAZO V2 (2026) STILL FAILING ===")
