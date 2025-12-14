# ml/prompt_templates.py
from models import UserData, SleepStatistics, SleepRecord

def create_sleep_analysis_prompt(user_data: UserData, sleep_statistics: SleepStatistics, sleep_record: SleepRecord) -> str:
    """
    Создает промпт для анализа сна на основе данных пользователя
    """
    
    # Базовые параметры пользователя
    user_info = f"""Демографические данные:
    - Возраст в месяцах: {user_data.get_age_months()}
    - Пол: {user_data.get_gender()}
    - Вес: {user_data.weight} кг
    - Рост: {user_data.height} см"""
    
    # Данные сна
    sleep_info = f"""Мои параметры сна за последний день:
    - Продолжительность сна: {sleep_record.duration} минут
    - Глубокий сон: {sleep_record.sleep_deep_duration} минут
    - Легкий сон: {sleep_record.sleep_light_duration} минут
    - Эффективность сна: {sleep_statistics.sleep_efficiency}%
    - Индекс фрагментации сна: {sleep_statistics.sleep_fragmentation_index}
    - Время засыпания: {sleep_statistics.latency_minutes} минут
    - Калории сожжённые во сне: {sleep_statistics.sleep_calories_burned} ккал"""
    
    # Добавляем REM-сон если есть данные
    if sleep_record.sleep_rem_duration and sleep_record.sleep_rem_duration > 0:
        sleep_info += f"\n- REM-сон: {sleep_record.sleep_rem_duration} минут"
    
    # Добавляем пульс если есть данные
    if sleep_record.avg_hr:
        sleep_info += f"\n- Средний пульс: {sleep_record.avg_hr} уд/мин"
    if sleep_record.min_hr:
        sleep_info += f"\n- Минимальный пульс: {sleep_record.min_hr} уд/мин"
    if sleep_record.max_hr:
        sleep_info += f"\n- Максимальный пульс: {sleep_record.max_hr} уд/мин"
    if sleep_record.awake_count:
        sleep_info += f"\n- Количество пробуждений: {sleep_record.awake_count}"
    
    prompt = f"""
    {user_info}

    {sleep_info}

    Внимательно проанализируй мою запись сна, учитывая все мои показатели. Дай конкретные советы, как улучшить мой сон.
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
