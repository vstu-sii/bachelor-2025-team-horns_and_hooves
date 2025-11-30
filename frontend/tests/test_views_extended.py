from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from sleep_tracking_app.models import SleepRecord, SleepStatistics, UserData

User = get_user_model()

class ExtendedViewTests(TestCase):
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

        cache.clear()

    def test_sleep_statistics_show_template_used(self):
        """Test that the correct template is used for sleep statistics"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('sleep_statistics_show'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sleep_statistic/sleep_statistics_show.html')

    def test_sleep_statistics_show_context_data(self):
        """Test that the view passes the correct context data"""
        self.client.login(username='testuser', password='testpass123')
        cache.clear()
        response = self.client.get(reverse('sleep_statistics_show'))

        # Проверяем существование ключей
        self.assertIn('metric', response.context)
        self.assertIn('plot_data', response.context)
        self.assertIn('graph_data', response.context)
        self.assertIn('page', response.context)  # страница с SleepRecord
        self.assertIn('rec', response.context)  # последний record


    def test_sleep_statistics_show_no_data(self):
        """Test the view when no sleep data exists"""
        # Delete existing data
        SleepRecord.objects.all().delete()
        SleepStatistics.objects.all().delete()
        
        self.client.login(username='testuser', password='testpass123')
        cache.clear()
        response = self.client.get(reverse('sleep_statistics_show'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('sleep_statistics'))
        self.assertIsNone(response.context.get('last_record'))


