# sleep_tracking_app/rag/ollama_client.py
import os
import time
from typing import Any, Dict, Optional
import requests
from langfuse import observe  # type: ignore

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral:7b-instruct-q4_K_M")


@observe(name="mistral_api_call")
def _generate_call(payload: Dict[str, Any], base_url: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Low-level call to Ollama.
    Returns dict:
      {
        "response": str | None,
        "response_preview": str,
        "latency": float,
        "model": str,
        "error": str | None
      }
    """
    start = time.time()
    try:
        resp = requests.post(base_url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        answer: Optional[str] = None
        if isinstance(data, dict):
            if isinstance(data.get("response"), str):
                answer = data.get("response")
            elif isinstance(data.get("results"), list) and data["results"]:
                first = data["results"][0]
                if isinstance(first, dict):
                    answer = first.get("content") or first.get("response") or str(first)
                else:
                    answer = str(first)
            else:
                answer = str(data)
        else:
            answer = str(data)

        latency = round(time.time() - start, 3)
        return {
            "response": answer,
            "response_preview": (answer or "")[:2000],
            "latency": latency,
            "model": payload.get("model"),
            "error": None
        }

    except Exception as exc:
        latency = round(time.time() - start, 3)
        return {
            "response": None,
            "response_preview": "",
            "latency": latency,
            "model": payload.get("model"),
            "error": str(exc)
        }


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or OLLAMA_URL
        self.model = model or MISTRAL_MODEL

    def is_available(self, timeout: int = 5) -> bool:
        try:
            status_url = self.base_url.replace("/api/generate", "/api/tags")
            r = requests.get(status_url, timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 512,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        High-level generate. Returns dict (see _generate_call).
        Caller must inspect dict['error'] or dict['response'].
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": num_predict
            }
        }
        if system:
            payload["system"] = system

        return _generate_call(payload=payload, base_url=self.base_url, timeout=timeout)
