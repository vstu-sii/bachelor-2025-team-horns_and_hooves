import os
import json
import re
from typing import Any, Dict, Optional

from google import genai 

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Вытащить первое JSON-подобное тело из текста."""
    try:
        match = re.search(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    raw = match.group()
    try:
        return json.loads(raw)
    except Exception:
        try:
            return json.loads(raw.replace("'", '"'))
        except Exception:
            return None


class SleepLLMJudge:
    """LLM-судья для оценивания ответа ассистента по сну."""

    def __init__(self):
        try:
            self.client = genai.Client()
        except Exception:
            self.client = None

    def _make_prompt(self, user_data, sleep_stats, sleep_record, response_text: str) -> str:
        return make_judge_prompt(user_data, sleep_stats, sleep_record, response_text)

    def evaluate(self, user_data, sleep_stats, sleep_record, response_text: str) -> Optional[Dict[str, Any]]:
        """Вернёт dict с оценками или None при ошибке."""
        if not self.client:
            return None

        prompt = self._make_prompt(user_data, sleep_stats, sleep_record, response_text)
        try:
            resp = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt]
            )
        except Exception as e:
            print("[judge] error:", e)
            return None

        text = ""
        if hasattr(resp, "text") and resp.text:
            text = resp.text
        elif hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if getattr(cand, "content", None) and cand.content.parts:
                text = cand.content.parts[0].text or ""
        else:
            text = str(resp)

        return _extract_json_block(text)
