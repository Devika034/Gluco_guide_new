import sys
import os

# Add module dir to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing app...")
    import app
    
    print("\n--- VERIFICATION ---")
    print(f"ICMR Guidelines Loaded: {len(app.ICMR_GUIDELINES) > 0}")
    print(f"Food DB Context Loaded: {len(app.FOOD_DB_CONTEXT) > 0}")
    
    if len(app.ICMR_GUIDELINES) > 100:
        print("SUCCESS: ICMR Guidelines detected.")
    else:
        print("FAILURE: ICMR Guidelines too short or empty.")
        
except Exception as e:
    print(f"FAILURE: {e}")
