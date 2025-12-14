from typing import List

from celery import shared_task
import pandas as pd
import os

from celery_progress.backend import ProgressRecorder
from django.contrib.auth.models import User

from sleepproject.celery import app  # Фоновая задача

from django.core.mail import send_mass_mail
from django.db import transaction

from .csv_data_extraction import sleep_record_from_csv
from .models import SleepRecord, SleepSegment, NightHeartRateEntry, SleepStatistics, UserData

from .sleep_statistic import calculate_sleep_statistics_metrics
from .prompts import get_sleep_recommendation

from sleep_tracking_app.rag.rag_service import RagService
from sleep_tracking_app.prompts.baseline import call_gemini
from sleep_tracking_app.prompts.prompts_templates import create_sleep_analysis_prompt, get_system_prompt
from sleep_tracking_app.models import UserData, SleepRecord, SleepStatistics

@shared_task(bind=True, name='import_sleep_records_task')
def import_sleep_records(self, user_id: int, csv_path: str):
    progress_recorder = ProgressRecorder(self)

    user = User.objects.get(pk=user_id)
    user_data = UserData.objects.get(user=user)
    # Считаем CSV прямо по пути
    df = pd.read_csv(csv_path, encoding='utf-8')
    sleep_data = sleep_record_from_csv(df, progress_recorder)

    if sleep_data is None:
        os.remove(csv_path)
        return {"status": "error", "message": "Invalid CSV file"}

    meta, items, night_hr = sleep_data
    total = len(meta)
    processed = 0

    # Получаем данные пользователя
    age = user_data.get_age_months()
    gender = user_data.gender
    weight = user_data.weight
    height = user_data.height

    with transaction.atomic():
        # Создаём или обновляем базовые записи сна и собираем их в словарь
        record_map = {}
        for sleep_time, meta_row in meta.iterrows():
            record, _ = SleepRecord.objects.update_or_create(
                user=user,
                sleep_date_time=sleep_time,
                defaults={
                    'sleep_rem_duration': meta_row.get('sleep_rem_duration'),
                    'has_rem': meta_row.get('has_rem'),
                    'min_hr': meta_row.get('min_hr'),
                    'device_bedtime': meta_row.get('device_bedtime'),
                    'sleep_deep_duration': meta_row.get('sleep_deep_duration'),
                    'wake_up_time': meta_row.get('wake_up_time'),
                    'bedtime': meta_row.get('bedtime'),
                    'awake_count': meta_row.get('awake_count'),
                    'duration': meta_row.get('duration'),
                    'max_hr': meta_row.get('max_hr'),
                    'sleep_awake_duration': meta_row.get('sleep_awake_duration'),
                    'avg_hr': meta_row.get('avg_hr'),
                    'sleep_light_duration': meta_row.get('sleep_light_duration'),
                    'device_wake_up_time': meta_row.get('device_wake_up_time'),
                }
            )
            record_map[sleep_time] = record

            processed += 1

            progress_recorder.set_progress(processed, total, f'Обработано: {processed}/{total}')

        # Удаляем старые дочерние объекты разом
        SleepSegment.objects.filter(record__in=record_map.values()).delete()
        NightHeartRateEntry.objects.filter(record__in=record_map.values()).delete()
        SleepStatistics.objects.filter(user=user).delete()

        # Подготавливаем объекты для bulk_create
        segments_to_create = []
        night_hr_to_create = []


        # --- подготавливаем сегменты сна ---
        for idx, seg in items.iterrows():
            record = record_map.get(idx)
            if record is None:
                continue
            segments_to_create.append(
                SleepSegment(
                    record=record,
                    start_time=seg['start_time'],
                    end_time=seg['end_time'],
                    state=seg['state']
                )
            )

        # --- подготавливаем пульс ---
        for record in record_map.values():
            # ночной пульс
            night_mask = (night_hr.index >= record.device_bedtime) & (
                    night_hr.index <= record.device_wake_up_time)
            night_df = night_hr[night_mask]
            night_hr_to_create.extend([
                NightHeartRateEntry(record=record, time=idx, bpm=row['bpm'])
                for idx, row in night_df.iterrows()
            ])

        # bulk insert
        SleepSegment.objects.bulk_create(segments_to_create, batch_size=1000)
        NightHeartRateEntry.objects.bulk_create(night_hr_to_create, batch_size=1000)

        # --- подготавливаем статистику сна ---
        sleep_statistic_to_create = []
        for record in record_map.values():
            record.refresh_from_db()
            stats  = calculate_sleep_statistics_metrics(record, age, gender, weight, height)

            sleep_statistic_to_create.append(
                SleepStatistics(
                    user=user,
                    date=record.sleep_date_time.date(),
                    latency_minutes=stats ['latency_minutes'],
                    sleep_efficiency=stats ['sleep_efficiency'],
                    sleep_phases=stats ['sleep_phases'],
                    sleep_fragmentation_index=stats ['sleep_fragmentation_index'],
                    sleep_calories_burned=stats ['sleep_calories_burned']
                )
            )

        # bulk insert
        SleepStatistics.objects.bulk_create(sleep_statistic_to_create, batch_size=1000)

    # transaction.atomic откатит изменения автоматически

    os.remove(csv_path)
    return {"status": "completed", "imported": processed}

@shared_task
def sleep_recommended(user_data_id: int, sleep_record_id: List[int], sleep_statistics_id:List[int]):
    user_data = UserData.objects.get(id=user_data_id)
    # Забираем записи сна и статистику одним запросом
    sleep_records_qs = SleepRecord.objects.only(
        'id', 'duration', 'sleep_rem_duration',
        'sleep_deep_duration', 'sleep_light_duration',
    ).filter(id__in=sleep_record_id)

    sleep_statistics_qs = SleepStatistics.objects.only(
        'id', 'sleep_efficiency', 'sleep_fragmentation_index',
        'latency_minutes', 'sleep_calories_burned', 'recommended',
    ).filter(id__in=sleep_statistics_id)

    sleep_records_map = {r.id: r for r in sleep_records_qs}
    sleep_statistics_map = {s.id: s for s in sleep_statistics_qs}

    # Сохраняем порядок такой же, как в списках id
    sleep_records_list = [sleep_records_map[i] for i in sleep_record_id if i in sleep_records_map]
    sleep_statistics_list = [sleep_statistics_map[i] for i in sleep_statistics_id if i in sleep_statistics_map]

    if not sleep_records_list or not sleep_statistics_list:
        return "Недостаточно данных для анализа сна."

     # Этап 1: Gemini (используем точно такой же промпт как раньше)
    system_prompt = get_system_prompt()
    user_prompt = create_sleep_analysis_prompt(user_data, sleep_statistics_list, sleep_records_list)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    gemini_response = call_gemini(full_prompt)
    if not gemini_response:
        return "Ошибка генерации рекомендаций."
    
    # Этап 2: RAG улучшение (Gemini → поиск статей → Mistral)
    rag_service = RagService()
    user_data_dict = {
        "age_months": user_data.get_age_months(),
        "gender": user_data.get_gender(),
        "weight": user_data.weight,
        "height": user_data.height
    }
    
    rag_result = rag_service.enhance(gemini_response, user_data_dict)
    final_recommendation = rag_result.get("enhanced", gemini_response)
    
    # Этап 3: Сохранение 
    latest_stat = sleep_statistics_list[0]
    latest_stat.recommended = final_recommendation
    
    """# сохраняем метаданные RAG для отладки
    rag_metadata = {
        "gemini_preview": gemini_response[:200],
        "rag_search_query": rag_result.get("search_query", ""),
        "rag_sources_count": len(rag_result.get("sources", [])),
        "mistral_used": bool(rag_result.get("enhanced"))
    }
    latest_stat.health_impact = json.dumps(rag_metadata)
    """
    latest_stat.save(update_fields=['recommended', 'health_impact'])    
    return latest_stat.recommended

@app.task
def send_reminder_email():
    # Получаем все активные напоминания, которые должны быть отправлены
    user = User.objects.filter(user_data__active=True)
    reminder_text = 'Уважаемый пользователь,\n\nМы надеемся, что наш сервис помогает вам лучше понять своё состояние сна. Чтобы обеспечить максимальную эффективность и точность данных, мы хотели бы напомнить вам о важности регулярного обновления информации в приложении.\nПожалуйста, не забывайте вносить данные о вашем сне ежедневно. Это поможет нам предоставить вам наиболее точные и полезные аналитические данные о вашем сне, что, в свою очередь, поможет вам лучше понять его влияние на ваше здоровье.\n\nМы ценим ваше участие в нашем проекте.\n\nС уважением,\nКоманда GoodSleepPro.'
    emails = list(user.values_list('email', flat=True))

    messages = [(
        'Напоминание о ежедневном заполнении данных о отслеживания качества сна',
        reminder_text,
        'goodsleeppro@yandex.ru',
        emails,
    )]

    # Отправляем все письма в одном запросе
    send_mass_mail(messages, fail_silently=False)
