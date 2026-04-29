import sys
import os
import joblib

print("Current Directory:", os.getcwd())

try:
    from app import predict_diabetic_complications
except ImportError:
    sys.path.append(os.getcwd())
    from app import predict_diabetic_complications

# Sample 1: Healthy Profile
# BP < 130, Chol < 200, Hba1c < 6.5 (GenHlth=2)
healthy_values = {
    "hba1c": 5.5,
    "bp_systolic": 115,
    "cholesterol": 180,
    "bmi": 22.0
}

# Sample 2: High Risk Profile
# BP > 130 (High), Chol > 200 (High), Hba1c > 8.0 (GenHlth=4)
high_risk_values = {
    "hba1c": 9.5,
    "bp_systolic": 145,
    "cholesterol": 240,
    "bmi": 32.0
}

print("\n--- Testing Module 3 (Real Clinical Models) ---")

print("\n[TEST 1] Healthy Profile:")
print(healthy_values)
res_healthy = predict_diabetic_complications(healthy_values)
print("Result:", res_healthy)

print("\n[TEST 2] High Risk Profile:")
print(high_risk_values)
res_high = predict_diabetic_complications(high_risk_values)
print("Result:", res_high)

# Verification Logic
if "Error" in res_healthy or "Error" in res_high:
    print("\n[FAILED] Prediction returned error.")
    sys.exit(1)

# Logic check: High risk should have higher probability than Healthy
risk_healthy = res_healthy["Nephropathy (5 years)"]
risk_high = res_high["Nephropathy (5 years)"]

if risk_high > risk_healthy:
    print(f"\n[SUCCESS] Logic Validated: High Risk ({risk_high}) > Healthy ({risk_healthy})")
else:
    print(f"\n[WARNING] Logic Check Failed: High Risk ({risk_high}) <= Healthy ({risk_healthy})")

print("\nDone.")
