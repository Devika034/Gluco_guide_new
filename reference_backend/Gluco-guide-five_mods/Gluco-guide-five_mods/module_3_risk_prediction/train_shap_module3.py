import pandas as pd
import shap
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

# Path to the BRFSS dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "diabetes_012_health_indicators_BRFSS2015.csv")
MODEL_PATH = os.path.join(BASE_DIR, "risk_model.pkl")
SHAP_PATH = os.path.join(BASE_DIR, "shap_risk_explainer.pkl")

def train_shap_module3():
    print("--- [Module 3] Training SHAP Explainer ---")
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV not found at {CSV_PATH}")
        return

    # 1. Load Data
    # Use only a subset to speed up background data creation if needed
    df = pd.read_csv(CSV_PATH) #, nrows=10000) 
    print(f"Data Loaded: {df.shape}")
    
    feature_cols = [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 
        'PhysActivity', 'GenHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age'
    ]
    
    X = df[feature_cols]
    
    # 2. Load Pipeline
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}. Run train_proper_model.py first.")
        return
        
    pipeline = joblib.load(MODEL_PATH)
    print("Pipeline loaded.")
    
    # Extract Model and Scaler from Pipeline
    # Pipeline steps: [('scaler', StandardScaler()), ('clf', RandomForestClassifier())]
    try:
        scaler = pipeline.named_steps['scaler']
        model = pipeline.named_steps['clf']
        print("Extracted Classifier from Pipeline.")
    except Exception as e:
        print(f"Error parsing pipeline: {e}")
        return

    # 3. Create Explainer
    # For TreeExplainer with Random Forest, passing the *model* is usually enough.
    # However, since we have a SCALER in the pipeline, the Input info passed to SHAP 
    # must match what the model expects (Scaled Data).
    # BUT, we want to explain in terms of ORIGINAL features if possible.
    # SHAP TreeExplainer explains the model's raw inputs.
    # So we will interpret the scaled features, OR we create a wrapper.
    # Simpler approach: Explain the SCALED features, but map feature names back. 
    # The impact direction is preserved (Scaling is linear).
    
    print("Creating TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # 4. Save
    joblib.dump(explainer, SHAP_PATH)
    print(f"SHAP Explainer saved to {SHAP_PATH}")

if __name__ == "__main__":
    train_shap_module3()
