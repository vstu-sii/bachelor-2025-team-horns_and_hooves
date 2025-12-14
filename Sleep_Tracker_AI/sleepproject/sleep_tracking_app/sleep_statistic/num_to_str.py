from datetime import time
import json
from pathlib import Path
from django.conf import settings




def interpret_chronotype(msf_time: time, name:str, language: str) -> dict:
    """
    Интерпретирует хронотип на основе MSF (Mid-Sleeping Frequency) времени.
    Возвращает словарь с интерпретацией хронотипа и его описанием
    """

    match msf_time:
        case msf_time if msf_time < time(hour=3):
            interpret = "skylark"
        case msf_time if time(hour=3) <= msf_time < time(hour=5):
            interpret = "pigeon"
        case msf_time if msf_time > time(hour=5):
            interpret = "owl"
        case _:
            interpret = ""

    file_path = Path(settings.BASE_DIR) / 'sleep_tracking_app' / 'static' / 'chronotype_info' / 'info.json'

    with open(file_path, 'r', encoding='utf-8') as f:
        chronotype_interpretations = json.load(f)
    if chronotype_interpretations[name][interpret]:
        description = chronotype_interpretations[name][interpret][language]
    else:
        description = ""

    return {interpret: description} if interpret else {}
