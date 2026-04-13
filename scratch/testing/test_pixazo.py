import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('Credentials.env')
PIXAZO_KEY = os.getenv('PIXAZO_API_KEY') # Ocp-Apim-Subscription-Key
MODEL = "flux-1-schnell"

def test_pixazo():
    print(f"--- Testing Pixazo AI (Model: {MODEL}) ---")
    # Endpoint derived from docs: https://gateway.pixazo.ai/flux-1-schnell/v1/getData
    url = f"https://gateway.pixazo.ai/{MODEL}/v1/getData"
    
    headers = {
        "Ocp-Apim-Subscription-Key": PIXAZO_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "A magical forest of crystal trees, ethereal glow, high detail",
        "num_steps": 4,
        "width": 1024,
        "height": 1024
    }
    
    try:
        print(f"Sending request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2))
            image_url = data.get("output")
            if image_url:
                print(f"\n✅ PIXAZO: ACCESS GRANTED")
                print(f"Image URL: {image_url}")
            else:
                print(f"\n❌ PIXAZO ERROR: No 'output' in response: {data}")
        elif response.status_code == 401 or response.status_code == 403:
            print(f"\n❌ PIXAZO ERROR: (Auth/Forbidden) {response.status_code}")
            print(response.text)
        else:
            print(f"\n❌ PIXAZO ERROR: ({response.status_code}) {response.text}")
            
    except Exception as e:
        print(f"\nПрерывание: {str(e)}")

if __name__ == "__main__":
    test_pixazo()
