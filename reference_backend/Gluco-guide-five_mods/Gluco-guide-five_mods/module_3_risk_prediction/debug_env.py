import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

try:
    import pdfplumber
    print("pdfplumber: FOUND")
except ImportError as e:
    print(f"pdfplumber: NOT FOUND ({e})")

try:
    import pytesseract
    print("pytesseract: FOUND")
except ImportError as e:
    print(f"pytesseract: NOT FOUND ({e})")

try:
    import cv2
    print("cv2: FOUND")
except ImportError as e:
    print(f"cv2: NOT FOUND ({e})")

try:
    import pdf2image
    print("pdf2image: FOUND")
except ImportError as e:
    print(f"pdf2image: NOT FOUND ({e})")
