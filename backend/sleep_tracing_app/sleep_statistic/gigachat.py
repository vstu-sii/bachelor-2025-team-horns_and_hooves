import requests
from dotenv import load_dotenv, find_dotenv
import os
import json
import urllib3

from sleep_tracking_app.models import UserData, SleepStatistics, SleepRecord

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv(find_dotenv())


def get_access_token() -> str:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'b38759ba-e5a6-4385-b920-bb41913576be',
        'Authorization': f'Basic {os.getenv("GigaChat_API")}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    return response.json()["access_token"]


def get_answer(prompt: [str]):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    access_token = get_access_token()

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    body = {
        "model": "GigaChat",
        "messages": [
            {"role": "system",
             "content": """Ты — эксперт по сну (сомнолог), 
             твоя задача дать краткую рекомендацию пользователю на основе показателей, которые он прислал. 
             Твой ответ должен в развёрнутых предложениях, чтобы пользователь понял, что ты эксперт который может донести свою мысль простыми словами.
             Примечание: запрещено использовать язык разметки Markdown.
             """

             },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "n": 1,
        "stream": False
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(body), verify=False)
    response.raise_for_status()  # Проверка на ошибки HTTP

    return response.json()["choices"][0]["message"]["content"]


def get_rec_to_prompt(user_data: UserData, sleep_statistics: [SleepStatistics], sleep_record: SleepRecord) -> str:

    if sleep_record.sleep_rem_duration > 0:
        prompt = (
            f'''Возраст в месяцах: {user_data.get_age_months()}, 
            Пол: {user_data.get_gender()}, Вес: {user_data.weight}, Рост:{user_data.height}. 
            Мои параметры сна за последний день: продолжительность сна {sleep_record.duration} минут, глубокий сон {sleep_record.sleep_deep_duration} минут, REM-сон {sleep_record.sleep_rem_duration} минут, легкий сон {sleep_record.sleep_light_duration} минут,
            эффективность сна {sleep_statistics.sleep_efficiency}%, 
            индекс фрагментации сна {sleep_statistics.sleep_fragmentation_index}, время засыпания {sleep_statistics.latency_minutes} минут, калории сожжённые во сне {sleep_statistics.sleep_calories_burned} ккал. 
            Внимательно проанализируй мою запись сна, учитывая все мои показатели. Дай конкретные советы, как улучшить мой сон.'''
        )
    else:
        prompt = (
            f'''Возраст в месяцах: {user_data.get_age_months()}, 
                   Пол: {user_data.get_gender()}, Вес: {user_data.weight}, Рост:{user_data.height}. 
                   Мои параметры сна за последний день: продолжительность сна {sleep_record.duration} минут, глубокий сон {sleep_record.sleep_deep_duration} минут, легкий сон {sleep_record.sleep_light_duration} минут,
                   эффективность сна {sleep_statistics.sleep_efficiency}%, 
                   индекс фрагментации сна {sleep_statistics.sleep_fragmentation_index}, время засыпания {sleep_statistics.latency_minutes} минут, калории сожжённые во сне {sleep_statistics.sleep_calories_burned} ккал. 
                   Внимательно проанализируй мою запись сна, учитывая все мои показатели. Дай конкретные советы, как улучшить мой сон.'''
        )
    return get_answer(prompt)


def main():
    # Пример данных пользователя
    prompt = (
        ''
    )

    answer = get_answer(prompt)
    print("Ответ GigaChat:\n", answer)


if __name__ == "__main__":
    main()
