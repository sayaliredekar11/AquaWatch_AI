import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

queries = [
    "Sangli",
    "Kolhapur",
    "Pune",
    "Nashik",
    "Mumbai",
    "Panchganga River, Kolhapur",
    "Krishna River, Sangli",
    "Venna Lake",
    "NonexistentRandomPlace12345"
]

for q in queries:
    resp = client.get(f"/gis/search?q={q}")
    print(f"Status for '{q}': {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Count: {len(data)}")
        for item in data[:2]:
            print(f"    - {item['name']} ({item['lat']}, {item['lon']}) | {item['type']}")
    else:
        print(f"  Error: {resp.text}")
