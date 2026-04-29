from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime

class AnswerSet(BaseModel):
    answers: Dict[str, int]  # question_id → option_score

class DiseaseResult(BaseModel):
    status: str
    trend: str
    score: float
    recommendations: List[str]
    timestamp: datetime
