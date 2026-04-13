import requests
import os
from dotenv import load_dotenv

load_dotenv('Credentials.env')
TOGETHER_KEY = os.getenv('TOGETHER_API_KEY')

def test_together():
    print("--- Testing Together AI (Model: FLUX.1-schnell) ---")
    url = "https://api.together.xyz/v1/images/generations"
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": "An astronaut riding a horse on Mars, cinematic lighting, 8k",
        "width": 1024,
        "height": 768,
        "steps": 4,
        "n": 1,
        "response_format": "url"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            image_url = data.get("data", [{}])[0].get("url")
            if image_url:
                print("\n✅ TOGETHER AI: ACCESS GRANTED")
                print(f"Image URL: {image_url}")
            else:
                print(f"\n❌ TOGETHER ERROR: No image data in response: {data}")
        elif response.status_code == 402:
            print("\n❌ TOGETHER ERROR: Insufficient balance (402)")
        else:
            print(f"\n❌ TOGETHER ERROR: ({response.status_code})")
            print(f"Body: {response.text}")
            
    except Exception as e:
        print(f"\nПрерывание: {str(e)}")

if __name__ == "__main__":
    test_together()
