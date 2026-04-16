import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
import json

load_dotenv("Credentials.env")

print("GROQ Key:", bool(os.getenv("GROQ_API_KEY")))
print("OR Key:", bool(os.getenv("OPENROUTER_API_KEY")))

msg = [{"role": "user", "content": "какая погода в минске"}]
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Погода",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    }
}]

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
try:
    print("Testing OpenRouter...")
    c = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=msg,
        tools=tools,
        tool_choice="auto"
    )
    m = c.choices[0].message
    print("OR tool_calls:", m.tool_calls)
    print("OR content:", m.content)
except Exception as e:
    print("OR Error:", str(e))
