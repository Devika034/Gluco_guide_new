from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import random
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="GlucoGuide – Module 1 Unified (Analysis & Recommendation)",
    version="FINAL-UNIFIED"
)

# --------------------------------------------------
# LOAD DATASET (SHARED)
# --------------------------------------------------

DATASET_PATH = os.path.join(BASE_DIR, "foods_master_final_with_veg_nonveg.csv")

if not os.path.exists(DATASET_PATH):
    raise RuntimeError(f"Dataset not found at {DATASET_PATH}")

df = pd.read_csv(DATASET_PATH)
df.columns = df.columns.str.strip()

required_cols = ["food", "GI", "GL_per_serving", "Veg/Non-veg"]
for col in required_cols:
    if col not in df.columns:
        raise RuntimeError(f"Missing column: {col}")

df["GI"] = pd.to_numeric(df["GI"], errors="coerce")
df["GL_per_serving"] = pd.to_numeric(df["GL_per_serving"], errors="coerce")
df = df.dropna(subset=required_cols)

# --------------------------------------------------
# ML MODEL (SHARED)
# --------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")
food_embeddings = model.encode(df["food"].tolist())

# --------------------------------------------------
# MODULE 1B: FOOD ANALYSIS LOGIC
# --------------------------------------------------

class FoodItem(BaseModel):
    food: str
    quantity: float = 1.0

class MealInput(BaseModel):
    patient_name: str
    preference: str              # "Veg" or "Non-Veg"
    meals: List[FoodItem]

def filter_by_preference(df: pd.DataFrame, preference: str) -> pd.DataFrame:
    if preference == "Veg":
        return df[df["Veg/Non-veg"] == "Veg"]
    return df

def ml_match_food(user_food: str, df_subset: pd.DataFrame):
    food_names = df_subset["food"].tolist()
    subset_embeddings = model.encode(food_names)

    user_vec = model.encode([user_food])
    similarities = cosine_similarity(user_vec, subset_embeddings)[0]

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])

    if best_score < 0.55:
        return None, None

    return df_subset.iloc[best_idx], best_score

def get_alternatives(df_subset: pd.DataFrame, gi_limit: float = 55):
    return (
        df_subset[df_subset["GI"] <= gi_limit]
        .sort_values("GL_per_serving")
        .head(5)
    )

@app.post("/analyze-consumed-meal/")
def analyze_meal(plan: MealInput):
    allowed_df = filter_by_preference(df, plan.preference)

    matched = []
    total_gl = 0.0
    total_gi = 0.0
    count = 0

    for item in plan.meals:
        row, score = ml_match_food(item.food, allowed_df)
        if row is None:
            continue

        gi = float(row["GI"])
        gl = float(row["GL_per_serving"]) * item.quantity * (gi / 100)

        matched.append({
            "input": item.food,
            "matched_food": row["food"],
            "food_type": row["Veg/Non-veg"],
            "similarity_score": round(score, 2),
            "GI": gi,
            "GL": round(gl, 2)
        })

        total_gl += gl
        total_gi += gi
        count += 1

    if count == 0:
        return {
            "error": "No food items could be matched within dietary preference"
        }

    avg_gi = total_gi / count

    if total_gl < 10 and avg_gi < 55:
        risk = "Low"
    elif total_gl < 20:
        risk = "Moderate"
    else:
        risk = "High"

    alternatives_df = get_alternatives(allowed_df)
    alternatives = [
        {
            "food": row["food"],
            "food_type": row["Veg/Non-veg"],
            "GI": float(row["GI"]),
            "GL": round(float(row["GL_per_serving"]), 2)
        }
        for _, row in alternatives_df.iterrows()
    ]

    return {
        "patient": plan.patient_name,
        "preference": plan.preference,
        "foods_analyzed": matched,
        "avg_gi": round(avg_gi, 2),
        "total_glycemic_load": round(total_gl, 2),
        "risk_level": risk,
        "alternatives": alternatives,
        "note": "ML-based semantic matching restricted to preference"
    }


# --------------------------------------------------
# MODULE 1A: MEAL RECOMMENDATION LOGIC
# --------------------------------------------------

KERALA_ANCHORS = [
    "puttu", "appam", "idiyappam", "pathiri", "kadala",
    "avial", "thoran", "olan", "theeyal", "pulissery",
    "meen curry", "fish curry", "stew", "ishtu", "kappa"
]

anchor_embeddings = model.encode(KERALA_ANCHORS)

def is_kerala_food(food_name: str) -> bool:
    vec = model.encode([food_name])
    score = cosine_similarity(vec, anchor_embeddings).max()
    return score >= 0.45

class PatientProfile(BaseModel):
    patient_name: str
    fasting_glucose: float
    hba1c: float
    current_glucose: float
    preference: str

class MealItemRecommendation(BaseModel):
    food: str
    quantity: str
    GI: float
    GL: float
    veg_nonveg: str
    explanation: str

NON_VEG_KEYWORDS = [
    "egg", "omelette", "omlet", "anda",
    "chicken", "fish", "meen", "beef",
    "mutton", "duck", "prawn", "shrimp",
    "crab", "chemeen"
]

def force_veg_nonveg(food, dataset_label):
    name = food.lower()
    for kw in NON_VEG_KEYWORDS:
        if kw in name:
            return "Non-Veg"
    return dataset_label

SWEET_KEYWORDS = ["kheer", "kulfi", "halwa", "burfi", "laddu", "jalebi", "dessert", "sweet", "ice cream", "payasam"]
FRIED_KEYWORDS = ["fried", "fry", "pakora", "pakoda", "bhaji", "chips"]

def is_sweet_or_fried(food):
    name = food.lower()
    return any(k in name for k in SWEET_KEYWORDS + FRIED_KEYWORDS)

DISCRETE_ITEMS = ["idli", "dosa", "appam", "puttu", "pathiri"]
RICE_ITEMS = ["rice", "ari", "chawal"]
LIQUID_ITEMS = ["kanji", "payasam", "soup"]

def food_form(food):
    f = food.lower()
    if any(k in f for k in DISCRETE_ITEMS): return "discrete"
    if any(k in f for k in RICE_ITEMS): return "rice"
    if any(k in f for k in LIQUID_ITEMS): return "liquid"
    return "curry"

def quantity_intelligence(food, strict, meal_type):
    form = food_form(food)
    if form == "discrete":
        return "2 pieces (≈120 g)" if strict else "3 pieces (≈180 g)"
    if form == "rice":
        return "½ cup cooked (≈75 g)" if strict else "1 cup cooked (≈150 g)"
    if form == "liquid":
        return "100 ml" if strict else "150 ml"
    return "50 g" if meal_type == "dinner" else ("75 g" if strict else "100 g")

STAPLE_KEYWORDS = ["puttu", "appam", "idiyappam", "pathiri", "rice", "kappa", "dosa", "idli"]

def infer_role(row):
    name = row["food"].lower()
    if any(k in name for k in STAPLE_KEYWORDS): return "staple"
    if any(k in name for k in ["thoran", "avial", "olan", "mezhukkupuratti"]): return "fiber"
    if any(k in name for k in ["curry", "stew", "ishtu"]): return "curry"
    return "other"

def is_strict(profile):
    return (profile.fasting_glucose > 126 or profile.hba1c > 7 or profile.current_glucose > 180)

def pick_food(df, role, used, optional=False):
    pool = df[(df["role"] == role) & (~df["food"].isin(used))]
    if pool.empty:
        if optional: return None
        raise HTTPException(400, f"No {role} foods available")
    return pool.sample(1).iloc[0]

def build_breakfast(df, strict, used):
    staple = pick_food(df, "staple", used)
    curry = pick_food(df, "curry", used)
    used.update([staple["food"], curry["food"]])
    return [
        MealItemRecommendation(
            food=staple["food"],
            quantity=quantity_intelligence(staple["food"], strict, "breakfast"),
            GI=staple["GI"],
            GL=round(staple["GL_per_serving"] * (0.6 if strict else 1), 2),
            veg_nonveg=staple["Veg/Non-veg"],
            explanation="Kerala breakfast staple"
        ),
        MealItemRecommendation(
            food=curry["food"],
            quantity=quantity_intelligence(curry["food"], strict, "breakfast"),
            GI=curry["GI"],
            GL=round(curry["GL_per_serving"] * 0.5, 2),
            veg_nonveg=curry["Veg/Non-veg"],
            explanation="Traditional Kerala breakfast side"
        )
    ]

def build_lunch(df, strict, used):
    items = []
    staple = pick_food(df, "staple", used)
    curry = pick_food(df, "curry", used)
    fiber = pick_food(df, "fiber", used, optional=True)
    used.update([staple["food"], curry["food"]])
    items.append(MealItemRecommendation(
        food=staple["food"],
        quantity=quantity_intelligence(staple["food"], strict, "lunch"),
        GI=staple["GI"],
        GL=round(staple["GL_per_serving"] * (0.6 if strict else 1), 2),
        veg_nonveg=staple["Veg/Non-veg"],
        explanation="Kerala lunch staple"
    ))
    items.append(MealItemRecommendation(
        food=curry["food"],
        quantity=quantity_intelligence(curry["food"], strict, "lunch"),
        GI=curry["GI"],
        GL=round(curry["GL_per_serving"], 2),
        veg_nonveg=curry["Veg/Non-veg"],
        explanation="Main Kerala curry"
    ))
    if fiber is not None:
        used.add(fiber["food"])
        items.append(MealItemRecommendation(
            food=fiber["food"],
            quantity=quantity_intelligence(fiber["food"], strict, "lunch"),
            GI=fiber["GI"],
            GL=round(fiber["GL_per_serving"] * 0.5, 2),
            veg_nonveg=fiber["Veg/Non-veg"],
            explanation="Kerala vegetable/thoran for fiber"
        ))
    return items

def build_dinner(df, strict, used):
    staple = pick_food(df, "staple", used)
    curry = pick_food(df, "curry", used)
    used.update([staple["food"], curry["food"]])
    return [
        MealItemRecommendation(
            food=staple["food"],
            quantity=quantity_intelligence(staple["food"], strict, "dinner"),
            GI=staple["GI"],
            GL=round(staple["GL_per_serving"] * 0.5, 2),
            veg_nonveg=staple["Veg/Non-veg"],
            explanation="Light Kerala dinner"
        ),
        MealItemRecommendation(
            food=curry["food"],
            quantity=quantity_intelligence(curry["food"], strict, "dinner"),
            GI=curry["GI"],
            GL=round(curry["GL_per_serving"] * 0.4, 2),
            veg_nonveg=curry["Veg/Non-veg"],
            explanation="Light dinner curry"
        )
    ]

@app.post("/generate-meal-plan/")
def generate(profile: PatientProfile):
    strict = is_strict(profile)
    plan_type = "Strict" if strict else "Normal"
    work = df.copy()
    work = work[work["food"].apply(is_kerala_food)]
    work["Veg/Non-veg"] = work.apply(lambda r: force_veg_nonveg(r["food"], r["Veg/Non-veg"]), axis=1)
    if profile.preference == "Veg": work = work[work["Veg/Non-veg"] == "Veg"]
    if strict: work = work[~work["food"].apply(is_sweet_or_fried)]
    work["role"] = work.apply(infer_role, axis=1)
    used = set()
    return {
        "patient": profile.patient_name,
        "plan_type": plan_type,
        "meals": {
            "breakfast": build_breakfast(work, strict, used),
            "lunch": build_lunch(work, strict, used),
            "dinner": build_dinner(work, strict, used)
        }
    }

@app.get("/")
def home():
    return {"status": "GlucoGuide Unified Module 1 Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
