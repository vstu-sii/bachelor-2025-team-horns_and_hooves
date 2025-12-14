from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from sleep_tracking_app.models import UserData, SleepRecord, SleepStatistics
from sleep_tracking_app.tasks import sleep_recommended


User = get_user_model()


class TasksTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tasker', password='pass12345', email='t@e.com')
        self.user_data = UserData.objects.create(user=self.user, date_of_birth='1990-01-01', weight=70, gender=1, height=175)
        from django.utils import timezone
        # sleep_date_time is required by the model (non-null), provide a timestamp
        self.record = SleepRecord.objects.create(
            user=self.user,
            sleep_date_time=timezone.now(),
            duration=420,
            sleep_rem_duration=30,
            sleep_deep_duration=90,
            sleep_light_duration=300,
        )
        self.stat = SleepStatistics.objects.create(user=self.user, date=self.record.sleep_date_time.date(), latency_minutes=10, sleep_efficiency=95.0, sleep_phases={'deep':90}, sleep_fragmentation_index=0.1, sleep_calories_burned=200)

    @patch('sleep_tracking_app.tasks.get_rec_to_prompt')
    def test_sleep_recommended_updates_sleepstatistics(self, mock_get):
        mock_get.return_value = 'Keep regular schedule and avoid caffeine.'
        # call task function directly
        rec = sleep_recommended(self.user_data.id, self.record.id, self.stat.id)
        # ensure returned recommendation equals mocked
        self.assertEqual(rec, mock_get.return_value)
        # refresh from db
        self.stat.refresh_from_db()
        self.assertEqual(self.stat.recommended, mock_get.return_value)
