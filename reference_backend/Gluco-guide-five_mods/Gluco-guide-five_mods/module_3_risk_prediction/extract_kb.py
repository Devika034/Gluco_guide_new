import pdfplumber
import os

pdf_path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\module3&4_knowledgebase\RNN1.pdf"
output_path = r"c:\Users\SAMSUNG\Desktop\glucoguide\Gluco-guide\module_3_risk_prediction\kb_context.txt"

try:
    print(f"Extracting from: {pdf_path}")
    if os.path.exists(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "CLINICAL GUIDELINES FOR DIABETIC COMPLICATIONS (RETINOPATHY, NEPHROPATHY, NEUROPATHY)\n\n"
            # Extract first 5 pages which usually contain the key protocols
            for i, page in enumerate(pdf.pages[:5]):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {i+1} ---\n{text}\n"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Success: Saved to {output_path}")
    else:
        print("Error: PDF not found.")

except Exception as e:
    print(f"Error: {e}")
