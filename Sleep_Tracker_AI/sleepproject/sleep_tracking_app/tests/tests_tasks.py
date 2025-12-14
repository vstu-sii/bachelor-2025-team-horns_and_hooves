from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from sleep_tracking_app.models import UserData, SleepRecord, SleepStatistics
from sleep_tracking_app.tasks import sleep_recommended


User = get_user_model()


class TasksTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tasker',
            password='pass12345',
            email='t@e.com'
        )
        self.user_data = UserData.objects.create(
            user=self.user,
            date_of_birth=date(1990, 1, 1),
            weight=70,
            gender=1,
            height=175
        )

        from django.utils import timezone

        self.record = SleepRecord.objects.create(
            user=self.user,
            sleep_date_time=timezone.now(),
            duration=420,
            sleep_rem_duration=30,
            sleep_deep_duration=90,
            sleep_light_duration=300,
        )

        self.stat = SleepStatistics.objects.create(
            user=self.user,
            date=self.record.sleep_date_time.date(),
            latency_minutes=10,
            sleep_efficiency=95.0,
            sleep_phases={'deep': 90},
            sleep_fragmentation_index=0.1,
            sleep_calories_burned=200
        )

    @patch('sleep_tracking_app.tasks.RagService')
    @patch('sleep_tracking_app.tasks.call_gemini')
    @patch('sleep_tracking_app.tasks.create_sleep_analysis_prompt')
    @patch('sleep_tracking_app.tasks.get_system_prompt')
    def test_sleep_recommended_updates_sleepstatistics(
            self,
            mock_get_system_prompt,
            mock_create_prompt,
            mock_call_gemini,
            mock_rag_service_cls,
    ):
        # Делаем промпты детерминированными
        mock_get_system_prompt.return_value = "SYS"
        mock_create_prompt.return_value = "USER"

        # Gemini вернул черновик
        mock_call_gemini.return_value = "Gemini draft"

        # RAG улучшил ответ
        rag_instance = mock_rag_service_cls.return_value
        rag_instance.enhance.return_value = {"enhanced": "Final recommendation"}

        rec = sleep_recommended(
            self.user_data.id,
            [self.record.id],
            [self.stat.id],
        )

        self.assertEqual(rec, "Final recommendation")

        self.stat.refresh_from_db()
        self.assertEqual(self.stat.recommended, "Final recommendation")

        # Проверяем, что Gemini вызван с ожидаемым full_prompt
        mock_call_gemini.assert_called_once_with("SYS\n\nUSER")

        # Проверяем, что enhance вызван с gemini_response и корректным user_data_dict
        expected_user_data_dict = {
            "age_months": self.user_data.get_age_months(),
            "gender": self.user_data.get_gender(),
            "weight": self.user_data.weight,
            "height": self.user_data.height,
        }
        rag_instance.enhance.assert_called_once_with("Gemini draft", expected_user_data_dict)
