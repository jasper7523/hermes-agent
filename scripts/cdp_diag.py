import urllib.request
import json

try:
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    targets = json.loads(req.read().decode('utf-8'))
    for t in targets:
        print(f"Type: {t.get('type')}, Title: {t.get('title')}, URL: {t.get('url')}")
except Exception as e:
    print(f"Error: {e}")
