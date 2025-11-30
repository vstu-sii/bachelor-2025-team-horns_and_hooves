import os
from google import genai
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta

# Импортируем ваши существующие модели и промпты
from models import UserData, SleepStatistics, SleepRecord
from prompt_templates import create_sleep_analysis_prompt, get_system_prompt

# Загрузка переменных окружения
load_dotenv(find_dotenv())

# Инициализация клиента Gemini
client = genai.Client()

def get_sleep_recommendation(user_data: UserData, sleep_statistics: SleepStatistics, sleep_record: SleepRecord) -> str:
    """
    Основная функция для получения рекомендаций по сну через Gemini API
    """
    try:
        # Создаем промпт на основе данных (используем вашу существующую функцию)
        user_prompt = create_sleep_analysis_prompt(user_data, sleep_statistics, sleep_record)
        system_prompt = get_system_prompt()
        
        # Объединяем системный и пользовательский промпты
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Вызов API Gemini с использованием новой библиотеки
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Рабочая модель
            contents=full_prompt
        )
        
        return response.text
        
    except Exception as e:
        print(f"Ошибка при вызове Gemini API: {e}")
        return "В настоящее время я не могу обработать ваш запрос. Пожалуйста, попробуйте позже."

def main():
    """
    Тестирование Gemini API на трех различных примерах сна
    """
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ GEMINI API ДЛЯ АНАЛИЗА СНА")
    print("=" * 60)
    
    # Проверяем API ключ
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ ОШИБКА: GEMINI_API_KEY не установлен")
        print("Добавьте GEMINI_API_KEY=your_key_here в файл .env")
        return
    
    print("✅ API ключ найден")
    
    # Пример 1: Хороший сон (оптимальные показатели)
    print("\n1. ТЕСТ: ХОРОШИЙ СОН")
    print("-" * 40)
    print("Параметры: 8 часов сна, эффективность 95%, оптимальные фазы")
    
    user_data_good = UserData(
        date_of_birth=datetime.now() - timedelta(days=365*30),  # 30 лет
        weight=70,
        gender=1,  # Мужской
        height=175,
        active=True
    )
    
    sleep_stats_good = SleepStatistics(
        sleep_efficiency=95.0,
        latency_minutes=8.0,
        sleep_fragmentation_index=5.0,
        sleep_calories_burned=450.0
    )
    
    sleep_record_good = SleepRecord(
        sleep_date_time=datetime.now(),
        duration=480,  # 8 часов
        sleep_deep_duration=120,  # 2 часа
        sleep_light_duration=300,  # 5 часов
        sleep_rem_duration=60,     # 1 час
        has_rem=True,
        avg_hr=55.0,
        min_hr=48,
        max_hr=65,
        awake_count=1
    )
    
    print("⏳ Отправка запроса к Gemini API...")
    recommendation_good = get_sleep_recommendation(user_data_good, sleep_stats_good, sleep_record_good)
    print("✅ РЕКОМЕНДАЦИЯ:")
    print(recommendation_good)
    print("-" * 50)
    
    # Пример 2: Плохой сон (проблемы с эффективностью и фрагментацией)
    print("\n2. ТЕСТ: ПЛОХОЙ СОН")  
    print("-" * 40)
    print("Параметры: 5 часов сна, эффективность 65%, высокая фрагментация")
    
    user_data_bad = UserData(
        date_of_birth=datetime.now() - timedelta(days=365*35),  # 35 лет
        weight=85,
        gender=0,  # Женский
        height=165,
        active=False
    )
    
    sleep_stats_bad = SleepStatistics(
        sleep_efficiency=65.0,
        latency_minutes=45.0,
        sleep_fragmentation_index=28.0,
        sleep_calories_burned=380.0
    )
    
    sleep_record_bad = SleepRecord(
        sleep_date_time=datetime.now(),
        duration=300,  # 5 часов
        sleep_deep_duration=45,   # 45 минут
        sleep_light_duration=240, # 4 часа
        sleep_rem_duration=15,    # 15 минут
        has_rem=True,
        avg_hr=72.0,
        min_hr=58,
        max_hr=85,
        awake_count=5,
        sleep_awake_duration=45
    )
    
    print("⏳ Отправка запроса к Gemini API...")
    recommendation_bad = get_sleep_recommendation(user_data_bad, sleep_stats_bad, sleep_record_bad)
    print("✅ РЕКОМЕНДАЦИЯ:")
    print(recommendation_bad)
    print("-" * 50)
    
    # Пример 3: Средний сон с проблемами засыпания
    print("\n3. ТЕСТ: СРЕДНИЙ СОН С ПРОБЛЕМАМИ ЗАСЫПАНИЯ")
    print("-" * 40)
    print("Параметры: 7 часов сна, долгое засыпание (35 минут)")
    
    user_data_avg = UserData(
        date_of_birth=datetime.now() - timedelta(days=365*28),  # 28 лет
        weight=65,
        gender=1,  # Мужской
        height=180,
        active=True
    )
    
    sleep_stats_avg = SleepStatistics(
        sleep_efficiency=82.0,
        latency_minutes=35.0,  # Долгое засыпание
        sleep_fragmentation_index=15.0,
        sleep_calories_burned=420.0
    )
    
    sleep_record_avg = SleepRecord(
        sleep_date_time=datetime.now(),
        duration=420,  # 7 часов
        sleep_deep_duration=90,   # 1.5 часа
        sleep_light_duration=285, # 4.75 часа
        sleep_rem_duration=45,    # 45 минут
        has_rem=True,
        avg_hr=62.0,
        min_hr=52,
        max_hr=75,
        awake_count=2
    )
    
    print("⏳ Отправка запроса к Gemini API...")
    recommendation_avg = get_sleep_recommendation(user_data_avg, sleep_stats_avg, sleep_record_avg)
    print("✅ РЕКОМЕНДАЦИЯ:")
    print(recommendation_avg)
    print("-" * 50)
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    main()
