"""
Diagnostic step 2: Test where controlnets go in v2 API.
Uses a tiny in-memory JPEG (no external downloads needed).
"""
import requests
import json
import time
import io

API_KEY = "811d09af-1667-4481-8a50-8ee3de75121a"
V2_URL = "https://cloud.leonardo.ai/api/rest/v2/generations"
V1_URL = "https://cloud.leonardo.ai/api/rest/v1/generations"
INIT_IMAGE_URL = "https://cloud.leonardo.ai/api/rest/v1/init-image"

HEADERS = {
    "accept": "application/json",
    "authorization": f"Bearer {API_KEY}",
    "content-type": "application/json",
}

def make_tiny_jpeg():
    """Create a minimal valid JPEG in memory (128x128 black)."""
    try:
        from PIL import Image
        img = Image.new('RGB', (128, 128), color=(0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        return buf.getvalue()
    except ImportError:
        # Fallback: minimal valid JPEG bytes
        # This is a valid 1x1 white JPEG
        return bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0x7B, 0x94, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00,
            0xFF, 0xD9
        ])


def upload_test_image():
    """Upload a test image to get an initImageId."""
    print("Creating and uploading test image...")
    image_bytes = make_tiny_jpeg()
    print(f"  Image size: {len(image_bytes)} bytes")
    
    # Step 1: Get upload URL
    resp = requests.post(INIT_IMAGE_URL, headers=HEADERS, json={"extension": "jpg"}, timeout=30)
    if resp.status_code != 200:
        print(f"  init-image failed: {resp.status_code} - {resp.text[:200]}")
        return None
    
    data = resp.json().get("uploadInitImage", {})
    init_image_id = data.get("id")
    fields_raw = data.get("fields")
    upload_url = data.get("url")
    
    if not init_image_id or not upload_url:
        print(f"  Missing id or url in response: {list(data.keys())}")
        return None
    
    fields = fields_raw
    if isinstance(fields_raw, str):
        fields = json.loads(fields_raw)
    
    # Step 2: Upload to S3
    upload_resp = requests.post(upload_url, data=fields, files={"file": image_bytes}, timeout=60)
    if upload_resp.status_code in (200, 204):
        print(f"  Upload OK! initImageId = {init_image_id}")
        return init_image_id
    else:
        print(f"  S3 upload failed: {upload_resp.status_code}")
        return None


def test_variant(label, url, payload):
    """Generic test runner."""
    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")
    print(f"URL: {url}")
    print(f"Payload:\n{json.dumps(payload, indent=2)}")
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    print(f"\nStatus: {resp.status_code}")
    try:
        print(f"Response:\n{json.dumps(resp.json(), indent=2)}")
    except:
        print(f"Response text: {resp.text[:300]}")
    return resp.status_code


if __name__ == "__main__":
    print("Leonardo AI Character Reference Diagnostic v2")
    print(f"Using key: ***{API_KEY[-6:]}\n")

    init_id = upload_test_image()
    if not init_id:
        print("FATAL: Could not upload test image.")
        exit(1)

    print("\nWaiting 3s for image processing...")
    time.sleep(3)

    results = {}
    prompt = "A portrait of the EXACT person from the reference photo, wearing a red tuxedo, photorealistic, cinematic lighting"

    # TEST A: v2 nested, controlnets IN parameters, ppId=397
    results["A"] = test_variant(
        "TEST A: v2 nested, controlnets IN parameters, ppId=397",
        V2_URL,
        {
            "model": "nano-banana-2",
            "parameters": {
                "width": 1024, "height": 1024,
                "prompt": prompt,
                "quantity": 1,
                "prompt_enhance": "OFF",
                "controlnets": [{"initImageId": init_id, "initImageType": "UPLOADED", "preprocessorId": 397, "strengthType": "High"}]
            },
            "public": False,
        }
    )

    # TEST B: v2 nested, controlnets AT ROOT, ppId=397
    results["B"] = test_variant(
        "TEST B: v2 nested, controlnets AT ROOT, ppId=397",
        V2_URL,
        {
            "model": "nano-banana-2",
            "parameters": {
                "width": 1024, "height": 1024,
                "prompt": prompt,
                "quantity": 1,
                "prompt_enhance": "OFF",
            },
            "controlnets": [{"initImageId": init_id, "initImageType": "UPLOADED", "preprocessorId": 397, "strengthType": "High"}],
            "public": False,
        }
    )

    # TEST C: v2 nested, controlnets IN parameters, ppId=133
    results["C"] = test_variant(
        "TEST C: v2 nested, controlnets IN parameters, ppId=133",
        V2_URL,
        {
            "model": "nano-banana-2",
            "parameters": {
                "width": 1024, "height": 1024,
                "prompt": prompt,
                "quantity": 1,
                "prompt_enhance": "OFF",
                "controlnets": [{"initImageId": init_id, "initImageType": "UPLOADED", "preprocessorId": 133, "strengthType": "High"}]
            },
            "public": False,
        }
    )

    # TEST D: v1 flat, controlnets at root, ppId=397
    results["D"] = test_variant(
        "TEST D: v1 flat, controlnets at root, ppId=397",
        V1_URL,
        {
            "modelId": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3",
            "prompt": prompt,
            "width": 1024, "height": 1024,
            "num_images": 1,
            "alchemy": True,
            "controlnets": [{"initImageId": init_id, "initImageType": "UPLOADED", "preprocessorId": 397, "strengthType": "High"}],
            "public": False,
        }
    )

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    for k, v in results.items():
        status = "OK" if v == 200 else "FAIL"
        print(f"  {k}) HTTP {v} [{status}]")
