import os
import google.generativeai as genai
import pandas as pd
import json
from typing import List, Optional

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        # Using the API key from previous successful activation
        self.api_key = api_key or "AIzaSyChS_bryHaNIUzR0FOmIMy98YOXw7Y53dY"
        
        if not self.api_key or "PASTE_YOUR_API_KEY_HERE" in self.api_key:
            print("WARNING: GEMINI_API_KEY not found or invalid. AI features will be disabled.")
            self.model = None
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("Gemini AI initialized successfully.")
        except Exception as e:
            print(f"FAILED to initialize Gemini: {e}")
            self.model = None

    def generate_adaptive_diet(self, user_profile: dict, foods_eaten: List[dict], food_dataset_path: str):
        if not self.model:
            return json.dumps({
                "analysis": "AI Coach is inactive. Please ensure your Gemini API Key is valid.",
                "recommendations": [],
                "nudge": "Set your API Key to get started!"
            })

        try:
            df = pd.read_csv(food_dataset_path)
            food_list = df[['food', 'GI', 'GL_per_serving', 'Veg/Non-veg']].to_csv(index=False)
        except Exception as e:
            food_list = "Dataset not available"

        prompt = f"""
        You are a clinical dietitian specialized in Kerala cuisine and Diabetic management.
        USER HEALTH DATA: {user_profile}
        MEALS EATEN TODAY: {foods_eaten}
        FOOD DATASET:
        {food_list}
        
        TASK:
        1. Analyze if GL limit was exceeded.
        2. Rearrange the NEXT meal to compensate.
        3. Provide 3 specific recommendations.
        4. Write a short, encouraging "AI Nudge" (max 30 words).
        
        FORMAT (Return ONLY clean JSON):
        {{
            "analysis": "...",
            "recommendations": [{{ "food": "...", "reason": "...", "portion": "..." }}],
            "nudge": "..."
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
            
            # Basic validation
            json.loads(text)
            return text
        except Exception as e:
            return json.dumps({
                "analysis": f"AI Coach is currently unavailable: {str(e)}",
                "recommendations": [],
                "nudge": "Stay healthy and keep tracking!"
            })

ai_assistant = GeminiService()
