# Symptom Tracking and Progression Prediction
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression

from database import get_db
from models import User, QuestionnaireScore, PatientRiskBaseline, MedicalProfile

router = APIRouter(prefix="/tracker", tags=["Disease Progress Tracking"])

# --------------------------------------------------
# SCHEMAS
# --------------------------------------------------
class AnswerSet(BaseModel):
    answers: Dict[str, int]

class DiseaseResult(BaseModel):
    status: str
    trend: str
    score: float
    interpretation: List[str]
    recommendations: List[str]
    forecast: Dict
    explanation: str = "No explanation"
    timestamp: datetime

# --------------------------------------------------
# QUESTIONS
# --------------------------------------------------
RETINOPATHY_QUESTIONS = {
    "blurred_vision": {"question": "Have you experienced blurred vision recently?", "options": {"No": 0, "Occasionally": 1, "Frequently": 2}},
    "floaters": {"question": "Do you notice dark spots or floaters?", "options": {"No": 0, "Sometimes": 1, "Often": 2}},
    "eye_strain": {"question": "Do your eyes feel strained or tired?", "options": {"No": 0, "Mild": 1, "Severe": 2}},
    "eye_exam": {"question": "When was your last eye examination?", "options": {"Within 6 months": 0, "6–12 months ago": 1, "More than 1 year": 2}}
}

NEPHROPATHY_QUESTIONS = {
    "swelling": {"question": "Any swelling in feet or face?", "options": {"No": 0, "Mild": 1, "Noticeable": 2}},
    "urination": {"question": "Any change in urination frequency?", "options": {"Normal": 0, "Slight change": 1, "Major change": 2}},
    "fatigue": {"question": "How fatigued do you feel?", "options": {"Normal": 0, "Moderate": 1, "Severe": 2}},
    "bp": {"question": "Recent blood pressure readings?", "options": {"Normal": 0, "Occasionally high": 1, "Frequently high": 2}}
}

NEUROPATHY_QUESTIONS = {
    "tingling": {"question": "Any tingling or numbness in limbs?", "options": {"No": 0, "Occasional": 1, "Frequent": 2}},
    "pain": {"question": "Burning or sharp nerve pain?", "options": {"No": 0, "Sometimes": 1, "Often": 2}},
    "balance": {"question": "Any balance issues while walking?", "options": {"No": 0, "Rare": 1, "Frequent": 2}},
    "foot_care": {"question": "How often do you inspect your feet?", "options": {"Daily": 0, "Occasionally": 1, "Rarely": 2}}
}

QUESTION_MAP = {
    "retinopathy": RETINOPATHY_QUESTIONS,
    "nephropathy": NEPHROPATHY_QUESTIONS,
    "neuropathy": NEUROPATHY_QUESTIONS
}

# --------------------------------------------------
# SCORING LOGIC
# --------------------------------------------------
def compute_score(answers: dict) -> float:
    if not answers: return 0.0
    total = sum(answers.values())
    max_score = len(answers) * 2
    return round(total / max_score, 2)

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "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")
    from groq import Groq
    return Groq(api_key=api_key)

def generate_ai_analysis(disease: str, score: float, current_answers: dict, previous_score: float | None):
    if previous_score is None:
        trend = "Baseline"
    elif score > previous_score + 0.05:
        trend = "Worsening"
    elif score < previous_score - 0.05:
        trend = "Improving"
    else:
        trend = "Stable"

    if score < 0.3:
        status = "Stable"
    elif score < 0.6:
        status = "Watchful"
    else:
        status = "High Risk"

    import json
    prompt = f"""
You are an expert Endocrinologist and Medical AI analyzing a diabetic patient's symptom progression.
Disease Module: {disease.upper()}
Current Impact Score: {score} (0.0 is perfect, 1.0 is severe)
Trend: {trend}
Patient's exact survey answers (values 0=No, 1=Mild/Sometimes, 2=Severe/Frequent):
{json.dumps(current_answers, indent=2)}

Provide a strict JSON response interpreting their exact symptoms and providing actionable recommendations.
{{
  "interpretation": [
    "string analyzing specific symptom 1",
    "string analyzing specific symptom 2"
  ],
  "recommendations": [
    "actionable lifestyle or medical advice 1",
    "actionable lifestyle or medical advice 2"
  ]
}}
"""
    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a medical AI. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        interpretation = data.get("interpretation", ["Symptoms noted."])
        recommendations = data.get("recommendations", ["Consult your doctor."])
    except Exception as e:
        print(f"Error in AI: {e}")
        interpretation = ["Unable to generate AI interpretation. Check connection."]
        recommendations = ["Monitor symptoms closely and consult a professional if they worsen."]

    return status, trend, interpretation, recommendations

def predict_progression(history_data, clinical_data: dict = None):
    if len(history_data) < 2:
        # If very little data, use clinical profile to suggest a baseline risk trend
        risk_level = "Standard"
        if clinical_data:
            hba1c = clinical_data.get("hba1c", 7.0)
            if hba1c > 8.5: risk_level = "High Potential for Worsening"
            elif hba1c > 7.5: risk_level = "Moderate Potential for Worsening"
        
        return {
            "prediction": f"Baseline established ({risk_level})",
            "slope": 0.0,
            "days_to_critical_risk": "N/A",
            "explanation": "Insufficient history for time-series forecasting. Prediction is based on current clinical profile."
        }

    start_date = history_data[0][0]
    dates = [x[0] for x in history_data]
    scores = [x[1] for x in history_data]
    
    X = np.array([(d - start_date).days for d in dates]).reshape(-1, 1)
    y = np.array(scores)
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_day = X[-1][0]
    future_day = last_day + 30
    pred_future = model.predict([[future_day]])[0]
    
    # Clip prediction between 0 and 1
    pred_future = max(0.0, min(1.0, pred_future))
    
    slope = model.coef_[0]
    
    # Adjust trend based on clinical data
    clinical_multiplier = 1.0
    if clinical_data:
        hba1c = clinical_data.get("hba1c", 7.0)
        if hba1c > 8.0: clinical_multiplier = 1.5 # Accelerate perceived worsening
    
    effective_slope = slope * clinical_multiplier

    if effective_slope > 0.005: trend_text = "Rapid Deterioration Detected"
    elif effective_slope > 0: trend_text = "Slow Worsening"
    elif effective_slope < -0.005: trend_text = "Significant Improvement"
    else: trend_text = "Stable Trend"

    days_to_risk = "N/A"
    current_score = scores[-1]
    
    # Use effective_slope for projection
    # If slope is 0 or negative, we assume a "Potential Drift" based on HbA1c to give the user a safety buffer estimate
    proj_slope = effective_slope
    if proj_slope <= 0:
        hba1c = (clinical_data or {}).get("hba1c", 7.0) or 7.0
        # Assume a minimal daily drift of 0.0005 to 0.001 based on HbA1c
        proj_slope = 0.0005 * (hba1c / 7.0)

    if current_score >= 0.8:
        days_to_risk = "Critical Risk Reached"
    else:
        days_needed = (0.8 - current_score) / proj_slope
        if days_needed < 365:
            days_to_risk = f"{int(days_needed)} Days"
        else:
            days_to_risk = "> 1 Year"
            
    # AI Explanation using GeminiService
    from services.gemini_service import get_ai_assistant
    from models import MedicalProfile # Local import for safety
    ai = get_ai_assistant()
    
    # Format a simple prediction string for the AI
    forecast_str = f"Score predicted to change from {current_score:.2f} to {pred_future:.2f} in 30 days ({trend_text})"
    
    explanation = ai.explain_progression(
        disease="symptom tracking", # Generic context or pass it in
        current_score=current_score,
        trend=trend_text,
        forecast=forecast_str,
        clinical_data=clinical_data or {}
    )
    
    return {
        "prediction": f"{trend_text} (Score {pred_future:.2f} in 30 days)",
        "slope": float(slope),
        "days_to_critical_risk": days_to_risk,
        "explanation": explanation
    }

# --------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------

@router.get("/questions/{disease}")
def get_questions(disease: str):
    return QUESTION_MAP.get(disease, {})

@router.post("/analyze/{user_id}/{disease}", response_model=DiseaseResult)
def analyze(user_id: int, disease: str, data: AnswerSet, db: Session = Depends(get_db)):
    if disease not in QUESTION_MAP:
        raise HTTPException(status_code=400, detail="Invalid disease type")
        
    current_score = compute_score(data.answers)
    
    # 2. Get baseline risk as previous score
    baseline = db.query(PatientRiskBaseline).filter(
        PatientRiskBaseline.patient_id == str(user_id)
    ).order_by(PatientRiskBaseline.created_at.desc()).first()
    
    previous_score = None
    if baseline:
        if disease == "neuropathy":
            previous_score = baseline.neuropathy_5y / 100.0
        elif disease == "retinopathy":
            previous_score = baseline.retinopathy_5y / 100.0
        elif disease == "nephropathy":
            previous_score = baseline.nephropathy_5y / 100.0
    
    # Compare with Baseline
    status, trend, interpretation, recommendations = generate_ai_analysis(disease, current_score, data.answers, previous_score)
    
    # Save to tracker history DB
    new_entry = QuestionnaireScore(
        user_id=user_id,
        disease_type=disease,
        score=current_score,
        trend=trend,
        created_at=datetime.utcnow()
    )
    db.add(new_entry)
    db.commit()
    
    # 3. Get Clinical Data for better prediction
    from models import MedicalProfile # Local import for safety
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()
    
    clinical_data = {}
    if profile:
        clinical_data = {
            "hba1c": profile.hba1c,
            "fasting_glucose": profile.fasting_glucose,
            "bp_systolic": profile.bp_systolic,
            "bmi": profile.bmi
        }

    # ML Forecasting based on history
    history_records = db.query(QuestionnaireScore).filter(
        QuestionnaireScore.user_id == user_id,
        QuestionnaireScore.disease_type == disease
    ).order_by(QuestionnaireScore.created_at.asc()).all()
    
    full_history = [(r.created_at, r.score) for r in history_records]
    forecast = predict_progression(full_history, clinical_data)

    return DiseaseResult(
        status=status,
        trend=trend,
        score=current_score,
        interpretation=interpretation,
        recommendations=recommendations,
        forecast=forecast,
        explanation=forecast.get("explanation", "N/A"),
        timestamp=datetime.utcnow()
    )

@router.get("/explain-trend/{user_id}/{disease}")
def explain_trend_only(user_id: int, disease: str, db: Session = Depends(get_db)):
    # Get Clinical Data
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()
    clinical_data = {"hba1c": profile.hba1c} if profile else {}

    history_records = db.query(QuestionnaireScore).filter(
        QuestionnaireScore.user_id == user_id,
        QuestionnaireScore.disease_type == disease
    ).order_by(QuestionnaireScore.created_at.asc()).all()
    
    full_history = [(r.created_at, r.score) for r in history_records]
    if not full_history:
        return {"forecast": "No history found", "explanation": "Insufficient data"}
        
    forecast = predict_progression(full_history, clinical_data)
    
    return {
        "disease": disease,
        "history_points": len(full_history),
        "forecast": forecast,
        "explanation": forecast.get("explanation", "N/A")
    }
