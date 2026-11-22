import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from locations.models import Region, District

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Kategoriya nomi")
    icon = models.CharField(max_length=60, default="fa-solid fa-circle-exclamation", verbose_name="Ikonka klassi (FontAwesome)")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    color = models.CharField(max_length=30, default="#2563EB", verbose_name="Rang kodi (#HEX)")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartibi")

    class Meta:
        verbose_name = "Muammo kategoriyasi"
        verbose_name_plural = "Muammo kategoriyalari"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def report_count(self):
        return self.reports.count()

class Report(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_ASSIGNED = 'assigned'
    STATUS_RESOLVED = 'resolved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Yangi'),
        (STATUS_IN_PROGRESS, 'Ko\'rib chiqilmoqda'),
        (STATUS_ASSIGNED, 'Mas\'ul tashkilotga yuborildi'),
        (STATUS_RESOLVED, 'Hal qilindi'),
        (STATUS_REJECTED, 'Rad etildi'),
    ]

    STATUS_COLORS = {
        STATUS_NEW: 'primary',
        STATUS_IN_PROGRESS: 'warning',
        STATUS_ASSIGNED: 'info',
        STATUS_RESOLVED: 'success',
        STATUS_REJECTED: 'danger',
    }

    tracking_code = models.CharField(max_length=32, unique=True, db_index=True, verbose_name="Noyob murojaat raqami")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name="Foydalanuvchi"
    )
    applicant_name = models.CharField(max_length=150, blank=True, verbose_name="Murojaatchi ismi")
    applicant_phone = models.CharField(max_length=30, verbose_name="Telefon raqami")
    title = models.CharField(max_length=250, verbose_name="Muammo sarlavhasi")
    description = models.TextField(verbose_name="Batafsil tavsif")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="Kategoriya"
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="Viloyat / Hudud"
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="Tuman / Shahar"
    )
    address = models.CharField(max_length=255, verbose_name="Aniq manzil / Mo'ljal")
    latitude = models.FloatField(default=41.2995, verbose_name="Kenglik (Latitude)")
    longitude = models.FloatField(default=69.2401, verbose_name="Uzunlik (Longitude)")
    image = models.ImageField(upload_to='reports/images/%Y/%m/', verbose_name="Muammo fotosurati")
    video = models.FileField(upload_to='reports/videos/%Y/%m/', blank=True, null=True, verbose_name="Video lavha (ixtiyoriy)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
        verbose_name="Holati"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reports",
        verbose_name="Biriktirilgan mas'ul xodim"
    )
    resolution_notes = models.TextField(blank=True, verbose_name="Yechim yoki rad etish izohi")
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Yaratilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan sana")

    class Meta:
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.tracking_code}] {self.title}"

    @classmethod
    def generate_tracking_code(cls):
        """Generates a unique code like MH-2026-7A9B3D."""
        year = timezone.now().year
        random_suffix = uuid.uuid4().hex[:6].upper()
        code = f"MH-{year}-{random_suffix}"
        while cls.objects.filter(tracking_code=code).exists():
            random_suffix = uuid.uuid4().hex[:6].upper()
            code = f"MH-{year}-{random_suffix}"
        return code

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)

    @property
    def status_badge_class(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

class ReportHistory(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Murojaat"
    )
    old_status = models.CharField(max_length=20, choices=Report.STATUS_CHOICES, verbose_name="Oldingi holat")
    new_status = models.CharField(max_length=20, choices=Report.STATUS_CHOICES, verbose_name="Yangi holat")
    comment = models.TextField(blank=True, verbose_name="Status izohi / Sabab")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="O'zgartirgan foydalanuvchi"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="O'zgartirilgan vaqt")

    class Meta:
        verbose_name = "Murojaat tarixi"
        verbose_name_plural = "Murojaat tarixlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report.tracking_code}: {self.old_status} -> {self.new_status}"

class AdminReply(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Murojaat"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_replies",
        verbose_name="Muallif (Mas'ul xodim)"
    )
    message = models.TextField(verbose_name="Rasmiy javob matni")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yuborilgan sana")

    class Meta:
        verbose_name = "Rasmiy javob"
        verbose_name_plural = "Rasmiy javoblar"
        ordering = ['created_at']

    def __str__(self):
        author = self.author.get_display_name() if self.author else 'Tizim'
        return f"Javob {self.report.tracking_code} ({author})"
