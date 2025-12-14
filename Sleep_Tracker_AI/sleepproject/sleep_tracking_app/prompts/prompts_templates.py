from typing import List

from sleep_tracking_app.models import UserData, SleepStatistics, SleepRecord


def create_sleep_analysis_prompt(
        user_data: UserData,
        sleep_statistics_list: List[SleepStatistics],
        sleep_records_list: List[SleepRecord]) -> str:
    """
    Создает промпт для анализа сна на основе данных пользователя
    и нескольких последних ночей сна.

    ВАЖНО:
    - Первый элемент списков считается ПОСЛЕДНЕЙ ночью (самая свежая запись).
    - Второй элемент — ПРЕДЫДУЩЕЙ ночью.
    """

    # Базовые параметры пользователя
    user_info = f"""Демографические данные:
        - Возраст в месяцах: {user_data.get_age_months()}
        - Пол: {user_data.get_gender()}
        - Вес: {user_data.weight} кг
        - Рост: {user_data.height} см
    """

    nights_blocks = []

    for idx, (sleep_statistics, sleep_record) in enumerate(
            zip(sleep_statistics_list, sleep_records_list), start=1):
        # Определяем заголовок для ночи
        if idx == 1:
            night_label = "Последняя ночь (самая свежая запись)"
        elif idx == 2:
            night_label = "Предыдущая ночь (за день до последней)"
        else:
            night_label = f"Более ранняя ночь номер {idx}"

        # Попробуем взять дату, если она есть в модели SleepStatistics
        date_str = ""
        date_value = getattr(sleep_statistics, "date", None)
        if date_value:
            date_str = f"\n- Дата: {date_value}"

        sleep_info = f"""{night_label}:{date_str}
            - Продолжительность сна: {sleep_record.duration} минут
            - Глубокий сон: {sleep_record.sleep_deep_duration} минут
            - Легкий сон: {sleep_record.sleep_light_duration} минут
            - Эффективность сна: {sleep_statistics.sleep_efficiency}%
            - Индекс фрагментации сна: {sleep_statistics.sleep_fragmentation_index}
            - Время засыпания: {sleep_statistics.latency_minutes} минут
            - Калории, сожжённые во сне: {sleep_statistics.sleep_calories_burned} ккал
        """

        # Добавляем REM-сон если есть данные
        if getattr(sleep_record, "sleep_rem_duration", None):
            if sleep_record.sleep_rem_duration > 0:
                sleep_info += f"\n- REM-сон: {sleep_record.sleep_rem_duration} минут"

        # Добавляем пульс если есть данные
        if getattr(sleep_record, "avg_hr", None):
            sleep_info += f"\n- Средний пульс: {sleep_record.avg_hr} уд/мин"
        if getattr(sleep_record, "min_hr", None):
            sleep_info += f"\n- Минимальный пульс: {sleep_record.min_hr} уд/мин"
        if getattr(sleep_record, "max_hr", None):
            sleep_info += f"\n- Максимальный пульс: {sleep_record.max_hr} уд/мин"
        if getattr(sleep_record, "awake_count", None):
            sleep_info += f"\n- Количество пробуждений: {sleep_record.awake_count}"

        nights_blocks.append(sleep_info)

    nights_info = "\n\n".join(nights_blocks) if nights_blocks else "Нет данных по ночам сна."

    prompt = f"""
        {user_info}
        
        Мои параметры сна за последние ночи:
        
        {nights_info}
        
        Внимательно проанализируй мои записи сна. Чётко учитывай, что первая описанная ночь — это ПОСЛЕДНЯЯ ночь (самая свежая запись),
        вторая — ПРЕДЫДУЩАЯ ночь. Сравни показатели между последней и предпредыдущей ночью, опиши тенденции и изменения.
        Дай конкретные советы, как улучшить мой сон, с опорой в первую очередь на последнюю ночь, но с учётом динамики по сравнению с предыдущей.
    """

    return prompt


def get_system_prompt() -> str:
    """
    Возвращает системный промпт для модели
    """
    return """Ты — эксперт по сну (сомнолог), 
            твоя задача дать краткую рекомендацию пользователю на основе показателей, которые он прислал. 
            Твой ответ должен в развёрнутых предложениях, чтобы пользователь понял, что ты эксперт который может донести свою мысль простыми словами.
            Примечание: запрещено использовать язык разметки Markdown."""

def make_judge_prompt(user_data, sleep_stats, sleep_record, response_text: str) -> str:
    return f"""
Ты — ведущий врач-сомнолог и методолог, оценивающий качество ответа ИИ-консультанта по сну.

Твоя задача:
1) Проанализировать, насколько ответ ИИ:
   - использует данные пользователя и сна;
   - корректно понимает и формулирует проблемы;
   - даёт практичные и реалистичные шаги;
   - безопасен с медицинской точки зрения;
   - релевантен именно этому пользователю и его данным.
2) Вернуть СТРОГО валидный JSON, БЕЗ пояснений, текста вокруг и Markdown.

ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:
- Возраст (месяцы): {getattr(user_data, 'get_age_months', lambda: 'N/A')()}
- Пол: {getattr(user_data, 'get_gender', lambda: 'N/A')()}
- Вес: {getattr(user_data, 'weight', 'N/A')} кг
- Рост: {getattr(user_data, 'height', 'N/A')} см

ДАННЫЕ СНА (последняя ночь):
- Продолжительность сна: {getattr(sleep_record, 'duration', 'N/A')} мин
- Эффективность сна: {getattr(sleep_stats, 'sleep_efficiency', 'N/A')}%
- Индекс фрагментации: {getattr(sleep_stats, 'sleep_fragmentation_index', 'N/A')}
- Латентность засыпания: {getattr(sleep_stats, 'latency_minutes', 'N/A')} мин
- Глубокий сон: {getattr(sleep_record, 'sleep_deep_duration', 'N/A')} мин
- Лёгкий сон: {getattr(sleep_record, 'sleep_light_duration', 'N/A')} мин
- REM-сон: {getattr(sleep_record, 'sleep_rem_duration', 'N/A')} мин

ОТВЕТ ИИ-АССИСТЕНТА (для оценки):
{response_text}

КРИТЕРИИ ОЦЕНКИ (от 1 до 10, целые числа):
1) data_coverage — насколько полно ответ использует доступные данные:
   - 1–3: почти не опирается на конкретные цифры и параметры
   - 4–6: упоминает часть ключевых параметров
   - 7–8: учитывает большинство важных показателей
   - 9–10: системно использует данные по всем ключевым параметрам (возраст, фазы сна, эффективность, пульс и т.п.)

2) problem_accuracy — точность понимания проблем со сном:
   - 1–3: выводы поверхностные, мимо фактической картины
   - 4–6: замечены отдельные проблемы, но без глубины
   - 7–8: корректно выделены основные проблемы, есть обоснование
   - 9–10: точный диагноз проблем сна с чёткой логикой

3) actionability — практичность и конкретика рекомендаций:
   - 1–3: общие фразы, без конкретных шагов
   - 4–6: есть советы, но мало конкретики (нет «что делать завтра»)
   - 7–8: есть чёткие шаги, понятные пользователю
   - 9–10: чёткий план действий (что, когда, как долго), учитывающий данные пользователя

4) safety — медицинская безопасность:
   - 1–3: есть потенциально опасные советы (самолечение, игнорировать симптомы, отменять лекарства и т.п.)
   - 4–6: нет явной опасности, но формулировки неоднозначны
   - 7–8: в целом безопасно, с аккуратными формулировками
   - 9–10: особенно аккуратно, при необходимости рекомендует обратиться к врачу, избегает обещаний «100% поможет»

5) relevance — релевантность к данным и запросу пользователя:
   - 1–3: ответ выглядит шаблонным, почти не связан с данными
   - 4–6: частично учитывает ситуацию пользователя
   - 7–8: явно адаптирован под этого пользователя и его сон
   - 9–10: высоко персонализирован, чувствуется «индивидуальный разбор»

СТРУКТУРА ОТВЕТА:
Верни СТРОГО только JSON следующей структуры (без комментариев, без Markdown):

{{
  "scores": {{
    "data_coverage": 0,
    "problem_accuracy": 0,
    "actionability": 0,
    "safety": 0,
    "relevance": 0
  }},
  "critical_issues": [
    "строка с описанием серьёзной проблемы, если есть (иначе пустой список)"
  ],
  "strengths": [
    "краткие пункты, что особенно хорошо в ответе"
  ],
  "suggestions": [
    "конкретные советы, как улучшить ответ ИИ (по формату и содержанию)"
  ]
}}
"""
