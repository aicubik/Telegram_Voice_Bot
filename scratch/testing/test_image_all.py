import os
import random
import requests
import base64
from urllib.parse import quote
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv('Credentials.env')
load_dotenv('../Credentials.env')

POLLINATIONS_KEY = os.getenv('POLLINATIONS_API_KEY')
PIXAZO_KEY = os.getenv('PIXAZO_API_KEY')
TOGETHER_KEY = os.getenv('TOGETHER_API_KEY')

def test_pollinations(model="zimage"):
    print(f"\n--- Testing Pollinations ({model}) ---")
    if not POLLINATIONS_KEY:
        print("[SKIP] POLLINATIONS_API_KEY is missing.")
        return False
    try:
        prompt = quote("A beautiful futuristic city, high quality, 8k")
        url = f"https://gen.pollinations.ai/image/{prompt}?model={model}&width=1024&height=1024&seed={random.randint(0, 999999)}&nologo=true&enhance=false&key={POLLINATIONS_KEY}"
        response = requests.get(url, timeout=60)
        if response.status_code == 200 and len(response.content) > 1000:
            print(f"[OK] {model} is active. Received {len(response.content)} bytes.")
            return True
        else:
            print(f"[FAIL] {model} status: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] {model} error: {e}")
    return False

def test_pixazo():
    print("\n--- Testing Pixazo (flux-1-schnell) ---")
    if not PIXAZO_KEY:
        print("[SKIP] PIXAZO_API_KEY is missing.")
        return False
    try:
        url = "https://gateway.pixazo.ai/api/v1/generation/text-to-image"
        headers = {"Ocp-Apim-Subscription-Key": PIXAZO_KEY, "Content-Type": "application/json"}
        payload = {"prompt": "futuristic city", "model": "flux-1-schnell", "width": 1024, "height": 1024, "steps": 4}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "images" in data and len(data["images"]) > 0:
                print(f"[OK] Pixazo is active. Received image base64.")
                return True
        print(f"[FAIL] Pixazo status: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Pixazo error: {e}")
    return False

def test_together():
    print("\n--- Testing Together AI (flux-schnell) ---")
    if not TOGETHER_KEY:
        print("[SKIP] TOGETHER_API_KEY is missing.")
        return False
    try:
        url = "https://api.together.xyz/v1/images/generations"
        headers = {"Authorization": f"Bearer {TOGETHER_KEY}", "Content-Type": "application/json"}
        payload = {"model": "black-forest-labs/FLUX.1-schnell", "prompt": "futuristic city", "width": 1024, "height": 1024, "steps": 4, "response_format": "b64_json"}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                print(f"[OK] Together AI is active. Received image base64.")
                return True
        print(f"[FAIL] Together AI status: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Together AI error: {e}")
    return False

if __name__ == "__main__":
    results = {}
    results["Pollinations (zimage)"] = test_pollinations("zimage")
    results["Pollinations (flux)"] = test_pollinations("flux")
    results["Pixazo (Flux)"] = test_pixazo()
    results["Together AI (Flux)"] = test_together()

    print("\n" + "="*40)
    print("IMAGE GENERATION PIPELINE STATUS:")
    for name, status in results.items():
        status_str = "ACTIVE" if status else "FAILED"
        print(f"{name:25}: {status_str}")
    print("="*40)
