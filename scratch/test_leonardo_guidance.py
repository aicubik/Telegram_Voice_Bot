import os
import json
import requests as http_requests
from dotenv import load_dotenv

load_dotenv("Credentials.env")
KEYS = os.getenv("LEONARDO_API_KEYS", "").split(",")
API_KEY = KEYS[0].strip()

def upload_image(image_path):
    url = "https://cloud.leonardo.ai/api/rest/v1/init-image"
    payload = {"extension": "jpg"}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    
    # 1. Get presigned URL
    print("Getting presigned URL...")
    resp = http_requests.post(url, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    data = resp.json().get("uploadInitImage", {})
    
    image_id = data.get("id")
    fields = data.get("fields")
    if isinstance(fields, str):
        fields = json.loads(fields)
    upload_url = data.get("url")
    
    # 2. Upload to S3
    print(f"Uploading to S3 (ID: {image_id})...")
    with open(image_path, "rb") as f:
        files = {"file": f}
        # S3 requires fields to be sent as data
        s3_resp = http_requests.post(upload_url, data=fields, files=files)
        print(f"S3 Upload Status: {s3_resp.status_code}")
    
    return image_id

def generate_with_ref(image_id, prompt):
    url = "https://cloud.leonardo.ai/api/rest/v2/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": "nano-banana-2",
        "parameters": {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "quantity": 1,
            "controlnets": [
                {
                    "initImageId": image_id,
                    "initImageType": "UPLOADED",
                    "preprocessorId": 133, # Character Reference
                    "strengthType": "High"
                }
            ]
        }
    }
    
    print("Submitting generation...")
    resp = http_requests.post(url, json=payload, headers=headers)
    print(f"Gen Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    # This is a scratch test script
    # test_image = "scratch/test_face.jpg" 
    # if os.path.exists(test_image):
    #     img_id = upload_image(test_image)
    #     generate_with_ref(img_id, "A cyberpunk warrior version of this person")
    pass
