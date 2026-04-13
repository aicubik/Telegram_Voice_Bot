import requests
import os
from urllib.parse import quote

def test_urls():
    prompt = "A simple red apple on a white table"
    encoded_prompt = quote(prompt)
    
    # Try different endpoints
    endpoints = [
        "https://image.pollinations.ai/prompt/{}?model={}",
        "https://pollinations.ai/p/{}?model={}",
    ]
    
    models = ["flux", "zimage"]
    
    for ep in endpoints:
        print(f"\n--- Testing Endpoint: {ep} ---")
        results = []
        for model in models:
            url = ep.format(encoded_prompt, model)
            try:
                # Add a unique param to bypass cache
                final_url = f"{url}&seed=123" if "?" in url else f"{url}?seed=123"
                response = requests.get(final_url, timeout=10)
                size = len(response.content)
                results.append(size)
                print(f"Model: {model} -> Size: {size}")
            except Exception as e:
                print(f"Model: {model} -> Error: {e}")
        
        if len(set(results)) > 1:
            print(">> SUCCESS: Endpoint returns different sizes for different models!")
        else:
            print(">> FAIL: All models returned the same size.")

if __name__ == "__main__":
    test_urls()
