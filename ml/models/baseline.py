import time
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
# LLM client
from google import genai
# Langfuse SDK
from langfuse.decorators import observe
from langfuse import get_client

from models import UserData, SleepStatistics, SleepRecord
from prompt_templates import create_sleep_analysis_prompt, get_system_prompt

load_dotenv()

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
MAX_RETRIES = int(os.environ.get("BASELINE_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.environ.get("BASELINE_RETRY_DELAY", "1.5"))

def _extract_text_from_response(resp: Any) -> str:
    """Извлечение текста из ответа Gemini"""
    if resp is None:
        return ""
    
    try:
        if hasattr(resp, 'text') and resp.text:
            return resp.text
        
        if hasattr(resp, 'candidates') and resp.candidates:
            candidate = resp.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                return candidate.content.parts[0].text
        
        return str(resp)
    except Exception as e:
        print(f"⚠️  Error extracting text from response: {e}")
        return ""

@observe(name="gemini_api_call")
def call_gemini(prompt: str, test_case_id: str = "unknown") -> str:
    """Вызов Gemini с повторными попытками"""
    if genai is None:
        print("❌ Gemini client not available")
        return ""

    client = genai.Client()

    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        
        try:
            # Вызов Gemini API
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            
            latency = round(time.time() - start_time, 3)
            text = _extract_text_from_response(response)

            print(f"✅ Attempt {attempt} successful - Latency: {latency}s")
            return text

        except Exception as e:
            latency = round(time.time() - start_time, 3)
            error_msg = str(e)
            
            print(f"❌ Attempt {attempt} failed: {error_msg}")

            if attempt < MAX_RETRIES:
                print(f"🔄 Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print("💥 All retry attempts exhausted")
                return ""

    return ""

@observe(name="sleep_analysis_pipeline")
def get_sleep_recommendation(
    user_data: UserData,
    sleep_statistics: SleepStatistics,
    sleep_record: SleepRecord
) -> str:
    """
    Основная функция для получения рекомендаций по сну
    """
    system_prompt = get_system_prompt()
    user_prompt = create_sleep_analysis_prompt(user_data, sleep_statistics, sleep_record)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    result = call_gemini(full_prompt)
    
    if not result:
        error_msg = "Извините, я не смог обработать ваш запрос. Попробуйте позже."        
        return error_msg
    
    return result

