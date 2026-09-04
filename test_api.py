import sys
import os
import requests
import json

URL = sys.argv[1] if len(sys.argv) > 1 else os.getenv("API_URL", "http://127.0.0.1:5000/audit")
IMAGE_PATH = sys.argv[2] if len(sys.argv) > 2 else os.getenv("IMAGE_PATH", "sadya.jpg")

if not os.path.exists(IMAGE_PATH):
    print(f"Error: Test image '{IMAGE_PATH}' not found.")
    sys.exit(1)

print(f"Sending '{IMAGE_PATH}' to {URL}...")
with open(IMAGE_PATH, "rb") as image:
    response = requests.post(
        URL,
        files={"image": image}
    )

print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=4))
except Exception:
    print(response.text)