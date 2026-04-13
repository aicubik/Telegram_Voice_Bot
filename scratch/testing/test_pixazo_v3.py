import os
import requests
import base64
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv('Credentials.env')
load_dotenv('../Credentials.env')

PIXAZO_KEY = os.getenv('PIXAZO_API_KEY')

def test_pixazo_v3_sync():
    """Тест синхронного API Pixazo 2026 для Flux 1 Schnell."""
    print("--- Testing Pixazo 2026 SYNC API ---")
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
            # В новом API картинка может быть в base64 в поле "image" или "images"
            if "image" in data:
                img_data = data["image"]
                print(f"[OK] Received image data (length: {len(img_data)}).")
                return True
            elif "images" in data and len(data["images"]) > 0:
                img_data = data["images"][0].get("base64") or data["images"][0].get("url")
                print(f"[OK] Received images list. Data start: {str(img_data)[:50]}...")
                return True
            else:
                print(f"[FAIL] Unexpected response structure: {data}")
        else:
            print(f"[FAIL] Request failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    return False

if __name__ == "__main__":
    if test_pixazo_v3_sync():
        print("\n=== PIXAZO V2 (SYNC) WORKING! ===")
    else:
        print("\n=== PIXAZO V2 (SYNC) FAILED ===")
