import os
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return None

def main():
    root_dir = r"c:\Users\SAMSUNG\Desktop\glucoguide_final"
    exclude_dirs = {'.git', 'venv_final', '__pycache__', '.dart_tool', 'build', '.idea', '.vscode'}
    
    hashes = defaultdict(list)
    
    print("--- Potentially Unnecessary Log/Temp Files ---")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # modify dirnames in-place to exclude certain directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir)
            
            # Check for possible unnecessary files
            lower_name = filename.lower()
            if lower_name.startswith('error') and lower_name.endswith('.txt'):
                print(f"Log/error file: {rel_path}")
            elif lower_name in ['trace.txt', 'uvicorn_logs.txt', 'check_500.py', 'test_report_crash.py', 'test_extract.py', 'test_imdecode.py', 'test_upload.py', 'test_report_gen.py']:
                print(f"Temp/Log/Test file: {rel_path}")
            elif lower_name.endswith('.pyc') or lower_name.endswith('.pyo') or lower_name.endswith('~'):
                print(f"Python byte code / backup: {rel_path}")
            elif lower_name in ['dummy.jpg', 'test.pdf', 'test_report.jpg']:
                print(f"Temp asset file: {rel_path}")
            elif 'synthetic_data.csv' == lower_name:
                 print(f"Large data file (check if needed): {rel_path} ({os.path.getsize(filepath)/1024/1024:.2f} MB)")
                
            file_hash = get_file_hash(filepath)
            if file_hash:
                # ignore synthetic data for duplicates as it's huge, but it's fine for md5
                hashes[file_hash].append(rel_path)
                
    print("\n--- Duplicate Files (Same exact content) ---")
    found_duplicates = False
    for h, paths in hashes.items():
        if len(paths) > 1:
            print(f"Duplicate content found in:")
            for p in paths:
                print(f"  - {p}")
            found_duplicates = True
            
    if not found_duplicates:
        print("No duplicates found.")

if __name__ == '__main__':
    main()
