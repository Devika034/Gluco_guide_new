from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List
from collections import defaultdict
import uvicorn

app = FastAPI(title="Module 4 – Disease Progress Tracker")

class AnswerSet(BaseModel):
    answers: Dict[str, int]

class DiseaseResult(BaseModel):
    status: str
    trend: str
    score: float
    interpretation: List[str]
    recommendations: List[str]
    timestamp: datetime

RETINOPATHY_QUESTIONS = {
    "blurred_vision": {
        "question": "Have you experienced blurred vision recently?",
        "options": {"No": 0, "Occasionally": 1, "Frequently": 2}
    },
    "floaters": {
        "question": "Do you notice dark spots or floaters?",
        "options": {"No": 0, "Sometimes": 1, "Often": 2}
    },
    "eye_strain": {
        "question": "Do your eyes feel strained or tired?",
        "options": {"No": 0, "Mild": 1, "Severe": 2}
    },
    "eye_exam": {
        "question": "When was your last eye examination?",
        "options": {"Within 6 months": 0, "6–12 months ago": 1, "More than 1 year": 2}
    }
}

NEPHROPATHY_QUESTIONS = {
    "swelling": {
        "question": "Any swelling in feet or face?",
        "options": {"No": 0, "Mild": 1, "Noticeable": 2}
    },
    "urination": {
        "question": "Any change in urination frequency?",
        "options": {"Normal": 0, "Slight change": 1, "Major change": 2}
    },
    "fatigue": {
        "question": "How fatigued do you feel?",
        "options": {"Normal": 0, "Moderate": 1, "Severe": 2}
    },
    "bp": {
        "question": "Recent blood pressure readings?",
        "options": {"Normal": 0, "Occasionally high": 1, "Frequently high": 2}
    }
}

NEUROPATHY_QUESTIONS = {
    "tingling": {
        "question": "Any tingling or numbness in limbs?",
        "options": {"No": 0, "Occasional": 1, "Frequent": 2}
    },
    "pain": {
        "question": "Burning or sharp nerve pain?",
        "options": {"No": 0, "Sometimes": 1, "Often": 2}
    },
    "balance": {
        "question": "Any balance issues while walking?",
        "options": {"No": 0, "Rare": 1, "Frequent": 2}
    },
    "foot_care": {
        "question": "How often do you inspect your feet?",
        "options": {"Daily": 0, "Occasionally": 1, "Rarely": 2}
    }
}

QUESTION_MAP = {
    "retinopathy": RETINOPATHY_QUESTIONS,
    "nephropathy": NEPHROPATHY_QUESTIONS,
    "neuropathy": NEUROPATHY_QUESTIONS
}

def compute_score(answers: dict) -> float:
    if not answers: return 0.0
    total = sum(answers.values())
    max_score = len(answers) * 2
    return round(total / max_score, 2)

def interpret_score(current: float, previous: float | None):
    if previous is None: trend = "Baseline"
    elif current > previous + 0.1: trend = "Worsening"
    elif current < previous - 0.1: trend = "Improving"
    else: trend = "Stable"

    interpretation = []
    if current < 0.3:
        status = "Stable"
        interpretation = ["Symptoms are minimal or absent", "condition appears stable", "Continue routine monitoring"]
    elif current < 0.6:
        status = "Watchful"
        interpretation = ["Some symptoms have increased", "May indicate rising stress on the system", "No emergency signs detected"]
    else:
        status = "High Risk"
        interpretation = ["Significant symptoms detected", "High likelihood of complications", "Immediate medical attention recommended"]
    return status, trend, interpretation

def recommendations_for(disease: str, score: float):
    base = {
        "retinopathy": ["Maintain stable blood glucose", "Limit screen strain", "Schedule regular eye exams"],
        "nephropathy": ["Monitor blood pressure", "Reduce salt intake", "Stay hydrated"],
        "neuropathy": ["Inspect feet daily", "Avoid walking barefoot", "Maintain glucose control"]
    }
    if score > 0.6:
        base[disease].append("Consult specialist urgently")
        if disease == "retinopathy": base[disease].append("Schedule eye exam within 3 months")
    return base[disease]

progress_store = defaultdict(lambda: defaultdict(list))

def save_score(patient_id, disease, score):
    progress_store[patient_id][disease].append(score)

def get_last_score(patient_id, disease):
    history = progress_store[patient_id][disease]
    return history[-2] if len(history) > 1 else None

@app.get("/questions/{disease}")
def get_questions(disease: str):
    return QUESTION_MAP[disease]

@app.post("/analyze/{patient_id}/{disease}", response_model=DiseaseResult)
def analyze(patient_id: str, disease: str, data: AnswerSet):
    current_score = compute_score(data.answers)
    previous_score = get_last_score(patient_id, disease)
    status, trend, interpretation = interpret_score(current_score, previous_score)
    save_score(patient_id, disease, current_score)
    return DiseaseResult(
        status=status, trend=trend, score=current_score,
        interpretation=interpretation, recommendations=recommendations_for(disease, current_score),
        timestamp=datetime.utcnow()
    )

@app.get("/")
def home():
    return {"message": "Module 4 Disease Progress Tracker Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
