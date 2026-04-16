import os
import sys
from dotenv import load_dotenv

# Add Scripts directory to path
sys.path.append(os.path.join(os.getcwd(), 'Scripts'))

# Load credentials
load_dotenv('Credentials.env')

from agent_tools import perform_web_search

def test_search():
    query = "какой фильм сейчас идет в кино в минске"
    print(f"Testing search for: {query}")
    result = perform_web_search(query)
    print("\n--- RESULT ---")
    print(result)
    print("--- END RESULT ---\n")
    
    if "=== SEARCH DATA START ===" in result and "=== SEARCH DATA END ===" in result:
        print("✅ SUCCESS: Markers found!")
    else:
        print("❌ FAILURE: Markers missing!")
        
    if "минск" in result.lower() or "беларусь" in result.lower():
        print("✅ SUCCESS: Localization working!")
    else:
        print("❌ FAILURE: Localization might be missing.")

if __name__ == "__main__":
    test_search()
