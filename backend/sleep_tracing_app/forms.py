from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import date, timedelta
from .models import UserData, User
from django.core.exceptions import ValidationError



class UserDataForm(forms.ModelForm):
    GENDER_CHOICES = (
        (1, 'Мужской'),
        (0, 'Женский'),
    )
    date_of_birth = forms.DateField(required=True, label='Дата рождения',
                                    widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'max': date.today().isoformat(),}), input_formats=['%Y-%m-%d', '%d.%m.%Y'])
    weight = forms.IntegerField(min_value=10, required=True, label='Вес',
                                widget=forms.TextInput(attrs={'placeholder': 'Введите ваш вес (кг)'}))
    gender = forms.TypedChoiceField(label='Пол', coerce=int, choices=GENDER_CHOICES)
    height = forms.IntegerField(min_value=40, max_value=270, required=True, label='Рост',
                                widget=forms.TextInput(attrs={'placeholder': 'Введите ваш рост (см)'}))
    active = forms.BooleanField(label='Подписаться на рассылку', required=False)

    class Meta:
        model = UserData
        fields = ['date_of_birth', 'weight', 'gender', 'height', 'active']

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        min_age_date = date.today() - timedelta(days=5 * 365)  # минимум 5 лет
        if dob > min_age_date:
            raise ValidationError("Пользователь должен быть старше 5 лет")
        return dob


class UserRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Ваш пароль должен содержать не менее 8 символов.'
        self.fields['password2'].help_text = 'Введите тот же пароль, что и раньше, для подтверждения.'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'Никнейм',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'password1': 'Пароль',
            'password2': 'Повторите пароль',
        }
        help_texts = {
            'username': 'Требуемый. не более 150 символов. Только буквы, цифры и @/./+/-/_.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email


class UserInfoUpdateForm(forms.ModelForm):
    username = forms.CharField(label='Ник', max_length=150)
    first_name = forms.CharField(label='Имя', max_length=150)
    last_name = forms.CharField(label='Фамилия', max_length=150)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Ник',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }



class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Выберите CSV-файл', widget=forms.ClearableFileInput(
        attrs={'class': 'dropzone','id': 'csv-dropzone', 'accept': '.csv'}))
