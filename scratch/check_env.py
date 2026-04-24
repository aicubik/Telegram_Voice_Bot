import os
from dotenv import load_dotenv

# Check both possible locations
load_dotenv('../Credentials.env')
load_dotenv('Credentials.env')

nvidia_key = os.getenv('NVIDIA_API_KEY')
if nvidia_key:
    # Masking for security
    masked = nvidia_key[:4] + "..." + nvidia_key[-4:] if len(nvidia_key) > 8 else "****"
    print(f"NVIDIA_API_KEY is present: {masked}")
else:
    print("NVIDIA_API_KEY is MISSING")
