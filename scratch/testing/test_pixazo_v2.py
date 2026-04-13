import os
import time
import requests
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv('Credentials.env')
load_dotenv('../Credentials.env')

PIXAZO_KEY = os.getenv('PIXAZO_API_KEY')

def test_pixazo_v2():
    print("--- Testing Pixazo 2026 Async API ---")
    if not PIXAZO_KEY:
        print("[SKIP] PIXAZO_API_KEY is missing.")
        return

    # 1. Отправка запроса на генерацию
    # В 2026 году модель указывается прямо в URL шлюза
    url = "https://gateway.pixazo.ai/flux-1-schnell/v1/getData"
    headers = {
        "Ocp-Apim-Subscription-Key": PIXAZO_KEY,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    payload = {
        "prompt": "Cyberpunk city with neon lights, high quality, digital art",
        "width": 1024,
        "height": 1024
    }

    try:
        print(f"Submitting request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"[FAIL] Submission failed: {response.status_code} - {response.text}")
            return

        data = response.json()
        request_id = data.get("request_id")
        
        if not request_id:
            # Некоторые эндпоинты могут возвращать другое поле, проверим
            print(f"[FAIL] No request_id in response: {data}")
            return

        print(f"[OK] Request submitted. ID: {request_id}")

        # 2. Опрос статуса (Polling)
        status_url = f"https://api.pixazo.ai/v2/requests/status/{request_id}"
        print(f"Polling status at: {status_url}")
        
        start_time = time.time()
        timeout = 180 # 3 минуты
        
        while time.time() - start_time < timeout:
            status_response = requests.get(status_url, headers=headers, timeout=20)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "").upper()
                print(f"Current status: {status}")

                if status == "COMPLETED":
                    # Ищем ссылку на медиа
                    output = status_data.get("output", {})
                    media_url = output.get("media_url")
                    if media_url:
                        print(f"[SUCCESS] Image ready! URL: {media_url}")
                        # Попробуем скачать первые несколько байт для проверки
                        img_check = requests.get(media_url, timeout=20)
                        if img_check.status_code == 200:
                            print(f"[OK] Image is accessible and valid ({len(img_check.content)} bytes).")
                            return True
                    else:
                        print(f"[FAIL] status is COMPLETED but media_url is missing: {status_data}")
                        return False

                elif status in ["FAILED", "ERROR", "CANCELLED"]:
                    print(f"[FAIL] Generation failed with status: {status}")
                    return False
            else:
                print(f"Wait... status request returned {status_response.status_code}")

            time.sleep(10) # Ждем 10 секунд перед следующей проверкой
            
        print("[TIMEOUT] Generation took too long.")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    
    return False

if __name__ == "__main__":
    result = test_pixazo_v2()
    if result:
        print("\n=== TEST PASSED: PIXAZO V2 IS WORKING ===")
    else:
        print("\n=== TEST FAILED: PIXAZO V2 IS NOT WORKING ===")
