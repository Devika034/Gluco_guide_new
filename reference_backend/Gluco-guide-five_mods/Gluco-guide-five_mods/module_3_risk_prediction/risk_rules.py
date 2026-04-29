import math

def evaluate_clinical_risk(data):
    """
    Evaluates clinical risk based on the provided data dictionary.
    Returns a dictionary with comprehensive risk assessments.
    
    Expected keys in data:
    - hba1c, glucose, ldl, hdl, triglycerides, bp_systolic, bp_diastolic
    - creatinine, age, sex (0=Female, 1=Male or vice versa - need standard), uacr, alt, ast
    - smoker, hypertension, heart_disease
    """
    
    # helper to safely get float/int
    def get_val(key, default=None):
        val = data.get(key)
        if val is None: return default
        try: return float(val)
        except: return default

    # --- 1. Data Parsing & Validation ---
    age = get_val("age")
    sex = get_val("sex") # Assuming 0=Female, 1=Male for eGFR (Standardize in prompt)
    hba1c = get_val("hba1c")
    glucose = get_val("glucose")
    ldl = get_val("ldl")
    hdl = get_val("hdl")
    trigs = get_val("triglycerides")
    sys = get_val("bp_systolic")
    dia = get_val("bp_diastolic")
    creat = get_val("creatinine")
    uacr = get_val("uacr")
    alt = get_val("alt")
    ast = get_val("ast")
    
    smoker = get_val("smoker", 0)
    history_htn = get_val("hypertension", 0)
    history_cvd = get_val("heart_disease", 0)
    
    missing_fields = [k for k in ["hba1c", "glucose", "ldl", "bp_systolic"] if get_val(k) is None]

    report = {
        "status": "Complete" if not missing_fields else "Partial",
        "missing_fields": missing_fields,
        "assessments": {},
        "risk_predictions": {}
    }

    # --- 2. Glycemic Status ---
    glycemic_status = "Unknown"
    glycemic_explanation = "Insufficient data."
    
    # Logic: OR condition for Diabetes, AND for Prediabetes if both present
    is_diabetes_a1c = hba1c and hba1c >= 6.5
    is_diabetes_glu = glucose and glucose >= 126
    
    if is_diabetes_a1c or is_diabetes_glu:
        glycemic_status = "Diabetes"
        glycemic_explanation = f"HbA1c ({hba1c}%)" if is_diabetes_a1c else f"Fasting Glu ({glucose})"
        glycemic_explanation += " indicates Diabetes."
    elif (hba1c and 5.7 <= hba1c <= 6.4) or (glucose and 100 <= glucose <= 125):
        glycemic_status = "Prediabetes"
        glycemic_explanation = "Markers indicate Prediabetes (Impaired Glucose Regulation)."
    elif hba1c and hba1c < 5.7:
        glycemic_status = "Normal"
        glycemic_explanation = "Glycemic markers are within normal range."
        
    report["assessments"]["glycemic"] = {
        "status": glycemic_status,
        "detail": glycemic_explanation,
        "hba1c": hba1c,
        "glucose": glucose
    }
    
    # --- 3. Lipid & CV Risk ---
    cv_risk_level = "Unknown"
    cv_factors = []
    
    if ldl is not None:
        if ldl >= 190: 
            cv_risk_level = "Very High"
            cv_factors.append("LDL >= 190 (Severe Hypercholesterolemia)")
        elif ldl >= 160:
            cv_risk_level = "High"
        elif ldl >= 130:
            cv_risk_level = "Moderate"
        elif ldl >= 100:
            cv_risk_level = "Mild"
        else:
            cv_risk_level = "Low"
            
        # Modifiers
        if cv_risk_level not in ["Very High"]:
            risk_drivers = 0
            if smoker: risk_drivers += 1; cv_factors.append("Smoking")
            if glycemic_status in ["Diabetes", "Prediabetes"]: risk_drivers += 1; cv_factors.append(f"{glycemic_status}")
            if history_htn or (sys and sys >= 130): risk_drivers += 1; cv_factors.append("Hypertension")
            if trigs and trigs >= 150: risk_drivers += 1; cv_factors.append("High Triglycerides")
            
            # HDL Check (sex dependent if possible, else strict <40)
            hdl_thresh = 50 if sex == 0 else 40 
            if hdl and hdl < hdl_thresh: risk_drivers += 1; cv_factors.append("Low HDL")
            
            # Escalation
            if risk_drivers >= 2 and cv_risk_level == "Moderate": cv_risk_level = "High"
            if risk_drivers >= 1 and cv_risk_level == "Low": cv_risk_level = "Mild-Moderate"
            
    report["assessments"]["cardiovascular"] = {
        "risk_level": cv_risk_level,
        "ldl": ldl,
        "modifiers": cv_factors
    }
    
    # --- 4. Blood Pressure ---
    bp_status = "Unknown"
    if sys and dia:
        if sys >= 130 or dia >= 80:
            bp_status = "Hypertension (Stage 1 or higher)"
        else:
            bp_status = "Normal"
            
    report["assessments"]["blood_pressure"] = {
        "status": bp_status,
        "systolic": sys,
        "diastolic": dia
    }
    
    # --- 5. Kidney Risk (eGFR & UACR) ---
    egfr = None
    kidney_status = "Unknown"
    
    # CKD-EPI Formula (Simplified 2021 w/o Race)
    # GFR = 142 * min(Scr/kappa, 1)**alpha * max(Scr/kappa, 1)**-1.200 * 0.9938**Age * 1.012 [if Female]
    # kappa = 0.7 (F), 0.9 (M)
    # alpha = -0.329 (F), -0.411 (M)
    if creat and age and sex is not None:
        kappa = 0.7 if sex == 0 else 0.9
        alpha = -0.329 if sex == 0 else -0.411
        factor_sex = 1.012 if sex == 0 else 1.0
        
        scr_norm = creat / kappa
        egfr = 142 * (min(scr_norm, 1)**alpha) * (max(scr_norm, 1)**-1.200) * (0.9938**age) * factor_sex
        egfr = round(egfr, 1)

    kidney_risks = []
    if uacr and uacr > 30: kidney_risks.append(f"Elevated UACR ({uacr})")
    if egfr and egfr < 60: kidney_risks.append(f"Reduced eGFR ({egfr})")
    
    if kidney_risks:
        kidney_status = "Elevated Risk"
    elif egfr and uacr:
        kidney_status = "Low Risk"
    else:
        kidney_status = "Incomplete Data"

    report["assessments"]["kidney"] = {
        "status": kidney_status,
        "egfr": egfr,
        "uacr": uacr,
        "flags": kidney_risks
    }
    
    # --- 6. Liver (MASLD Screening) ---
    liver_status = "Normal / Unknown"
    if alt and ast:
        if alt > 40: # Generic upper limit
            if glycemic_status != "Normal" or cv_risk_level in ["High", "Very High"] or (data.get("bmi", 25) > 30):
                liver_status = "Possible Metabolic-Associated Fatty Liver Disease (MASLD)"
    
    report["assessments"]["liver"] = {
         "status": liver_status,
         "alt": alt
    }
    
    # --- 7. Microvascular Predictions (Output Generation) ---
    
    # Neuropathy
    neuro_risk_5y = 5 # Baseline
    if glycemic_status == "Diabetes": neuro_risk_5y += 20
    if glycemic_status == "Prediabetes": neuro_risk_5y += 5
    if hba1c and hba1c > 8: neuro_risk_5y += 15
    if age and age > 60: neuro_risk_5y += 10
    
    # Retinopathy (Strongly HbA1c dependent)
    retino_risk_5y = 5
    if hba1c:
        if hba1c > 6.5: retino_risk_5y = 15
        if hba1c > 7.5: retino_risk_5y = 25
        if hba1c > 9.0: retino_risk_5y = 40
        
    # Nephropathy (BP & UACR dependent)
    nephro_risk_5y = 5
    if bp_status.startswith("Hypertension"): nephro_risk_5y += 15
    if uacr and uacr > 30: nephro_risk_5y += 30
    if egfr and egfr < 60: nephro_risk_5y += 20
    
    # Qualitative Overrides for Low Risk
    if glycemic_status == "Normal" and bp_status == "Normal":
        report["risk_predictions"] = {
            "neuropathy": {"5_years": 1.0, "10_years": 1.0},
            "retinopathy": {"5_years": 1.0, "10_years": 1.0},
            "nephropathy": {"5_years": 1.0, "10_years": 1.0}
        }
    else:
        # Cap at 95%
        report["risk_predictions"] = {
            "neuropathy": {"5_years": min(neuro_risk_5y, 95), "10_years": min(neuro_risk_5y * 1.5, 95)},
            "retinopathy": {"5_years": min(retino_risk_5y, 95), "10_years": min(retino_risk_5y * 1.5, 95)},
            "nephropathy": {"5_years": min(nephro_risk_5y, 95), "10_years": min(nephro_risk_5y * 1.5, 95)}
        }

    # --- Explanation Generation ---
    summary = []
    summary.append(f"Glycemic Status: {glycemic_status}. {glycemic_explanation}")
    summary.append(f"Cardiovascular Risk: {cv_risk_level}. Factors: {', '.join(cv_factors) if cv_factors else 'None significant'}.")
    summary.append(f"Kidney Health: {kidney_status}. {', '.join(kidney_risks)}.")
    if liver_status.startswith("Possible"): summary.append(f"Liver: {liver_status}.")
    
    report["clinical_explanation"] = " ".join(summary)
    
    return report
