import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import joblib
import os

# Set paths relative to this script so it works in any environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "diabetes_012_health_indicators_BRFSS2015.csv")

# The model should be saved in the global 'models' folder at the root of the project
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", ".."))
model_path = os.path.join(PROJECT_ROOT, "models", "risk_model.pkl")

def train():
    print("Loading Dataset...")
    if not os.path.exists(csv_path):
        print(f"Error: CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Data Loaded: {df.shape}")
    
    feature_cols = [
        'HighBP', 'HighChol', 'BMI', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 
        'PhysActivity', 'GenHlth', 'PhysHlth', 'DiffWalk', 'Sex', 'Age'
    ]
    
    X = df[feature_cols]
    y = df['Diabetes_012']
    
    print("Training Random Forest with optimized hyperparameters on full dataset...")
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(
            n_estimators=200, 
            max_depth=None, 
            min_samples_split=2,
            random_state=42, 
            n_jobs=-1
        ))
    ])
    
    pipeline.fit(X, y)
    print("Training Complete.")
    
    print("Evaluating on Full Training Set (as per original baseline)...")
    y_pred = pipeline.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"Full Dataset Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Ensure models directory exists
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")
    
    # Validation check
    print(f"Features expected: {feature_cols}")
    print(f"Has predict_proba? {hasattr(pipeline, 'predict_proba')}")

if __name__ == "__main__":
    train()
