import pdfplumber
import os

pdf_path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\Medical Lab Report.pdf"

try:
    print(f"Analyzing: {pdf_path}")
    if not os.path.exists(pdf_path):
        print("Error: File not found.")
    else:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {i+1} ---\n{text}"
            
            print("extracted_text_start (Writing to debug_pdf_text.txt)")
            with open(r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\debug_pdf_text.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
            print("Done.")

except Exception as e:
    print(f"Error: {e}")
