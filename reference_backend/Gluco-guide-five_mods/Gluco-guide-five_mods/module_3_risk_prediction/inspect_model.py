import joblib
import os
import pandas as pd

path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\risk_model.pkl"

try:
    print(f"Loading {path}...")
    model = joblib.load(path)
    print(f"Type: {type(model)}")
    
    if hasattr(model, "feature_names_in_"):
        print("Expected Features:")
        print(model.feature_names_in_)
    elif hasattr(model, "steps"): # Pipeline
        print("It is a Pipeline.")
        # Check the last step or 'clf'
        # Try to find the step that has feature_names_in_
        pass
        
    # Validating predict_proba
    print(f"Has predict_proba? {hasattr(model, 'predict_proba')}")

except Exception as e:
    print(f"Error: {e}")
