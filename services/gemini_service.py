import os
import json
from groq import Groq
from typing import List, Dict

class GeminiService:
    """
    Renamed implementation that uses Groq internally to bypass Gemini quota issues.
    We keep the class name 'GeminiService' to avoid breaking imports elsewhere.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "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")
        
        try:
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile" # High quality model
            print(f"Groq AI initialized successfully for explanations using {self.model}")
        except Exception as e:
            print(f"FAILED to initialize Groq: {e}")
            self.client = None

    def explain_progression(self, disease: str, current_score: float, trend: str, forecast: str, clinical_data: Dict) -> str:
        if not self.client:
            return "AI Analysis unavailable."

        prompt = f"""
        You are a Specialist Endocrinologist. Analyze this diabetic patient's symptom progression.
        
        Disease: {disease.upper()}
        Current Symptom Impact: {current_score:.2f} (0=None, 1=Severe)
        Observed Trend: {trend}
        ML Forecast: {forecast}
        
        Patient Clinical Profile:
        {json.dumps(clinical_data, indent=2)}
        
        TASK:
        Provide a concise, professional medical explanation (max 3 sentences) for the "AI Context / SHAP Reasoning" section.
        - Explain how their clinical markers (like HbA1c, BP) relate to their symptom trend.
        - Be direct and medically sound.
        - Avoid generic advice; focus on explaining the "Why" behind the forecast.
        
        Return ONLY the explanation text.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API Error in explain_progression: {e}")
            return f"The progression trend is currently {trend.lower()} based on reported symptoms and clinical risk markers."

    def generate_insight_suggestions(self, context_type: str, analysis_data: List[Dict]) -> List[str]:
        if not self.client:
            return []

        # Convert the analysis data into a readable string for the prompt
        factors_str = ""
        for item in analysis_data:
            impact_direction = "increases" if item['impact'] > 0 else "decreases"
            val = item.get('value', 'N/A')
            factors_str += f"- {item['feature']} (Current Value: {val}): {impact_direction} the prediction (Impact value: {item['impact']:.2f})\n"

        prompt = f"""
        You are an expert clinical dietitian and diabetes coach providing personalized feedback.
        Context: The user just ran a {context_type} analysis on their health data.
        
        Here are the most significant factors driving the AI's prediction:
        {factors_str}
        
        TASK:
        Write exactly 3 distinct, highly personalized, and actionable suggestions based on these factors.
        - Reference the specific numbers (Current Value) AND the predicted rise (Forecast) in your advice.
        - If the forecast shows a peak at a specific time (e.g. 60m or 90m), give timing-specific advice.
        - Use the Recent Meal names (if provided in the Context) to make the advice feel unique to what they just ate.
        - Avoid generic advice; if a factor is driving the spike, explain how to counteract it specifically.
        - Return ONLY a strict JSON array of 3 strings.
        
        Example Output:
        ["suggestion 1", "suggestion 2", "suggestion 3"]
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            content = chat_completion.choices[0].message.content
            data = json.loads(content)
            
            # The JSON might be {"suggestions": [...]} or just [...]
            if isinstance(data, list):
                return data[:3]
            elif isinstance(data, dict):
                for key in ["suggestions", "recommendations", "items"]:
                    if key in data and isinstance(data[key], list):
                        return data[key][:3]
                # Fallback: find any list in the dict
                for v in data.values():
                    if isinstance(v, list):
                        return v[:3]
            
            return []
        except Exception as e:
            print(f"Groq API Error: {e}")
            return []

_ai_assistant_instance = None

def get_ai_assistant():
    global _ai_assistant_instance
    if _ai_assistant_instance is None:
        _ai_assistant_instance = GeminiService()
    return _ai_assistant_instance
