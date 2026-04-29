import pdfplumber
import os

pdf_path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\module3&4_knowledgebase\RNN1.pdf"

try:
    print(f"Analyzing: {pdf_path}")
    if not os.path.exists(pdf_path):
        print("Error: File not found.")
    else:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract first 2 pages
            for i, page in enumerate(pdf.pages[:2]):
                text = page.extract_text()
                if text:
                    print(f"\n--- Page {i+1} ---\n{text[:1000]}") # Print first 1000 chars

except Exception as e:
    print(f"Error: {e}")
