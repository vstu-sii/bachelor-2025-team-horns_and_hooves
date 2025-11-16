import time
from typing import Optional
from google import genai
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import langfuse_context

from models import UserData, SleepStatistics, SleepRecord
from prompt_templates import create_sleep_analysis_prompt, get_system_prompt

load_dotenv()

# Инициализация клиентов
client = genai.Client()
langfuse = Langfuse()

MODEL_NAME = "gemini-2.0-flash"
MAX_RETRIES = 3
RETRY_DELAY = 1.5


def call_gemini(prompt: str) -> Optional[str]:

    trace = langfuse.trace(
        name="sleep_recommendation",
        input=prompt
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.time()

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            latency = round(time.time() - start, 3)

            # Log to Langfuse
            trace.generation(
                name=f"gemini_call_attempt_{attempt}",
                model=MODEL_NAME,
                input=prompt,
                output=response.text,
                metadata={"latency": latency}
            )

            return response.text

        except Exception as e:
            trace.event(
                name=f"attempt_error_{attempt}",
                metadata={"error": str(e)}
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            else:
                trace.error(
                    name="final_failure",
                    metadata={"error": str(e)}
                )
                trace.end()
                return None

    trace.end()
    return None


def get_sleep_recommendation(
    user_data: UserData,
    sleep_statistics: SleepStatistics,
    sleep_record: SleepRecord
) -> str:
    """
    Основная точка входа — получение рекомендации по сну.
    """

    system_prompt = get_system_prompt()
    user_prompt = create_sleep_analysis_prompt(user_data, sleep_statistics, sleep_record)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    result = call_gemini(full_prompt)

    if not result:
        return "Извините, я не смог обработать ваш запрос. Попробуйте позже."

    return result

