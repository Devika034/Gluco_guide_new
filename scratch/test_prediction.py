import sys
import os
from datetime import datetime, timedelta

# Mock dependencies
sys.path.append(os.getcwd())
os.environ["GROQ_API_KEY"] = "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"

from routers.module4_tracking import predict_progression

# Test Case 1: Sparse Data (Baseline)
history_1 = [(datetime.now(), 0.75)]
clinical_1 = {"hba1c": 9.0}
res_1 = predict_progression(history_1, clinical_1)
print("\nTest Case 1 (Sparse Data):")
print(res_1)

# Test Case 2: Multi-point Data
history_2 = [
    (datetime.now() - timedelta(days=60), 0.5),
    (datetime.now() - timedelta(days=30), 0.6),
    (datetime.now(), 0.75)
]
clinical_2 = {"hba1c": 8.5}
res_2 = predict_progression(history_2, clinical_2)
print("\nTest Case 2 (Multi-point):")
print(res_2)
