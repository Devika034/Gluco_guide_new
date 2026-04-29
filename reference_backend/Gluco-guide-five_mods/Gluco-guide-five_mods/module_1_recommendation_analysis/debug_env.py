import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Version: {sys.version}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

print("\nAttempting to import dotenv...")
try:
    import dotenv
    print(f"SUCCESS: dotenv imported from {dotenv.__file__}")
except ImportError as e:
    print(f"FAILURE: {e}")
except Exception as e:
    print(f"ERROR: {e}")

print("\nCheck pip availability:")
try:
    import pip
    print(f"pip is available at {pip.__file__}")
except ImportError:
    print("pip is NOT available")
