import requests
import json
import os

# Set URL (Module 1 runs on 8001)
url_gen = "http://127.0.0.1:8001/generate-meal-plan/"
url_analyze = "http://127.0.0.1:8001/analyze-consumed-meal/"

# Ensure API Key is available for the app (environment)
# But here we just test the endpoint

def test_generate_plan():
    print("\n--- Testing /generate-meal-plan/ ---")
    payload = {
        "patient_name": "Test User",
        "fasting_glucose": 140,
        "hba1c": 7.0,
        "current_glucose": 200,
        "preference": "Non-Veg"
    }
    
    try:
        response = requests.post(url_gen, json=payload)
        if response.status_code == 200:
            print("SUCCESS! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_analyze_meal():
    print("\n--- Testing /analyze-consumed-meal/ ---")
    payload = {
        "patient_name": "Test User",
        "meals": [
            {"food": "Chicken Biriyani", "quantity": 1.5},
            {"food": "Gulab Jamun", "quantity": 2.0}
        ]
    }
    
    try:
        response = requests.post(url_analyze, json=payload)
        if response.status_code == 200:
            print("SUCCESS! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Verifying Module 1 (Pure LLM)... Ensure app.py is running on port 8001.")
    test_generate_plan()
    test_analyze_meal()
