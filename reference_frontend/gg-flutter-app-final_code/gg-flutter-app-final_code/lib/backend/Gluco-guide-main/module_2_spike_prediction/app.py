from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
import torch
import torch.nn as nn
import numpy as np
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="GlucoGuide - Module 2",
    description="Post-meal Glucose Spike Prediction",
    version="1.0"
)

class LSTMModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(16, 64, batch_first=True)
        self.fc = nn.Linear(64, 4)

    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(h[-1])

model = LSTMModel()
model.load_state_dict(torch.load(os.path.join(BASE_DIR, "glucose_lstm.pth")))
model.eval()

with open(os.path.join(BASE_DIR, "scaler_X.pkl"), "rb") as f:
    scaler_X = pickle.load(f)

with open(os.path.join(BASE_DIR, "scaler_y.pkl"), "rb") as f:
    scaler_y = pickle.load(f)

class SpikeInput(BaseModel):
    current_glucose: float
    avg_GI: float
    total_GL: float
    duration_years: float
    age: int
    bmi: float
    activity_level: float
    medication_dose: float
    hba1c: float
    bp_systolic: float
    bp_diastolic: float
    cholesterol: float
    fasting_glucose: float
    time_of_day: int
    family_history: int
    alcohol_smoking: int

@app.get("/")
def home():
    return {"module": "Module 2 - Spike Prediction", "status": "Ready"}

@app.post("/predict-spike/")
def predict(data: SpikeInput):
    arr = np.array([[ 
        data.current_glucose, data.avg_GI, data.total_GL,
        data.duration_years, data.age, data.bmi,
        data.activity_level, data.medication_dose,
        data.hba1c, data.bp_systolic, data.bp_diastolic,
        data.cholesterol, data.fasting_glucose,
        data.time_of_day, data.family_history,
        data.alcohol_smoking
    ]])

    scaled = scaler_X.transform(arr).reshape(1, 1, 16)
    tensor = torch.tensor(scaled, dtype=torch.float32)

    with torch.no_grad():
        pred_scaled = model(tensor).numpy()
        pred = scaler_y.inverse_transform(pred_scaled)[0]

    predictions = {
        "30min": float(round(float(pred[0]), 1)),
        "60min": float(round(float(pred[1]), 1)),
        "90min": float(round(float(pred[2]), 1)),
        "120min": float(round(float(pred[3]), 1))
    }

    spike = any(float(v) > 180 for v in predictions.values())

    return {
        "predictions": predictions,
        "spike_risk": "High" if spike else "Low",
        "advice": "Avoid high GL foods" if spike else "Good control expected"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
