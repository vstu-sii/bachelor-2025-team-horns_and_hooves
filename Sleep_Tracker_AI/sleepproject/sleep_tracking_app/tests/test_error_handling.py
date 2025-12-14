from datetime import timedelta, timezone
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from django.db import IntegrityError
from django.http import JsonResponse

from sleep_tracking_app.models import UserData, SleepRecord
User = get_user_model()


class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='tester',
            password='testpass123',
            email='tester@example.com'
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
            sleep_date_time=timezone.now() - timedelta(days=1),
            sleep_deep_duration=240,
            sleep_light_duration=180,
            total_time_bed=480
        )

    @override_settings(DEBUG=False)  # Ensure DEBUG is False to test 500 handling
    def test_500_error_handling(self):
        """Test that 500 errors are properly handled"""
        # Mock the view to raise an exception
        with patch('sleep_tracking_app.views.sleep_statistics_show',
                   side_effect=Exception("Test exception")) as mock_view:
            self.client.login(username='tester', password='testpass123')
            with self.assertRaises(Exception):
                response = self.client.get(reverse('sleep_statistics_show'))
                self.assertEqual(response.status_code, 500)
                self.assertTemplateUsed('500.html')

    def test_404_error_handling(self):
        """Test that 404 errors are properly handled for non-existent records"""
        self.client.login(username='tester', password='testpass123')
        # Test with a non-existent URL pattern that should 404
        response = self.client.get('/non-existent-url/')
        self.assertEqual(response.status_code, 404)

    def test_database_integrity_errors(self):
        """Test database integrity constraints"""
        # Test unique constraint
        with self.assertRaises(IntegrityError):
            UserData.objects.create(
                user=self.user,  # Duplicate user
                date_of_birth='1990-01-01',
                weight=70,
                gender=1,
                height=175
            )

    @patch('sleep_tracking_app.tasks.sleep_recommended.delay')
    def test_async_task_error_handling(self, mock_task):
        """Test error handling in async tasks"""
        # Simulate task failure
        mock_task.side_effect = Exception("Task failed")

        with self.assertRaises(Exception):
            response = self.client.get(reverse('get_sleep_recommendation'))
            self.assertEqual(response.status_code, 500)

    def test_custom_404_template(self):
        """Test that custom 404 template is used"""
        response = self.client.get('/non-existent-url/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed('404.html')
