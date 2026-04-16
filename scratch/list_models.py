import os
import requests
from dotenv import load_dotenv

load_dotenv('Credentials.env')
api_key = os.getenv('OPENROUTER_API_KEY')

try:
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    response.raise_for_status()
    data = response.json().get('data', [])
    
    print(f"{'Model ID':<65}")
    print("-" * 65)
    
    for m in data:
        m_id = m.get('id', '')
        if 'nvidia' in m_id:
            desc = m.get('description', 'No description')
            has_vision = 'vision' in desc.lower() or 'image' in desc.lower() or ' vl ' in m_id.lower() or '-vl' in m_id.lower()
            v_tag = "[VISION]" if has_vision else "[TEXT ONLY]"
            print(f"{m_id:<65} | {v_tag}")
            print(f"   Description: {desc[:100]}...")

except Exception as e:
    print(f"Error: {e}")
