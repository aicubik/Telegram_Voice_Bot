"""
Test script for Leonardo AI integration.
Run: python scratch/test_leonardo.py
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'Credentials.env'))

from leonardo_client import LeonardoClient, LeonardoKeyPool


def test_key_pool():
    """Test key pool rotation logic."""
    print("=" * 50)
    print("TEST 1: Key Pool Rotation")
    print("=" * 50)
    
    pool = LeonardoKeyPool(["key_a", "key_b", "key_c"])
    
    # Should return keys in order
    k1 = pool.get_active_key()
    k2 = pool.get_active_key()
    k3 = pool.get_active_key()
    print(f"  Keys returned: {k1}, {k2}, {k3}")
    assert k1 == "key_a"
    assert k2 == "key_b"
    assert k3 == "key_c"
    
    # Mark one as exhausted
    pool.mark_exhausted("key_b")
    status = pool.get_status()
    assert status["active"] == 2
    assert status["exhausted"] == 1
    print(f"  After exhausting key_b: {status}")
    
    # Should skip exhausted key
    k4 = pool.get_active_key()
    assert k4 != "key_b"
    print(f"  Next key after exhaustion: {k4}")
    
    # Exhaust all
    pool.mark_exhausted("key_a")
    pool.mark_exhausted("key_c")
    k_none = pool.get_active_key()
    assert k_none is None
    print(f"  All exhausted -> get_active_key() = {k_none}")
    
    # Reset
    pool.reset_all()
    k_reset = pool.get_active_key()
    assert k_reset is not None
    print(f"  After reset -> got key: {k_reset}")
    
    print("  [PASS] Key pool tests PASSED\n")


def test_empty_pool():
    """Test with no keys."""
    print("=" * 50)
    print("TEST 2: Empty Pool")
    print("=" * 50)
    
    pool = LeonardoKeyPool([])
    assert pool.get_active_key() is None
    assert pool.total_keys == 0
    print("  [PASS] Empty pool test PASSED\n")


def test_live_generation():
    """Test actual API generation (requires valid keys)."""
    print("=" * 50)
    print("TEST 3: Live Generation (requires LEONARDO_API_KEYS)")
    print("=" * 50)
    
    raw_keys = os.getenv("LEONARDO_API_KEYS", "")
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    
    if not keys:
        print("  [SKIP] No LEONARDO_API_KEYS in env")
        print("  Set LEONARDO_API_KEYS=key1,key2,key3 to enable\n")
        return
    
    client = LeonardoClient(keys)
    print(f"  Keys loaded: {client.pool.total_keys}")
    print(f"  Generating test image (16:9 Small)...")
    
    image_bytes = client.generate_image(
        "A cute orange cat wearing astronaut suit floating in deep space, "
        "stars and nebula background, photorealistic, high quality"
    )
    
    if image_bytes:
        # Save to file for inspection
        out_path = os.path.join(os.path.dirname(__file__), "test_leonardo_output.jpg")
        with open(out_path, "wb") as f:
            f.write(image_bytes)
        print(f"  [PASS] Image generated: {len(image_bytes):,} bytes")
        print(f"  Saved to: {out_path}")
    else:
        print(f"  [FAIL] Generation failed")
        print(f"  Pool status: {client.get_status()}")
    
    print()


if __name__ == "__main__":
    test_key_pool()
    test_empty_pool()
    test_live_generation()
    print("All tests complete!")
