from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import asyncio
import httpx

app = FastAPI(
    title="GlucoGuide – Module 5 (Centralized XAI Dashboard)",
    description="Aggregates Explanations from Spike Prediction, Risk Prediction, and Disease Tracker modules.",
    version="1.0"
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
# Assuming modules run on these ports locally
MODULE_2_URL = "http://127.0.0.1:8003" # Spike
MODULE_3_URL = "http://127.0.0.1:8004" # Risk
MODULE_4_URL = "http://127.0.0.1:8005" # Tracker

# --------------------------------------------------
# INPUT SCHEMAS (Mirroring other modules)
# --------------------------------------------------

class SpikeInput(BaseModel):
    # Reduced subset or full set needed for Mod 2
    current_glucose: float
    avg_GI: float
    total_GL: float
    duration_years: float
    age: int
    bmi: float
    activity_level: int 
    medication_dose: float 
    hba1c: float
    bp_systolic: float
    bp_diastolic: float
    cholesterol: float
    fasting_glucose: float
    time_of_day: int 
    family_history: int 
    alcohol_smoking: int 

class RiskInput(BaseModel):
    hba1c: Optional[float] = 0.0
    bmi: Optional[float] = 25.0
    age: Optional[int] = 50
    hypertension: Optional[int] = 0
    cholesterol: Optional[float] = 180.0
    smoker: Optional[int] = 0
    heart_disease: Optional[int] = 0
    phys_activity: Optional[int] = 1

class GlobalRequest(BaseModel):
    patient_id: str
    spike_data: Optional[SpikeInput] = None
    risk_data: Optional[RiskInput] = None
    # For Module 4, we just need ID as history is in DB

# --------------------------------------------------
# AGGREGATION LOGIC
# --------------------------------------------------

@app.post("/explain/global")
async def explain_global(request: GlobalRequest):
    """
    Queries all active modules and returns a consolidated 'Why' report.
    """
    results = {
        "spike_explanation": None,
        "risk_explanation": None,
        "progression_explanation": {}
    }

    async with httpx.AsyncClient() as client:
        # 1. Module 2: Spike Explanation
        if request.spike_data:
            try:
                # Mod 2 expects the data dict directly
                resp = await client.get(f"{MODULE_2_URL}/explain-spike/", json=request.spike_data.dict())
                if resp.status_code == 200:
                    results["spike_explanation"] = resp.json()
                else:
                    results["spike_explanation"] = {"error": f"Module 2 Error: {resp.text}"}
            except Exception as e:
                results["spike_explanation"] = {"error": str(e)}

        # 2. Module 3: Risk Explanation
        if request.risk_data:
            try:
                resp = await client.post(f"{MODULE_3_URL}/explain-risk-json/", json=request.risk_data.dict())
                if resp.status_code == 200:
                    results["risk_explanation"] = resp.json()
                else:
                    results["risk_explanation"] = {"error": f"Module 3 Error: {resp.text}"}
            except Exception as e:
                results["risk_explanation"] = {"error": str(e)}

        # 3. Module 4: Progression Trends
        # We check for all 3 diseases
        diseases = ["neuropathy", "retinopathy", "nephropathy"]
        for disease in diseases:
             try:
                resp = await client.get(f"{MODULE_4_URL}/explain-trend/{request.patient_id}/{disease}")
                if resp.status_code == 200:
                    results["progression_explanation"][disease] = resp.json()
             except Exception as e:
                 results["progression_explanation"][disease] = {"error": "Service Unreachable"}

    # 4. Synthesize Summary
    summary = []
    
    # Spike Summary
    if results["spike_explanation"] and "contributors" in results["spike_explanation"]:
        top = results["spike_explanation"]["contributors"][0]
        summary.append(f"Immediate Glucose Spikes are primarily driven by {top['feature']}.")

    # Risk Summary
    if results["risk_explanation"] and "contributors" in results["risk_explanation"]:
        top_risk = results["risk_explanation"]["contributors"][0]
        summary.append(f"Long-term Complication risks are most affected by {top_risk['feature']}.")

    results["executive_summary"] = " ".join(summary)

    return results

@app.get("/")
def home():
    return {"module": "Module 5 - Centralized XAI", "status": "Ready"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8006)
