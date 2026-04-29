import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import joblib
import shap
import os

def train_shap():
    print("--- [Module 2] Training SHAP Explainers ---")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "..", "synthetic_data.csv")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Dataset not found at {DATA_PATH}")
        return

    # Load Data (Same as app.py)
    df = pd.read_csv(DATA_PATH)
    
    feature_cols = [
        "current_glucose", "avg_GI", "total_GL", "duration_years", "age", "bmi",
        "activity_level", "medication_dose", "hba1c", "bp_systolic", "bp_diastolic",
        "cholesterol", "fasting_glucose", "time_of_day", "family_history", "alcohol_smoking"
    ]
    
    X = df[feature_cols]
    
    # Load Models
    try:
        if os.path.exists("rf_regressor.pkl") and os.path.exists("rf_classifier.pkl"):
            rf_regressor = joblib.load("rf_regressor.pkl")
            rf_classifier = joblib.load("rf_classifier.pkl")
            print("Models loaded.")
        else:
            print("Models not found. Please run app.py first to train models.")
            return
            
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # Train Explainers
    # We use a background sample (kmeans) to reduce size and speed up, 
    # but for TreeExplainer on Random Forest, we can pass the model directly.
    # However, passing X is safer for feature perturbation range.
    # Using a summary of X (kmeans) is best for KernelExplainer, but TreeExplainer is optimized.
    # TreeExplainer calculates SHAP values based on the tree structure.
    
    print("Creating Regressor Explainer...")
    # TreeExplainer is self-contained with the model usually, but providing data makes feature_perturbation="interventional" possible (safer).
    # However, "tree_path_dependent" (default) is faster and doesn't need background data at inference time usually, 
    # BUT generating the explainer object might need it.
    
    explainer_reg = shap.TreeExplainer(rf_regressor)
    
    print("Creating Classifier Explainer...")
    explainer_clf = shap.TreeExplainer(rf_classifier)
    
    # Save Explainers
    # Note: shap explainers can be pickled.
    print("Saving Explainers...")
    joblib.dump(explainer_reg, "shap_regressor.pkl")
    joblib.dump(explainer_clf, "shap_classifier.pkl")
    
    print("--- SHAP Explainers Saved ---")

if __name__ == "__main__":
    train_shap()
