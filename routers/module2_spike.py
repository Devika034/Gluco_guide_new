import os
import joblib
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, MedicalProfile, SpikePrediction, LoggedMeal

router = APIRouter(prefix="/spike", tags=["Spike Prediction"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

rf_regressor = None
rf_classifier = None
shap_explainer_reg = None

try:
    reg_path = os.path.join(MODELS_DIR, "rf_regressor.pkl")
    clf_path = os.path.join(MODELS_DIR, "rf_classifier.pkl")
    shap_path = os.path.join(MODELS_DIR, "shap_regressor.pkl")
    
    if os.path.exists(reg_path) and os.path.exists(clf_path):
        rf_regressor = joblib.load(reg_path)
        rf_classifier = joblib.load(clf_path)
        if os.path.exists(shap_path):
            shap_explainer_reg = joblib.load(shap_path)
        else:
            import shap
            print("Dynamically instantiating SHAP TreeExplainer for module 2")
            shap_explainer_reg = shap.TreeExplainer(rf_regressor)
except Exception as e:
    print(f"Failed to load or instantiate SHAP regressor explainer: {e}")

class SpikeInput(BaseModel):
    current_glucose: float
    time_of_day: int # 0=Morning, 1=Evening

@router.post("/predict-spike/{user_id}")
def predict_spike(user_id: int, request: SpikeInput, db: Session = Depends(get_db)):
    if rf_regressor is None or rf_classifier is None:
        raise HTTPException(status_code=500, detail="Spike models not initialized.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()
    
    if not profile:
        raise HTTPException(status_code=400, detail="Active medical profile not found")

    from datetime import datetime, timedelta
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    recent_meals = db.query(LoggedMeal).filter(
        LoggedMeal.user_id == user_id,
        LoggedMeal.created_at >= two_hours_ago
    ).all()
    
    avg_gi = 0.0
    total_gl = 0.0
    
    if recent_meals:
        # Sum GL and calculate weighted average GI
        total_gl = sum(m.total_gl for m in recent_meals)
        # For GI, we'll take the max or a simple average of the meals
        avg_gi = max(m.avg_gi for m in recent_meals)

    # Mapping logic
    # 1. Activity Level
    mapped_activity = 2500.0
    if profile.activity_level == 0:
        mapped_activity = 8500.0 # Active
    elif profile.activity_level == 1:
        mapped_activity = 2500.0 # Sedentary

    # 2. Medication Dose
    mapped_dose = (profile.medication_dose or 0) / 25.0
    if mapped_dose > 60:
        mapped_dose = 60.0

    # 3. Time of Day
    mapped_time = 8.0 if request.time_of_day == 0 else 20.0

    # 4. Alcohol/Smoking
    mapped_alc = 1 if (profile.alcohol_smoking and profile.alcohol_smoking > 0) else 0

    # Features: [current_glucose, avg_GI, total_GL, duration_years, age, bmi, activity_level, medication_dose, hba1c, bp_systolic, bp_diastolic, cholesterol, fasting_glucose, time_of_day, family_history, alcohol_smoking]
    
    # Calculate approximate age from created_at or default
    age = profile.age or 50
    duration_years = profile.duration_years or 5.0
    bmi = profile.bmi or 25.0
    hba1c = profile.hba1c or 6.0
    bp_sys = profile.bp_systolic or 120.0
    bp_dia = profile.bp_diastolic or 80.0
    chol = profile.cholesterol or 180.0
    fasting_gluc = profile.fasting_glucose or 100.0
    fam_hist = profile.family_history or 0

    features = [
        min(request.current_glucose, 175.0), # Cap for RF model to prevent flatlining
        avg_gi,
        min(total_gl, 40.0), # Cap GL to prevent flatlining on heavy meals
        duration_years,
        age,
        bmi,
        mapped_activity,
        mapped_dose,
        hba1c,
        bp_sys,
        bp_dia,
        chol,
        fasting_gluc,
        mapped_time,
        fam_hist,
        mapped_alc
    ]
    
    input_vector = np.array([features])
    
    try:
        preds_reg = rf_regressor.predict(input_vector)[0]
        pred_risk = rf_classifier.predict(input_vector)[0]
        
        # 1. Linear extrapolation for glucose > 175.0
        if request.current_glucose > 175.0:
            glucose_delta = request.current_glucose - 175.0
            preds_reg = preds_reg + glucose_delta
            
        # 2. Linear extrapolation for heavy meals (GL > 40.0)
        if total_gl > 40.0:
            gl_delta = (total_gl - 40.0) * 0.15
            preds_reg = preds_reg + gl_delta
        
        predictions = {
            "30min": float(round(preds_reg[0], 1)),
            "60min": float(round(preds_reg[1], 1)),
            "90min": float(round(preds_reg[2], 1)),
            "120min": float(round(preds_reg[3], 1))
        }

        max_spike = max(predictions.values())
        advice = "Blood sugar levels look stable."
        severity = "Low"
        if max_spike > 220:
            advice = "Critical Spike Warning! High risk of hyperglycemia. Consider immediate activity."
            severity = "High"
        elif max_spike > 180:
            advice = "Moderate Spike expected. Monitor your levels closely."
            severity = "Moderate"
        elif max_spike < 70:
            advice = "Risk of Hypoglycemia (Low Sugar). Have a snack nearby."
            severity = "Low"
            
        # Strictly linear probability based on predicted spike height
        # This ensures the percentage ALWAYS increases as the spike prediction goes up.
        max_p = max(predictions.values())
        
        # Scale: 120mg/dL = ~10%, 180mg/dL = ~60%, 220mg/dL = ~85%, 250mg/dL+ = ~98%
        if max_p <= 120:
            spike_prob = 0.05 + (max_p / 120.0) * 0.1
        else:
            # Linear ramp from 120 to 250+
            spike_prob = 0.15 + ((max_p - 120) / 130.0) * 0.83
            
        spike_prob = max(0.05, min(0.99, spike_prob))

        # Save to DB
        spike_data = SpikePrediction(
            user_id=user_id,
            current_glucose=request.current_glucose,
            avg_gi=avg_gi,
            total_gl=total_gl,
            spike_probability=spike_prob,
            severity=severity,
            created_at=datetime.utcnow()
        )
        db.add(spike_data)
        db.commit()

        return {
            "predictions": predictions,
            "spike_risk": pred_risk,
            "advice": advice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-spike/{user_id}")
def explain_spike(user_id: int, request: SpikeInput, db: Session = Depends(get_db)):
    global shap_explainer_reg
    
    if shap_explainer_reg is None:
        # Fallback to dynamic instantiation if file load failed initially but model exists
        if rf_regressor is not None:
            import shap
            print("Dynamically instantiating SHAP TreeExplainer inside endpoint...")
            shap_explainer_reg = shap.TreeExplainer(rf_regressor)
        else:
            raise HTTPException(status_code=503, detail="Both Models and SHAP Explainer are unavailable.")
    
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()
    
    if not profile:
        raise HTTPException(status_code=400, detail="Active medical profile not found")

    from datetime import datetime, timedelta
    two_hours_ago = datetime.utcnow() - timedelta(hours=2)
    recent_meals = db.query(LoggedMeal).filter(
        LoggedMeal.user_id == user_id,
        LoggedMeal.created_at >= two_hours_ago
    ).all()
    
    avg_gi = 0.0
    total_gl = 0.0
    
    if recent_meals:
        total_gl = sum(m.total_gl for m in recent_meals)
        avg_gi = max(m.avg_gi for m in recent_meals)

    mapped_activity = 2500.0
    if profile.activity_level == 0: mapped_activity = 8500.0
    elif profile.activity_level == 1: mapped_activity = 2500.0

    mapped_dose = (profile.medication_dose or 0) / 25.0
    if mapped_dose > 60: mapped_dose = 60.0

    mapped_time = 8.0 if request.time_of_day == 0 else 20.0
    mapped_alc = 1 if (profile.alcohol_smoking and profile.alcohol_smoking > 0) else 0

    # True values for explanation context
    true_features = [
        request.current_glucose, avg_gi, total_gl,
        profile.duration_years or 5.0, 50, profile.bmi or 25.0,
        mapped_activity, mapped_dose, profile.hba1c or 6.0,
        profile.bp_systolic or 120.0, profile.bp_diastolic or 80.0,
        profile.cholesterol or 180.0, profile.fasting_glucose or 100.0,
        mapped_time, profile.family_history or 0, mapped_alc
    ]

    # Capped values for model stability
    features = [
        min(request.current_glucose, 175.0), avg_gi, min(total_gl, 40.0),
        profile.duration_years or 5.0, 50, profile.bmi or 25.0,
        mapped_activity, mapped_dose, profile.hba1c or 6.0,
        profile.bp_systolic or 120.0, profile.bp_diastolic or 80.0,
        profile.cholesterol or 180.0, profile.fasting_glucose or 100.0,
        mapped_time, profile.family_history or 0, mapped_alc
    ]
    
    input_vector = np.array([features])
    
    try:
        shap_values = shap_explainer_reg.shap_values(input_vector)
        target_idx = 1 # 60min
        
        if isinstance(shap_values, list):
            vals = shap_values[target_idx][0]
            base_val = shap_explainer_reg.expected_value[target_idx]
        elif hasattr(shap_values, "shape") and len(shap_values.shape) == 3:
            vals = shap_values[0, :, target_idx]
            base_val = shap_explainer_reg.expected_value[target_idx] if isinstance(shap_explainer_reg.expected_value, (list, np.ndarray)) else shap_explainer_reg.expected_value
        else:
            vals = shap_values[0]
            base_val = shap_explainer_reg.expected_value
            
        feature_names = [
            "Current Glucose", "Avg GI", "Total GL", "Diabetes Years", "Age", "BMI",
            "Activity Level", "Medication", "HbA1c", "BP Systolic", "BP Diastolic",
            "Cholesterol", "Fasting Glucose", "Time of Day", "Family History", "Alcohol/Smoking"
        ]
        
        explanation = []
        for name, val, actual_val in zip(feature_names, vals, true_features):
            explanation.append({
                "feature": name, 
                "impact": float(val),
                "value": float(actual_val)
            })
            
        explanation.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "base_value": float(base_val),
            "contributors": explanation[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

