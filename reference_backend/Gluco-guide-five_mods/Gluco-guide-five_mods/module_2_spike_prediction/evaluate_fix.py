import requests
import json

url = "http://127.0.0.1:8003/predict-spike/"

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
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    
    spike_risk = data.get("spike_risk")
    predictions = data.get("predictions", {})
    max_spike = max(predictions.values()) if predictions else 0
    
    print(f"Max Spike: {max_spike}")
    print(f"Risk: {spike_risk}")
    
    if spike_risk in ["Moderate", "High"]:
        print("SUCCESS")
    else:
        print("FAILURE")

except Exception as e:
    print(f"Error: {e}")
