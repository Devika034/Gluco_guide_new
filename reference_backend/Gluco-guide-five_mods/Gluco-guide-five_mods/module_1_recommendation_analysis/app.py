from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
import os
import json
import random
import csv
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# APP CONFIG
# -------------------------------
app = FastAPI(
    title="GlucoGuide – Module 1 (LLM + Memory)",
    version="LLM-1.1"
)

# -------------------------------
# SIMPLE IN-MEMORY FOOD MEMORY
# -------------------------------
# Structure:
# {
#   "PatientName": ["Food1", "Food2", ...]
# }
patient_food_memory = {}

# -------------------------------
# RAG: KNOWLEDGE BASE LOADING
# -------------------------------
# -------------------------------
# RAG: KNOWLEDGE BASE LOADING & SMART FILTERING
# -------------------------------
KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
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
    """
    Filters the merged.csv dataset to find scientifically valid foods for the specific patient context.
    - strict: Only Suitability > 0.7
    - non-strict: Suitability > 0.5
    - Matches Veg/Non-Veg preference
    - Matches Breakfast/Lunch/Dinner/Snack
    """
    valid_foods = []
    min_score = 0.7 if is_strict else 0.5
    
    try:
        if not os.path.exists(FOOD_DB_PATH):
            return "No food database found."

        with open(FOOD_DB_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 1. Check Suitability Score
                try:
                    score = float(row.get("Diabetic Suitability", 0))
                except:
                    score = 0.0
                
                if score < min_score:
                    continue

                # 2. Check Veg/Non-Veg (If patient is Veg, strictly Veg. If Non-Veg, can eat both)
                # However, for variety, if patient is Non-Veg, we show them everything.
                food_type = row.get("Veg/Non-Veg", "Veg").strip()
                if preference == "Veg" and food_type != "Veg":
                    continue
                
                # 3. Check Meal Type (contains string match)
                # stored as "Breakfast|Dinner"
                db_meal_types = row.get("Meal Type", "").lower()
                if meal_type.lower() not in db_meal_types:
                    continue
                
                # 4. Add to list
                valid_foods.append(f"{row['Food Name']} (GI: {row['Glycemic Index']}, {row['Calories (per 100g)']} kcal)")

    except Exception as e:
        print(f"Error reading DB: {e}")
        return ""
    
    # 5. Randomly select top 15 items to provide as "Menu Options"
    if not valid_foods:
        return "No specific database matches found. Use general knowledge."
        
    selected = random.sample(valid_foods, min(len(valid_foods), 15))
    return "\n".join(selected)


# Load Static Retrieval Contexts at Startup
ICMR_GUIDELINES = load_guidelines("icmr_diet_guidelines.txt")
print(f"DEBUG: Loaded ICMR Guidelines ({len(ICMR_GUIDELINES)} chars)")

# -------------------------------
# LLM CONFIG (GROQ)
# -------------------------------
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    return Groq(api_key=api_key)

# -------------------------------
# DATA MODELS
# -------------------------------
class PatientProfile(BaseModel):
    patient_name: str
    fasting_glucose: float
    hba1c: float
    current_glucose: float
    preference: str  # "Veg" or "Non-Veg"

class RecommendedItem(BaseModel):
    food: str
    quantity: str
    quantity_grams: str
    GI: float
    GL: float
    Veg_NonVeg: str
    Reasoning: str

class MealPlanResponse(BaseModel):
    patient_name: str
    plan_type: str
    breakfast: List[RecommendedItem]
    lunch: List[RecommendedItem]
    dinner: List[RecommendedItem]

class FoodInputItem(BaseModel):
    food: str
    quantity: float = 1.0

class MealAnalysisInput(BaseModel):
    patient_name: str
    meals: List[FoodInputItem]

# -------------------------------
# ENDPOINT 1: MEAL RECOMMENDATION
# -------------------------------
@app.post("/generate-meal-plan/", response_model=MealPlanResponse)
def generate_meal_plan(profile: PatientProfile):
    client = get_groq_client()

    # Determine diabetic strictness
    is_strict = (
        profile.fasting_glucose > 130 or
        profile.hba1c > 6.5 or
        profile.current_glucose > 180
    )
    plan_type = "Strict (Diabetic Friendly)" if is_strict else "Normal (Healthy Maintenance)"

    # Fetch previous foods for this patient
    previous_foods = patient_food_memory.get(profile.patient_name, [])

    # Soft randomizer
    variation_token = random.choice(["A", "B", "C", "D", "E"])

    # -------------------------------
    # SMART RAG: Get Contexts
    # -------------------------------
    bf_options = get_smart_food_recommendations("Breakfast", profile.preference, is_strict)
    lu_options = get_smart_food_recommendations("Lunch", profile.preference, is_strict)
    dn_options = get_smart_food_recommendations("Dinner", profile.preference, is_strict)

    prompt = f"""
You are an expert Clinical Dietitian and Nutritionist specializing in Authentic Kerala Cuisine.

Patient Profile:
- Name: {profile.patient_name}
- Diet Preference: {profile.preference}
- HbA1c: {profile.hba1c}%
- Plan Type: {plan_type}

Previously used foods for this patient:
{previous_foods if previous_foods else "None"}

# ---------------------------------------------------------
# RETRIEVAL AUGMENTED GENERATION (RAG) CONTEXT
# ---------------------------------------------------------
The following are STRICT CLINICAL GUIDELINES from the Indian Council of Medical Research (ICMR).
You MUST align your recommendations with these rules.

[ICMR DIETARY GUIDELINES]
{ICMR_GUIDELINES}

[APPROVED KERALA FOOD MENU (SCIENTIFICALLY VALIDATED)]
The following items have been retrieved from our Clinical Dataset as SAFE for this patient.
YOU MUST PRIORITIZE SELECTING FROM THIS LIST.

>> Breakfast Options (Suitability > {'0.7' if is_strict else '0.5'}):
{bf_options}

>> Lunch Options:
{lu_options}

>> Dinner Options:
{dn_options}
# ---------------------------------------------------------

CRITICAL RULES:
1. The value of "patient_name" in the output MUST exactly match "{profile.patient_name}".
2. Avoid repeating any food listed in previously used foods.
3. Rotate to culturally correct and nutritionally equivalent Kerala alternatives.
4. All GI and GL values are estimates (not clinical measurements).
5. Use realistic Indian GI ranges (GI between 35 and 65).
6. Recommend practical portions (cups, bowls, pieces).
7. ALSO provide the estimated weight in grams for each item (e.g., "150g").
8. Do not include units or calculations in numeric fields. Use only final raw numbers.

Variety Token: {variation_token}

Task:
Create a 1-day meal plan (Breakfast, Lunch, Dinner).

Return STRICT JSON in this format:
{{
  "patient_name": "{profile.patient_name}",
  "plan_type": "{plan_type}",
  "breakfast": [
    {{
      "food": "...",
      "quantity": "...",
      "quantity_grams": "...",
      "GI": 0.0,
      "GL": 0.0,
      "Veg_NonVeg": "...",
      "Reasoning": "..."
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

        result = json.loads(completion.choices[0].message.content)

        # -------------------------------
        # UPDATE MEMORY
        # -------------------------------
        used_foods = []
        for meal in ["breakfast", "lunch", "dinner"]:
            for item in result.get(meal, []):
                used_foods.append(item["food"])

        patient_food_memory[profile.patient_name] = list(set(used_foods))

        return result

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}\nTraceback:\n{error_details}")

# -------------------------------
# ENDPOINT 2: MEAL ANALYSIS
# -------------------------------
@app.post("/analyze-consumed-meal/")
def analyze_meal(plan: MealAnalysisInput):
    client = get_groq_client()

    meal_desc = ", ".join([f"{item.quantity} x {item.food}" for item in plan.meals])

    prompt = f"""
You are an expert Endocrinologist and Nutritionist.

Analyze the following meal:
{meal_desc}

Tasks:
1. Estimate GI and GL for each item.
2. Calculate total meal GL.
3. Predict 2-hour glucose spike.
4. Assess risk level.
5. JSON Validation Rule: Do not return mathematical expressions (e.g. "1.5 * 35"). You MUST calculate the final value and return ONLY the number.

Return STRICT JSON:
{{
  "analysis": [
    {{
      "input": "...",
      "matched": "...",
      "score": 1.0,
      "GI": 0.0,
      "GL": 0.0
    }}
  ],
  "total_meal_gl": 0.0,
  "predicted_2hr_glucose": 0.0,
  "risk_assessment": "Low/Moderate/High"
}}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a medical analysis assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# ROOT
# -------------------------------
@app.get("/")
def root():
    return {"message": "GlucoGuide Module 1 (LLM + Memory) Running"}

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)