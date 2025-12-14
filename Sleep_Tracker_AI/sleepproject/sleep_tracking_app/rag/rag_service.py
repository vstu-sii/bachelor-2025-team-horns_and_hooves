# sleep_tracking_app/rag/rag_service.py
import json
from typing import Any, Dict, List, Optional
from langfuse import observe  # type: ignore

from .vector_db import SleepVectorDB
from .ollama_client import OllamaClient

DEFAULT_SYSTEM_PROMPT = (
    "Ты — AI-эксперт по сну. Используй научные исследования чтобы улучшить рекомендации. "
    "Сначала дай научное обоснование со ссылками на исследования (имена файлов), затем улучшенные рекомендации, "
    "практические шаги и ожидаемые результаты. Будь краток и структурирован."
)


class RagService:
    def __init__(self, vector_db: Optional[SleepVectorDB] = None, ollama_client: Optional[OllamaClient] = None):
        # Optional в аннотации и конкретная инициализация внутри
        self.vector_db = vector_db if vector_db is not None else SleepVectorDB()
        self.ollama = ollama_client if ollama_client is not None else OllamaClient()

    def _create_search_query(self, gemini_response: str, user_data: Dict[str, Any]) -> str:
        problem_indicators = [
            "бессонница", "апноэ", "храп", "пробуждения", "засыпание", "сонливость", "фрагментация", "латентность"
        ]
        text = (gemini_response or "").lower()
        keywords = [k for k in problem_indicators if k in text]

        age = user_data.get("age")
        if age is None and user_data.get("age_months"):
            try:
                age = int(user_data["age_months"]) // 12
            except Exception:
                age = None

        if isinstance(age, int):
            if age < 25:
                keywords.append("подростковый сон")
            if age > 60:
                keywords.append("пожилой сон")

        if keywords:
            seen = set()
            uniq = []
            for k in keywords:
                if k not in seen:
                    uniq.append(k)
                    seen.add(k)
            return " ".join(uniq)
        return "качество сна улучшение исследование"

    def _build_research_context(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "Научные исследования не найдены."
        parts = []
        for i, r in enumerate(results, 1):
            txt = r.get("text", "")
            excerpt = (txt[:500] + "...") if isinstance(txt, str) and len(txt) > 500 else txt
            parts.append(
                f"--- ИССЛЕДОВАНИЕ {i} ---\n"
                f"Источник: {r.get('source','unknown')}\n"
                f"Релевантность: {r.get('score', 0):.3f}\n"
                f"{excerpt}\n"
            )
        return "\n".join(parts)

    @observe(name="rag_enhance")
    def enhance(self, gemini_response: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1) query
        search_query = self._create_search_query(gemini_response, user_data)

        # 2) search
        try:
            search_hits = self.vector_db.search(search_query, limit=4) or []
        except Exception:
            search_hits = []

        sources = [
            {"source": h.get("source"), "score": h.get("score"), "chunk_id": h.get("chunk_id")}
            for h in search_hits
        ]

        # 3) context
        research_context = self._build_research_context(search_hits)

        # 4) prompt
        system_prompt = DEFAULT_SYSTEM_PROMPT or ""
        full_prompt = (
            f"{system_prompt}\n\n"
            f"НАУЧНЫЕ ИССЛЕДОВАНИЯ:\n{research_context}\n\n"
            f"ИСХОДНЫЕ РЕКОМЕНДАЦИИ (Gemini):\n{gemini_response}\n\n"
            f"ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n{json.dumps(user_data, ensure_ascii=False, indent=2)}\n\n"
            "Улучшить рекомендации, опираясь на исследования."
        )

        # 5) call Ollama
        mistral_result = self.ollama.generate(full_prompt, system=system_prompt)

        enhanced_text = ""
        error_text: Optional[str] = None

        if isinstance(mistral_result, dict):
            error_text = mistral_result.get("error")
            enhanced_text = mistral_result.get("response") or mistral_result.get("response_preview") or ""
        else:
            enhanced_text = str(mistral_result)

        result: Dict[str, Any] = {
            "original": gemini_response,
            "search_query": search_query,
            "sources": sources,
            "prompt_preview": full_prompt[:1500],
            "enhanced": enhanced_text,
            "error": error_text
        }
        return result
