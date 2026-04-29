import asyncio
import random
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from models import MedicalProfile, SpikePrediction, PatientRiskBaseline

from routers.module2_spike import explain_spike, SpikeInput
from routers.module3_risk import explain_risk_json
from routers.module4_tracking import explain_trend_only
from services.gemini_service import get_ai_assistant

router = APIRouter(prefix="/explain", tags=["Explainable AI (Module 5)"])

class GlobalRequest(BaseModel):
    user_id: int
    spike_data: Optional[SpikeInput] = None

@router.post("/global")
def explain_global(request: GlobalRequest, db: Session = Depends(get_db)):
    results = {
        "spike_explanation": None,
        "risk_explanation": None,
        "progression_explanation": {}
    }

    # 1. Spike Explanation
    if request.spike_data:
        try:
            results["spike_explanation"] = explain_spike(request.user_id, request.spike_data, db)
        except Exception as e:
            results["spike_explanation"] = {"error": str(e)}

    # 2. Risk Explanation
    try:
        results["risk_explanation"] = explain_risk_json(request.user_id, db)
    except Exception as e:
        results["risk_explanation"] = {"error": str(e)}

    # 3. Progression Trends
    diseases = ["neuropathy", "retinopathy", "nephropathy"]
    for disease in diseases:
         try:
            results["progression_explanation"][disease] = explain_trend_only(request.user_id, disease, db)
         except Exception as e:
             results["progression_explanation"][disease] = {"error": str(e)}

    # 4. Synthesize Summary
    summary = []
    
    if results["spike_explanation"] and "contributors" in results["spike_explanation"]:
        top = results["spike_explanation"]["contributors"][0]
        summary.append(f"Immediate Glucose Spikes are primarily driven by {top['feature']}.")

    if results["risk_explanation"] and "contributors" in results["risk_explanation"]:
        top_risk = results["risk_explanation"]["contributors"][0]
        summary.append(f"Long-term Complication risks are most affected by {top_risk['feature']}.")

    results["executive_summary"] = " ".join(summary)

    return results


@router.get("/spike/{user_id}")
def explain_spike_dashboard(user_id: int, db: Session = Depends(get_db)):
    # Fetch most recent spike prediction
    recent_spike = db.query(SpikePrediction).filter(
        SpikePrediction.user_id == user_id
    ).order_by(SpikePrediction.created_at.desc()).first()

    if not recent_spike:
        raise HTTPException(status_code=404, detail="No recent meal/spike data found to explain.")

    # Recreate SpikeInput
    spike_request = SpikeInput(
        current_glucose=recent_spike.current_glucose,
        time_of_day=8 # simplified for explanation UI
    )

    try:
        raw_explanation = explain_spike(user_id, spike_request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

    # Format feature importance
    feature_importance = {}
    analysis_data = []
    
    for item in raw_explanation.get("contributors", []):
        feature = item["feature"]
        impact = item["impact"]
        value = item.get("value", "N/A")
        feature_importance[feature] = abs(impact)
        analysis_data.append({"feature": feature, "impact": impact, "value": value})

    # Call Gemini for dynamic suggestions
    recommendations = []
    if analysis_data:
        try:
            # Fetch recent meal names for better context
            from models import LoggedMeal
            from datetime import datetime, timedelta
            two_hours_ago = datetime.utcnow() - timedelta(hours=2)
            meals = db.query(LoggedMeal).filter(
                LoggedMeal.user_id == user_id,
                LoggedMeal.created_at >= two_hours_ago
            ).all()
            
            meal_names = []
            import json
            for m in meals:
                try:
                    foods = json.loads(m.foods_json)
                    for f in foods:
                        name = f.get("name") or f.get("food_name")
                        if name: meal_names.append(name)
                except:
                    continue
            
            # Re-calculate the actual minute-by-minute predictions to feed the AI
            from routers.module2_spike import predict_spike
            pred_response = predict_spike(user_id, spike_request, db)
            predictions = pred_response.get("predictions", {})
            levels_str = ", ".join([f"{k}: {v}mg/dL" for k, v in predictions.items()])
            
            top_factors = analysis_data[:5]
            ai_assistant = get_ai_assistant()
            
            # Pass everything: Meal Names + Specific Minute-by-Minute Forecasts
            context = f"Spike Prediction (Forecast: {levels_str}, Recent Meals: {', '.join(meal_names)})"
            recommendations = ai_assistant.generate_insight_suggestions(context, top_factors)
        except Exception as e:
            print(f"DEBUG: AI Suggestion Error: {e}")
            recommendations = []

    # Fallback if Gemini fails or returns empty
    if not recommendations:
        recommendations = [
            "Maintain a balanced diet and regular exercise routine.",
            "Keep focusing on whole foods and consistent activity.",
            "Stay hydrated and monitor your post-meal patterns."
        ]

    return {
        "prediction_type": "spike",
        "spike_probability": recent_spike.spike_probability,
        "feature_importance": feature_importance,
        "recommendation": recommendations
    }


@router.get("/risk/{user_id}")
def explain_risk_dashboard(user_id: int, db: Session = Depends(get_db)):
    baseline = db.query(PatientRiskBaseline).filter(
        PatientRiskBaseline.patient_id == str(user_id)
    ).order_by(PatientRiskBaseline.created_at.desc()).first()

    if not baseline:
        raise HTTPException(status_code=404, detail="No risk baseline found. Please run an analysis first.")

    try:
        raw_explanation = explain_risk_json(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

    feature_importance = {}
    analysis_data = []

    for item in raw_explanation.get("contributors", []):
        feature = item["feature"]
        impact = item["impact"]
        value = item.get("value", "N/A")
        feature_importance[feature] = abs(impact)
        analysis_data.append({"feature": feature, "impact": impact, "value": value})

    # Call Gemini for dynamic suggestions
    recommendations = []
    if analysis_data:
        try:
            top_factors = analysis_data[:5]
            ai_assistant = get_ai_assistant()
            recommendations = ai_assistant.generate_insight_suggestions("Long-term Complication Risk", top_factors)
        except Exception as e:
            print(f"Failed to get Gemini suggestions: {e}")

    if not recommendations:
        recommendations = [
            "Schedule regular screenings for eyes, kidneys, and feet.",
            "Maintain strict glycemic control.",
            "Monitor your blood pressure and cholesterol levels."
        ]

    return {
        "prediction_type": "risk",
        "feature_importance": feature_importance,
        "recommendation": recommendations
    }
