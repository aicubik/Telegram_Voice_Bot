import requests
import os
from dotenv import load_dotenv

load_dotenv('Credentials.env')
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN')

def test_hf():
    print("--- Testing Hugging Face (Model: FLUX.1-schnell) ---")
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    payload = {
        "inputs": "A futuristic city in the clouds, cyberpunk style, high detail",
        "parameters": {"num_inference_steps": 4}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n✅ HUGGING FACE: ACCESS GRANTED (Image generated)")
            # save to file to verify
            with open("hf_test.webp", "wb") as f:
                f.write(response.content)
            print("Saved as hf_test.webp")
        elif response.status_code == 503:
            print("\n⚠️ MODEL LOADING... (503)")
        else:
            print(f"\n❌ HF ERROR: {response.text}")
            
    except Exception as e:
        print(f"\nПрерывание: {str(e)}")

if __name__ == "__main__":
    test_hf()
