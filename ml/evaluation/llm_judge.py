"""
LLM-судья: использует google-genai SDK, если установлен, иначе можно добавить HTTP fallback.
Функция evaluate_response возвращает dict:
{
  "scores": {"data_coverage": int, "problem_accuracy": int, "actionability": int, "safety": int, "relevance": int},
  "critical_issues": [...],
  "strengths": [...],
  "suggestions": [...]
}
или None при ошибке.
"""

import os
import re
import json
import time
from typing import Dict, Any, Optional

# try SDK
USE_GENAI = False
try:
    from google import genai  # type: ignore
    USE_GENAI = True
except Exception:
    USE_GENAI = False

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
SDK_TIMEOUT = int(os.environ.get("LLM_JUDGE_TIMEOUT", "30"))

# Instantiate client if SDK available
_client = None
if USE_GENAI:
    try:
        _client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", None))
    except Exception:
        _client = None


def _make_prompt(user_data, sleep_stats, sleep_record, response_text):
    # compact prompt in Russian for judge
    prompt = f"""
Ты - ведущий эксперт-сомнолог. Оцени ответ ИИ-ассистента по критериям и верни только JSON.

ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
- Возраст (месяцы): {getattr(user_data, 'get_age_months', lambda: 'N/A')()}
- Пол: {getattr(user_data, 'get_gender', lambda: 'N/A')()}
- Вес: {getattr(user_data, 'weight', 'N/A')} кг, Рост: {getattr(user_data, 'height', 'N/A')} см

ДАННЫЕ СНА:
- Продолжительность: {getattr(sleep_record, 'duration', 'N/A')} мин
- Эффективность: {getattr(sleep_stats, 'sleep_efficiency', 'N/A')}%
- Фрагментация: {getattr(sleep_stats, 'sleep_fragmentation_index', 'N/A')}
- Засыпание: {getattr(sleep_stats, 'latency_minutes', 'N/A')} мин
- Глубокий сон: {getattr(sleep_record, 'sleep_deep_duration', 'N/A')} мин
- REM-сон: {getattr(sleep_record, 'sleep_rem_duration', 'N/A')} мин

ОТВЕТ АССИСТЕНТА:
{response_text}

КРИТЕРИИ (1-10):
1) data_coverage - покрытие данных
2) problem_accuracy - точность выявления проблемы
3) actionability - практичность рекомендаций
4) safety - безопасность
5) relevance - релевантность

ВЕРНИ СТРОГО ТОЛЬКО JSON следующей структуры:
{{
  "scores": {{
    "data_coverage": 0,
    "problem_accuracy": 0,
    "actionability": 0,
    "safety": 0,
    "relevance": 0
  }},
  "critical_issues": [],
  "strengths": [],
  "suggestions": []
}}
"""
    return prompt


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Находит первое JSON-подобное тело в тексте"""
    try:
        match = re.search(r'\{(?:[^{}]|(?R))*\}', text, flags=re.DOTALL)
    except Exception:
        match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return None
    jtxt = match.group()
    try:
        return json.loads(jtxt)
    except Exception:
        jtxt2 = jtxt.replace("'", '"')
        try:
            return json.loads(jtxt2)
        except Exception:
            return None


def evaluate_response_via_sdk(prompt_text: str) -> Optional[Dict[str, Any]]:
    """Вызов Gemini SDK для оценки"""
    if not _client:
        return None
    try:
        resp = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt_text],
            config={"temperature": 0.0, "maxOutputTokens": 512}
        )
        text = ""
        if hasattr(resp, "text") and resp.text:
            text = resp.text
        elif isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                text = resp["candidates"][0].get("output") or json.dumps(resp, ensure_ascii=False)
            else:
                text = json.dumps(resp, ensure_ascii=False)
        else:
            text = str(resp)
        return _extract_json_from_text(text)
    except Exception as e:
        print(f"[llm_judge] SDK error: {e}")
        return None


def evaluate_response(user_data, sleep_stats, sleep_record, response_text) -> Optional[Dict[str, Any]]:
    """Главный метод — оценивает ответ через SDK"""
    prompt = _make_prompt(user_data, sleep_stats, sleep_record, response_text)
    if USE_GENAI and _client:
        out = evaluate_response_via_sdk(prompt)
        if out:
            return out
    return None


# --- Обёртка для совместимости ---
class LLMSleepJudge:
    """Обёртка над функциями LLM-судьи"""
    def evaluate_response(self, user_data, sleep_stats, sleep_record, response_text):
        return evaluate_response(user_data, sleep_stats, sleep_record, response_text)
