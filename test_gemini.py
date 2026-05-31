import sys
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Copy schema definition from gemini_client.py for verification
class StarFramework(BaseModel):
    situation: str
    task: str
    action: str
    result: str

class InterviewAnalysis(BaseModel):
    question_thai: str
    category: str
    focus_areas: List[str]
    key_points: List[str]
    star_framework: Optional[StarFramework] = None
    answer_strategy: str
    example_outline: List[str]

def test_gemini():
    config_file = "config.json"
    if not os.path.exists(config_file):
        print("config.json not found. Run app.py or create config.json with your Gemini API key.")
        return
        
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    api_key = config.get("gemini_api_key", "")
    if not api_key:
        print("Gemini API Key is empty in config.json. Please add it first.")
        return
        
    model_name = config.get("gemini_model", "gemini-3.1-flash-lite")
    print(f"Initializing Gemini client with model '{model_name}'...")
    try:
        client = genai.Client(api_key=api_key)
        
        sample_question = "Explain OOP encapsulation and how you use it in your code."
        print(f"\nSending test question to Gemini using '{model_name}': '{sample_question}'")
        
        prompt = f"""
        Analyze this interview question: "{sample_question}"
        Provide structured response guidance.
        Do NOT write a complete script. Write in Thai.
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InterviewAnalysis,
                temperature=0.2,
            ),
        )
        
        # Verify JSON
        result = json.loads(response.text)
        print("\n--- GEMINI RESPONSE RECEIVED ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\nGemini integration test PASSED! Pydantic schema validation succeeded.")
        
    except Exception as e:
        print(f"\nGemini API Test FAILED: {e}")

if __name__ == "__main__":
    test_gemini()
