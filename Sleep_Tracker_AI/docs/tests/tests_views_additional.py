from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from unittest.mock import patch

from sleep_tracking_app.models import UserData


User = get_user_model()


class ViewsAdditionalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='pass12345')
        # create corresponding UserData
        UserData.objects.create(user=self.user, date_of_birth='1990-01-01', weight=70, gender=1, height=175)



    def test_user_update_post(self):
        self.client.login(username='tester', password='pass12345')
        url = reverse('profile')  # profile used as redirect target after update
        # post to user_update
        resp = self.client.post(reverse('user_update'), data={
            'username': 'tester',
            'first_name': 'T',
            'last_name': 'User',
            'email': 't@example.com',
            'date_of_birth': '1990-01-01',
            'weight': 70,
            'gender': 1,
            'height': 175,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('profile'))

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    @patch('sleep_tracking_app.views.import_sleep_records')
    def test_sleep_records_from_csv_posts_and_calls_celery(self, mock_import):
        # mock .delay() to return object with id
        mock_import.delay.return_value.id = 'fake-task-id'

        self.client.login(username='tester', password='pass12345')
        url = reverse('sleep_records_from_csv')
        csv_content = b'sleep_date_time,sleep_deep_duration\n2025-11-22,480\n'
        upload = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')
        resp = self.client.post(url, data={'csv_file': upload})
        # should return JSON with task_id
        self.assertEqual(resp.status_code, 200)
        self.assertIn('task_id', resp.json())
