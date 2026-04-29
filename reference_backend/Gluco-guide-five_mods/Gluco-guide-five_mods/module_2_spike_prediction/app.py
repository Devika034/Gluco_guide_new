from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
import os
import joblib

app = FastAPI(
    title="GlucoGuide - Module 2 (ML Classification)",
    description="Post-meal Glucose Spike Prediction using Random Forest Regressor & Classifier",
    version="3.0"
)

# Global Models
rf_regressor = None
rf_classifier = None
shap_explainer_reg = None


# --------------------------------------------------
# 1. TRAINING LOGIC (Regressor + Classifier)
# --------------------------------------------------
def train_models():
    global rf_regressor, rf_classifier
    print("--- [Module 2] Starting Random Forest Training (Regressor + Classifier) ---")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "..", "synthetic_data.csv")
    
    if not os.path.exists(DATA_PATH):
        print(f"CRITICAL ERROR: Dataset not found at {DATA_PATH}")
        return

    # Load & Clean
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} records.")
    
    # Features (16)
    feature_cols = [
        "current_glucose", "avg_GI", "total_GL", "duration_years", "age", "bmi",
        "activity_level", "medication_dose", "hba1c", "bp_systolic", "bp_diastolic",
        "cholesterol", "fasting_glucose", "time_of_day", "family_history", "alcohol_smoking"
    ]
    # Regression Targets
    target_cols = ["glucose_30min", "glucose_60min", "glucose_90min", "glucose_120min"]
    
    X = df[feature_cols]
    y_reg = df[target_cols]
    
    # Derive Classification Target (Risk Level)
    # Rules for training data ground truth:
    # > 180 : High
    # > 140 : Moderate
    # <= 140 : Low
    df['max_spike'] = df[target_cols].max(axis=1)
    
    def classify_risk(val):
        if val > 180: return "High"
        elif val > 140: return "Moderate"
        else: return "Low"

    y_class = df['max_spike'].apply(classify_risk)
    
    # Train Random Forest Regressor
    print("Training Regressor...")
    reg = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    reg.fit(X, y_reg)
    rf_regressor = reg
    
    # Train Random Forest Classifier
    print("Training Classifier...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    clf.fit(X, y_class)
    rf_classifier = clf
    
    # Save Models
    joblib.dump(rf_regressor, "rf_regressor.pkl")
    joblib.dump(rf_classifier, "rf_classifier.pkl")
    print("--- [Module 2] Models Trained and Saved Successfully ---")

# Initialize Models
try:
    if os.path.exists("rf_regressor.pkl") and os.path.exists("rf_classifier.pkl"):
        rf_regressor = joblib.load("rf_regressor.pkl")
        rf_classifier = joblib.load("rf_classifier.pkl")
        print("Models loaded from disk.")
        
        if os.path.exists("shap_regressor.pkl"):
             shap_explainer_reg = joblib.load("shap_regressor.pkl")
             print("SHAP Explainer loaded.")
        else:
             print("SHAP Explainer not found (Run train_shap_module2.py).")

    else:
        train_models()
except Exception as e:
    print(f"Error initializing models: {e}")
    # Fallback if pickle fails immediately
    train_models()

# --------------------------------------------------
# 2. INPUT SCHEMA & MAPPING
# --------------------------------------------------
class SpikeInput(BaseModel):
    current_glucose: float
    avg_GI: float
    total_GL: float
    duration_years: float
    age: int
    bmi: float
    activity_level: int # 0=Active, 1=Sedentary
    medication_dose: float # mg (e.g., 500, 1000)
    hba1c: float
    bp_systolic: float
    bp_diastolic: float
    cholesterol: float
    fasting_glucose: float
    time_of_day: int # 0=Morning, 1=Evening
    family_history: int # 0=No, 1=Yes
    alcohol_smoking: int # 0=No, 1=Yes

@app.get("/")
def home():
    status = "Ready" if (rf_regressor and rf_classifier) else "Not Initialized"
    return {"module": "Module 2 - Spike Prediction (RF Classification)", "status": status}

def prepare_features(data: SpikeInput):
    # --- INPUT MAPPING LAYER ---
    # 1. Activity Level
    if data.activity_level == 0:
        mapped_activity = 8500.0 # Active
    elif data.activity_level == 1:
        mapped_activity = 2500.0 # Sedentary
    else:
        mapped_activity = 2500.0 # Default

    # 2. Medication Dose
    # Dataset uses units, User uses mg. Ratio approx 25:1
    mapped_dose = data.medication_dose / 25.0
    if mapped_dose > 60: mapped_dose = 60.0 # Clamp

    # 3. Time of Day
    if data.time_of_day == 0:
        mapped_time = 8.0  # Morning
    elif data.time_of_day == 1:
        mapped_time = 20.0 # Evening
    else:
        mapped_time = 8.0

    # 4. Alcohol/Smoking
    mapped_alc = 1 if data.alcohol_smoking > 0 else 0

    # Construct Feed Vector
    features = [
        data.current_glucose,
        data.avg_GI,
        data.total_GL,
        data.duration_years,
        data.age,
        data.bmi,
        mapped_activity,   # MAPPED
        mapped_dose,       # MAPPED
        data.hba1c,
        data.bp_systolic,
        data.bp_diastolic,
        data.cholesterol,
        data.fasting_glucose,
        mapped_time,       # MAPPED
        data.family_history,
        mapped_alc         # MAPPED
    ]
    return np.array([features]), {
        "activity_mapped": mapped_activity,
        "time_mapped": mapped_time,
        "dose_mapped": mapped_dose
    }

@app.get("/explain-spike/")
def explain(data: SpikeInput):
    if shap_explainer_reg is None:
         raise HTTPException(status_code=503, detail="SHAP Explainer not ready.")
         
    try:
        input_vector, _ = prepare_features(data)
        
        # Calculate SHAP values
        shap_values = shap_explainer_reg.shap_values(input_vector)
        
        # If output is multi-output (regressor predicting 4 values), we get a list of arrays.
        # We usually want to explain the MAX spike or the aggregate.
        # But let's simplify and explain the 3rd output (90min) or average?
        # Actually, let's just return the contributions for the first output (30min) or sum?
        # A common approach for multi-output is to explain one specific target or all.
        # Let's explain the 'glucose_60min' (index 1) which is usually the peak.
        
        # Check shape
        # shap_values shape for Random Forest Regressor on multi-output:
        # It IS a list of arrays, one for each output column.
        
        target_idx = 1 # 60min
        if isinstance(shap_values, list):
            vals = shap_values[target_idx][0] # First sample
            base_val = shap_explainer_reg.expected_value[target_idx]
        else:
            vals = shap_values[0]
            base_val = shap_explainer_reg.expected_value
            
        feature_names = [
            "Current Glucose", "Avg GI", "Total GL", "Diabetes Years", "Age", "BMI",
            "Activity Level", "Medication", "HbA1c", "BP Systolic", "BP Diastolic",
            "Cholesterol", "Fasting Glucose", "Time of Day", "Family History", "Alcohol/Smoking"
        ]
        
        # Create sorted list of (Feature, Impact)
        explanation = []
        for name, val in zip(feature_names, vals):
            explanation.append({"feature": name, "impact": float(val)})
            
        # Sort by absolute impact
        explanation.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "base_value": float(base_val),
            "contributors": explanation[:5] # Top 5 factors
        }
            
    except Exception as e:
        print(f"Explanation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-spike/")

def predict(data: SpikeInput):
    if rf_regressor is None or rf_classifier is None:
        raise HTTPException(status_code=500, detail="Models not initialized.")
    
    try:
        input_vector, debug_mappings = prepare_features(data)

        
        # 1. Predict Values (Regressor)
        preds_reg = rf_regressor.predict(input_vector)[0]
        
        # 2. Predict Risk (Classifier)
        pred_risk = rf_classifier.predict(input_vector)[0]

        predictions = {
            "30min": float(round(preds_reg[0], 1)),
            "60min": float(round(preds_reg[1], 1)),
            "90min": float(round(preds_reg[2], 1)),
            "120min": float(round(preds_reg[3], 1))
        }

        # Advice Logic (Secondary, for UI text)
        max_spike = max(predictions.values())
        
        advice = "Blood sugar levels look stable."
        if max_spike > 200:
            advice = "Critical Spike Warning! Consider post-meal walk and hydration."
        elif max_spike > 160:
            advice = "Moderate Spike expected. Monitor closely."
        elif max_spike < 70:
             advice = "Risk of Hypoglycemia (Low Sugar). Have a snack nearby."

        return {
            "predictions": predictions,
            "spike_risk": pred_risk, # Direct output from Random Forest Classifier
            "advice": advice,
            "debug_mappings": debug_mappings

        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
