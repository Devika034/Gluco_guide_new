from fastapi import FastAPI, UploadFile, File, HTTPException
import json
from dotenv import load_dotenv
load_dotenv()
from risk_rules import evaluate_clinical_risk

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
print("DEBUG: Starting Module 3 (Pure LLM Version) - 2026-01-18")
import uvicorn
import pdfplumber
import pytesseract
import cv2
import numpy as np
import easyocr
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
import re
import tempfile
import os
import uuid
import json
from datetime import datetime


# -------------------------------
# DATABASE (SQLITE)
# -------------------------------
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./glucoguide.db"

# -------------------------------
# RAG: KNOWLEDGE BASE LOADING
# -------------------------------
KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))

def load_guidelines(filename):
    try:
        path = os.path.join(KNOWLEDGE_BASE_DIR, "diet_guidelines", filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Error loading guideline {filename}: {e}")
    return ""

ADA_CONTEXT = load_guidelines("ada_standards_2024.txt")
print(f"DEBUG: Loaded ADA Standards ({len(ADA_CONTEXT)} chars)")

# Load KB Context (New Hybrid Source)
KB_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "kb_context.txt")
KB_CONTEXT = ""
if os.path.exists(KB_CONTEXT_PATH):
    with open(KB_CONTEXT_PATH, "r", encoding="utf-8") as f:
        KB_CONTEXT = f.read()
    print(f"DEBUG: Loaded KB Context ({len(KB_CONTEXT)} chars)")

# Load ML Risk Model
RISK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")
ML_MODEL = None
if os.path.exists(RISK_MODEL_PATH):
    ML_MODEL = joblib.load(RISK_MODEL_PATH)
    print("DEBUG: Loaded Random Forest Risk Model")
    
    SHAP_PATH = os.path.join(os.path.dirname(__file__), "shap_risk_explainer.pkl")
    SHAP_EXPLAINER = None
    if os.path.exists(SHAP_PATH):
        try:
             SHAP_EXPLAINER = joblib.load(SHAP_PATH)
             print("DEBUG: Loaded SHAP Explainer")
        except Exception as e:
             print(f"Warning: Failed to load SHAP explainer: {e}")

else:
    print("WARNING: risk_model.pkl not found. Falling back to pure LLM.")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

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

Base.metadata.create_all(bind=engine)

# -------------------------------
# FASTAPI APP
# -------------------------------
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="GlucoGuide – Module 3 (Diabetic Complication Risk Prediction)",
    version="FINAL"
)

# New Schema for direct JSON XAI requests
class RiskInput(BaseModel):
    hba1c: Optional[float] = 0.0
    bmi: Optional[float] = 25.0
    age: Optional[int] = 50
    hypertension: Optional[int] = 0
    cholesterol: Optional[float] = 180.0
    smoker: Optional[int] = 0
    heart_disease: Optional[int] = 0
    phys_activity: Optional[int] = 1


# --------------------------------------------------
# OCR PREPROCESSING
# --------------------------------------------------

# Global EasyOCR Reader (Lazy load or init once)
READER = None

def get_reader():
    global READER
    if READER is None:
        print("Loading EasyOCR Model...")
        READER = easyocr.Reader(['en']) #gpu=False if no GPU
    return READER

def preprocess_for_ocr(img_input):
    """
    Advanced preprocessing:
    1. Convert PIL to Numpy if needed
    2. Grayscale
    3. Denoising
    4. Thresholding
    5. Deskewing (Simple)
    """
    # Handle PIL Image (from pdf2image)
    if isinstance(img_input, Image.Image):
        # PIL is RGB, convert to BGR for consistency if needed, or straight to Gray
        # Let's just convert to array. PIL -> RGB.
        img_array = np.array(img_input)
        # Convert RGB to BGR if we were strictly using BGR, but for Gray it's:
        # Gray = 0.299*R + 0.587*G + 0.114*B.
        # cv2.COLOR_BGR2GRAY expects BGR. 
        # So we should convert RGB(PIL) -> BGR(CV2) or use RGB2GRAY.
        # Let's use RGB2GRAY for PIL source.
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    elif isinstance(img_input, np.ndarray):
        img_array = img_input
        # check dimensions
        if len(img_array.shape) == 3:
            # Assumed BGR from cv2.imread
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array
    else:
        raise ValueError("Unsupported image format for preprocessing")

    # Denoise

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Thresholding for Deskewing Calculation
    # Use THRESH_BINARY_INV so text becomes White (255) and background Black (0)
    # This ensures minAreaRect calculates angle of the TEXT, not the background.
    thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Deskewing
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    (h, w) = thresh.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Rotate the original grayscale (or denoised) image, not the thresholded one if we want better OCR
    # But wait, OCR engines often like clean binarized images. 
    # Tesseract likes binarized. EasyOCR deals with colors/gray.
    # Let's return the rotated grayscale/denoised image for EasyOCR.
    # Use 'white' (255) border for consistency with paper.
    rotated = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))

    return rotated

def extract_text_from_image(image_bytes=None, file_path=None):
    """
    Extracts text from an image file (bytes or path) using EasyOCR + Tesseract fallback/combo.
    """
    text_out = ""
    
    # Load Image
    if file_path:
        img = cv2.imread(file_path)
    elif image_bytes:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        return ""

    if img is None:
        return "[Error: Could not decode image]"

    # Preprocess
    processed_img = preprocess_for_ocr(img)

    # 1. Try EasyOCR (Good for structure)
    try:
        reader = get_reader()
        results = reader.readtext(processed_img, detail=0)
        text_out += "\n".join(results)
    except Exception as e:
        text_out += f"\n[EasyOCR Failed: {e}]"

    # 2. Try Tesseract (Good for density) - Append or use as fallback?
    # Let's append for maximum coverage, regex will find values anywhere.
    try:
        tess_text = pytesseract.image_to_string(processed_img)
        text_out += "\n" + tess_text
    except Exception as e:
        text_out += f"\n[Tesseract Failed: {e}]"

    return text_out

def extract_text_mixed_pdf(pdf_path):
    final_text = ""
    images = None
    
    # Try to load images only if needed (lazy load or safe load)
    # Actually, we can't load images if poppler is missing. 
    # We will check if we can convert later.

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                final_text += f"\n--- Page {page_num+1} (Digital) ---\n{text}"
            else:
                # Digital extraction failed, try OCR
                try:
                    if images is None:
                        # Only attempt to convert to images if we actually need OCR
                        # This prevents crashing on startup/processing if Poppler is missing but PDF is text-based.
                        images = convert_from_path(pdf_path)
                    
                    if images and page_num < len(images):
                        processed_img = preprocess_for_ocr(images[page_num])
                        ocr_text = pytesseract.image_to_string(processed_img)
                        final_text += f"\n--- Page {page_num+1} (OCR) ---\n{ocr_text}"
                except PDFInfoNotInstalledError:
                    final_text += f"\n[Warning: OCR unavailable (Poppler not installed). Could not read Page {page_num+1} as image.]"
                except Exception as e:
                    final_text += f"\n[Warning: OCR failed for Page {page_num+1}: {str(e)}]"
                    
    return final_text

# --------------------------------------------------


# --------------------------------------------------
# LLM ANALYSIS (Groq)
# --------------------------------------------------
from groq import Groq
import json # Ensure json is imported for json.loads

def analyze_with_groq(text_content):
    """
    Uses Groq API (Llama 3.3) to analyze the medical text.
    Extracts structured data and provides a brief summary.
    """
    # Use Environment Variable or Hardcoded key as fallback
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key.strip() == "":
        api_key = "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"
        print("DEBUG: Using fallback hardcoded GROQ_API_KEY")
    else:
        print("DEBUG: Using GROQ_API_KEY from environment")
        
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are a Specialist Diabetologist assisting with a Hybrid AI Analysis.
    
    TASK 1: EXTRACT structured clinical data from the report below.
    Return a JSON with these keys (use null if not found):
    - hba1c (float, e.g. 7.2)
    - bmi (float)
    - age (int)
    - sex (0 for Female, 1 for Male)
    - glucose (fasting, int)
    - bp_systolic (int)
    - bp_diastolic (int)
    - ldl (int, Low Density Lipoprotein)
    - hdl (int, High Density Lipoprotein)
    - triglycerides (int)
    - creatinine (float)
    - uacr (float, Urine Albumin/Creatinine Ratio)
    - egfr (int, Estimated Glomerular Filtration Rate)
    - alt (int, Alanine Aminotransferase)
    - ast (int, Aspartate Aminotransferase)
    - smoker (0 or 1)
    - hypertension (0 or 1, infer from BP > 130/80)
    - heart_disease (0 or 1)
    
    TASK 2: Generate a Clinical Explanation.
    Based on the extracted values AND the following Guidelines, explain the specific risks.
    
    [CLINICAL GUIDELINES FROM KNOWLEDGE BASE]
    {KB_CONTEXT[:2000]}... (Truncated for fit)
    
    Medical Report Text:
    {text_content}
    
    Return STRICT JSON:
    {{
        "extracted_features": {{ "hba1c": ..., "bmi": ... }},
        "clinical_summary": "Your explanation here..."
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a medical data extraction assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        response_content = completion.choices[0].message.content
        data = json.loads(response_content)
        
        # Robust Fallback: If LLM returned flat JSON instead of nested
        if "extracted_features" not in data and "hba1c" in data:
            data["extracted_features"] = data
            
        print(f"DEBUG: LLM Output Keys: {data.keys()}") # Debug print
        
        # -------------------------------
        # HYBRID LOGIC: ADVANCED CLINICAL RULES
        # -------------------------------
        features = data.get("extracted_features", {})
        
        # Call the logic engine
        risk_report = evaluate_clinical_risk(features)
        
        # Attach raw values for API response to maintain compatibility
        risk_report["parsed_values"] = features
        
        return risk_report
        
    except Exception as e:
        error_msg = f"Groq API Error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {"error": error_msg}

# --------------------------------------------------
# API ENDPOINT
# --------------------------------------------------

from typing import List

@app.post("/analyze-diabetic-risk/")
async def analyze_risk(reports: List[UploadFile] = File(...)):

    full_extracted_text = ""
    
    for report in reports:
        # Check proper file type
        content_type = report.content_type
        filename = report.filename.lower()
        
        extracted_text = ""
        
        if "pdf" in content_type or filename.endswith(".pdf"):
             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await report.read())
                pdf_path = tmp.name
                
             extracted_text = extract_text_mixed_pdf(pdf_path)
             
             try:
                os.remove(pdf_path)
             except:
                pass

        elif "image" in content_type or filename.endswith((".jpg", ".jpeg", ".png", ".bmp")):
            # Direct Image Processing
            img_bytes = await report.read()
            extracted_text = extract_text_from_image(image_bytes=img_bytes)
            
        else:
            extracted_text = "[Unsupported file format. Please upload PDF or Image.]"

        full_extracted_text += f"\n\n--- Report: {report.filename} ---\n{extracted_text}"
            
    # -------------------------------
    # SAVE AND ANALYZE WITH LLM
    # -------------------------------
    
    # Ensure directory exists
    os.makedirs("extracted_data", exist_ok=True)
    
    # Save extracted text to JSON
    json_filename = f"extracted_data/{uuid.uuid4()}_extracted.json"
    with open(json_filename, "w") as f:
        json.dump({"filename": reports[0].filename, "text": full_extracted_text}, f, indent=4)
        
    print(f"DEBUG: Saved extracted text to {json_filename}")

    # Call Groq/Llama for Analysis
    llm_insights = analyze_with_groq(full_extracted_text)
    
    if not llm_insights:
        return {"Error": "LLM Analysis failed. No response from Groq."}
    
    if isinstance(llm_insights, dict) and "error" in llm_insights:
        return {"Error": f"LLM Analysis failed: {llm_insights['error']}"}

    parsed_values = llm_insights.get("parsed_values", {})
    risks = llm_insights.get("risk_predictions", {})
    explanation = llm_insights.get("explanation", "No explanation available.")
    
    # Format risks as percentages strings for consistency with request
    def fmt(val):
        return f"{val}%" if isinstance(val, (int, float)) else "N/A"

    neuropathy = risks.get("neuropathy", {})
    retinopathy = risks.get("retinopathy", {})
    nephropathy = risks.get("nephropathy", {})

    # -------------------------------
    # SAVE BASELINE TO DATABASE
    # -------------------------------
    # Storing raw integers in DB for analytics, returning strings to UI
    patient_id = str(uuid.uuid4())
    db = SessionLocal()

    baseline = PatientRiskBaseline(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        neuropathy_5y=float(neuropathy.get("5_years") or 0),
        neuropathy_10y=float(neuropathy.get("10_years") or 0),
        retinopathy_5y=float(retinopathy.get("5_years") or 0),
        retinopathy_10y=float(retinopathy.get("10_years") or 0),
        nephropathy_5y=float(nephropathy.get("5_years") or 0),
        nephropathy_10y=float(nephropathy.get("10_years") or 0),
    )

    db.add(baseline)
    db.commit()
    db.close()

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

@app.post("/explain-risk-json/")
def explain_risk_json(data: RiskInput):
    """
    Direct endpoint for Module 5 Aggregator.
    Returns feature contribution for High Risk Classification.
    """
    if SHAP_EXPLAINER is None:
         raise HTTPException(status_code=503, detail="SHAP Explainer not available.")
    
    try:
        # Create input vector matching the model
        # Mapped to cols: 'HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 'GenHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age'
        
        # Mapping Logic
        high_bp = 1 if (data.hypertension == 1) else 0
        high_chol = 1 if (data.cholesterol > 200) else 0
        
        # Age Mapping (CDC BRFSS uses buckets, we approximate linear for now or map)
        # 1=18-24 ... 8=55-59 ... 13=80+
        # Simple Logic: (Age - 20) / 5. But lets just pass raw or default 8 (55yo)
        age_bucket = 8
        if data.age:
            age_bucket = min(13, max(1, (data.age - 18) // 5))

        input_vector = pd.DataFrame([{
            'HighBP': high_bp,
            'HighChol': high_chol,
            'BMI': data.bmi,
            'Smoker': data.smoker,
            'Stroke': 0, 
            'HeartDiseaseorAttack': data.heart_disease,
            'PhysActivity': data.phys_activity,
            'GenHlth': 3, 
            'PhysHlth': 0,
            'DiffWalk': 0,
            'Sex': 1, 
            'Age': age_bucket
        }])
        
        shap_vals = SHAP_EXPLAINER.shap_values(input_vector)
        
        # Handle shape (Binary vs Multiclass)
        if isinstance(shap_vals, list):
            # Target "Diabetes" (Class 2 or Positive)
            # BRFSS: 0=No, 1=Pre, 2=Yes. If binary: 0=No, 1=Yes.
            # Assuming we want to explain RISK INCREASE (Positive Class)
            target_idx = -1 
            vals = shap_vals[target_idx][0]
            base_val = SHAP_EXPLAINER.expected_value[target_idx]
        else:
            vals = shap_vals[0]
            base_val = SHAP_EXPLAINER.expected_value

        feature_names = ['HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 
                         'PhysActivity', 'GenHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age']

        contributors = []
        for name, val in zip(feature_names, vals):
            contributors.append({"feature": name, "impact": float(val)})
            
        contributors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "base_value": float(base_val),
            "contributors": contributors[:5]
        }

    except Exception as e:
        print(f"XAI Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def home():
    return {"status": "Module 3 – Diabetic Risk Prediction Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)
