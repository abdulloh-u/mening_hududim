import re

from django import forms
from .models import Report
from locations.models import Region, District

PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{6,24}$')
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.avi', '.mkv'}


class ReportCreateForm(forms.ModelForm):
    applicant_name = forms.CharField(
        max_length=150,
        required=False,
        label="Ism va familiyangiz (ixtiyoriy)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masalan: Alisher Navoiy'
        })
    )
    applicant_phone = forms.CharField(
        max_length=30,
        required=True,
        label="Telefon raqamingiz",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998 90 123 45 67'
        })
    )
    title = forms.CharField(
        max_length=250,
        label="Muammo sarlavhasi",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Qisqa va aniq ifodalang (masalan: 12-maktab yonidagi chuqur yo‘l)'
        })
    )
    description = forms.CharField(
        label="Batafsil tavsif",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Muammo haqida batafsil ma\'lumot bering: qachondan beri mavjud, qanday xavf tug\'dirmoqda...'
        })
    )
    address = forms.CharField(
        max_length=255,
        label="Aniq manzil va mo'ljal",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ko‘cha, uy raqami yoki mashhur mo‘ljal'
        })
    )
    latitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'id_latitude'}),
        initial=41.2995
    )
    longitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'id_longitude'}),
        initial=69.2401
    )

    class Meta:
        model = Report
        fields = [
            'applicant_name', 'applicant_phone', 'title', 'category',
            'region', 'district', 'address', 'latitude', 'longitude',
            'image', 'video'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select', 'id': 'id_region'}),
            'district': forms.Select(attrs={'class': 'form-select', 'id': 'id_district'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'video': forms.FileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'].queryset = District.objects.none()

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['district'].queryset = District.objects.filter(
                    region_id=region_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.region:
            self.fields['district'].queryset = self.instance.region.districts.order_by('name')
        elif Region.objects.exists():
            first_region = Region.objects.first()
            self.fields['district'].queryset = first_region.districts.order_by('name')

    def clean_applicant_phone(self):
        phone = self.cleaned_data.get('applicant_phone', '').strip()
        if not PHONE_RE.match(phone):
            raise forms.ValidationError(
                "Telefon raqamini to'g'ri kiriting (masalan: +998 90 123 45 67)."
            )
        return phone

    def clean(self):
        cleaned_data = super().clean()
        region = cleaned_data.get('region')
        district = cleaned_data.get('district')

        # JS fills the district list dynamically, but the server must never
        # accept a district that belongs to another region.
        if region and district and district.region_id != region.pk:
            self.add_error(
                'district',
                "Tanlangan tuman ushbu viloyatga tegishli emas. Qaytadan tanlang."
            )

        lat, lng = cleaned_data.get('latitude'), cleaned_data.get('longitude')
        if lat is not None and not (-90 <= lat <= 90):
            self.add_error('latitude', "Kenglik (latitude) -90 dan 90 gacha bo'lishi kerak.")
        if lng is not None and not (-180 <= lng <= 180):
            self.add_error('longitude', "Uzunlik (longitude) -180 dan 180 gacha bo'lishi kerak.")
        return cleaned_data

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise forms.ValidationError("Muammo fotosuratini yuklash majburiy.")
        if image.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Rasm hajmi 10 MB dan oshmasligi kerak.")
        return image

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if not video:
            return video
        if video.size > 25 * 1024 * 1024:
            raise forms.ValidationError("Video hajmi 25 MB dan oshmasligi kerak.")
        name = (video.name or '').lower()
        if any(name.endswith(ext) for ext in VIDEO_EXTENSIONS):
            return video
        content_type = (getattr(video, 'content_type', '') or '').lower()
        if content_type.startswith('video/'):
            return video
        raise forms.ValidationError(
            "Faqat video fayllari (MP4, MOV, WEBM, AVI, MKV) qabul qilinadi."
        )
