import urllib.request
import urllib.parse
import json
import time

queries = [
    'Sangli',
    'Kolhapur',
    'Pune',
    'Nashik',
    'Mumbai',
    'Panchganga River, Kolhapur',
    'Krishna River, Sangli',
    'Venna Lake'
]

for q in queries:
    params = {
        'q': q,
        'format': 'json',
        'addressdetails': '1',
        'countrycodes': 'in',
        'viewbox': '72.5,22.2,80.9,15.6',
        'bounded': '1',
        'limit': '8',
    }
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'AquaWatch-AI/1.0 (contact@aquawatch.ai)'})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            print(f"QUERY: '{q}' -> found {len(data)} results")
            for d in data[:2]:
                print(f"   -> {d.get('name') or d.get('display_name')} (lat: {d.get('lat')}, lon: {d.get('lon')})")
    except Exception as e:
        print(f"QUERY: '{q}' -> Error: {e}")
    time.sleep(1)
