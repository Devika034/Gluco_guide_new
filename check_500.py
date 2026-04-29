import urllib.request
import urllib.error

try:
    print("Sending GET request to local uvicorn server...")
    response = urllib.request.urlopen("http://127.0.0.1:9000/report/health-summary/34")
    print("Status Code:", response.getcode())
    print("Response Content:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError Status Code:", e.code)
    print("HTTPError Content:", e.read().decode())
except Exception as e:
    print("Failed to connect:", e)
