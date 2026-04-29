
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Add module path
sys.path.append(r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction")

from app import extract_text_from_image, preprocess_for_ocr

def create_test_image(text, filename="test_ocr.png", rotate_angle=0):
    # Create white image
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
        
    d.text((50, 50), "Medical Report", fill=(0,0,0), font=font)
    d.text((50, 100), text, fill=(0,0,0), font=font)
    
    # Rotate if needed
    if rotate_angle != 0:
        img = img.rotate(rotate_angle, expand=True, fillcolor='white')
        
    img.save(filename)
    return filename

def test_ocr():
    print("--- Starting OCR Verification ---")
    
    # 1. Test Clean Image
    print("\n[Test 1] Clean Image (HbA1c: 5.7)")
    img_path = create_test_image("HbA1c: 5.7\nFBG: 100", "test_clean.png")
    
    try:
        text = extract_text_from_image(file_path=img_path)
        print(f"Extracted Text:\n{text.strip()}")
        if "5.7" in text and "100" in text:
            print(">>> SUCCESS: Values detected.")
        else:
            print(">>> FAILURE: Values missing.")
    except Exception as e:
        print(f">>> ERROR: {e}")

    # 2. Test Skewed Image (Rotated 5 degrees)
    print("\n[Test 2] Skewed Image (5 deg)")
    img_path_skew = create_test_image("HbA1c: 6.2\nCholesterol: 180", "test_skew.png", rotate_angle=5)
    
    try:
        text = extract_text_from_image(file_path=img_path_skew)
        print(f"Extracted Text:\n{text.strip()}")
        if "6.2" in text:
             print(">>> SUCCESS: Values detected despite skew.")
        else:
             print(">>> FAILURE: Skew might have affected extraction.")
    except Exception as e:
        print(f">>> ERROR: {e}")

    # Cleanup
    # os.remove("test_clean.png")
    # os.remove("test_skew.png")

if __name__ == "__main__":
    test_ocr()
