import json
import pandas as pd
from celery_progress.backend import ProgressRecorder
from typing import Tuple

def convert_to_readable_time(list_of_unix_timestamps: list, df_column: pd.DataFrame) -> None:
    """Преобразует UNIX-метку времени в читаемый формат."""
    for col in list_of_unix_timestamps:
        if col in df_column.columns:
            df_column[col] = pd.to_datetime(df_column[col].astype(int), unit='s', utc=True).dt.tz_convert(
                'UTC').dt.strftime('%Y-%m-%d %H:%M:%S%z')


def mask_night(heart_idx: pd.Index, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    """
    Создает маску для фильтрации сердечного ритма по ночным интервалам
    """

    if start < end:
        return (heart_idx >= start) & (heart_idx < end)
    else:
        return (heart_idx >= start) | (heart_idx < end)


def sleep_record_from_csv(sleep_data: pd.DataFrame, progress_recorder: ProgressRecorder = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Извлекает данные из CSV-файла, фильтруя записи сна и ночной сердечный ритм
    Возвращает кортеж (meta, items, night_hr, df_day) или None, если данные невалидны
    """
    # Проверяем наличие обязательных колонок
    required_columns = ['Key', 'Time', 'Value']
    if not all(col in sleep_data.columns for col in required_columns):
        return None

    # Проверяем наличие хотя бы одной записи сна с валидным JSON
    sleep_entries = sleep_data[sleep_data['Key'] == 'sleep']
    if sleep_entries.empty:
        return None

    # Проверяем, что хотя бы одна запись имеет валидный JSON с items
    has_valid_sleep = False
    for value in sleep_entries['Value'].head(5):  # Проверяем только первые 5 записей
        try:
            data = json.loads(value)
            if isinstance(data, dict) and 'items' in data and data.get('version') == 2 and data.get('has_stage'):
                has_valid_sleep = True
                break
        except (json.JSONDecodeError, AttributeError):
            continue

    if not has_valid_sleep:
        return None

    total_steps = 9

    # Разделяем на sleep и heart_rate
    df_sleep = sleep_data[sleep_data['Key'] == 'sleep'].copy()
    df_hr = sleep_data[sleep_data['Key'] == 'heart_rate'].copy()
    progress_recorder.set_progress(1, total_steps)

    # Преобразуем JSON в столбцы
    df_sleep['json'] = df_sleep['Value'].apply(json.loads)
    # Оставляем только version==2 и непустые items (has_stage как флаг, что есть стадии сна)
    valid_sleep = df_sleep['json'].apply(lambda d: d.get('version') == 2 and d.get('has_stage'))
    df_sleep = df_sleep[valid_sleep]
    progress_recorder.set_progress(2, total_steps)

    # Конвертируем Time в datetime
    df_sleep['Time_dt'] = (
        pd.to_datetime(df_sleep['Time'].astype(int), unit='s', utc=True)
        .dt.tz_convert('UTC')
    )
    progress_recorder.set_progress(3, total_steps)

    # Метаданные
    df_meta = pd.json_normalize(df_sleep['json'])
    df_meta = df_meta.drop(columns=['items', 'version', 'timezone', 'has_stage'])
    df_meta.index = df_sleep['Time_dt']
    df_meta.index.name = 'Time'
    progress_recorder.set_progress(4, total_steps)

    # Разворачиваем список items
    df_sleep['items_list'] = df_sleep['json'].apply(lambda d: d['items'])
    df_items_exp = df_sleep.explode('items_list')
    # Нормализуем вложенные словари
    df_items = pd.json_normalize(df_items_exp['items_list'])
    # Индексируем по тому же времени
    df_items.index = df_items_exp['Time_dt']
    df_items.index.name = 'Time'
    progress_recorder.set_progress(5, total_steps)

    # Пульс
    df_hr['json'] = df_hr['Value'].apply(json.loads)
    df_heart = pd.json_normalize(df_hr['json'])
    df_heart.index = pd.to_datetime(df_heart['time'], unit='s', utc=True).dt.tz_convert('UTC')
    df_heart.index.name = 'Time'
    df_heart = df_heart.drop(columns=['time'])
    progress_recorder.set_progress(6, total_steps)

    # Разделение на ночь
    # Интервалы из метаданных
    intervals = pd.DataFrame({
        'start': pd.to_datetime(df_meta['device_bedtime'], unit='s', utc=True).dt.tz_convert('UTC'),
        'end': pd.to_datetime(df_meta['device_wake_up_time'], unit='s', utc=True).dt.tz_convert('UTC')
    }, index=df_meta.index)
    progress_recorder.set_progress(7, total_steps)

    night_parts = []
    for idx, row in intervals.iterrows():
        mask = mask_night(df_heart.index, row['start'], row['end'])
        night_parts.append(df_heart[mask])

    df_night = pd.concat(night_parts)
    progress_recorder.set_progress(8, total_steps)
    # df_day = df_heart.drop(df_night.index)

    # Преобразование времени к строкам с сохранением информации о временной зоне
    df_meta.index = df_meta.index.strftime('%Y-%m-%d %H:%M:%S%z')
    df_items.index = df_items.index.strftime('%Y-%m-%d %H:%M:%S%z')
    df_night.index = df_night.index.strftime('%Y-%m-%d %H:%M:%S%z')
    # df_day.index = df_day.index.strftime('%Y-%m-%d %H:%M:%S%z')

    list_item_time = [c for c in df_items.columns if 'time' in c]
    list_meta_time = [c for c in df_meta.columns if 'time' in c]

    convert_to_readable_time(list_item_time, df_items)
    convert_to_readable_time(list_meta_time, df_meta)
    progress_recorder.set_progress(9, total_steps)

    return df_meta, df_items, df_night


def main():
    csv_file_path = "F:/Pasha/Courses/Web-sleep-app/dataset/hlth_center_fitness_data.csv"
    df = pd.read_csv(csv_file_path, delimiter=',', encoding='utf-8')


    meta, items, night_hr = sleep_record_from_csv(df)



if __name__ == "__main__": main()
