from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import pdfplumber
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
import re
import tempfile
import os
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

import hashlib

# -------------------------------
# DATABASE (SQLITE)
# -------------------------------
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Move DB to root of backend for visibility
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(BASE_DIR), 'glucoguide.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    age = Column(Float)
    weight = Column(Float)
    height = Column(Float)
    diet_preference = Column(String)
    medication = Column(String)
    has_family_history = Column(Boolean)
    sleeping_hours = Column(Float)
    alcohol_consumption = Column(String)
    smoking_status = Column(String)
    
    # Clinical Fields
    last_hba1c = Column(Float, nullable=True)
    last_fasting_glucose = Column(Float, nullable=True)
    last_systolic_bp = Column(Float, nullable=True)
    last_diastolic_bp = Column(Float, nullable=True)
    medical_notes = Column(String, nullable=True)

class PatientRiskBaseline(Base):
    __tablename__ = "patient_risk_baseline"

    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True) # Linked to User.email
    neuropathy_5y = Column(Float)
    neuropathy_10y = Column(Float)
    retinopathy_5y = Column(Float)
    retinopathy_10y = Column(Float)
    nephropathy_5y = Column(Float)
    nephropathy_10y = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyMeal(Base):
    __tablename__ = "daily_meals"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True)
    date = Column(String, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    meal_type = Column(String) # Breakfast, Lunch, Dinner
    food_name = Column(String)
    is_as_prescribed = Column(Boolean, default=True)
    gl_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# -------------------------------
# SCHEMAS
# -------------------------------
from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileUpdate(BaseModel):
    email: str
    name: Optional[str]
    age: Optional[int]
    weight: Optional[float]
    height: Optional[float]
    dietPreference: Optional[str]
    medication: Optional[str]
    hasFamilyHistory: Optional[bool]
    sleepingHours: Optional[float]
    alcoholConsumption: Optional[str]
    smokingStatus: Optional[str]
    lastHbA1c: Optional[float]
    lastFastingGlucose: Optional[float]
    lastSystolicBP: Optional[float]
    lastDiastolicBP: Optional[float]
    medicalNotes: Optional[str]

class LogMealRequest(BaseModel):
    email: str
    meal_type: str
    food_name: str
    is_as_prescribed: bool
    gl_value: float

# -------------------------------
# UTILS
# -------------------------------
def get_password_hash(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------------
# FASTAPI APP
# -------------------------------
app = FastAPI(
    title="GlucoGuide – Module 3 (Auth & Clinical Data)",
    version="FINAL"
)

# --------------------------------------------------
# AUTH ENDPOINTS
# --------------------------------------------------

@app.post("/register")
async def register(req: RegisterRequest):
    db = SessionLocal()
    if db.query(User).filter(User.email == req.email).first():
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=req.email,
        password_hash=get_password_hash(req.password),
        name=req.name,
        # Default values for initial onboarding
        age=30, weight=70, height=170, diet_preference="Veg",
        has_family_history=False, sleeping_hours=8,
        alcohol_consumption="Never", smoking_status="Never"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"message": "User registered successfully", "email": user.email}

@app.post("/login")
async def login(req: LoginRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.email == req.email).first()
    if not user or user.password_hash != get_password_hash(req.password):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return profile data
    profile = {
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "weight": user.weight,
        "height": user.height,
        "dietPreference": user.diet_preference,
        "medication": user.medication,
        "hasFamilyHistory": user.has_family_history,
        "sleepingHours": user.sleeping_hours,
        "alcoholConsumption": user.alcohol_consumption,
        "smokingStatus": user.smoking_status,
        "lastHbA1c": user.last_hba1c,
        "lastFastingGlucose": user.last_fasting_glucose,
        "lastSystolicBP": user.last_systolic_bp,
        "lastDiastolicBP": user.last_diastolic_bp,
        "medicalNotes": user.medical_notes,
    }
    db.close()
    return {"message": "Login successful", "profile": profile}

@app.post("/update-profile")
async def update_profile(req: ProfileUpdate):
    db = SessionLocal()
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    if req.name: user.name = req.name
    if req.age: user.age = req.age
    if req.weight: user.weight = req.weight
    if req.height: user.height = req.height
    if req.dietPreference: user.diet_preference = req.dietPreference
    if req.medication: user.medication = req.medication
    if req.hasFamilyHistory is not None: user.has_family_history = req.hasFamilyHistory
    if req.sleepingHours: user.sleeping_hours = req.sleepingHours
    if req.alcoholConsumption: user.alcohol_consumption = req.alcoholConsumption
    if req.smokingStatus: user.smoking_status = req.smokingStatus
    if req.lastHbA1c: user.last_hba1c = req.lastHbA1c
    if req.lastFastingGlucose: user.last_fasting_glucose = req.lastFastingGlucose
    if req.lastSystolicBP: user.last_systolic_bp = req.lastSystolicBP
    if req.lastDiastolicBP: user.last_diastolic_bp = req.lastDiastolicBP
    if req.medicalNotes: user.medical_notes = req.medicalNotes
    
    db.commit()
    db.close()
    return {"message": "Profile updated successfully"}

@app.post("/log-meal")
async def log_meal(req: LogMealRequest):
    db = SessionLocal()
    meal = DailyMeal(
        email=req.email,
        meal_type=req.meal_type,
        food_name=req.food_name,
        is_as_prescribed=req.is_as_prescribed,
        gl_value=req.gl_value
    )
    db.add(meal)
    db.commit()
    db.close()
    return {"message": "Meal logged successfully"}

@app.get("/daily-gl/{email}")
async def get_daily_gl(email: str):
    db = SessionLocal()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    meals = db.query(DailyMeal).filter(
        DailyMeal.email == email,
        DailyMeal.date == today
    ).all()
    total_gl = sum(m.gl_value for m in meals)
    db.close()
    return {"total_gl": total_gl, "meals": [m.food_name for m in meals]}

# --------------------------------------------------
# OCR & EXTRACTION
# --------------------------------------------------

@app.post("/extract-medical-data")
async def extract_medical(report: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await report.read())
        pdf_path = tmp.name

    extracted_text = extract_text_mixed_pdf(pdf_path)
    values = extract_medical_values(extracted_text)
    
    try:
        os.remove(pdf_path)
    except:
        pass

    return {
        "extracted_text": extracted_text,
        "parsed_values": values
    }

@app.post("/analyze-diabetic-risk/")
async def analyze_risk(report: UploadFile = File(...), email: str = "guest@example.com"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await report.read())
        pdf_path = tmp.name

    extracted_text = extract_text_mixed_pdf(pdf_path)
    values = extract_medical_values(extracted_text)

    try:
        os.remove(pdf_path)
    except:
        pass

    risks = predict_diabetic_complications(values)

    db = SessionLocal()
    baseline = PatientRiskBaseline(
        id=str(uuid.uuid4()),
        patient_id=email, # Link to User email
        neuropathy_5y=risks["Neuropathy (5 years)"],
        neuropathy_10y=risks["Neuropathy (10 years)"],
        retinopathy_5y=risks["Retinopathy (5 years)"],
        retinopathy_10y=risks["Retinopathy (10 years)"],
        nephropathy_5y=risks["Nephropathy (5 years)"],
        nephropathy_10y=risks["Nephropathy (10 years)"],
    )

    db.add(baseline)
    db.commit()
    db.close()

    return {
        "patient_id": email,
        "extracted_report_text": extracted_text,
        "parsed_health_values": values,
        "risk_probabilities": risks,
        "note": "Baseline risk stored. Module 4 will track changes from this point."
    }

@app.get("/")
def home():
    return {"status": "Module 3 – Diabetic Risk Prediction Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
