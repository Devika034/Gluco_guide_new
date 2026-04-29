import pdfplumber
import pytesseract
import cv2
import numpy as np
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image

def extract_text_from_pdf(file_path):
    text_content = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content += text + "\n"
    except:
        pass

    # 🔥 Fallback to OCR if no text found
    if not text_content.strip():
        try:
            images = convert_from_path(file_path)
            for img in images:
                img = np.array(img)
                processed = preprocess_image(img)
                text_content += pytesseract.image_to_string(processed)
        except Exception as e:
            print("OCR fallback failed:", e)

    return text_content

def extract_values(text):

    def find(pattern, group=1):
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(group)) if match else None

    return {
    "hba1c": find(r"hba1c\s*[:\-]?\s*(\d+\.?\d*)"),
    "fasting_glucose": find(r"fasting.*?(\d+)", 1),
    "bp_systolic": find(r"(\d{2,3})\/(\d{2,3})", 1),
    "bp_diastolic": find(r"(\d{2,3})\/(\d{2,3})", 2),
    "cholesterol": find(r"cholesterol\s*[:\-]?\s*(\d+)")
    }