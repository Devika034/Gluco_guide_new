from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime

class AnswerSet(BaseModel):
    answers: Dict[str, int]

class DiseaseResult(BaseModel):
    status: str
    trend: str
    score: float
    interpretation: List[str]
    recommendations: List[str]
    timestamp: datetime
