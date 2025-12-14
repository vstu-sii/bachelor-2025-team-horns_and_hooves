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
