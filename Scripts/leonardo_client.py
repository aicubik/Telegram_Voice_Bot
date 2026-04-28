"""
Leonardo AI REST API v2 Client with multi-key rotation.

Architecture:
    - LeonardoKeyPool: Round-robin rotation of API keys with exhaustion tracking.
    - LeonardoClient: 2-step async generation (POST -> poll GET -> download).

API Reference: https://docs.leonardo.ai/docs/nano-banana-2
"""

import time
import threading
import requests as http_requests


class LeonardoKeyPool:
    """
    Manages a pool of Leonardo AI API keys with automatic rotation.

    When a key returns HTTP 402 (insufficient funds), it is marked as
    exhausted and the pool moves to the next available key.
    """

    def __init__(self, keys: list):
        self._keys = [k.strip() for k in keys if k.strip()]
        self._exhausted: set = set()
        self._current_index = 0
        self._lock = threading.Lock()

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    @property
    def active_keys(self) -> int:
        return len(self._keys) - len(self._exhausted)

    def get_active_key(self) -> str | None:
        """Return the next non-exhausted key, or None if all exhausted."""
        with self._lock:
            if not self._keys:
                return None

            # Try all keys starting from current index
            for _ in range(len(self._keys)):
                key = self._keys[self._current_index % len(self._keys)]
                self._current_index += 1
                if key not in self._exhausted:
                    return key

            return None  # All keys exhausted

    def mark_exhausted(self, key: str):
        """Mark a key as exhausted (insufficient balance)."""
        with self._lock:
            self._exhausted.add(key)
            remaining = self.active_keys
            print(f"[KEY] Leonardo key exhausted (***{key[-6:]}). "
                  f"Remaining active: {remaining}/{self.total_keys}")

    def reset_all(self):
        """Reset all keys to active state (e.g. after manual top-up)."""
        with self._lock:
            self._exhausted.clear()
            print(f"[KEY] Leonardo: All {self.total_keys} keys reset to active.")

    def get_status(self) -> dict:
        """Return pool status for diagnostics."""
        with self._lock:
            return {
                "total": self.total_keys,
                "active": self.active_keys,
                "exhausted": len(self._exhausted),
            }


class LeonardoClient:
    """
    Client for Leonardo AI REST API v2.

    Usage:
        client = LeonardoClient(["key1", "key2", "key3"])
        image_bytes = client.generate_image("a cat in space")
    """

    BASE_URL_V2 = "https://cloud.leonardo.ai/api/rest/v2/generations"
    BASE_URL_V1 = "https://cloud.leonardo.ai/api/rest/v1/generations"

    # Default: 16:9 Small (1376x768) - $0.04 per generation
    DEFAULT_WIDTH = 1376
    DEFAULT_HEIGHT = 768
    DEFAULT_MODEL = "nano-banana-2"

    # Polling settings
    POLL_INTERVAL = 3      # seconds between status checks
    POLL_TIMEOUT = 90      # max seconds to wait for completion
    REQUEST_TIMEOUT = 30   # HTTP request timeout

    def __init__(self, keys: list):
        self._pool = LeonardoKeyPool(keys)

    @property
    def pool(self) -> LeonardoKeyPool:
        return self._pool

    def _headers(self, api_key: str) -> dict:
        return {
            "accept": "application/json",
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }

    def _upload_init_image(self, api_key: str, image_bytes: bytes, extension: str = "jpg") -> str | None:
        """
        Step 1: POST to v1/init-image -> get S3 fields -> upload to S3.
        Returns initImageId on success.
        """
        url_v1 = "https://cloud.leonardo.ai/api/rest/v1/init-image"
        payload = {"extension": extension}
        
        try:
            resp = http_requests.post(
                url_v1, 
                headers=self._headers(api_key), 
                json=payload,
                timeout=self.REQUEST_TIMEOUT
            )
            if resp.status_code != 200:
                print(f"[ERR] Leonardo init-image failed: {resp.status_code}")
                return None
            
            data = resp.json().get("uploadInitImage", {})
            init_image_id = data.get("id")
            fields_raw = data.get("fields")
            upload_url = data.get("url")
            
            if not init_image_id or not upload_url:
                return None
            
            # Parse fields if it's a string
            fields = fields_raw
            if isinstance(fields_raw, str):
                import json
                fields = json.loads(fields_raw)
            
            # 2. Upload to S3
            files = {"file": image_bytes}
            upload_resp = http_requests.post(upload_url, data=fields, files=files, timeout=60)
            
            if upload_resp.status_code in (200, 204):
                print(f"[OK] Leonardo reference image uploaded: {init_image_id}")
                return init_image_id
            else:
                print(f"[ERR] S3 upload failed: {upload_resp.status_code}")
        except Exception as e:
            print(f"[ERR] Leonardo upload exception: {e}")
            
        return None

    def _submit_generation(self, api_key: str, prompt: str,
                           width: int, height: int,
                           init_image_id: str | None = None) -> str | None:
        """
        Step 1: POST to v2/generations -> returns generationId.
        Supports optional Character Reference (preprocessorId 133).
        """
        payload = {
            "model": self.DEFAULT_MODEL,
            "parameters": {
                "width": width,
                "height": height,
                "prompt": prompt,
                "quantity": 1,
                "prompt_enhance": "OFF",
            },
            "public": False,
        }

        # Add Character Reference if image provided
        if init_image_id:
            payload["parameters"]["controlnets"] = [
                {
                    "initImageId": init_image_id,
                    "initImageType": "UPLOADED",
                    "preprocessorId": 133,  # Character Reference (Magic for face consistency)
                    "strengthType": "High"  # High resemblance
                }
            ]

        resp = http_requests.post(
            self.BASE_URL_V2,
            headers=self._headers(api_key),
            json=payload,
            timeout=self.REQUEST_TIMEOUT,
        )

        if resp.status_code == 402:
            raise ValueError("INSUFFICIENT_FUNDS")

        if resp.status_code not in (200, 201):
            print(f"[ERR] Leonardo POST failed: {resp.status_code} - {resp.text[:200]}")
            return None

        data = resp.json()
        gen_id = None

        if "generate" in data:
            gen_id = data["generate"].get("generationId")
        elif "sdGenerationJob" in data:
            gen_id = data["sdGenerationJob"].get("generationId")
        elif "generationId" in data:
            gen_id = data["generationId"]
        elif "id" in data:
            gen_id = data["id"]

        if gen_id:
            print(f"[OK] Leonardo generation submitted: {gen_id[:12]}...")
        else:
            print(f"[WARN] Leonardo: Unexpected response structure: {list(data.keys())}")

        return gen_id

    def _poll_generation(self, api_key: str, generation_id: str) -> str | None:
        """
        Step 2: Poll GET /v1/generations/{id} until status is COMPLETE.
        """
        url = f"{self.BASE_URL_V1}/{generation_id}"
        start_time = time.time()

        while (time.time() - start_time) < self.POLL_TIMEOUT:
            try:
                resp = http_requests.get(
                    url,
                    headers=self._headers(api_key),
                    timeout=self.REQUEST_TIMEOUT,
                )

                if resp.status_code != 200:
                    print(f"[WARN] Leonardo poll error: {resp.status_code}")
                    time.sleep(self.POLL_INTERVAL)
                    continue

                data = resp.json()
                gen_data = data
                if "generations_by_pk" in data:
                    gen_data = data["generations_by_pk"]

                status = gen_data.get("status", "UNKNOWN")

                if status == "COMPLETE":
                    images = gen_data.get("generated_images", [])
                    if images:
                        image_url = images[0].get("url")
                        if image_url:
                            print("[OK] Leonardo generation complete. Downloading...")
                            return image_url
                    print("[WARN] Leonardo: COMPLETE but no images found")
                    return None

                elif status == "FAILED":
                    print("[ERR] Leonardo generation FAILED")
                    return None

                else:
                    elapsed = int(time.time() - start_time)
                    print(f"[WAIT] Leonardo status: {status} ({elapsed}s elapsed)")

            except Exception as e:
                print(f"[WARN] Leonardo poll exception: {e}")

            time.sleep(self.POLL_INTERVAL)

        print(f"[TIMEOUT] Leonardo generation timed out after {self.POLL_TIMEOUT}s")
        return None

    def _download_image(self, image_url: str) -> bytes | None:
        """Step 3: Download image from CDN."""
        try:
            resp = http_requests.get(image_url, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content
        except Exception as e:
            print(f"[ERR] Leonardo download error: {e}")
        return None

    def generate_image(self, prompt: str,
                       width: int | None = None,
                       height: int | None = None,
                       reference_image: bytes | None = None) -> bytes | None:
        """
        Full pipeline: submit -> poll -> download.
        Supports optional reference image (Character Reference).
        """
        w = width or self.DEFAULT_WIDTH
        h = height or self.DEFAULT_HEIGHT

        attempts = 0
        max_attempts = self._pool.total_keys

        while attempts < max_attempts:
            api_key = self._pool.get_active_key()
            if not api_key:
                return None

            attempts += 1
            try:
                # Optional: Upload reference image
                init_image_id = None
                if reference_image:
                    init_image_id = self._upload_init_image(api_key, reference_image)
                    if not init_image_id:
                        print("[WARN] Leonardo: Failed to upload reference, proceeding without it.")

                # Step 1: Submit
                gen_id = self._submit_generation(api_key, prompt, w, h, init_image_id)
                if not gen_id:
                    continue

                # Step 2: Poll
                image_url = self._poll_generation(api_key, gen_id)
                if not image_url:
                    continue

                # Step 3: Download
                return self._download_image(image_url)

            except ValueError as e:
                if "INSUFFICIENT_FUNDS" in str(e):
                    self._pool.mark_exhausted(api_key)
                    continue
                raise
            except Exception as e:
                print(f"[ERR] Leonardo unexpected error: {e}")
                return None

        return None

    def get_status(self) -> dict:
        """Return client status for bot diagnostics."""
        return self._pool.get_status()
