from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Ensure modules can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Helper to safely import modules
def load_module(name, path):
    try:
        from importlib import import_module
        mod = import_module(path)
        print(f"Successfully loaded {name}")
        return mod.app
    except Exception as e:
        print(f"Error loading {name} from {path}: {e}")
        return FastAPI(title=f"Placeholder for {name}")

module1 = load_module("Module 1", "module_1_recommendation_analysis.app")
module2 = load_module("Module 2", "module_2_spike_prediction.app")
module3 = load_module("Module 3", "module_3_risk_prediction.app")
module4 = load_module("Module 4", "module_4_tracker.app")
module5 = load_module("Module 5", "module_5.app")

app = FastAPI(title="GlucoGuide Unified Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/module1", module1)
app.mount("/module2", module2)
app.mount("/module3", module3)
app.mount("/module4", module4)
app.mount("/module5", module5)

@app.get("/")
def read_root():
    return {"message": "GlucoGuide Unified Backend is running"}

from gemini_service import ai_assistant
from module_3_risk_prediction.app import SessionLocal, User, DailyMeal
from datetime import datetime

@app.get("/adaptive-plan/{email}")
async def get_adaptive_plan(email: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        return {"error": "User not found"}
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    meals = db.query(DailyMeal).filter(
        DailyMeal.email == email,
        DailyMeal.date == today
    ).all()
    
    eaten_today = [
        {"meal_type": m.meal_type, "food": m.food_name, "gl": m.gl_value, "as_prescribed": m.is_as_prescribed}
        for m in meals
    ]
    
    profile = {
        "name": user.name,
        "hba1c": user.last_hba1c or 7.0,
        "glucose": user.last_fasting_glucose or 120,
        "weight": user.weight
    }
    
    db.close()
    
    # Path to the food dataset
    dataset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "module_1_recommendation_analysis", 
                                "foods_master_final_with_veg_nonveg.csv")
    
    analysis = ai_assistant.generate_adaptive_diet(profile, eaten_today, dataset_path)
    return {"plan": analysis}

if __name__ == "__main__":
    print("Listing all registered routes:")
    for route in app.routes:
        print(f"Path: {route.path}, Name: {route.name}")
    uvicorn.run(app, host="0.0.0.0", port=8005)
