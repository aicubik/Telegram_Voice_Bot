import requests
import os
from urllib.parse import quote
from dotenv import load_dotenv

def test_pollinations_auth():
    dotenv_path = os.path.join(os.path.dirname(__file__), '../../Credentials.env')
    load_dotenv(dotenv_path)
    api_key = os.getenv("POLLINATIONS_API_KEY")
    prompt = "A high-quality 3D render of a futuristic robot cat, cinematic lighting"
    encoded_prompt = quote(prompt)
    model = "zimage"
    
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model={model}&width=1024&height=1024&seed=42&nologo=true&key={api_key}"
    
    print(f"Testing Pollinations AUTH with model: {model}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            print(f"[OK] Success! Image size: {len(response.content)} bytes")
            # Save for verification
            os.makedirs("scratch/testing", exist_ok=True)
            with open("scratch/testing/test_pollinations_auth.jpg", "wb") as f:
                f.write(response.content)
            print("Saved to scratch/testing/test_pollinations_auth.jpg")
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    test_pollinations_auth()
