from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
import tempfile
import os

from database import get_db
from models import MedicalProfile
from routers.services.ocr_service import extract_text_from_pdf, extract_values

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.post("/upload-report/{user_id}")
async def upload_report(
    user_id: int,
    report: UploadFile = File(...),   # ✅ SINGLE FILE (IMPORTANT)
    db: Session = Depends(get_db)
):

    # Get active medical profile
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()

    if not profile:
        return {"error": "Active profile not found"}

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await report.read())
        file_path = tmp.name

    # Extract text + values
    text = extract_text_from_pdf(file_path)
    values = extract_values(text)

    os.remove(file_path)

    # Update DB only if values found
    if values.get("hba1c") is not None:
        profile.hba1c = values["hba1c"]

    if values.get("fasting_glucose") is not None:
        profile.fasting_glucose = values["fasting_glucose"]

    if values.get("bp_systolic") is not None:
        profile.bp_systolic = values["bp_systolic"]

    if values.get("bp_diastolic") is not None:
        profile.bp_diastolic = values["bp_diastolic"]

    if values.get("cholesterol") is not None:
        profile.cholesterol = values["cholesterol"]

    db.commit()

    return {
        "message": "Report processed successfully",
        "extracted_values": values
    }