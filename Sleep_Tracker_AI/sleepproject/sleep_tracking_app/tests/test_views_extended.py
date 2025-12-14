# sleep_tracking_app/tests/test_views_extended.py

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from sleep_tracking_app.models import SleepRecord, SleepStatistics, UserData


User = get_user_model()


class ExtendedViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Переконфигурируем кэш на locmem если используется Redis
        from django.conf import settings
        if 'redis' in str(settings.CACHES.get('default', {}).get('BACKEND', '')).lower():
            settings.CACHES = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': 'test-cache',
                }
            }

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user_data = UserData.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            weight=70,
            gender=1,
            height=175
        )

        self.sleep_record = SleepRecord.objects.create(
            user=self.user,
            sleep_date_time=timezone.now(),
            device_bedtime=timezone.now() - timedelta(hours=8),
            bedtime=timezone.now() - timedelta(hours=8, minutes=15),
            wake_up_time=timezone.now(),
            device_wake_up_time=timezone.now(),
            duration=480,
            sleep_light_duration=300,
            sleep_deep_duration=120,
            sleep_rem_duration=60,
            has_rem=True,
            awake_count=1,
            min_hr=50,
            max_hr=100,
            avg_hr=70
        )

        self.sleep_stat = SleepStatistics.objects.create(
            user=self.user,
            recommended=None,
            date=timezone.now().date() - timedelta(days=1),
            sleep_duration=480,
            sleep_quality=94.1,
            sleep_efficiency=85.3,
            sleep_phases={'deep': 25, 'light': 62.5, 'rem': 12.5, 'awake': 6.25},
            sleep_fragmentation_index=0.5,
            sleep_calories_burned=350.5
        )

        # Безопасно очищаем кэш
        self._safe_cache_clear()

    def _safe_cache_clear(self):
        """Безопасно очищаем кэш, игнорируя ошибки Redis"""
        try:
            cache.clear()
        except Exception as e:
            # Логируем но не падаем
            print(f"Cache clear warning (expected in tests): {type(e).__name__}")

    def test_sleep_statistics_show_template_used(self):
        """Test that the correct template is used for sleep statistics"""
        self.client.login(username='testuser', password='testpass123')

        # Мокируем Celery task, чтобы не дергать реальный ИИ
        with patch('sleep_tracking_app.tasks.sleep_recommended.delay') as mock_task:
            mock_task.return_value = MagicMock(id='test-task-id')
            response = self.client.get(reverse('sleep_statistics_show'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sleep_statistic/sleep_statistics_show.html')

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    def test_sleep_statistics_show_context_data(self, mock_task):
        """Test that the view passes the correct context data"""
        # Мокируем Celery task
        mock_task.return_value = MagicMock(id='test-task-id')

        self.client.login(username='testuser', password='testpass123')
        self._safe_cache_clear()

        response = self.client.get(reverse('sleep_statistics_show'))

        # Проверяем существование ключей
        self.assertIn('metric', response.context)
        self.assertIn('plot_data', response.context)
        self.assertIn('graph_data', response.context)
        self.assertIn('page', response.context)  # страница с SleepRecord
        self.assertIn('rec', response.context)  # рекомендация по сну (строка или None)

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    def test_sleep_statistics_show_no_data(self, mock_task):
        """Test the view when no sleep data exists"""
        mock_task.return_value = MagicMock(id='test-task-id')

        # Удаляем все данные
        SleepRecord.objects.all().delete()
        SleepStatistics.objects.all().delete()

        self.client.login(username='testuser', password='testpass123')
        self._safe_cache_clear()

        response = self.client.get(reverse('sleep_statistics_show'))

        self.assertEqual(response.status_code, 200)
        # Во вьюхе теперь, скорее всего, пустые списки, а не None
        self.assertFalse(response.context.get('sleep_statistics'))
        self.assertFalse(response.context.get('last_record'))
        # Рекомендации при отсутствии данных быть не должно
        self.assertIsNone(response.context.get('rec'))

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    def test_sleep_statistics_context_has_user_data(self, mock_task):
        """Test that context includes user data"""
        mock_task.return_value = MagicMock(id='test-task-id')

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('sleep_statistics_show'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('user', response.context)
        self.assertEqual(response.context['user'], self.user)

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    def test_sleep_statistics_triggers_celery_for_missing_recommendation(self, mock_task):
        """
        Test that Celery task is triggered when latest statistics
        has no recommendation, and that rec in context is still None
        (рекомендация ещё не получена).
        """
        mock_task.return_value = MagicMock(id='test-task-id')

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('sleep_statistics_show'))

        self.assertEqual(response.status_code, 200)

        # Таска должна быть вызвана, так как recommended=None
        mock_task.assert_called_once()
        _, kwargs = mock_task.call_args

        # Проверяем, что в таску переданы корректные аргументы (списки id)
        self.assertEqual(kwargs['user_data_id'], self.user_data.id)
        self.assertEqual(kwargs['sleep_statistics_id'], [self.sleep_stat.id])
        self.assertEqual(kwargs['sleep_record_id'], [self.sleep_record.id])

        # В контексте ключ rec должен быть, но пока без текста рекомендации
        self.assertIn('rec', response.context)
        self.assertIsNone(response.context['rec'])

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    @patch('django.core.cache.cache.clear')
    def test_sleep_statistics_with_mocked_cache(self, mock_cache_clear, mock_task):
        """Test that cache operations don't break the view"""
        # Mock cache.clear to avoid Redis connection
        mock_cache_clear.return_value = None
        mock_task.return_value = MagicMock(id='test-task-id')

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('sleep_statistics_show'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sleep_statistic/sleep_statistics_show.html')
