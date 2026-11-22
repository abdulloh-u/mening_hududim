import re

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User
from locations.models import Region

PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{6,24}$')


def validate_phone(value):
    value = (value or '').strip()
    if value and not PHONE_RE.match(value):
        raise forms.ValidationError(
            "Telefon raqamini to'g'ri kiriting (masalan: +998 90 123 45 67)."
        )
    return value

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ushbu login band. Boshqa login tanlang.")
        return username

class AdminPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Amaldagi parol",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )
    new_password = forms.CharField(
        label="Yangi parol",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        min_length=12
    )
    confirm_password = forms.CharField(
        label="Yangi parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Amaldagi parol noto'g'ri kiritildi.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Kiritilgan yangi parollar mos kelmadi.")
        if new_password:
            try:
                password_validation.validate_password(new_password, self.user)
            except DjangoValidationError as exc:
                self.add_error('new_password', exc.messages)
        return cleaned_data

class StaffCreateForm(forms.ModelForm):
    # Super Admin is intentionally absent. New admins are always bound to one
    # region; regional admins may only create workers for their own region.
    ROLE_CHOICES_STAFF = [
        (User.ROLE_SPECIALIST, 'Usta / Ijrochi mutaxassis'),
        (User.ROLE_REGIONAL_STAFF, 'Hududiy mas\'ul xodim'),
        (User.ROLE_ADMIN, 'Viloyat administratori'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES_STAFF,
        label="Xodim vazifasi / Roli",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password = forms.CharField(
        label="Boshlang'ich parol",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
        min_length=12
    )
    password_confirm = forms.CharField(
        label="Parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'})
    )

    class Meta:
        model = User
        fields = ['full_name', 'username', 'role', 'region', 'phone', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism va familiya'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 90 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'xodim@meninghududim.uz'}),
        }

    def __init__(self, *args, is_superadmin=False, fixed_region=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_region = fixed_region
        # Phone is mandatory; email stays optional and remains in its place.
        self.fields['phone'].required = True
        self.fields['email'].required = False

        if not is_superadmin:
            # A regional admin may only add workers, never another admin.
            self.fields['role'].choices = [
                choice for choice in self.ROLE_CHOICES_STAFF
                if choice[0] != User.ROLE_ADMIN
            ]
            self.fields['region'].queryset = (
                Region.objects.filter(pk=fixed_region.pk) if fixed_region else Region.objects.none()
            )
            self.fields['region'].initial = fixed_region
            self.fields['region'].help_text = "Faqat o'z viloyatingizga ishchi qo'shishingiz mumkin."

    def clean_region(self):
        region = self.cleaned_data.get('region')
        if self.fixed_region and region and region.pk != self.fixed_region.pk:
            raise forms.ValidationError("Faqat o'z viloyatingizga ishchi qo'shishingiz mumkin.")
        return region

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ushbu login tizimda allaqachon mavjud.")
        return username

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get('phone'))

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        region = cleaned_data.get('region')

        if role in (User.ROLE_ADMIN, User.ROLE_REGIONAL_STAFF, User.ROLE_SPECIALIST) and not region:
            self.add_error('region', "Bu rol uchun biriktiriladigan viloyatni tanlang.")

        if role == User.ROLE_ADMIN and region:
            existing = User.objects.filter(role=User.ROLE_ADMIN, region=region)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error(
                    'region',
                    "Bu viloyatda allaqachon administrator bor. Bitta viloyatga bitta admin qo'yiladi."
                )

        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Kiritilgan parollar mos kelmadi.")
        if password:
            try:
                password_validation.validate_password(password)
            except DjangoValidationError as exc:
                self.add_error('password', exc.messages)
        return cleaned_data
