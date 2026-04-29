import requests
import os
import json

# Set URL
url = "http://127.0.0.1:8004/analyze-diabetic-risk/"

# Ensure API Key is set for the test (Optional if set in system env)
# os.environ["GROQ_API_KEY"] = "YOUR_API_KEY" 

# Create a dummy image or PDF
with open("test_report.txt", "w") as f:
    f.write("Patient: John Doe\nHbA1c: 5.7%\nFasting Glucose: 110 mg/dL\nBP: 130/85 mmHg\nTotal Cholesterol: 210 mg/dL\nAge: 45\nSex: Male")

# Convert to image or just send as text file? 
# The app expects image/pdf. Let's create a dummy image using PIL
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (800, 600), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "Patient Name: John Doe", fill=(0,0,0))
d.text((10,30), "HbA1c: 7.2%", fill=(0,0,0))
d.text((10,50), "Fasting Blood Sugar: 140 mg/dL", fill=(0,0,0))
d.text((10,70), "Blood Pressure: 135/85", fill=(0,0,0))
d.text((10,90), "Total Cholesterol: 220 mg/dL", fill=(0,0,0))
d.text((10,110), "Age: 55", fill=(0,0,0))
d.text((10,130), "Sex: Male", fill=(0,0,0))

img.save("test_ocr_llm.png")

# Send Request
files = {'reports': ('test_ocr_llm.png', open('test_ocr_llm.png', 'rb'), 'image/png')}

try:
    print("Sending request to Module 3... (Ensure app is running)")
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        data = response.json()
        print("\n--- Response ---")
        print(json.dumps(data, indent=2))
        
        # Check for JSON file creation
        extracted_dir = "extracted_data"
        if os.path.exists(extracted_dir):
            files = os.listdir(extracted_dir)
            if files:
                print(f"\n[SUCCESS] Extracted data JSON found: {files[-1]}")
            else:
                print("\n[WARNING] extracted_data directory empty.")
        else:
            print("\n[WARNING] extracted_data directory not found.")
            
        # Check LLM specifics
        if "llm_analysis" in data and data["llm_analysis"] != "LLM Analysis failed or skipped.":
             print("\n[SUCCESS] LLM Analysis received.")
        else:
             print("\n[INFO] LLM Analysis skipped (Likely due to missing API Key).")

    else:
        print(f"Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"Test Failed: {e}")
