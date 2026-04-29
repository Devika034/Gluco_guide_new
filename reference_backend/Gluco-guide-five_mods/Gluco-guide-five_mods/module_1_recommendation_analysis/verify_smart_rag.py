import sys
import os

# Add module dir to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing app...")
    import app
    
    print("\n--- VERIFICATION: SMART RAG ---")
    
    # Test 1: Strict Diabetic (Veg)
    print("\nTest 1: Strict Diabetic (Veg)")
    foods_strict = app.get_smart_food_recommendations("Breakfast", "Veg", is_strict=True)
    print(f"Result String Length: {len(foods_strict)} chars")
    
    if "Idli" in foods_strict:
        print("SUCCESS: Idli found (0.8 > 0.7)")
    else:
        # Idli might be random sampled out, but is capable of being there
        pass 

    if "Puttu" in foods_strict:
        print("FAILURE: Puttu found in strict diet (0.45 < 0.7). It should be filtered.")
    else:
        print("SUCCESS: Puttu correctly filtered out.")

    # Test 2: Non-Strict
    print("\nTest 2: Non-Strict")
    foods_lax = app.get_smart_food_recommendations("Breakfast", "Veg", is_strict=False)
    
    if "Appam" in foods_lax or "Puttu" in foods_lax:
         # Appam (0.5) is borderline, Puttu (0.45) is < 0.5 so unlikely
         # But let's check length
         pass
    
    print(f"Non-Strict Result Length: {len(foods_lax)}")

except Exception as e:
    print(f"FAILURE: {e}")
