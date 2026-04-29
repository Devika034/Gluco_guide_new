import requests
import json

url = "http://127.0.0.1:8002/predict-spike/"

payload = {
  "current_glucose": 155.0,
  "avg_GI": 88.0,
  "total_GL": 45.0,
  "duration_years": 12.0,
  "age": 58,
  "bmi": 34.0,
  "activity_level": 1,
  "medication_dose": 2000.0,
  "hba1c": 8.8,
  "bp_systolic": 150.0,
  "bp_diastolic": 95.0,
  "cholesterol": 230.0,
  "fasting_glucose": 145.0,
  "time_of_day": 1,
  "family_history": 1,
  "alcohol_smoking": 1
}

try:
    print("Sending request to Module 2...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        
        risk = data.get("spike_risk")
        max_val = max(data["predictions"].values())
        print(f"\nMax Spike: {max_val}")
        print(f"Risk Label: {risk}")
        
        if max_val > 160 and risk == "Low":
            print("ISSUE REPRODUCED: Value > 160 but Risk is Low.")
        else:
            print("Issue not reproduced exactly as described.")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Connection Failed: {e}")
