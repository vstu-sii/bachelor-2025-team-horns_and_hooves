from django.db.models import QuerySet

from sleep_tracking_app.models import SleepRecord, SleepStatistics
from math import log


def get_sleep_phases_pie_data(stat: [SleepStatistics]) -> list:
    """
    Возвращает данные для круговых диаграмм фаз сна за последнюю ночь.
    Возвращает пустой список, если данных о фазах сна нет.
    """
    if not stat:
        return []

    phases = stat.sleep_phases

    def point(name, key):
        val = round(phases.get(key, 0), 2)
        size = round(log(max(1, val)), 2) * 5 if val > 0 else 0
        return {'name': name, 'y': val, 'z': size}

    if phases.get('rem', 0) == 0:
        return [
            point('Глубокий', 'deep'),
            point('Легкий', 'light'),
            point('Бодрствование', 'awake'),
        ]

    return [
        point('Глубокий', 'deep'),
        point('Легкий', 'light'),
        point('REM', 'rem'),
        point('Бодрствование', 'awake'),
    ]


def get_heart_rate_bell_curve_data(latest_sleep: SleepRecord) -> dict:
    """
    Возвращает данные для точечной диаграммы пульса за последнюю ночь.
    Возвращает пустой словарь, если данных о пульсе нет.
    """
    if not latest_sleep:
        return {'date': [], 'bpm': []}

    hr_entries = list(latest_sleep.night_hr_entries.all())

    if not hr_entries:
        return {'date': [], 'bpm': []}

    date = [e.time.strftime('%H:%M') for e in hr_entries]
    bpm = [e.bpm for e in hr_entries]

    return {'date': date, 'bpm': bpm}


def get_sleep_duration_trend(items: list) -> dict:
    """
    Тренд: sleep_duration
    columns: ['date', 'sleep_duration']
    Возвращает данные для линейного графика продолжительности сна за последние N дней.
    items: список объектов SleepStatistics
    """
    if not items:
        return { "dates": [], "sleep_duration": [] }

    dates = []
    durations = []
    for s in items:
        dates.append(s.sleep_date_time.strftime('%Y-%m-%d'))
        durations.append(s.duration)

    graph_data_dict = {
        "dates": dates,
        "sleep_duration": durations
    }
    return graph_data_dict


def get_sleep_efficiency_trend(items: list) -> dict:
    """
    Тренд: sleep_efficiency, latency_minutes, sleep_fragmentation_index, sleep_calories_burned
    columns: ['date', 'sleep_efficiency', 'latency_minutes', 'sleep_fragmentation_index', 'sleep_calories_burned']
    Возвращает пустой словарь, если данные отсутствуют.
    """
    if not items:
        return {}

    dates = []
    latency_list = []
    efficiency_list = []
    fragmentation_list = []
    calories_list = []

    for s in items:
        dates.append(s.date.isoformat())
        latency_list.append(round(s.latency_minutes, 2) if s.latency_minutes is not None else None)
        efficiency_list.append(round(s.sleep_efficiency, 2) if s.sleep_efficiency is not None else None)
        fragmentation_list.append(
            round(s.sleep_fragmentation_index, 2) if s.sleep_fragmentation_index is not None else None)
        calories_list.append(round(s.sleep_calories_burned, 2) if s.sleep_calories_burned is not None else None)

    graph_data_dict = {
        "dates": dates,
        "latency_minutes": latency_list,
        "sleep_efficiency": efficiency_list,
        "sleep_fragmentation_index": fragmentation_list,
        "sleep_calories_burned": calories_list,
    }
    return graph_data_dict
