import storage
import scoring
from datetime import datetime, timedelta
import random

def verify():
    patient_id = "test_patient_ml"
    disease = "neuropathy"
    
    # 1. Clear previous test data
    # (Simplified: just ignore old data or ensure unique ID)
    
    print("Injecting synthetic history (Worsening Trend)...")
    # Day 0: Score 0.2
    storage.save_score(patient_id, disease, 0.2)
    # Hack DB timestamps to simplify testing (SQL update)
    # But storage.save_score saves datetime.now().
    # We need to manually inject past dates to test regression over time.
    
    import sqlite3
    conn = sqlite3.connect("module_4_tracker/tracker.db")
    c = conn.cursor()
    
    # Clear for test
    c.execute("DELETE FROM tracker_history WHERE patient_id=?", (patient_id,))
    
    # Insert Data with Past Dates
    now = datetime.now()
    dates = [
        (now - timedelta(days=60), 0.2),
        (now - timedelta(days=45), 0.3),
        (now - timedelta(days=30), 0.4),
        (now - timedelta(days=15), 0.55),
        (now, 0.65) # High slope!
    ]
    
    for dt, sc in dates:
        c.execute("INSERT INTO tracker_history (patient_id, disease, score, timestamp) VALUES (?, ?, ?, ?)",
                  (patient_id, disease, sc, dt))
    conn.commit()
    conn.close()
    
    print("History injected. Running Forecast...")
    history = storage.get_history(patient_id, disease)
    result = scoring.predict_progression(history)
    
    print("\n--- ML FORECAST RESULT ---")
    print(f"Prediction: {result['prediction']}")
    print(f"Slope: {result['slope']:.5f}")
    print(f"Days to Critical (0.8): {result['days_to_critical_risk']}")
    
    if result['slope'] > 0 and result['days_to_critical_risk']:
        print("\nSUCCESS: Model correctly identified worsening trend and predicted future risk.")
    else:
        print("\nFAILURE: Model failed to detect trend.")

if __name__ == "__main__":
    verify()
