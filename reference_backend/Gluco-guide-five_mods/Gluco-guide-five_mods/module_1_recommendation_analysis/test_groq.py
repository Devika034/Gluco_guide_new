import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    return Groq(api_key=api_key)

def test_call():
    client = get_groq_client()
    prompt = "Test prompt"
    
    print("Attempting to call Groq API...")
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a dietitian assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            top_p=0.9,
            response_format={"type": "json_object"}
        )
        print("Success!")
        print(completion.choices[0].message.content)
    except Exception as e:
        print("\n\nERROR CAUGHT:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_call()
