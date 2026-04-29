from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, MedicalProfile, MealPlan, SpikePrediction, PatientRiskBaseline, QuestionnaireScore
from routers import auth, profile, module3_risk, module1_meal, module2_spike, module4_tracking, module5_explain, report

app = FastAPI(title="GlucoGuide Backend", version="2.0")

# Enable CORS for Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
Base.metadata.create_all(bind=engine)

from fastapi.responses import JSONResponse
from fastapi import Request
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("GLOBAL EXCEPTION CAUGHT:")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(module3_risk.router)
app.include_router(module1_meal.router)
app.include_router(module2_spike.router)
app.include_router(module4_tracking.router)
app.include_router(module5_explain.router)
app.include_router(report.router)

@app.get("/")
def root():
    return {"status": "Backend Running Successfully"}

@app.get("/debug/user/{user_id}")
def debug_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    medical_profile = db.query(MedicalProfile).filter(MedicalProfile.user_id == user_id).all()
    meal_plan = db.query(MealPlan).filter(MealPlan.user_id == user_id).all()
    spike_prediction = db.query(SpikePrediction).filter(SpikePrediction.user_id == user_id).all()
    risk_baseline = db.query(PatientRiskBaseline).filter(PatientRiskBaseline.patient_id == str(user_id)).all()
    questionnaire_scores = db.query(QuestionnaireScore).filter(QuestionnaireScore.user_id == user_id).all()

    return {
        "user": user,
        "medical_profiles": medical_profile,
        "meal_plans": meal_plan,
        "spike_predictions": spike_prediction,
        "patient_risk_baselines": risk_baseline,
        "questionnaire_scores": questionnaire_scores
    }
