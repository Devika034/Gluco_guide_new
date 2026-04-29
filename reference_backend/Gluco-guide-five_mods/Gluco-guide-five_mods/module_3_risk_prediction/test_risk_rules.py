from risk_rules import evaluate_clinical_risk
import json

def run_test(name, data):
    print(f"--- Test Case: {name} ---")
    report = evaluate_clinical_risk(data)
    # Simplify output for readability
    summary = {
        "glycemic": report["assessments"]["glycemic"]["status"],
        "cv_risk": report["assessments"]["cardiovascular"]["risk_level"],
        "kidney": report["assessments"]["kidney"]["status"],
        "microvascular": report["risk_predictions"]
    }
    print(json.dumps(summary, indent=2))
    print(f"Explanation: {report['clinical_explanation']}\n")

# 1. Healthy
run_test("Healthy Person", {
    "hba1c": 5.0, "glucose": 90, "ldl": 80, "bp_systolic": 110, "bp_diastolic": 70,
    "creatinine": 0.8, "age": 30, "sex": 1, "uacr": 10
})

# 2. Diabetes
run_test("Diabetes High Risk", {
    "hba1c": 8.0, "glucose": 180, "ldl": 110, "bp_systolic": 140, "bp_diastolic": 90,
    "creatinine": 1.2, "age": 55, "sex": 0, "uacr": 300,
    "smoker": 1, "hypertension": 1
})

# 3. High CV Risk
run_test("High CV Risk (Non-Diabetic)", {
    "hba1c": 5.5, "glucose": 95, "ldl": 195, "bp_systolic": 135, "bp_diastolic": 85,
    "creatinine": 0.9, "age": 60, "sex": 1, "uacr": 15,
    "smoker": 1
})

# 4. Partial
run_test("Partial Data", {
    "glucose": 105
})
