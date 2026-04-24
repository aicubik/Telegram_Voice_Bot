"""Debug: see raw Leonardo API response."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'Credentials.env'))
import requests as http_requests

keys = [k.strip() for k in os.getenv("LEONARDO_API_KEYS", "").split(",") if k.strip()]
if not keys:
    print("No keys found"); exit()

key = keys[0]
print(f"Using key: ***{key[-6:]}")

payload = {
    "model": "nano-banana-2",
    "parameters": {
        "width": 1376,
        "height": 768,
        "prompt": "a cute cat in space",
        "quantity": 1,
        "prompt_enhance": "OFF",
    },
    "public": False,
}

resp = http_requests.post(
    "https://cloud.leonardo.ai/api/rest/v2/generations",
    headers={
        "accept": "application/json",
        "authorization": f"Bearer {key}",
        "content-type": "application/json",
    },
    json=payload,
    timeout=30,
)

print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
