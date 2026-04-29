@echo off
echo Starting all GlucoGuide Modules...

start "Module 1 - Recommendation" cmd /k "call venv\Scripts\activate && cd module_1_recommendation_analysis && python app.py"
start "Module 2 - Spike Prediction" cmd /k "call venv\Scripts\activate && cd module_2_spike_prediction && python app.py"
start "Module 3 - Risk Prediction" cmd /k "call venv\Scripts\activate && cd module_3_risk_prediction && python app.py"
start "Module 4 - Progress Tracker" cmd /k "call venv\Scripts\activate && cd module_4_tracker && python app.py"

echo All modules launched.
echo Module 1: http://127.0.0.1:8001
echo Module 2: http://127.0.0.1:8002
echo Module 3: http://127.0.0.1:8003
echo Module 4: http://127.0.0.1:8004
