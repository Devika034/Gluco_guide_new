
import os
import json
import traceback
from groq import Groq

# Mocking the KB_CONTEXT for the prompt
KB_CONTEXT = "Mock KB Context"

def analyze_with_groq(text_content):
    """
    Uses Groq API (Llama 3.3) to analyze the medical text.
    Extracts structured data and provides a brief summary.
    """
    # Use Environment Variable or Hardcoded key as fallback
    api_key = os.environ.get("GROQ_API_KEY") or "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"
    
    print(f"DEBUG: Using API Key: '{api_key}'") # Added debug print to see the key

    if not api_key:
        print("WARNING: GROQ_API_KEY not found. Skipping LLM analysis.")
        return None
        
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are a Specialist Diabetologist assisting with a Hybrid AI Analysis.
    
    TASK 1: EXTRACT structured clinical data from the report below.
    Return a JSON with these keys (use null if not found):
    - hba1c (float, e.g. 7.2)
    - bmi (float)
    - age (int)
    - glucose (fasting, int)
    - bp_systolic (int)
    - bp_diastolic (int)
    - cholesterol (int)
    - uacr (float, Urine Albumin/Creatinine Ratio)
    - egfr (int, Estimated Glomerular Filtration Rate)
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
        
        # NOTE: Skipping the ML part for this isolation test as it depends on local pkl files
        return data
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Running reproduction of analyze_with_groq...")
    result = analyze_with_groq("Patient Name: John Doe\nHbA1c: 7.2%")
    if result:
        print("Success!")
    else:
        print("Failed.")
