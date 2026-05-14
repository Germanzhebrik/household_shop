from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class ExtendedRegisterForm(forms.ModelForm):
    first_name = forms.CharField(label="Имя", max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Иван'}))
    last_name = forms.CharField(label="Фамилия", max_length=100,
                                widget=forms.TextInput(attrs={'placeholder': 'Иванов'}))
    email = forms.EmailField(label="Электронная почта",
                             widget=forms.EmailInput(attrs={'placeholder': 'example@mail.com'}))

    # Поле для города
    city = forms.CharField(label="Город", max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Минск'}))

    # Поле телефона с подсказкой
    phone = forms.CharField(
        label="Номер телефона",
        help_text="Формат: +375 (29) XXX-XX-XX",
        widget=forms.TextInput(attrs={'placeholder': '+375 (__) ___-__-__'})
    )

    # Поле возраста с проверкой
    age = forms.IntegerField(label="Возраст", min_value=18,
                             error_messages={'min_value': "Регистрация доступна только лицам старше 18 лет."})

    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Подтвердите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Проверка формата регулярным выражением
        pattern = r'^\+375\s\(\d{2}\)\s\d{3}-\d{2}-\d{2}$'
        if not re.match(pattern, phone):
            raise ValidationError("Неверный формат телефона. Используйте: +375 (29) XXX-XX-XX")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password != password_confirm:
            raise ValidationError("Пароли не совпадают!")
        return cleaned_data