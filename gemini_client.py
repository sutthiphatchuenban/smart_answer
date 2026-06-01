import threading
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional

# Define the Pydantic schema for structured output
class StarFramework(BaseModel):
    situation: Optional[str] = Field(default=None, description="สิ่งที่ควรสมมติหรือเล่าเกี่ยวกับสถานการณ์ (S - Situation) ในภาษาไทย")
    task: Optional[str] = Field(default=None, description="บทบาท หน้าที่ หรือเป้าหมายที่ต้องทำให้สำเร็จ (T - Task) ในภาษาไทย")
    action: Optional[str] = Field(default=None, description="ขั้นตอนการลงมือแก้ปัญหาหรือทำงานนั้นๆ (A - Action) ในภาษาไทย")
    result: Optional[str] = Field(default=None, description="ผลลัพธ์ที่เกิดขึ้น ตัวเลขที่วัดผลได้ หรือบทเรียนที่ได้รับ (R - Result) ในภาษาไทย")

class InterviewAnalysis(BaseModel):
    is_interview_question: bool = Field(
        description="ค่าความจริงว่าข้อความเสียงนี้เป็นคำถามหรือหัวข้อสัมภาษณ์งานจริงหรือไม่ (ตั้งเป็น False หากเป็นเพียงคำทักทาย การพูดคุยทั่วไป ทดสอบเสียง หรือข้อความที่ไม่ใช่คำถามสำหรับการสัมภาษณ์งาน)"
    )
    question_thai: Optional[str] = Field(default=None, description="สรุปคำถามในภาษาไทยให้กระชับและเข้าใจง่าย")
    category: Optional[str] = Field(default=None, description="หมวดหมู่ของคำถาม เช่น OOP, React, Soft Skills, Behavioral, Salary, Technical, etc. ในภาษาไทย")
    focus_areas: Optional[List[str]] = Field(default=None, description="ประเด็นสำคัญที่ผู้สัมภาษณ์ต้องการวัดผลจากคำถามนี้ ในภาษาไทย")
    key_points: Optional[List[str]] = Field(default=None, description="ประเด็นสำคัญที่ควรตอบ (Bullet points) ในภาษาไทย เพื่อเป็นแนวทางให้ตอบเอง")
    star_framework: Optional[StarFramework] = Field(
        default=None,
        description="แนวทางการตอบแบบ STAR Framework (ใส่เฉพาะเมื่อเป็นคำถามเชิงพฤติกรรม/ Behavioral Question)"
    )
    answer_strategy: Optional[str] = Field(default=None, description="กลยุทธ์/ข้อควรระวังในการตอบคำถามนี้ ในภาษาไทย")
    example_outline: Optional[List[str]] = Field(default=None, description="โครงร่างลำดับการพูดตอบคำถาม (Example Outline) เป็นข้อๆ ในภาษาไทย")
    suggested_answer: Optional[str] = Field(default=None, description="ตัวอย่างคำตอบที่สมบูรณ์และเป็นมืออาชีพ สามารถนำไปพูดตามหรือปรับใช้ได้ทันที (Suggested/Sample Answer) ในภาษาไทย")

class GeminiAnalyzer:
    def __init__(self, api_key="", model_name="gemini-3.1-flash-lite", 
                 provider="gemini", custom_api_key="", custom_base_url="", custom_model="",
                 strict_filter=True, resume_enabled=False, resume_text=""):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.custom_api_key = custom_api_key
        self.custom_base_url = custom_base_url
        self.custom_model = custom_model
        self.strict_filter = strict_filter
        self.resume_enabled = resume_enabled
        self.resume_text = resume_text
        
        self.client = None
        if api_key and provider == "gemini":
            self._init_client()
            
    def _init_client(self):
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            self.client = None

    def update_api_key(self, api_key):
        self.api_key = api_key
        self._init_client()

    def update_model_name(self, model_name):
        self.model_name = model_name
        print(f"Gemini Analyzer model updated to: {model_name}")

    def update_provider_config(self, provider, api_key, model_name, custom_api_key, custom_base_url, custom_model, strict_filter=True, resume_enabled=False, resume_text=""):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.custom_api_key = custom_api_key
        self.custom_base_url = custom_base_url
        self.custom_model = custom_model
        self.strict_filter = strict_filter
        self.resume_enabled = resume_enabled
        self.resume_text = resume_text
        if provider == "gemini":
            self._init_client()

    def validate_api_key(self):
        """
        Validates the current API Key by making a minimal test request.
        Returns:
            (success_bool, message_str)
        """
        if self.provider == "gemini":
            if not self.api_key:
                return False, "กรุณากรอก API Key ก่อนทดสอบ"
                
            if not self.client:
                self._init_client()
                if not self.client:
                    return False, "ไม่สามารถสร้าง Gemini Client ได้"
                    
            try:
                # Send a tiny query to test the key
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents="test"
                )
                # If we get a response, the key is valid!
                return True, "พร้อมใช้งาน! เชื่อมต่อสำเร็จ"
            except Exception as e:
                err_msg = str(e)
                print(f"[API Key Validation Error] {err_msg}")
                # Try to make error message user friendly
                if "API_KEY_INVALID" in err_msg or "invalid" in err_msg.lower():
                    return False, "คีย์ไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง"
                elif "quota" in err_msg.lower() or "limit" in err_msg.lower():
                    return False, "โควตาใช้งาน API Key นี้หมดแล้ว"
                else:
                    return False, "เชื่อมต่อล้มเหลว (เช็คอินเทอร์เน็ต/คีย์)"
        else:
            if not self.custom_base_url:
                return False, "กรุณากรอก Base URL ก่อนทดสอบ"
            
            import requests
            url = self.custom_base_url.rstrip('/') + "/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            if self.custom_api_key:
                headers["Authorization"] = f"Bearer {self.custom_api_key}"
            
            data = {
                "model": self.custom_model or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "test connection"}],
                "max_tokens": 5
            }
            try:
                response = requests.post(url, headers=headers, json=data, timeout=25)
                if response.status_code == 200:
                    return True, "พร้อมใช้งาน! เชื่อมต่อสำเร็จ"
                else:
                    return False, f"เชื่อมต่อล้มเหลว (HTTP {response.status_code}): {response.text[:100]}"
            except Exception as e:
                return False, f"เชื่อมต่อล้มเหลว: {str(e)[:100]}"

    def analyze_audio(self, audio_bytes, callback, status_callback=None):
        """Runs the Gemini multimodal audio analysis in a background thread."""
        if not self.api_key:
            if callback:
                callback(None, "Gemini API Key is missing. Please set it in Settings.")
            return

        if not self.client:
            self._init_client()
            if not self.client:
                if callback:
                    callback(None, "Failed to initialize Gemini Client. Check API Key.")
                return

        if status_callback:
            status_callback("กำลังวิเคราะห์ด้วย Gemini...")

        def worker():
            try:
                # Wrap the audio bytes in a multimodal Part
                audio_part = types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav"
                )
                
                prompt = """
                You are a premium career coaching assistant and interview expert. 
                An interviewer just asked a question in a job interview. You are given the recorded raw audio of this question.
                
                Please perform the following steps:
                1. Listen to the audio and transcribe the speech. Correct any acoustic or phonetic speech errors.
                   Pay special attention to English technical terms that might be spoken with a Thai accent or transcribed into phonetically similar Thai words (e.g. "พอลูก" or "ฟอลูก" -> "for loop", "ไวรัส" or "วาย" -> "while loop", "โอโอพี" -> "OOP").
                
                2. Check if this audio is actually a job interview question or topic (technical, soft-skill, behavioral, background, scenario-based, salary, etc.).
                   - If it is NOT an interview question (e.g. casual greeting "สวัสดีครับ", sound test "ฮัลโหล ได้ยินมั้ย", simple acknowledgement "โอเคครับ", chit-chat, etc.), you MUST set `is_interview_question = false` and leave all other fields as null/empty.
                   - If it IS an actual interview question, set `is_interview_question = true` and proceed with the full analysis.
                
                3. If `is_interview_question` is true:
                   - In `question_thai`, put the corrected, clear version of the question in Thai (e.g. "การใช้งาน for loop และตัวอย่างการใช้งาน").
                   - Provide a complete, high-quality, professional sample answer in Thai (`suggested_answer`) that the candidate can read or say directly. It should be natural, convincing, and demonstrate deep expertise.
                   - Fill in all other fields (category, focus_areas, key_points, answer_strategy, star_framework, example_outline) using THAI language.
                   
                IMPORTANT: Keep other fields concise, but make the `suggested_answer` a full, well-structured, professional response. Write everything in THAI.
                """
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[audio_part, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=InterviewAnalysis,
                        temperature=0.2,
                    ),
                )
                
                result_json = json.loads(response.text)
                print("Gemini audio response parsed successfully.")
                if status_callback:
                    status_callback("พร้อมใช้งาน")
                if callback:
                    callback(result_json, None)
                    
            except Exception as e:
                error_msg = f"Gemini API Error: {str(e)}"
                print(error_msg)
                if status_callback:
                    status_callback("เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini")
                if callback:
                    callback(None, error_msg)

        threading.Thread(target=worker, daemon=True).start()

    def _get_resume_prompt_addition(self):
        if self.resume_enabled and self.resume_text:
            return f"""
            
            [Candidate Resume & Background Profile]
            You have access to the candidate's resume/profile details. Use this context to personalize and tailor the "suggested_answer" (ตัวอย่างคำตอบที่แนะนำ) and "key_points" to highlight their actual relevant projects, skills, and background when answering. Do not fabricate experience not mentioned.
            Candidate Profile:
            {self.resume_text}
            """
        return ""

    def analyze_question(self, question_text, callback, status_callback=None):
        """Runs the AI structured text analysis for a transcribed question in a background thread."""
        if self.provider == "gemini":
            if not self.api_key:
                if callback:
                    callback(None, "Gemini API Key is missing. Please set it in Settings.")
                return

            if not self.client:
                self._init_client()
                if not self.client:
                    if callback:
                        callback(None, "Failed to initialize Gemini Client. Check API Key.")
                    return

            if status_callback:
                status_callback("กำลังวิเคราะห์คำถามด้วย Gemini...")

            # Define VAD strict/loose filter behavior dynamically
            if self.strict_filter:
                filter_instruction = """
                - Set `is_interview_question = true` ONLY if it is strictly a job interview question or topic (technical, soft-skill, behavioral, background, scenario-based, salary, etc.).
                - If it is a general knowledge question (e.g. "ประเทศไทยมีกี่จังหวัด"), casual greeting ("สวัสดีครับ"), sound test ("ฮัลโหล ได้ยินมั้ย"), simple acknowledgement ("โอเคครับ"), or general chit-chat, you MUST set `is_interview_question = false` and leave all other fields as null/empty.
                """
            else:
                filter_instruction = """
                - Treat almost all questions, queries, or knowledge checks (including general knowledge like "ประเทศไทยมีกี่จังหวัด", general questions, or brainstorming queries) as interview-relevant, and set `is_interview_question = true`.
                - ONLY set `is_interview_question = false` if the input is a pure sound test, meaningless noise, or a short greeting (like "hello", "สวัสดีครับ", "เทสๆ") that doesn't contain any actual question or query.
                """

            def worker():
                try:
                    print(f"[Gemini Log] Sending text to Gemini model '{self.model_name}' for structured analysis: '{question_text}'")
                    resume_addition = self._get_resume_prompt_addition()
                    prompt = f"""
                    You are a premium career coaching assistant and interview expert. 
                    An interviewer just asked a question in a job interview. Here is the transcribed text of the question:
                    
                    "{question_text}"
                    {resume_addition}
                    
                    Please perform the following steps:
                    1. Review the transcribed question text. Correct any transcription errors, spelling mistakes, or grammatical errors.
                       Pay special attention to English technical terms that might be transcribed phonetically in Thai (e.g. "พอลูก" -> "for loop").
                    
                    2. Check if this text is a valid question to analyze:
                       {filter_instruction}
                    
                    3. If `is_interview_question` is true:
                       - In `question_thai`, put the corrected, clear version of the question in Thai (e.g. "การใช้งาน for loop และตัวอย่างการใช้งาน").
                       - Provide a complete, high-quality, professional sample answer in Thai (`suggested_answer`) that the candidate can read or say directly. It should be natural, convincing, and demonstrate deep expertise.
                       - Fill in all other fields (category, focus_areas, key_points, answer_strategy, star_framework, example_outline) using THAI language.
                       
                    IMPORTANT: Keep other fields concise, but make the `suggested_answer` a full, well-structured, professional response. Write everything in THAI.
                    """
                    
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=InterviewAnalysis,
                            temperature=0.2,
                        ),
                    )
                    
                    result_json = json.loads(response.text)
                    print(f"[Gemini Log] Response successfully received and parsed: {result_json}")
                    if status_callback:
                        status_callback("พร้อมใช้งาน")
                    if callback:
                        callback(result_json, None)
                        
                except Exception as e:
                    error_msg = f"Gemini API Error: {str(e)}"
                    print(f"[Gemini Log] {error_msg}")
                    if status_callback:
                        status_callback("เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini")
                    if callback:
                        callback(None, error_msg)

            threading.Thread(target=worker, daemon=True).start()
        else:
            self._analyze_question_custom(question_text, callback, status_callback)

    def _analyze_question_custom(self, question_text, callback, status_callback=None):
        """Runs the Custom OpenAI-compatible structured text analysis for a transcribed question in a background thread."""
        if not self.custom_base_url:
            if callback:
                callback(None, "API Base URL (Endpoint) is missing. Please set it in Settings.")
            return

        if status_callback:
            status_callback("กำลังวิเคราะห์คำถามด้วย Custom AI...")

        # Define VAD strict/loose filter behavior dynamically for Custom AI
        if self.strict_filter:
            filter_instruction = """
            - Set `is_interview_question = true` ONLY if it is strictly a job interview question or topic (technical, soft-skill, behavioral, background, scenario-based, salary, etc.).
            - If it is a general knowledge question (e.g. "ประเทศไทยมีกี่จังหวัด"), casual greeting ("สวัสดีครับ"), sound test ("ฮัลโหล ได้ยินมั้ย"), simple acknowledgement ("โอเคครับ"), or general chit-chat, you MUST set `is_interview_question = false` and leave all other fields as null/empty.
            """
        else:
            filter_instruction = """
            - Treat almost all questions, queries, or knowledge checks (including general knowledge like "ประเทศไทยมีกี่จังหวัด", general questions, or brainstorming queries) as interview-relevant, and set `is_interview_question = true`.
            - ONLY set `is_interview_question = false` if the input is a pure sound test, meaningless noise, or a short greeting (like "hello", "สวัสดีครับ", "เทสๆ") that doesn't contain any actual question or query.
            """

        def worker():
            import requests
            try:
                url = self.custom_base_url.rstrip('/') + "/chat/completions"
                headers = {
                    "Content-Type": "application/json"
                }
                if self.custom_api_key:
                    headers["Authorization"] = f"Bearer {self.custom_api_key}"
                
                resume_addition = self._get_resume_prompt_addition()
                system_prompt = f"""
                You are a premium career coaching assistant and interview expert.
                An interviewer just asked a question in a job interview.
                {resume_addition}
                
                You MUST return a valid JSON object matching the following structure:
                {{
                  "is_interview_question": boolean,
                  "question_thai": string or null,
                  "category": string or null,
                  "focus_areas": [string] or null,
                  "key_points": [string] or null,
                  "star_framework": {{
                    "situation": string or null,
                    "task": string or null,
                    "action": string or null,
                    "result": string or null
                  }} or null,
                  "answer_strategy": string or null,
                  "example_outline": [string] or null,
                  "suggested_answer": string
                }}
                
                Important Guidelines:
                1. Review the transcribed question text. Correct any transcription errors, spelling mistakes, or grammatical errors.
                   Pay special attention to English technical terms that might be transcribed phonetically in Thai (e.g. "พอลูก" -> "for loop").
                2. Check if this text is a valid question to analyze:
                   {filter_instruction}
                3. If `is_interview_question` is true:
                   - In `question_thai`, put the corrected, clear version of the question in Thai (e.g. "การใช้งาน for loop และตัวอย่างการใช้งาน").
                   - Provide a complete, high-quality, professional sample answer in Thai (`suggested_answer`) that the candidate can read or say directly. It should be natural, convincing, and demonstrate deep expertise.
                   - Fill in all other fields (category, focus_areas, key_points, answer_strategy, star_framework, example_outline) using THAI language.
                   
                Make the `suggested_answer` a full, well-structured, professional response. Write everything in THAI.
                Respond ONLY with the JSON object. Do not include markdown code block syntax.
                """
                
                user_content = f'Analyze this transcribed question: "{question_text}"'
                
                payload = {
                    "model": self.custom_model or "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.2
                }
                
                # Attempt to request JSON format
                payload["response_format"] = {"type": "json_object"}
                
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=25)
                    if response.status_code != 200:
                        # Retry without response_format if not supported
                        if "response_format" in payload:
                            del payload["response_format"]
                            response = requests.post(url, headers=headers, json=payload, timeout=25)
                except Exception as e:
                    # Retry without response_format if it failed/timed out on connection
                    if "response_format" in payload:
                        del payload["response_format"]
                        response = requests.post(url, headers=headers, json=payload, timeout=25)
                    else:
                        raise e

                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
                resp_json = response.json()
                content = resp_json["choices"][0]["message"]["content"].strip()
                
                # Parse JSON content, dealing with potential markdown backticks
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                result_json = json.loads(content)
                print(f"[Custom AI Log] Response successfully received and parsed: {result_json}")
                
                if status_callback:
                    status_callback("พร้อมใช้งาน")
                if callback:
                    callback(result_json, None)
                    
            except Exception as e:
                error_msg = f"Custom AI Error: {str(e)}"
                print(f"[Custom AI Log] {error_msg}")
                if status_callback:
                    status_callback("เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Custom AI")
                if callback:
                    callback(None, error_msg)

        threading.Thread(target=worker, daemon=True).start()

