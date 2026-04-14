import os
import requests
from dotenv import load_dotenv

# Загружаем ключи
load_dotenv('Credentials.env')
JINA_API_KEY = os.getenv("JINA_API_KEY")

def test_jina_reader():
    print("\n--- Testing Jina Reader API ---")
    url = "https://r.jina.ai/https://example.com"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"} if JINA_API_KEY else {}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("[OK] Reader works! Content extracted.")
            print(f"Preview: {response.text[:100]}...")
        else:
            print(f"[FAIL] Reader Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Reader request failed: {e}")

def test_jina_embeddings():
    print("\n--- Testing Jina Embeddings API ---")
    if not JINA_API_KEY:
        print("[FAIL] JINA_API_KEY not found in Credentials.env")
        return

    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }
    data = {
        "model": "jina-embeddings-v3",
        "task": "text-matching",
        "dimensions": 1024,
        "late_chunking": False,
        "embedding_type": "float",
        "input": ["Hello, testing bot memory!"]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("[OK] Embeddings work! Vector received.")
            dims = len(response.json()['data'][0]['embedding'])
            print(f"Vector dimensions: {dims}")
        else:
            print(f"[FAIL] Embeddings Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] Embeddings request failed: {e}")

if __name__ == "__main__":
    if not JINA_API_KEY:
        print("WARNING: You haven't added JINA_API_KEY to Credentials.env!")
    test_jina_reader()
    test_jina_embeddings()
