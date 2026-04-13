"""Test web search methods for the bot."""
import requests
import re

def test_html_fallback(query):
    """Test direct HTML DuckDuckGo search."""
    print(f"\n=== Testing HTML fallback: '{query}' ===")
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": "https://duckduckgo.com/"
    }
    resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response length: {len(resp.text)} chars")
    
    # Parse results
    snippets = re.findall(
        r'class="result__a"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>(.*?)</span>',
        resp.text, re.DOTALL
    )
    print(f"Found {len(snippets)} results")
    
    for i, (title, body) in enumerate(snippets[:3], 1):
        clean_body = re.sub(r'<[^>]+>', '', body).strip()
        print(f"\n{i}. {title.strip()}")
        print(f"   {clean_body[:150]}")
    
    return len(snippets)

def test_ddgs_library(query):
    """Test ddgs library."""
    print(f"\n=== Testing DDGS library: '{query}' ===")
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=3))
        print(f"Found {len(results)} results")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.get('title', 'N/A')}")
            print(f"   {r.get('body', 'N/A')[:150]}")
        return len(results)
    except Exception as e:
        print(f"DDGS failed: {e}")
        return 0

if __name__ == "__main__":
    queries = [
        "курс доллара Беларусь",
        "последние новости Беларусь",
        "кто такой Илон Маск",
    ]
    
    for q in queries:
        n1 = test_ddgs_library(q)
        n2 = test_html_fallback(q)
        print(f"\n--- Summary for '{q}': ddgs={n1}, html={n2} ---\n")
