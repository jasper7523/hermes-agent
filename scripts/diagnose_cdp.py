import urllib.request
import json

def diagnose():
    try:
        req = urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2)
        targets = json.loads(req.read().decode('utf-8'))
        print(f"[*] Found {len(targets)} targets:")
        for t in targets:
            print(f" - {t.get('title')} | {t.get('url')} | {t.get('type')}")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    diagnose()
