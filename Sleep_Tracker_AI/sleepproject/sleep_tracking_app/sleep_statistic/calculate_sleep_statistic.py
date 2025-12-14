from datetime import datetime, timedelta, time
import numpy as np
from ..models import SleepRecord, User
from .num_to_str import interpret_chronotype


def calculate_calories_burned(gender: int, weight: float, height: int, age: np.float64,
                              sleep_duration: int) -> float:
    # Расчёт BMR (Basal Metabolic Rate) по формуле Миффлина-Джеора
    bmr = 10 * weight + 6.25 * height - 5 * age / 12 + 5 if gender else 10 * weight + 6.25 * height - 5 * age / 12 - 161

    calories_burned = (bmr * (
            int(sleep_duration) / 60)) / 24  # round((bmr / 24 ) * 0.85 * float(sleep_duration / 60), 1)
    return round(calories_burned, 1)


def evaluate_bedtime(sleep_data: SleepRecord) -> datetime:
    if sleep_data.device_bedtime <= sleep_data.bedtime:
        return sleep_data.device_bedtime
    return sleep_data.bedtime


def evaluate_wake_time(sleep_data: SleepRecord) -> datetime:
    if sleep_data.device_wake_up_time >= sleep_data.wake_up_time:
        return sleep_data.device_wake_up_time
    return sleep_data.wake_up_time


def chronotype_assessment(sleep_records: list ) -> dict:
    """
    Если sleep_records передан — используется он, иначе делаем fallback на запрос.
    """

    if not sleep_records:
        return {}

    free_midpoints = []
    all_midpoints = []
    free_durations = []
    all_durations = []

    for record in sleep_records:
        total_bedtime = evaluate_bedtime(record)  # не делает SQL, должен использовать поля record
        midpoint = total_bedtime + timedelta(minutes=(record.duration or 0) / 2)
        midpoint_hour = midpoint.hour + midpoint.minute / 60 + midpoint.second / 3600
        all_midpoints.append(midpoint_hour)
        all_durations.append((record.duration or 0) / 60)
        if total_bedtime.weekday() >= 5:
            free_midpoints.append(midpoint_hour)
            free_durations.append((record.duration or 0) / 60)

    # защитные проверки: длина массивов
    if not free_midpoints:
        return {}

    msf = float(np.mean(np.array(free_midpoints)))
    sd_free = float(np.mean(np.array(free_durations))) if free_durations else 0
    sd_week = float(np.mean(np.array(all_durations))) if all_durations else 0

    msf_sc = msf - 0.5 * (sd_free - sd_week)
    msf_sc_hours = int(msf_sc)
    msf_sc_minutes = int((msf_sc % 1) * 60)
    interpret_str = interpret_chronotype(msf_time=time(hour=msf_sc_hours, minute=msf_sc_minutes),
                                         name="sleep_statistic", language="ru")

    key = interpret_str.keys()

    match key:
        case key if 'skylark' in key:
            interpret_str['img'] = 'skylark.png'
        case key if 'pigeon' in key:
            interpret_str['img'] = 'pigeon.png'
        case key if 'owl' in key:
            interpret_str['img'] = 'owl.png'
        case _:
            interpret_str['img'] = None

    return interpret_str


def calculate_cycle_count(sleep_data: SleepRecord) -> int:
    """
    Количество циклов сна в последней записи сна пользователя.
    Цикл считается завершённым, если он длится более 90 минут и содержит как минимум одну фазу глубокого и REM сна.
    1 цикл = 90 минут (минимум) + глубокий сон + REM
    Если цикл не завершён, то он не учитывается.
    """

    # Находим последнюю запись сна для пользователя
    segments = sleep_data.segments.order_by('start_time')
    cycle_count = 0
    current_cycle_duration = 0
    has_deep = False
    has_rem = False
    for i, seg in enumerate(segments):
        duration_min = (seg['end_time'] - seg['start_time']).total_seconds() / 60
        if seg['state'] in [2, 3, 4]:  # Light, Deep, REM
            current_cycle_duration += duration_min
            if seg['state'] == 3:
                has_deep = True
            if seg['state'] == 4:
                has_rem = True
        if seg['state'] == 5 or i == len(segments) - 1:  # Awake or end
            if current_cycle_duration >= 90 and has_deep and has_rem:
                cycle_count += 1
            current_cycle_duration = 0
            has_deep = False
            has_rem = False
    return cycle_count


def time_to_minutes(dt, ref_hour=20):
    """
    Преобразует время в минуты от 00:00, нормализуя относительно заданного референсного часа (по умолчанию 20:00).
    """

    if not dt:
        return None
    # Извлекаем часы и минуты
    hours = dt.hour
    minutes = dt.minute
    # Преобразуем в минуты от 00:00
    total_minutes = hours * 60 + minutes
    # Нормализуем относительно ref_hour (20:00), чтобы учесть переход через полночь
    ref_minutes = ref_hour * 60
    normalized_minutes = (total_minutes - ref_minutes) % 1440  # 1440 минут = 24 часа
    return normalized_minutes


def sleep_regularity(sleep_records: list ) -> dict:

    if not sleep_records:
        return {}
    bedtimes = [time_to_minutes(r.bedtime) for r in sleep_records if r.bedtime]
    wake_times = [time_to_minutes(r.wake_up_time) for r in sleep_records if r.wake_up_time]

    bedtime_std = round(float(np.std(bedtimes)), 2) if len(bedtimes) >= 2 else 0
    wake_time_std = round(float(np.std(wake_times)), 2) if len(wake_times) >= 2 else 0

    return {'bedtime_std': bedtime_std, 'wake_time_std': wake_time_std}




def calculate_sleep_statistics_metrics(sleep_data: SleepRecord, age: np.float64, gender: int, weight: float,
                                       height: int) -> dict:
    """
    Вычисляет основные метрики сна на основе последней записи сна пользователя.
    Возвращает словарь с метриками:
    - latency_minutes: Латентность сна в минутах
    - sleep_efficiency: Эффективность сна в процентах
    - sleep_phases: Процент каждой фазы сна (глубокий, легкий, REM, бодрствование)
    - sleep_fragmentation_index: Индекс фрагментации сна
    - sleep_calories_burned: Сожжённые калории во время сна (на основе BMR)
    """
    if not sleep_data:
        return {}

    total_bedtime = evaluate_bedtime(sleep_data)
    total_wake_time = evaluate_wake_time(sleep_data)

    # Латентность сна в минутах
    latency_delta = sleep_data.segments.order_by('start_time').values_list('start_time',
                                                                           flat=True).first() - total_bedtime
    latency_minutes = latency_delta.total_seconds() / 60 if latency_delta else 0

    # Эффективность сна
    total_time_in_bed_min = (total_wake_time - total_bedtime).total_seconds() / 60
    sleep_efficiency = sleep_data.duration * 100 / total_time_in_bed_min if total_time_in_bed_min else 0

    # Процент каждой фазы сна
    sleep_phases = {
        'deep': sleep_data.sleep_deep_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'light': sleep_data.sleep_light_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'rem': sleep_data.sleep_rem_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'awake': sleep_data.sleep_awake_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
    }

    # Индекс фрагментации сна
    interpret_fragmentation = (sleep_data.awake_count / (sleep_data.duration / 60)) if sleep_data.duration else 0

    # Сожжённые калории во время сна (на основе BMR)
    sleep_calories_burned = calculate_calories_burned(gender=gender, weight=weight, height=height, age=age,
                                                      sleep_duration=sleep_data.duration)

    return {
        'latency_minutes': latency_minutes,
        'sleep_efficiency': sleep_efficiency,
        'sleep_phases': sleep_phases,
        'sleep_fragmentation_index': interpret_fragmentation,
        'sleep_calories_burned': sleep_calories_burned,
    }


def avg_sleep_duration(items: list):
    """
    Средняя продолжительность сна за последние N дней.
    items: список объектов SleepStatistics
    """

    durations = [r.duration for r in items if r.duration]
    if durations:
        return round(np.mean(durations) / 60, 2)
    return 0
