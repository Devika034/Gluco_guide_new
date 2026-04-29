print("module3_risk.py loaded")
import os
import uuid
import json
import tempfile
import numpy as np
import cv2
import pdfplumber
import pytesseract
import easyocr
import joblib
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from groq import Groq
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import MedicalProfile, PatientRiskBaseline
from routers.risk_rules import evaluate_clinical_risk
from pydantic import BaseModel
from typing import Optional
import pandas as pd

router = APIRouter(tags=["Risk Prediction"])

# Load KB Context
KB_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "kb_context.txt")
KB_CONTEXT = ""
if os.path.exists(KB_CONTEXT_PATH):
    with open(KB_CONTEXT_PATH, "r", encoding="utf-8") as f:
        KB_CONTEXT = f.read()

# Load ML Risk Model
RISK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")
ML_MODEL = None

if os.path.exists(RISK_MODEL_PATH):
    ML_MODEL = joblib.load(RISK_MODEL_PATH)

print("ML_MODEL:", ML_MODEL)   # 👈 ADD THIS LINE

# Load SHAP Explainer (simplified)
SHAP_EXPLAINER = None

if ML_MODEL is not None:
    try:
        import shap
        print("Initializing SHAP Explainer...")

        if hasattr(ML_MODEL, 'named_steps') and 'clf' in ML_MODEL.named_steps:
            SHAP_EXPLAINER = shap.TreeExplainer(ML_MODEL.named_steps['clf'])
        else:
            SHAP_EXPLAINER = shap.TreeExplainer(ML_MODEL)

        print("SHAP loaded successfully!")

    except Exception as e:
        print("SHAP initialization failed:", e)
        SHAP_EXPLAINER = None

READER = None

def get_reader():
    global READER
    if READER is None:
        READER = easyocr.Reader(['en'])
    return READER

def preprocess_for_ocr(img_input):
    if isinstance(img_input, Image.Image):
        img_array = np.array(img_input)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    elif isinstance(img_input, np.ndarray):
        img_array = img_input
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array
    else:
        raise ValueError("Unsupported image format for preprocessing")

    # 1. Resize if too small (standard height 1800px)
    h, w = gray.shape[:2]
    if h < 1000:
        scaling_factor = 1800.0 / h
        gray = cv2.resize(gray, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_CUBIC)

    # 2. Denoising
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3. Adaptive Thresholding (better for photos/scans)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # 4. Morphological Cleaning (remove some noise)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # 5. Deskewing
    coords = np.column_stack(np.where(cleaned > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        (h, w) = cleaned.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))
        return rotated
    
    return gray

def extract_text_from_image(image_bytes=None, file_path=None):
    text_out = ""
    if file_path:
        img = cv2.imread(file_path)
    elif image_bytes:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        return ""

    if img is None:
        return "[Error: Could not decode image]"

    processed_img = preprocess_for_ocr(img)

    try:
        reader = get_reader()
        results = reader.readtext(processed_img, detail=0)
        text_out += "\n".join(results)
    except Exception as e:
        pass

    try:
        tess_text = pytesseract.image_to_string(processed_img)
        text_out += "\n" + tess_text
    except Exception as e:
        pass

    return text_out

def extract_text_mixed_pdf(pdf_path):
    final_text = ""
    images = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                final_text += f"\n--- Page {page_num+1} (Digital) ---\n{text}"
            else:
                try:
                    if images is None:
                        images = convert_from_path(pdf_path)
                    if images and page_num < len(images):
                        processed_img = preprocess_for_ocr(images[page_num])
                        ocr_text = pytesseract.image_to_string(processed_img)
                        final_text += f"\n--- Page {page_num+1} (OCR) ---\n{ocr_text}"
                except Exception as e:
                    pass
    return final_text

def analyze_with_groq(text_content):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key.strip() == "":
        api_key = "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"
        
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are a Specialist Diabetologist and Medical Data Analyst.
    
    TASK 1: EXTRACT structured clinical data from the potentially noisy OCR text provided below.
    
    Medical Report Text (OCR Output):
    \"\"\"
    {text_content}
    \"\"\"
    
    GUIDELINES for Extraction:
    - Look for standard diabetic markers: HbA1c, Fasting Blood Sugar (FBS), Blood Pressure (BP), Cholesterol, UACR (Urine Albumin-to-Creatinine Ratio), and eGFR (estimated Glomerular Filtration Rate).
    - Handle common OCR errors (e.g., '1' for 'l', '0' for 'O', misread decimals).
    - Convert all values to standard units: HbA1c in %, Glucose in mg/dL, BP in mmHg, Cholesterol in mg/dL, UACR in mg/g, eGFR in mL/min/1.73m².
    - If a range is provided, use the latest or most specific value.
    - If a value is missing or unreadable, use `null`.
    
    TASK 2: Generate a Clinical Explanation.
    Explain the risks associated with these specific levels based on standard clinical guidelines.
    
    Reference Highlights from Guidelines:
    {KB_CONTEXT[:1500]}
    
    JSON Output Requirements:
    - Return ONLY a JSON object.
    - STRICT Keys: "hba1c", "fasting_glucose", "bp_systolic", "bp_diastolic", "cholesterol", "uacr", "egfr".
    - Include a "clinical_summary" key with your explanation.
    
    Example Structure:
    {{
        "extracted_features": {{
            "hba1c": 7.5,
            "fasting_glucose": 140,
            "bp_systolic": 135,
            "bp_diastolic": 85,
            "cholesterol": 190,
            "uacr": 25,
            "egfr": 72
        }},
        "clinical_summary": "High HbA1c and fasting glucose indicate poorly controlled diabetes..."
    }}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a precise medical data extraction engine. You output valid JSON only based on the provided text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        data = json.loads(response_content)
        
        # Normalize structure if LLM didn't nest it
        if "extracted_features" not in data:
            # Check if keys are at root
            if any(k in data for k in ["hba1c", "fasting_glucose", "uacr"]):
                features = {k: data.get(k) for k in ["hba1c", "fasting_glucose", "bp_systolic", "bp_diastolic", "cholesterol", "uacr", "egfr"]}
                summary = data.get("clinical_summary", "Extraction complete.")
                data = {"extracted_features": features, "clinical_summary": summary}
            else:
                return {"error": "LLM failed to extract structured features"}
            
        features = data.get("extracted_features", {})
        
        # Ensure 'glucose' key which risk_rules.py expects
        if "fasting_glucose" in features and "glucose" not in features:
            features["glucose"] = features["fasting_glucose"]
            
        risk_report = evaluate_clinical_risk(features)
        risk_report["parsed_values"] = features
        risk_report["explanation"] = data.get("clinical_summary", "No explanation provided.")
        return risk_report
    except Exception as e:
        return {"error": f"LLM Analysis Exception: {str(e)}"}

@router.post("/analyze-diabetic-risk/{user_id}")
async def analyze_risk(user_id: int, reports: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    full_extracted_text = ""
    
    for report in reports:
        content_type = report.content_type
        filename = report.filename.lower()
        extracted_text = ""
        
        if "pdf" in content_type or filename.endswith(".pdf"):
             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await report.read())
                pdf_path = tmp.name
             try:
                 extracted_text = extract_text_mixed_pdf(pdf_path)
             except Exception as e:
                 extracted_text = f"[Error reading PDF: {str(e)}]"
                 
             try:
                os.remove(pdf_path)
             except:
                pass
        elif "image" in content_type or filename.endswith((".jpg", ".jpeg", ".png", ".bmp")):
            img_bytes = await report.read()
            extracted_text = extract_text_from_image(image_bytes=img_bytes)
        else:
            extracted_text = "[Unsupported file format. Please upload PDF or Image.]"

        full_extracted_text += f"\n\n--- Report: {report.filename} ---\n{extracted_text}"
            
    llm_insights = analyze_with_groq(full_extracted_text)
    
    if not llm_insights or "error" in llm_insights:
        return {"Error": f"LLM Analysis failed: {llm_insights.get('error', 'No response')}"}

    parsed_values = llm_insights.get("parsed_values", {})

    # -------------------------------
    # UPDATE MEDICAL PROFILE
    # -------------------------------
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()

    if profile:
        new_profile = MedicalProfile(
            user_id=profile.user_id,
            hba1c=profile.hba1c,
            fasting_glucose=profile.fasting_glucose,
            bp_systolic=profile.bp_systolic,
            bp_diastolic=profile.bp_diastolic,
            cholesterol=profile.cholesterol,
            uacr=profile.uacr,
            egfr=profile.egfr,
            age=profile.age,
            bmi=profile.bmi,
            activity_level=profile.activity_level,
            family_history=profile.family_history,
            alcohol_smoking=profile.alcohol_smoking,
            duration_years=profile.duration_years,
            medication_dose=profile.medication_dose,
            is_active=True
        )

        field_map = [
            "hba1c",
            "fasting_glucose",
            "bp_systolic",
            "bp_diastolic",
            "cholesterol",
            "uacr",
            "egfr"
        ]

        for field in field_map:
            value = parsed_values.get(field)
            if value is not None:
                if hasattr(new_profile, field):
                    setattr(new_profile, field, float(value))

        profile.is_active = False
        db.add(new_profile)
        db.commit()

    risks = llm_insights.get("risk_predictions", {})
    explanation = llm_insights.get("explanation", "No explanation available.")

    def fmt(val):
        return f"{val}%" if isinstance(val, (int, float)) else "N/A"

    neuropathy = risks.get("neuropathy", {})
    retinopathy = risks.get("retinopathy", {})
    nephropathy = risks.get("nephropathy", {})

    # -------------------------------
    # SAVE BASELINE TO DATABASE
    # -------------------------------
    baseline = PatientRiskBaseline(
        id=str(uuid.uuid4()),
        patient_id=str(user_id),
        neuropathy_5y=float(neuropathy.get("5_years") or 0),
        neuropathy_10y=float(neuropathy.get("10_years") or 0),
        retinopathy_5y=float(retinopathy.get("5_years") or 0),
        retinopathy_10y=float(retinopathy.get("10_years") or 0),
        nephropathy_5y=float(nephropathy.get("5_years") or 0),
        nephropathy_10y=float(nephropathy.get("10_years") or 0),
    )
    db.add(baseline)
    db.commit()

    return {
        "extracted_text": full_extracted_text,
        "extracted_values": parsed_values,
        "clinical_explanation": explanation,
        "neuropathy": {
            "5_years": fmt(neuropathy.get("5_years")),
            "10_years": fmt(neuropathy.get("10_years"))
        },
        "retinopathy": {
            "5_years": fmt(retinopathy.get("5_years")),
            "10_years": fmt(retinopathy.get("10_years"))
        },
        "nephropathy": {
            "5_years": fmt(nephropathy.get("5_years")),
            "10_years": fmt(nephropathy.get("10_years"))
        }
    }

@router.post("/risk/predict/{user_id}")
def predict_risk_from_db(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()
    
    if not profile:
        raise HTTPException(status_code=400, detail="Active medical profile not found")
        
    risk_input = {
        "hba1c": profile.hba1c,
        "fasting_glucose": profile.fasting_glucose,
        "bp_systolic": profile.bp_systolic,
        "bp_diastolic": profile.bp_diastolic,
        "cholesterol": profile.cholesterol,
        "uacr": profile.uacr,
        "egfr": profile.egfr,
        "bmi": profile.bmi,
        "age": profile.age,
        "family_history": profile.family_history,
        "duration_years": profile.duration_years
    }
    
    # Run prediction model using the existing medical rules
    risk_report = evaluate_clinical_risk(risk_input)
    
    risks = risk_report.get("risk_predictions", {})
    neuropathy = risks.get("neuropathy", {})
    retinopathy = risks.get("retinopathy", {})
    nephropathy = risks.get("nephropathy", {})

    baseline = PatientRiskBaseline(
        id=str(uuid.uuid4()),
        patient_id=str(user_id),
        neuropathy_5y=float(neuropathy.get("5_years") or 0),
        neuropathy_10y=float(neuropathy.get("10_years") or 0),
        retinopathy_5y=float(retinopathy.get("5_years") or 0),
        retinopathy_10y=float(retinopathy.get("10_years") or 0),
        nephropathy_5y=float(nephropathy.get("5_years") or 0),
        nephropathy_10y=float(nephropathy.get("10_years") or 0),
    )
    db.add(baseline)
    db.commit()

    return {
        "neuropathy": {
            "5_years": float(neuropathy.get("5_years") or 0),
            "10_years": float(neuropathy.get("10_years") or 0)
        },
        "retinopathy": {
            "5_years": float(retinopathy.get("5_years") or 0),
            "10_years": float(retinopathy.get("10_years") or 0)
        },
        "nephropathy": {
            "5_years": float(nephropathy.get("5_years") or 0),
            "10_years": float(nephropathy.get("10_years") or 0)
        }
    }


@router.get("/explain-risk/{user_id}")
def explain_risk_json(user_id: int, db: Session = Depends(get_db)):

    # ✅ Fallback if SHAP not available
    if SHAP_EXPLAINER is None:
        return {
            "base_value": 0.5,
            "contributors": [
                {"feature": "HbA1c", "impact": 0.5},
                {"feature": "Fasting Glucose", "impact": 0.3},
                {"feature": "Blood Pressure", "impact": 0.1},
                {"feature": "Cholesterol", "impact": 0.1}
            ],
            "note": "SHAP not available, using fallback explanation"
        }

    profile = db.query(MedicalProfile).filter(
        MedicalProfile.user_id == user_id,
        MedicalProfile.is_active == True
    ).first()

    if not profile:
        raise HTTPException(status_code=400, detail="Active medical profile not found")
        
    try:
        high_bp = 1 if (profile.bp_systolic and profile.bp_systolic > 130) else 0
        high_chol = 1 if (profile.cholesterol and profile.cholesterol > 200) else 0
        
        age_bucket = 8
        
        input_vector = pd.DataFrame([{
            'HighBP': high_bp,
            'HighChol': high_chol,
            'BMI': profile.bmi or 25.0,
            'Smoker': 1 if profile.alcohol_smoking else 0,
            'Stroke': 0, 
            'HeartDiseaseorAttack': 0,
            'PhysActivity': 1 if profile.activity_level == 0 else 0,
            'GenHlth': 3, 
            'PhysHlth': 0,
            'DiffWalk': 0,
            'Sex': 1, 
            'Age': age_bucket
        }])
        
        if hasattr(ML_MODEL, 'named_steps') and 'scaler' in ML_MODEL.named_steps:
            scaled_input = ML_MODEL.named_steps['scaler'].transform(input_vector)
            shap_vals = SHAP_EXPLAINER.shap_values(scaled_input)
        else:
            shap_vals = SHAP_EXPLAINER.shap_values(input_vector)
        
        target_idx = -1 

        if isinstance(shap_vals, list):
            vals = shap_vals[target_idx][0]
            base_val = SHAP_EXPLAINER.expected_value[target_idx]
        elif hasattr(shap_vals, "shape") and len(shap_vals.shape) == 3:
            vals = shap_vals[0, :, target_idx]
            base_val = (
                SHAP_EXPLAINER.expected_value[target_idx]
                if isinstance(SHAP_EXPLAINER.expected_value, (list, np.ndarray))
                else SHAP_EXPLAINER.expected_value
            )
        else:
            vals = shap_vals[0]
            base_val = SHAP_EXPLAINER.expected_value
            
        if isinstance(base_val, np.ndarray):
            base_val = base_val[target_idx]

        feature_names = [
            'HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke',
            'HeartDiseaseorAttack', 'PhysActivity', 'GenHlth',
            'PhysHlth', 'DiffWalk', 'Sex', 'Age'
        ]

        contributors = []
        for name, val in zip(feature_names, vals):
            contributors.append({
                "feature": name,
                "impact": float(val)
            })
            
        contributors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "base_value": float(base_val),
            "contributors": contributors[:5]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
