import requests
import time

URL = "http://127.0.0.1:8000"

print("Waiting for API...")
time.sleep(1)

print("\n--- Testing Predict (Clause Detection & DB Insert) ---")
payload = {"text": "This is a confidential non-disclosure agreement. Governing law is California. Arbitration clause applies. Non-compete for 12 months. Force majeure included. Contains data privacy CCPA obligations."}
try:
    r1 = requests.post(f"{URL}/predict", json=payload, timeout=10)
    print("Status:", r1.status_code)
    if r1.status_code == 200:
        data = r1.json()
        print("Clauses detected:", {k: v for k, v in data.get("clauses", {}).items() if v})
    else:
        print(r1.text)
except Exception as e:
    print(e)

print("\n--- Testing History (DB Query) ---")
try:
    r2 = requests.get(f"{URL}/history", timeout=5)
    print("Status:", r2.status_code)
    if r2.status_code == 200:
        print("History Entries:", len(r2.json().get("history", [])))
    else:
        print(r2.text)
except Exception as e:
    print(e)

print("\n--- Testing Chat QA ---")
chat_payload = {
    "context": payload["text"],
    "question": "What is the governing law?"
}
try:
    r3 = requests.post(f"{URL}/chat", json=chat_payload, timeout=10)
    print("Status:", r3.status_code)
    if r3.status_code == 200:
        print("QA Result:", r3.json())
    else:
        print(r3.text)
except Exception as e:
    print(e)
