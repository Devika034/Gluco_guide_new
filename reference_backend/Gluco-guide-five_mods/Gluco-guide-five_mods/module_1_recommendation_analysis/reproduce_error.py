import requests
import json

url = "http://127.0.0.1:8001/generate-meal-plan/"
payload = {
  "patient_name": "TestUser",
  "fasting_glucose": 150,
  "hba1c": 7.5,
  "current_glucose": 200,
  "preference": "Veg"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.text)
except Exception as e:
    print(f"Connection Error: {e}")
