import re

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User

PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{6,24}$')


def validate_phone(value):
    value = (value or '').strip()
    if value and not PHONE_RE.match(value):
        raise forms.ValidationError(
            "Telefon raqamini to'g'ri kiriting (masalan: +998 90 123 45 67)."
        )
    return value


class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        min_length=12
    )
    password_confirm = forms.CharField(
        label="Parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'phone', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login (username)'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism va familiyangiz'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'elektron@pochta.uz'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = True  # label says *.

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Bu login band. Boshqa login tanlang.")
        return username

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get('phone'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Kiritilgan parollar bir-biriga mos kelmadi.")
        if password:
            try:
                password_validation.validate_password(password)
            except DjangoValidationError as exc:
                self.add_error('password', exc.messages)
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login (username)', 'autofocus': True}),
        label="Login"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol'}),
        label="Parol"
    )


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get('phone'))
