import sys
import os

# Add module dir to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing app...")
    import app
    
    print("\n--- VERIFICATION ---")
    print(f"ADA Context Loaded: {len(app.ADA_CONTEXT) > 0}")
    
    if len(app.ADA_CONTEXT) > 50:
        print("SUCCESS: ADA Context detected.")
    else:
        print("FAILURE: ADA Context too short or empty.")
        
except Exception as e:
    print(f"FAILURE: {e}")
