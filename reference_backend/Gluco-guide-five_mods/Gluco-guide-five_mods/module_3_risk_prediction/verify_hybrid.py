import sys
import os
import asyncio

# Add module dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env from module dir
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

if not os.environ.get("GROQ_API_KEY"):
    # Fallback to hardcoded if needed for immediate testing, 
    # but preferably rely on the user having set it in .env
    pass

try:
    print("Importing app...")
    import app
    
    # Mock Text matching the one usually found in reports
    mock_text = """
    Patient: Test User
    HbA1c: 8.2%
    Fasting Glucose: 160 mg/dL
    BP: 145/90 mmHg
    BMI: 31.5
    Age: 55
    Smoker: No
    """
    
    print("\n--- TEST: Checking ML Model Load ---")
    if app.ML_MODEL:
        print("SUCCESS: ML Model Loaded.")
    else:
        print("WARNING: ML Model NOT loaded (using fallback).")

    print("\n--- TEST: Hybrid Analysis (LLM + ML) ---")
    print("Sending mock report to analyze_with_groq...")
    
    result = app.analyze_with_groq(mock_text)
    
    if result:
        print("\n[RESULT SUCCESS]")
        print("1. Extracted Features:", result.get("parsed_values"))
        
        risks = result.get("risk_predictions", {})
        print("2. Risks Calculated:")
        print(f"   - Neuropathy (5y): {risks.get('neuropathy', {}).get('5_years')}%")
        print(f"   - Retinopathy (5y): {risks.get('retinopathy', {}).get('5_years')}%")
        print(f"   - Nephropathy (5y): {risks.get('nephropathy', {}).get('5_years')}%")
        
        print("\n3. Explanation:")
        print(result.get("explanation")[:200] + "...")
        
        # Validation Logic
        feats = result.get("parsed_values", {})
        if feats.get("hba1c") == 8.2:
            print("\nVALIDATION: Extraction Accurate.")
        else:
            print(f"\nVALIDATION: Extraction Failed. Got {feats.get('hba1c')}")
            
    else:
        print("FAILURE: No result returned (Check API Key).")

except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
