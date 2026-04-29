try:
    with open('app_verify.log', 'r', encoding='utf-16') as f:
        content = f.read()
    with open('debug_trace.txt', 'w', encoding='utf-8') as f:
        f.write(content)
except Exception as e:
    print(f"Error: {e}")
