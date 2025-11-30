import random
from datetime import datetime, timedelta
from models import UserData, SleepRecord, SleepStatistics
from baselinetest import get_sleep_recommendation


def random_date(years_ago=30):
    """Генерация случайной даты рождения"""
    today = datetime.now()
    delta_days = random.randint(0, 365 * years_ago)
    return today - timedelta(days=delta_days)

def build_test_case(
    description,
    duration,
    deep,
    light,
    rem,
    latency,
    efficiency,
    fragmentation,
    calories,
    avg_hr=None,
    min_hr=None,
    max_hr=None,
    awakenings=None
):
    user = UserData(
        date_of_birth=random_date(),
        weight=random.randint(55, 110),
        gender=random.choice([0,1]),
        height=random.randint(155, 195),
        active=False
    )
    
    record = SleepRecord(
        sleep_date_time=datetime.now() - timedelta(hours=8),
        duration=duration,
        sleep_deep_duration=deep,
        sleep_light_duration=light,
        sleep_rem_duration=rem,
        has_rem=(rem is not None and rem > 0),
        avg_hr=avg_hr,
        min_hr=min_hr,
        max_hr=max_hr,
        awake_count=awakenings
    )
    
    stats = SleepStatistics(
        latency_minutes=latency,
        sleep_efficiency=efficiency,
        sleep_fragmentation_index=fragmentation,
        sleep_calories_burned=calories
    )
    
    return {
        "description": description,
        "user": user,
        "record": record,
        "stats": stats
    }


test_cases = [
    build_test_case(
        "Идеальная ночь — хороший непрерывный сон",
        duration=480, deep=120, light=280, rem=80,
        latency=10, efficiency=95, fragmentation=5, calories=420,
        avg_hr=58, min_hr=50, max_hr=75, awakenings=1
    ),

    build_test_case(
        "Короткий сон — 4 часа",
        duration=240, deep=60, light=150, rem=30,
        latency=25, efficiency=75, fragmentation=18, calories=280,
        avg_hr=62, min_hr=55, max_hr=85, awakenings=3
    ),

    build_test_case(
        "Очень фрагментированный сон",
        duration=390, deep=70, light=200, rem=40,
        latency=30, efficiency=70, fragmentation=35, calories=350,
        avg_hr=68, min_hr=55, max_hr=95, awakenings=8
    ),

    build_test_case(
        "Высокий пульс ночью — возможный стресс",
        duration=420, deep=90, light=260, rem=70,
        latency=15, efficiency=90, fragmentation=10, calories=500,
        avg_hr=88, min_hr=70, max_hr=120, awakenings=2
    ),

    build_test_case(
        "Мало глубокого сна — стресс/перегрузка",
        duration=450, deep=30, light=350, rem=70,
        latency=20, efficiency=85, fragmentation=15, calories=400,
        avg_hr=65, min_hr=50, max_hr=95, awakenings=5
    ),

    build_test_case(
        "Долгое засыпание (>45 мин)",
        duration=460, deep=100, light=280, rem=80,
        latency=55, efficiency=80, fragmentation=20, calories=460,
        avg_hr=60, min_hr=50, max_hr=80, awakenings=4
    ),

    build_test_case(
        "Очень низкая эффективность сна (≤60%)",
        duration=400, deep=50, light=200, rem=40,
        latency=35, efficiency=58, fragmentation=40, calories=310,
        avg_hr=70, min_hr=55, max_hr=100, awakenings=10
    ),

    build_test_case(
        "Почти нет REM — возможно переутомление",
        duration=470, deep=140, light=310, rem=10,
        latency=12, efficiency=88, fragmentation=12, calories=450,
        avg_hr=63, min_hr=52, max_hr=90, awakenings=3
    ),

    build_test_case(
        "Много пробуждений — плохая гигиена сна",
        duration=440, deep=90, light=250, rem=100,
        latency=18, efficiency=82, fragmentation=30, calories=420,
        avg_hr=67, min_hr=55, max_hr=100, awakenings=12
    ),

    build_test_case(
        "Очень длительный сон — 10+ часов",
        duration=620, deep=130, light=360, rem=130,
        latency=10, efficiency=92, fragmentation=8, calories=550,
        avg_hr=57, min_hr=49, max_hr=85, awakenings=2
    ),
]

len(test_cases)


results = []

for i, case in enumerate(test_cases, 1):
    print(f"\n=== ТЕСТ {i}: {case['description']} ===")
    
    response = get_sleep_recommendation(
        case["user"],
        case["stats"],
        case["record"]
    )
    
    results.append({
        "description": case["description"],
        "response": response
    })
    
    print(response)
