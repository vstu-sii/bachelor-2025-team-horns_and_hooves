from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.db.models import QuerySet

import numpy as np

# Create your models here.
class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_data')
    date_of_birth = models.DateField()
    weight = models.FloatField(validators=[MinValueValidator(10)])  # Вес в кг
    gender = models.PositiveSmallIntegerField(
        choices=(
            (0, 'Женский'),
            (1, 'Мужской'),
        ),
        default=0,
    )  # Пол: 0 – женщина, 1 – мужчина
    height = models.PositiveSmallIntegerField(validators=[MinValueValidator(10)])  # Рост в см

    active = models.BooleanField(default=False)

    def get_age_months(self)->np.float64:
        """
        Возвращает возраст пользователя в месяцах на основе даты рождения.
        """

        date_current = timezone.now().date()
        age = np.float64((date_current.year - self.date_of_birth.year) * 12 + (
                date_current.month - self.date_of_birth.month))
        return age

    def get_gender(self) ->str:
        return 'Женский ' if self.gender == 0 else 'Мужской'


class SleepRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sleep_date_time = models.DateTimeField(db_index=True)  # дата фиксации сна в БД

    sleep_rem_duration = models.PositiveSmallIntegerField(null=True, blank=True,
                                                          validators=[MinValueValidator(0), MaxValueValidator(
                                                              1440)])  # в минутах продолжительность REM-сна

    has_rem = models.BooleanField(default=False)  # есть ли REM-сон в записи

    min_hr = models.PositiveSmallIntegerField(null=True, blank=True)  # минимальный пульс за время сна

    device_bedtime = models.DateTimeField(null=True, blank=True)  # время, когда устройство зафиксировало начало сна

    sleep_deep_duration = models.PositiveSmallIntegerField(null=True, blank=True,
                                                           validators=[MinValueValidator(0), MaxValueValidator(
                                                               1440)])  # в минутах продолжительность глубокой фазы сна

    wake_up_time = models.DateTimeField(null=True, blank=True)  # время пробуждения по данным устройства

    bedtime = models.DateTimeField(null=True,
                                   blank=True)  # время, когда пользователь лег спать (может отличаться от device_bedtime)

    awake_count = models.PositiveSmallIntegerField(null=True, blank=True)  # количество пробуждений за ночь

    duration = models.PositiveSmallIntegerField(null=True,
                                                blank=True)  # в минутах время сна, включая все фазы (глубокий, легкий, REM)

    max_hr = models.PositiveSmallIntegerField(null=True, blank=True)  # максимальный пульс за время сна

    sleep_awake_duration = models.PositiveSmallIntegerField(null=True,
                                                            blank=True)  # в минутах общая продолжительность пробуждений за время сна

    avg_hr = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # средний пульс за время сна

    sleep_light_duration = models.PositiveSmallIntegerField(null=True, blank=True,
                                                            validators=[MinValueValidator(0),
                                                                        MaxValueValidator(
                                                                            1440)])  # в минутах продолжительность легкой фазы сна

    device_wake_up_time = models.DateTimeField(null=True,
                                               blank=True)  # время, когда устройство зафиксировало пробуждение (может отличаться от wake_up_time)

    total_time_bed = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2,
                                         validators=[MinValueValidator(0),
                                                     MaxValueValidator(1440)])  # Убрать везде (устарело)

    class Meta:
        unique_together = ('user', 'sleep_date_time')
        indexes = [
            models.Index(fields=['user', 'sleep_date_time']),
        ]

    @classmethod
    def get_last_sleep_records(cls, user) -> QuerySet:
        """
        Возвращает записи сна пользователя за последние `days` дней
        относительно самой последней записи (по sleep_date_time).
        """

        return cls.objects.filter(user=user).only('sleep_date_time', 'id','device_bedtime','duration', 'bedtime', 'wake_up_time', 'night_hr_entries').order_by('-sleep_date_time')[:7]

    @classmethod
    def get_delta_days_sleep_records(cls, user: User) -> QuerySet:
        """
        Возвращает QuerySet записей SleepRecords для пользователя,
        упорядоченных от самой последней к самой ранней
        """

        return cls.objects.filter(user=user).order_by('-sleep_date_time', 'id')


"""class DayHeartRateEntry(models.Model):
    record = models.ForeignKey(SleepRecord, on_delete=models.CASCADE, related_name='day_hr_entries')
    time = models.DateTimeField()
    bpm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(300)])
"""


class NightHeartRateEntry(models.Model):
    record = models.ForeignKey(SleepRecord, on_delete=models.CASCADE, related_name='night_hr_entries')
    time = models.DateTimeField()
    bpm = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(300)])


class SleepSegment(models.Model):
    record = models.ForeignKey(SleepRecord, on_delete=models.CASCADE, related_name='segments')
    start_time = models.DateTimeField()  # время начала сегмента сна
    end_time = models.DateTimeField()  # время окончания сегмента сна
    state = models.PositiveSmallIntegerField(choices=(
        (2, 'Light'),
        (3, 'Deep'),
        (4, 'REM'),
        (5, 'Awake'),
    ))  # тип сегмента сна


class SleepStatistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    latency_minutes = models.FloatField(null=True, blank=True)  # Латентность сна в минутах
    sleep_efficiency = models.FloatField(null=True, blank=True)  # Эффективность сна в процентах
    sleep_phases = models.JSONField(null=True,
                                    blank=True)  # Процент каждой фазы сна (глубокий, легкий, REM, бодрствование)
    sleep_fragmentation_index = models.FloatField(null=True, blank=True)  # Индекс фрагментации сна
    sleep_calories_burned = models.FloatField(null=True, blank=True)  # Сожжённые калории во время сна (на основе BMR)
    date = models.DateField(db_index=True)  # Дата, к которой относятся эти данные

    recommended = models.TextField(null=True, blank=True)  # Рекомендовано ли пользователю улучшение сна



    sleep_duration = models.PositiveSmallIntegerField(null=True,
                                                      blank=True)  # deep_sleep_duration + fast_sleep_duration
    sleep_quality = models.FloatField(null=True, blank=True)  # Это поле генерируется на основании данных пользователя
    health_impact = models.CharField(null=True, blank=True,
                                     max_length=255)  # краткая сводка которая основывается на полученных результатах

    calories_burned = models.FloatField(null=True, blank=True)  # сожженные калории во сне

    class Meta:
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    @classmethod
    def get_last_sleep_statistics(cls, user: User) -> "SleepStatistics | None":
        """
        Возвращает статистику пользователя за последний день
        """

        last = cls.objects.filter(user=user).order_by('-date').first()

        return last

    @classmethod
    def get_delta_days_sleep_statistics(cls, user: User) -> QuerySet:
        """
        Возвращает QuerySet записей SleepStatistics для пользователя,
        упорядоченных от самой последней к самой ранней
        """

        return cls.objects.filter(user=user).order_by('-date', 'id')

