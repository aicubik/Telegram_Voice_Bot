import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('Credentials.env')
api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    print("Error: GROQ_API_KEY not found")
    exit(1)

client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

try:
    models = client.models.list()
    print(f"{'Model ID':<40} | {'Developer'}")
    print("-" * 60)
    for model in models.data:
        m_id = model.id.lower()
        print(f"{model.id:<40} | {model.owned_by}")
except Exception as e:
    print(f"Error: {e}")
