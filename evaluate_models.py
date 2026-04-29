import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score, confusion_matrix
import joblib
import os

print("Evaluating Models and Generating Graphs...")

# Paths
BASE_DIR = r"c:\Users\niran\OneDrive\Desktop\Gluco-guide-devika - Copy (2)"
OUTPUT_DIR = os.path.join(BASE_DIR, "evaluation_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

module2_data_path = os.path.join(BASE_DIR, "synthetic_data.csv")
module3_data_path = os.path.join(BASE_DIR, "reference_backend", "Gluco-guide-five_mods", "Gluco-guide-five_mods", "module_3_risk_prediction", "diabetes_012_health_indicators_BRFSS2015.csv")

rf_classifier_path = os.path.join(BASE_DIR, "models", "rf_classifier.pkl")
rf_regressor_path = os.path.join(BASE_DIR, "models", "rf_regressor.pkl")
risk_model_path = os.path.join(BASE_DIR, "models", "risk_model.pkl")

# Evaluate Module 2 Classifier and Regressor
if os.path.exists(module2_data_path) and os.path.exists(rf_classifier_path) and os.path.exists(rf_regressor_path):
    print("\n--- Evaluating Module 2 Models (Spike Prediction) ---")
    df = pd.read_csv(module2_data_path)
    feature_cols = [
        "current_glucose", "avg_GI", "total_GL", "duration_years", "age", "bmi",
        "activity_level", "medication_dose", "hba1c", "bp_systolic", "bp_diastolic",
        "cholesterol", "fasting_glucose", "time_of_day", "family_history", "alcohol_smoking"
    ]
    target_cols = ["glucose_30min", "glucose_60min", "glucose_90min", "glucose_120min"]
    
    X = df[feature_cols]
    y_reg = df[target_cols]
    
    df['max_spike'] = df[target_cols].max(axis=1)
    def classify_risk(val):
        if val > 220: return "High"
        elif val > 180: return "Moderate"
        else: return "Low"
    y_class = df['max_spike'].apply(classify_risk)

    # 1. Classification Performance
    rf_classifier = joblib.load(rf_classifier_path)
    y_pred_class = rf_classifier.predict(X)
    acc = accuracy_score(y_class, y_pred_class)
    print(f"RF Classifier Accuracy: {acc:.4f}")
    
    # Confusion Matrix Plot
    plt.figure(figsize=(8,6))
    cm = confusion_matrix(y_class, y_pred_class, labels=["High", "Moderate", "Low"])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=["High", "Moderate", "Low"], yticklabels=["High", "Moderate", "Low"])
    plt.title("Module 2: Spike Risk Confusion Matrix")
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.savefig(os.path.join(OUTPUT_DIR, "m2_confusion_matrix.png"))
    plt.close()

    # 2. Regression Performance
    from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
    rf_regressor = joblib.load(rf_regressor_path)
    y_pred_reg = rf_regressor.predict(X)
    r2 = r2_score(y_reg, y_pred_reg)
    mape = mean_absolute_percentage_error(y_reg, y_pred_reg)
    print(f"RF Regressor R2 Score: {r2:.4f}")
    print(f"RF Regressor Estimated Accuracy (100 - MAPE): {(1-mape)*100:.2f}%")

    # Regression Plot (Actual vs Predicted)
    plt.figure(figsize=(10,6))
    plt.scatter(y_reg.values.flatten(), y_pred_reg.flatten(), alpha=0.3, color='teal')
    plt.plot([y_reg.min().min(), y_reg.max().max()], [y_reg.min().min(), y_reg.max().max()], 'r--')
    plt.title("Module 2: Predicted vs Actual Glucose Levels")
    plt.xlabel("Actual Glucose (mg/dL)")
    plt.ylabel("Predicted Glucose (mg/dL)")
    plt.savefig(os.path.join(OUTPUT_DIR, "m2_regression_accuracy.png"))
    plt.close()

# Evaluate Module 3 Risk Model
if os.path.exists(module3_data_path) and os.path.exists(risk_model_path):
    print("\n--- Evaluating Module 3 Risk Model ---")
    df3 = pd.read_csv(module3_data_path)
    feature_cols_3 = [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 
        'PhysActivity', 'GenHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age'
    ]
    X3 = df3[feature_cols_3]
    y3 = df3['Diabetes_012']

    risk_model = joblib.load(risk_model_path)
    y_pred_3 = risk_model.predict(X3)
    acc3 = accuracy_score(y3, y_pred_3)
    print(f"Risk Model Accuracy: {acc3:.4f}")

    # Plot Accuracy
    plt.figure(figsize=(6,4))
    plt.bar(["Risk Model"], [acc3], color='orange')
    plt.ylim(0, 1.0)
    plt.title("Module 3 Model Accuracy")
    plt.ylabel("Accuracy Score")
    for i, v in enumerate([acc3]):
        plt.text(i, v + 0.02, f"{v:.4f}", ha='center', fontweight='bold')
    plt.savefig(os.path.join(OUTPUT_DIR, "m3_accuracy.png"))
    plt.close()

print(f"\nAll graphs have been saved in: {OUTPUT_DIR}")
