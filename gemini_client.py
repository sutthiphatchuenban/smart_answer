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
    def __init__(self, api_key="", model_name="gemini-3.1-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if api_key:
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

    def validate_api_key(self):
        """
        Validates the current Gemini API Key by making a minimal generate_content request.
        Returns:
            (success_bool, message_str)
        """
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

    def analyze_question(self, question_text, callback, status_callback=None):
        """Runs the Gemini structured text analysis for a transcribed question in a background thread."""
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

        def worker():
            try:
                print(f"[Gemini Log] Sending text to Gemini model '{self.model_name}' for structured analysis: '{question_text}'")
                prompt = f"""
                You are a premium career coaching assistant and interview expert. 
                An interviewer just asked a question in a job interview. Here is the transcribed text of the question:
                
                "{question_text}"
                
                Please perform the following steps:
                1. Review the transcribed question text. Correct any transcription errors, spelling mistakes, or grammatical errors.
                   Pay special attention to English technical terms that might be transcribed phonetically in Thai (e.g. "พอลูก" -> "for loop").
                
                2. Check if this text is actually a job interview question or topic (technical, soft-skill, behavioral, background, scenario-based, salary, etc.).
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

