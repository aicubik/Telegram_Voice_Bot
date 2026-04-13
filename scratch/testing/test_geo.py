import requests, urllib.parse, json

def test_geocode(name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(name)}&count=5&language=en&format=json"
    res = requests.get(url).json()
    print(f"--- Results for '{name}' ---")
    if "results" in res:
        for r in res["results"]:
            print(json.dumps({"name": r.get("name"), "country": r.get("country"), "admin1": r.get("admin1")}))
    else:
        print("No results or error:", res)

test_geocode("бобруйск")
test_geocode("bobruysk")
test_geocode("babruysk")
