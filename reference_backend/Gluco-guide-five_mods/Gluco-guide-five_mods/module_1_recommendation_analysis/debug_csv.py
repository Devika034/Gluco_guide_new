import csv
import os

path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\knowledge_base\nutrition_tables\merged.csv"

try:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print(f"Headers found: {reader.fieldnames}")
        
        for i, row in enumerate(reader):
            if i > 5: break
            print(f"Row {i}: {row}")
            print(f"Suitability Raw: '{row.get('Diabetic Suitability')}'")
            
            # Explicit check for Puttu
            if "Puttu" in row.get("Food Name", ""):
                 print(f"FOUND PUTTU: {row}")

except Exception as e:
    print(e)
