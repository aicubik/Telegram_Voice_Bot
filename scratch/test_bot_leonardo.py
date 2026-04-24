"""
Test Leonardo integration exactly as the bot uses it.
Simulates the bot's generate_image_leonardo() call path.
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'Credentials.env'))

from leonardo_client import LeonardoClient

# Same init as tg_assistant_bot.py lines 47-48
raw = os.getenv('LEONARDO_API_KEYS', '')
keys = [k.strip() for k in raw.split(',') if k.strip()]

print(f"Keys found: {len(keys)}")
if not keys:
    print("[FAIL] No LEONARDO_API_KEYS in env!")
    sys.exit(1)

leonardo = LeonardoClient(keys)
print(f"Pool status: {leonardo.get_status()}")

# Same call as generate_image_leonardo() in tg_assistant_bot.py
prompt = "beautiful sunset over mountains, photorealistic landscape"
print(f"\nGenerating: '{prompt}'")
start = time.time()

result = leonardo.generate_image(prompt)

elapsed = time.time() - start
if result:
    print(f"\n[PASS] Success! {len(result):,} bytes in {elapsed:.1f}s")
    out = os.path.join(os.path.dirname(__file__), "test_bot_leonardo.jpg")
    with open(out, "wb") as f:
        f.write(result)
    print(f"Saved: {out}")
else:
    print(f"\n[FAIL] generate_image returned None after {elapsed:.1f}s")
    print(f"Pool status: {leonardo.get_status()}")
