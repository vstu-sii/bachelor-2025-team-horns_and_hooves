from django.test import TestCase
from datetime import timedelta, date

from sleep_tracking_app.forms import UserRegistrationForm, UserDataForm
from django.contrib.auth import get_user_model

User = get_user_model()

class FormValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='formtester',
            password='testpass123',
            email='formtest@example.com'
        )
        self.user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user_profile_data = {
            'date_of_birth': (date.today() - timedelta(days=25 * 365)).strftime('%Y-%m-%d'),  # 25 лет
            'weight': 70,
            'gender': 1,
            'height': 175,
            'active': True
        }


    def test_user_registration_form_validation(self):
        """Test UserRegistrationForm validation"""
        # Test valid data
        form = UserRegistrationForm(data=self.user_data)
        self.assertTrue(form.is_valid())

        # Test password mismatch
        invalid_data = self.user_data.copy()
        invalid_data['password2'] = 'DifferentPass123!'
        form = UserRegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

        # Test weak password
        weak_password_data = self.user_data.copy()
        weak_password_data['password1'] = '123'
        weak_password_data['password2'] = '123'
        form = UserRegistrationForm(data=weak_password_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

        # Test duplicate email
        User.objects.create_user(username='existing', email='duplicate@example.com', password='testpass123')
        duplicate_email = self.user_data.copy()
        duplicate_email['email'] = 'duplicate@example.com'
        form = UserRegistrationForm(data=duplicate_email)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_user_data_form_validation(self):
        """Test UserDataForm validation"""

        # Валидные данные
        form = UserDataForm(data=self.user_profile_data)
        self.assertTrue(form.is_valid())

        # Дата рождения в будущем
        future_dob = self.user_profile_data.copy()
        future_dob['date_of_birth'] = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        form = UserDataForm(data=future_dob)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

        # Пользователь младше 5 лет
        too_young = self.user_profile_data.copy()
        too_young['date_of_birth'] = (date.today() - timedelta(days=3 * 365)).strftime('%Y-%m-%d')
        form = UserDataForm(data=too_young)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

        # Неверный вес
        invalid_weight = self.user_profile_data.copy()
        invalid_weight['weight'] = 0
        form = UserDataForm(data=invalid_weight)
        self.assertFalse(form.is_valid())
        self.assertIn('weight', form.errors)

        # Неверный рост (слишком низкий)
        invalid_height = self.user_profile_data.copy()
        invalid_height['height'] = 39
        form = UserDataForm(data=invalid_height)
        self.assertFalse(form.is_valid())
        self.assertIn('height', form.errors)

        # Неверный рост (слишком высокий)
        invalid_height_high = self.user_profile_data.copy()
        invalid_height_high['height'] = 272
        form = UserDataForm(data=invalid_height_high)
        self.assertFalse(form.is_valid())
        self.assertIn('height', form.errors)


