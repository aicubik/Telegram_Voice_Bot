import requests

def test_pollinations():
    print("--- Testing Pollinations.ai (Model: nanobanana-pro) ---")
    prompt = "A cyberpunk neon cat, detailed digital art"
    url = f"https://image.pollinations.ai/prompt/{prompt}?model=nanobanana-pro&nologo=true"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            print("\n✅ POLLINATIONS: ACCESS GRANTED (Image generated)")
        else:
            print("\n❌ POLLINATIONS: ACCESS FAILED or not an image")
            print(f"Response snippet: {response.text[:100]}")
            
    except Exception as e:
        print(f"\nПрерывание: {str(e)}")

if __name__ == "__main__":
    test_pollinations()
