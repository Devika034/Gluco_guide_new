from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class MedicalProfile(Base):
    __tablename__ = "medical_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    hba1c = Column(Float, nullable=True)
    fasting_glucose = Column(Float, nullable=True)
    bp_systolic = Column(Float, nullable=True)
    bp_diastolic = Column(Float, nullable=True)
    cholesterol = Column(Float, nullable=True)
    uacr = Column(Float, nullable=True)
    egfr = Column(Float, nullable=True)

    age = Column(Integer, nullable=True)
    bmi = Column(Float, nullable=True)
    activity_level = Column(Integer, nullable=True)
    family_history = Column(Integer, nullable=True)
    alcohol_smoking = Column(Integer, nullable=True)
    duration_years = Column(Integer, nullable=True)
    medication_dose = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

class PatientRiskBaseline(Base):
    __tablename__ = "patient_risk_baseline"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)

    neuropathy_5y = Column(Float)
    neuropathy_10y = Column(Float)
    retinopathy_5y = Column(Float)
    retinopathy_10y = Column(Float)
    nephropathy_5y = Column(Float)
    nephropathy_10y = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    breakfast = Column(String)
    lunch = Column(String)
    dinner = Column(String)

    avg_gi = Column(Float)
    total_gl = Column(Float)

    created_at = Column(DateTime)

class LoggedMeal(Base):
    __tablename__ = "logged_meals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    
    foods_json = Column(String)  # Stored as JSON string
    avg_gi = Column(Float)
    total_gl = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

class SpikePrediction(Base):
    __tablename__ = "spike_predictions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    current_glucose = Column(Float)
    avg_gi = Column(Float)
    total_gl = Column(Float)

    spike_probability = Column(Float)
    severity = Column(String)

    created_at = Column(DateTime)

class QuestionnaireScore(Base):
    __tablename__ = "questionnaire_scores"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

    disease_type = Column(String)
    score = Column(Float)
    trend = Column(String)

    created_at = Column(DateTime)