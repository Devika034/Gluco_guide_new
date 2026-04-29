from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, MedicalProfile
from schemas import UserSignup, SignupResponse, UserLogin

router = APIRouter(prefix="/auth", tags=["Authentication"])

import traceback
from fastapi.responses import JSONResponse

@router.post("/signup", response_model=SignupResponse)
def signup(user: UserSignup, db: Session = Depends(get_db)):
    try:
        # Check if user already exists due to previous blocked CORS attempts
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            return {
                "message": "User already registered",
                "user_id": existing_user.id
            }

        # Create User
        new_user = User(
            full_name=user.full_name,
            email=user.email,
            password=user.password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Calculate BMI
        height_m = user.height_cm / 100
        bmi = user.weight_kg / (height_m ** 2)

        # Create Medical Profile (initial, without report values)
        profile = MedicalProfile(
            user_id=new_user.id,
            hba1c=None,
            fasting_glucose=None,
            bp_systolic=None,
            bp_diastolic=None,
            cholesterol=None,
            uacr=None,
            egfr=None,
            age=user.age,
            bmi=bmi,
            activity_level=user.activity_level,
            family_history=user.family_history,
            alcohol_smoking=user.alcohol_smoking,
            duration_years=user.duration_years,
            medication_dose=user.medication_dose,
            is_active=True
        )

        db.add(profile)
        db.commit()

        return {
            "message": "User and medical profile created successfully",
            "user_id": new_user.id
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": traceback.format_exc()})

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or db_user.password != user.password:
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
        
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == db_user.id,
        MedicalProfile.is_active == True
    ).order_by(MedicalProfile.created_at.desc()).first()
    
    return {
        "message": "Login successful",
        "id": db_user.id,
        "name": db_user.full_name,
        "email": db_user.email,
        "age": profile.age if profile and profile.age else 30,
        "weight": 70.0, 
        "height": 170.0,
        "dietPreference": "Veg",
        "medication": "",
        "lastHbA1c": profile.hba1c if profile else None,
        "lastFastingGlucose": profile.fasting_glucose if profile else None,
        "lastSystolicBP": profile.bp_systolic if profile else None,
        "lastDiastolicBP": profile.bp_diastolic if profile else None,
        "cholesterol": profile.cholesterol if profile else None,
        "uacr": profile.uacr if profile else None,
        "egfr": profile.egfr if profile else None,
        "medicationDose": profile.medication_dose if profile else None,
        "medicalNotes": None
    }