import requests
import os
from urllib.parse import quote

def compare_pollinations():
    prompt = "A detailed portrait of a steampunk space explorer in a futuristic jungle, cinematic lighting, ultra-realistic, 8k"
    encoded_prompt = quote(prompt)
    seed = 42
    
    # Corrected model IDs from browser research
    models = ["flux", "zimage", "nanobanana-pro"]
    
    os.makedirs("scratch/testing/comparison", exist_ok=True)
    
    print(f"--- Pollinations Model Comparison (Final Check) ---")
    
    for model in models:
        # Using gen.pollinations.ai as confirmed by subagent
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}?model={model}&seed={seed}&width=1024&height=1024&nologo=true"
        print(f">> Requesting: {url}")
        
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                filename = f"scratch/testing/comparison/{model}.jpg"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"[OK] Saved to {filename} (Size: {len(response.content)})")
            else:
                print(f"[FAIL] {model} returned status {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {model} failed: {e}")

if __name__ == "__main__":
    compare_pollinations()
