import sys
import os
import joblib

print("Current Directory:", os.getcwd())

try:
    from app import extract_medical_values, map_features, predict_diabetic_complications
except ImportError:
    sys.path.append(os.getcwd())
    from app import extract_medical_values, map_features, predict_diabetic_complications

# Simulate the text from the user's report
sample_text_from_user = """
HEMOGLOBIN; GLYCATED 5.96 %
Fasting Blood Sugar (FBS)
FBS 122.5 mg/dL
Cholesterol, Total 236.68 mg/dL
Sex / Age : Male / 37 Yrs.
"""

print("\n--- Testing Refined Extraction ---")
print("Input extraction text:", sample_text_from_user)

extracted = extract_medical_values(sample_text_from_user)
print("Extracted Values:", extracted)

# Verification Expectations
# HbA1c: 5.96
# FBS: 122.5
# Cholesterol: 236.68
# Age: 37
# Gender: Male

if extracted.get("hba1c") != 5.96: print("[FAIL] HbA1c mismatch")
if extracted.get("fasting_glucose") != 122.5: print("[FAIL] FBS mismatch")
if extracted.get("cholesterol") != 236.68: print("[FAIL] Cholesterol mismatch")
if extracted.get("age") != 37: print("[FAIL] Age mismatch")

print("\n--- Testing Prediction with Extracted Values ---")
pred = predict_diabetic_complications(extracted)
print(pred)

if "Error" in pred:
    print("[FAIL] Prediction Error")
else:
    print("[SUCCESS] Prediction generated")
