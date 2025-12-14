from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import json


class E2ETests(TestCase):

    def test_register_and_update_profile(self):
        """
        E2E: регистрация, логин и изменение профиля через `user_update`.
        """
        username = 'e2eupdate'
        password = 'E2E-pass-456'
        reg_url = reverse('register')
        dob = (date.today() - timedelta(days=25 * 365)).isoformat()  # 25 лет
        data = {
            'username': username,
            'first_name': 'Initial',
            'last_name': 'User',
            'email': 'init@example.test',
            'password1': password,
            'password2': password,
            'date_of_birth': dob,
            'weight': '70',
            'gender': '1',
            'height': '175',
            'active': '',
        }
        resp = self.client.post(reg_url, data)
        self.assertIn(resp.status_code, (302, 301))

        logged = self.client.login(username=username, password=password)
        self.assertTrue(logged)

        update_url = reverse('user_update')
        new_data = {
            'username': username,
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.test',
            'date_of_birth': dob,
            'weight': '75',
            'gender': '1',
            'height': '180',
            'active': '',
        }
        resp2 = self.client.post(update_url, new_data)
        self.assertEqual(resp2.status_code, 302)
        self.assertEqual(resp2.url, reverse('profile'))

        # Проверяем, что данные пользователя обновлены в БД
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username=username)
        self.assertEqual(user.first_name, 'Updated')

