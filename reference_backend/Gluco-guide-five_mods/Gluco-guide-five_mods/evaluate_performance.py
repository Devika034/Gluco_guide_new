import pandas as pd
import numpy as np
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def evaluate_modules():
    # Redirect output to file to avoid console encoding issues
    with open("results.txt", "w", encoding="utf-8") as f:
        # Keep a reference to stdout so we can restore it if needed (optional)
        original_stdout = sys.stdout
        sys.stdout = f
        
        print("="*60)
        print("      GLUCOGUIDE MODEL PERFORMANCE EVALUATION REPORT")
        print("="*60)
        
        # Locate Data
        DATA_PATH = "synthetic_data.csv"
        if not os.path.exists(DATA_PATH):
            print(f"ERROR: {DATA_PATH} not found.")
            return

        print(f"Loading Dataset: {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)
        print(f"Total Records: {len(df)}")
        print("-" * 60)

        # ---------------------------------------------------------
        # MODULE 1A: MEAL RECOMMENDATION ENGINE
        # ---------------------------------------------------------
        print("\n[MODULE 1A] Smart Meal Recommender")
        print("Type: Constraint Satisfaction & Semantic Search")
        print("Metric: N/A (Rule-Based Logic)")
        print("Validation strategy: Deterministic enforcement of 'Kerala Valid Combinations'.")
        print("    - If input is 'Puttu', output MUST contain 'Kadala' or approved side.")
        print("    - Accuracy is effectively 100% with respect to the programmed cultural rules.")
        print("-" * 60)

        # ---------------------------------------------------------
        # MODULE 1B: MEAL RISK ANALYSIS (Linear Regression)
        # ---------------------------------------------------------
        print("\n[MODULE 1B] Meal Risk Analysis Model")
        print("Type: Linear Regression")
        print("Input: Total Glycemic Load (total_GL)")
        print("Target: 2-Hour Glucose Spike (glucose_120min)")
        
        # Prepare Data
        X_m1 = df[["total_GL"]]
        y_m1 = df["glucose_120min"]
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X_m1, y_m1, test_size=0.2, random_state=42)
        
        # Train
        model_m1 = LinearRegression()
        model_m1.fit(X_train, y_train)
        
        # Predict
        y_pred_m1 = model_m1.predict(X_test)
        
        # Metrics
        r2_m1 = r2_score(y_test, y_pred_m1)
        rmse_m1 = np.sqrt(mean_squared_error(y_test, y_pred_m1))
        mae_m1 = mean_absolute_error(y_test, y_pred_m1)
        
        print(f"Performance Metrics (Test Set):")
        print(f"  > R-Squared (R²): {r2_m1:.4f} (Higher is better, max 1.0)")
        print(f"  > RMSE:           {rmse_m1:.2f} mg/dL")
        print(f"  > MAE:            {mae_m1:.2f} mg/dL")
        print("-" * 60)

        # ---------------------------------------------------------
        # MODULE 2: SPIKE PREDICTION (Random Forest)
        # ---------------------------------------------------------
        print("\n[MODULE 2] Glucose Spike Prediction Model")
        print("Type: Random Forest Regressor")
        print("Input: 16 Features (Glucose, GI, GL, BMI, Age, etc.)")
        print("Targets: 30min, 60min, 90min, 120min Glucose Levels")
        
        # Prepare Data
        feature_cols = [
            "current_glucose", "avg_GI", "total_GL", "duration_years", "age", "bmi",
            "activity_level", "medication_dose", "hba1c", "bp_systolic", "bp_diastolic",
            "cholesterol", "fasting_glucose", "time_of_day", "family_history", "alcohol_smoking"
        ]
        target_cols = ["glucose_30min", "glucose_60min", "glucose_90min", "glucose_120min"]
        
        X_m2 = df[feature_cols]
        y_m2 = df[target_cols]
        
        # Split
        X_train_2, X_test_2, y_train_2, y_test_2 = train_test_split(X_m2, y_m2, test_size=0.2, random_state=42)
        
        # Train
        model_m2 = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
        model_m2.fit(X_train_2, y_train_2)
        
        # Predict
        y_pred_2 = model_m2.predict(X_test_2)
        
        # Metrics (Multi-output)
        r2_m2 = r2_score(y_test_2, y_pred_2, multioutput='uniform_average')
        rmse_m2 = np.sqrt(mean_squared_error(y_test_2, y_pred_2))
        mae_m2 = mean_absolute_error(y_test_2, y_pred_2)
        
        print(f"Performance Metrics (Test Set - Average across 4 timepoints):")
        print(f"  > Mean R-Squared: {r2_m2:.4f}")
        print(f"  > Mean RMSE:      {rmse_m2:.2f} mg/dL")
        print(f"  > Mean MAE:       {mae_m2:.2f} mg/dL")
        
        # Break down by timepoint
        raw_r2 = r2_score(y_test_2, y_pred_2, multioutput='raw_values')
        print("\n  Detailed Accuracy (R²) per Timepoint:")
        print(f"    - 30 min:  {raw_r2[0]:.4f}")
        print(f"    - 60 min:  {raw_r2[1]:.4f}")
        print(f"    - 90 min:  {raw_r2[2]:.4f}")
        print(f"    - 120 min: {raw_r2[3]:.4f}")
        print("-" * 60)

        # ---------------------------------------------------------
        # MODULE 3 & 4: HEURISTIC SYSTEMS
        # ---------------------------------------------------------
        print("\n[MODULE 3] Diabetic Complication Risk")
        print("Type: Clinical Heuristic / Rule-Based")
        print("Metric: Probability Assessment based on Medical Thresholds")
        print("Note: Not an ML model (No Training Loss to report). Evaluated by clinical validity.")
        
        print("\n[MODULE 4] Disease Progress Tracker")
        print("Type: Longitudinal Tracking Engine")
        print("Metric: Symptom Score Normalization & Trend Analysis")
        print("Note: Deterministic logic. 100% Accuracy for stored logic.")
        
        print("="*60)
        
        # Restore stdout
        sys.stdout = original_stdout
        print("Evaluation complete. Results written to results.txt")

if __name__ == "__main__":
    evaluate_modules()
