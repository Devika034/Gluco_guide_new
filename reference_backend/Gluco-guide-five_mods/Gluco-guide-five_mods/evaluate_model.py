import torch
import numpy as np
import pickle
from module2_spike_prediction.app import LSTMModel

model = LSTMModel()
model.load_state_dict(torch.load("module2_spike_prediction/glucose_lstm.pth"))
model.eval()

X_test = np.load("X_test.npy")
y_test = np.load("y_test.npy")

with open("module2_spike_prediction/scaler_X.pkl", "rb") as f:
    scaler_X = pickle.load(f)
with open("module2_spike_prediction/scaler_y.pkl", "rb") as f:
    scaler_y = pickle.load(f)

X_scaled = scaler_X.transform(X_test)
X_tensor = torch.tensor(X_scaled.reshape(-1, 1, 16), dtype=torch.float32)

with torch.no_grad():
    preds_scaled = model(X_tensor).numpy()

preds = scaler_y.inverse_transform(preds_scaled)
actual = scaler_y.inverse_transform(y_test)

mae = np.mean(np.abs(preds - actual))
rmse = np.sqrt(np.mean((preds - actual) ** 2))
spike_acc = np.mean(
    np.any(preds > 180, axis=1) == np.any(actual > 180, axis=1)
)

print(f"MAE: {mae:.2f} mg/dL")
print(f"RMSE: {rmse:.2f} mg/dL")
print(f"Spike Detection Accuracy: {spike_acc * 100:.1f}%")
