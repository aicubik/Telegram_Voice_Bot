"""Test Serper.dev Google Search API (free tier, 2500 queries)"""
import requests
import json

# Get API key from https://serper.dev (free, no credit card)
SERPER_API_KEY = ""  # TODO: paste key here

def test_serper(query):
    """Perform search via Serper.dev API."""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "q": query,
        "gl": "by",  # Belarus region
        "hl": "ru",  # Russian language
        "num": 3
    })
    
    resp = requests.post(url, headers=headers, data=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        organic = data.get("organic", [])
        print(f"Results: {len(organic)}")
        for i, r in enumerate(organic[:3], 1):
            print(f"\n{i}. {r.get('title', 'N/A')}")
            print(f"   {r.get('snippet', 'N/A')[:150]}")
        
        # Knowledge graph (for currency, etc.)
        kg = data.get("knowledgeGraph", {})
        if kg:
            print(f"\n📊 Knowledge Graph: {kg.get('title', '')} - {kg.get('description', '')}")
        
        # Answer box
        answer = data.get("answerBox", {})
        if answer:
            print(f"\n💡 Answer: {answer.get('answer', answer.get('snippet', ''))}")
    else:
        print(f"Error: {resp.text}")

if __name__ == "__main__":
    if not SERPER_API_KEY:
        print("❌ Set SERPER_API_KEY first!")
        print("1. Go to https://serper.dev")
        print("2. Sign up (free, no credit card)")
        print("3. Copy API key")
        print("4. Paste it in this script")
    else:
        test_serper("курс доллара Беларусь")
        print("\n" + "="*60)
        test_serper("последние новости Беларусь")
