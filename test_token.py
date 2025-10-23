import requests
import json

# Paste your newest token here
TOKEN = "2eQ4C0UIkhJe4M_BZpF2zbNU0I3NC8FjUgwVaM-qu8pvvfHyqGydFh3f75Ef6tae"

SEARCH_URL = "https://api.genius.com/search"
QUERY = "Sorry Justin Bieber"

# --- This is the test ---
headers = {'Authorization': f'Bearer {TOKEN}'}
params = {'q': QUERY}

print(f"Attempting to connect to Genius with token: {TOKEN[:10]}...")

try:
    response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
    
    # This is the most important line:
    print(f"\nRAW RESPONSE TEXT (first 500 chars):\n{response.text[:500]}")
    
    # Now, let's try to decode it, just like the real script
    print("\nAttempting to parse JSON...")
    json_data = response.json()
    
    print("\n✅ SUCCESS! Token is valid.")
    print(json_data['response']['hits'][0]['result']['full_title'])

except json.JSONDecodeError:
    print("\n❌ FAILED: 'Expecting value: line 1 column 1 (char 0)'")
    print("This means the API did not send JSON. The token is invalid or incomplete.")
except Exception as e:
    print(f"\n❌ FAILED with a different error: {e}")