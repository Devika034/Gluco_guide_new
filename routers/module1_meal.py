import os
import json
import random
import csv
from groq import Groq
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from models import User, MedicalProfile, MealPlan, LoggedMeal
from schemas import LogMealRequest, LogMealResponse

router = APIRouter(prefix="/meal", tags=["Meal Recommendation"])

KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "knowledge_base"))
FOOD_DB_PATH = os.path.join(KNOWLEDGE_BASE_DIR, "nutrition_tables", "merged.csv")

def load_guidelines(filename):
    try:
        path = os.path.join(KNOWLEDGE_BASE_DIR, "diet_guidelines", filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Error loading guideline {filename}: {e}")
    return ""

def get_smart_food_recommendations(meal_type: str, preference: str, is_strict: bool) -> str:
    valid_foods = []
    min_score = 0.7 if is_strict else 0.5
    
    try:
        if not os.path.exists(FOOD_DB_PATH):
            return "No food database found."

        with open(FOOD_DB_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    score = float(row.get("Diabetic Suitability", 0))
                except:
                    score = 0.0
                
                if score < min_score:
                    continue

                food_type = row.get("Veg/Non-Veg", "Veg").strip()
                if preference.lower() == "veg" and food_type.lower() != "veg":
                    continue
                
                db_meal_types = row.get("Meal Type", "").lower()
                if meal_type.lower() not in db_meal_types:
                    continue
                
                valid_foods.append(f"{row['Food Name']} (GI: {row['Glycemic Index']}, {row['Calories (per 100g)']} kcal)")

    except Exception as e:
        return ""
    
    if not valid_foods:
        return "No specific database matches found."
        
    selected = random.sample(valid_foods, min(len(valid_foods), 15))
    return "\n".join(selected)

ICMR_GUIDELINES = load_guidelines("icmr_diet_guidelines.txt")

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "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")
    return Groq(api_key=api_key)

class MealPlanRequest(BaseModel):
    preference: str
    is_strict: bool

class RecommendedItem(BaseModel):
    food: str
    quantity: str
    quantity_grams: str
    GI: float
    GL: float
    veg_nonveg: str
    explanation: str

class MealPlanResponse(BaseModel):
    meal_plan: dict
    avg_GI: float
    total_GL: float

@router.post("/generate-meal-plan/{user_id}", response_model=MealPlanResponse)
def generate_meal_plan(user_id: int, request: MealPlanRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()

    hba1c = profile.hba1c if (profile and profile.hba1c) else 5.5

    client = get_groq_client()
    is_strict = request.is_strict
    plan_type = "Strict (Diabetic Friendly)" if is_strict else "Normal (Healthy Maintenance)"

    bf_options = get_smart_food_recommendations("Breakfast", request.preference, is_strict)
    lu_options = get_smart_food_recommendations("Lunch", request.preference, is_strict)
    dn_options = get_smart_food_recommendations("Dinner", request.preference, is_strict)

    prompt = f"""
You are an expert Clinical Dietitian and Nutritionist specializing in Authentic Kerala Cuisine.

Patient Profile:
- Name: {user.full_name}
- Diet Preference: {request.preference}
- HbA1c: {hba1c}%
- Plan Type: {plan_type}

# ---------------------------------------------------------
# RETRIEVAL AUGMENTED GENERATION (RAG) CONTEXT
# ---------------------------------------------------------
The following are STRICT CLINICAL GUIDELINES from the Indian Council of Medical Research (ICMR).

[ICMR DIETARY GUIDELINES]
{ICMR_GUIDELINES}

[APPROVED FOOD MENU]
>> Breakfast Options:
{bf_options}
>> Lunch Options:
{lu_options}
>> Dinner Options:
{dn_options}

CRITICAL RULES:
1. All GI and GL values are estimates.
2. Provide the estimated weight in grams.
3. Replace mathematical expressions with final calculated values.

Return STRICT JSON:
{{
  "patient_name": "{user.full_name}",
  "plan_type": "{plan_type}",
  "breakfast": [
    {{
      "food": "...",
      "quantity": "...",
      "quantity_grams": "...",
      "GI": 0.0,
      "GL": 0.0,
      "veg_nonveg": "...",
      "explanation": "..."
    }}
  ],
  "lunch": [ ... ],
  "dinner": [ ... ]
}}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a dietitian assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            top_p=0.9,
            response_format={"type": "json_object"}
        )

        meal_plan = json.loads(completion.choices[0].message.content)

        # Calculate avg_GI and total_GL
        total_gi = 0.0
        total_gl = 0.0
        item_count = 0

        for meal in ["breakfast", "lunch", "dinner"]:
            for item in meal_plan.get(meal, []):
                total_gi += float(item.get("GI", 0))
                total_gl += float(item.get("GL", 0))
                item_count += 1
        
        avg_gi = (total_gi / item_count) if item_count > 0 else 0.0
        total_gl = float(total_gl)

        # Save to DB
        from datetime import datetime
        meal_data = MealPlan(
            user_id=user_id,
            breakfast=json.dumps(meal_plan.get("breakfast", [])),
            lunch=json.dumps(meal_plan.get("lunch", [])),
            dinner=json.dumps(meal_plan.get("dinner", [])),
            avg_gi=avg_gi,
            total_gl=total_gl,
            created_at=datetime.utcnow()
        )
        db.add(meal_data)
        db.commit()

        return {
            "meal_plan": meal_plan,
            "avg_GI": avg_gi,
            "total_GL": total_gl
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/log-meal/{user_id}", response_model=LogMealResponse)
def log_meal(user_id: int, request: LogMealRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Load foods from dataset to look up GI and Carbs
    food_db = {}
    if os.path.exists(FOOD_DB_PATH):
        try:
            with open(FOOD_DB_PATH, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None) # Skip broken header
                for row in reader:
                    if len(row) > 3:
                        name = row[0].strip().lower()
                        try:
                            gi = float(row[1])
                            carbs = float(row[3])
                        except:
                            gi, carbs = 0.0, 0.0
                        food_db[name] = {"gi": gi, "carbs": carbs}
        except:
            pass

    total_gi_sum = 0.0
    total_gl_sum = 0.0
    valid_count = 0
    
    foods_to_store = []

    for item in request.foods:
        name_lower = item.food_name.strip().lower()
        qty = float(item.quantity_g)
        
        # Strict validation for medical accuracy: 
        # If the user enters a very small quantity it is likely they entered a portion count (e.g., 1 bowl) instead of grams.
        # Since this is a medical app, we must enforce accurate gram measurements rather than guessing.
        if qty < 5.0:
            raise HTTPException(
                status_code=400, 
                detail=f"For accurate medical predictions, please enter the actual weight of '{item.food_name}' in grams (e.g., 150 for 150g). You entered {qty}, which appears to be a portion count (like '1 bowl' or '2 pieces')."
            )
        
        # Use exact match or fallback to 0
        gi = 0.0
        carbs = 0.0
        
        if name_lower in food_db:
            gi = food_db[name_lower]["gi"]
            carbs = food_db[name_lower]["carbs"]
        else:
            # Try partial matching if exact fails
            for db_name, data in food_db.items():
                if name_lower in db_name or db_name in name_lower:
                    gi = data["gi"]
                    carbs = data["carbs"]
                    break
        
        # GL Formula: (GI * Carbs per 100g * quantity in g) / 10000
        # Since GL standard formula is (GI * available carbs in the portion) / 100
        # Carbs in portion = (carbs_per_100g * quantity_g) / 100
        # Wait, the user formula: (GI * carbs_per_100g * quantity_g) / 10000
        item_gl = (gi * carbs * qty) / 10000.0
        
        if gi > 0:
            total_gi_sum += gi
            valid_count += 1
            
        total_gl_sum += item_gl
        
        foods_to_store.append({
            "food": item.food_name,
            "qty": qty,
            "gi": gi,
            "carbs_per_100g": carbs,
            "gl": item_gl
        })
        
    avg_gi = (total_gi_sum / valid_count) if valid_count > 0 else 0.0
    
    from datetime import datetime
    logged_meal = LoggedMeal(
        user_id=user_id,
        foods_json=json.dumps(foods_to_store),
        avg_gi=avg_gi,
        total_gl=total_gl_sum,
        created_at=datetime.utcnow()
    )
    db.add(logged_meal)
    db.commit()

    return {
        "avg_gi": avg_gi,
        "total_gl": total_gl_sum
    }

