from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import datetime

def compute_score(answers: dict) -> float:
    """
    Normalized risk score between 0 and 1
    """
    total = sum(answers.values())
    max_score = len(answers) * 2
    if max_score == 0: return 0.0
    return round(total / max_score, 2)

def interpret_score(current: float, previous: float | None):
    if previous is None:
        trend = "Baseline"
    elif current > previous + 0.05: # Sensitivity
        trend = "Worsening"
    elif current < previous - 0.05:
        trend = "Improving"
    else:
        trend = "Stable"

    interpretation = []
    if current < 0.3:
        status = "Stable"
        interpretation = [
            "Symptoms are minimal or absent",
            "Condition appears stable",
            "Continue routine monitoring"
        ]
    elif current < 0.6:
        status = "Watchful"
        interpretation = [
            "Some symptoms have increased",
            "May indicate rising stress on the system",
            "No emergency signs detected"
        ]
    else:
        status = "High Risk"
        interpretation = [
            "Significant symptoms detected",
            "High likelihood of complications",
            "Immediate medical attention recommended"
        ]

    return status, trend, interpretation

def recommendations_for(disease: str, score: float):
    base = {
        "retinopathy": [
            "Maintain stable blood glucose",
            "Limit screen strain",
            "Schedule regular eye exams"
        ],
        "nephropathy": [
            "Monitor blood pressure",
            "Reduce salt intake",
            "Stay hydrated"
        ],
        "neuropathy": [
            "Inspect feet daily",
            "Avoid walking barefoot",
            "Maintain glucose control"
        ]
    }

    if score > 0.6:
        base[disease].append("Consult specialist urgently")
        if disease == "retinopathy":
             base[disease].append("Schedule eye exam within 3 months")

    return base[disease]

def predict_progression(history_data):
    """
    Uses Linear Regression to forecast future risk.
    history_data: List of (datetime, score) tuples.
    """
    if len(history_data) < 3:
        return {
            "prediction": "Insufficient Data (Need > 2 logs)",
            "slope": 0.0,
            "days_to_high_risk": None
        }

    # Prepare X (Days since start) and y (Scores)
    start_date = history_data[0][0]
    dates = [x[0] for x in history_data]
    scores = [x[1] for x in history_data]
    
    # Convert dates to days (integers)
    X = np.array([(d - start_date).days for d in dates]).reshape(-1, 1)
    y = np.array(scores)
    
    # Train Model
    model = LinearRegression()
    model.fit(X, y)
    
    # Forecast 30 days ahead
    last_day = X[-1][0]
    future_day = last_day + 30
    pred_future = model.predict([[future_day]])[0]
    
    slope = model.coef_[0]
    
    # Interpretation
    if slope > 0.005:
        trend_text = "Rapid Deterioration Detected"
    elif slope > 0:
        trend_text = "Slow Worsening"
    elif slope < -0.005:
        trend_text = "Significant Improvement"
    else:
        trend_text = "Stable Trend"

    # Days to High Risk (Score 0.8) logic
    days_to_risk = "N/A"
    current_score = scores[-1]
    
    if slope > 0 and current_score < 0.8:
        # 0.8 = slope * days + intercept
        # days = (0.8 - intercept) / slope
        # Easier: days_needed = (0.8 - current_score) / slope
        days_needed = (0.8 - current_score) / slope
        if days_needed < 365:
            days_to_risk = int(days_needed)
            
    # SHAP Explanation for Forecast
    # Explaining the prediction for 'future_day'
    import shap
    try:
        # LinearExplainer for the single-feature model
        explainer = shap.LinearExplainer(model, X)
        
        # Explain the future point
        # shap_values expects array of features
        future_X = np.array([[future_day]])
        shap_values = explainer.shap_values(future_X)
        
        # For single output, shap_values is an array
        # For simple linear regression y = mx + c, SHAP for x is m*(x - E[x])
        # It explains how the deviation from mean time affects the score deviation
        
        shap_val = shap_values[0] # Single feature
        
        if isinstance(shap_val, np.ndarray):
             shap_val = shap_val[0]
             
        explanation = f"Time Factor Contribution: {shap_val:.3f} (Base: {explainer.expected_value:.3f})"
    except Exception as e:
        explanation = f"Explanation Error: {e}"
        print(f"SHAP Error Mod4: {e}")
    
    return {
        "prediction": f"{trend_text} (Score {pred_future:.2f} in 30 days)",
        "slope": float(slope),
        "days_to_critical_risk": days_to_risk,
        "explanation": explanation
    }

