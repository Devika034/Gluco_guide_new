from pydantic import BaseModel
from typing import Optional

class UserSignup(BaseModel):
    full_name: str
    email: str
    password: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: int
    family_history: int
    alcohol_smoking: int
    duration_years: int
    medication_dose: float

class SignupResponse(BaseModel):
    message: str
    user_id: int

class UserLogin(BaseModel):
    email: str
    password: str

class FoodItem(BaseModel):
    food_name: str
    quantity_g: float

class LogMealRequest(BaseModel):
    foods: list[FoodItem]

class LogMealResponse(BaseModel):
    avg_gi: float
    total_gl: float