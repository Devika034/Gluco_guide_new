import os
from groq import Groq

# The key user just provided
API_KEY = "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"

def test_groq():
    print(f"Testing Groq API with key: {API_KEY[:10]}...")
    
    try:
        client = Groq(api_key=API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "Hello, simply reply with 'OK'."}
            ],
            temperature=0
        )
        
        print("Success!")
        print("Response:", completion.choices[0].message.content)
        
    except Exception as e:
        print("FAILED.")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_groq()
