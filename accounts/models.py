from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CITIZEN = 'citizen'
    ROLE_SPECIALIST = 'specialist'
    ROLE_REGIONAL_STAFF = 'regional_staff'
    ROLE_ADMIN = 'admin'
    ROLE_SUPERADMIN = 'superadmin'

    ROLE_CHOICES = [
        (ROLE_CITIZEN, 'Fuqaro'),
        (ROLE_SPECIALIST, 'Usta / Ijrochi mutaxassis'),
        (ROLE_REGIONAL_STAFF, 'Hududiy mas\'ul xodim'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_SUPERADMIN, 'Bosh Administrator'),
    ]

    full_name = models.CharField(max_length=200, verbose_name="To'liq ism-familiya", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami", blank=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_CITIZEN,
        verbose_name="Foydalanuvchi roli"
    )
    region = models.ForeignKey(
        'locations.Region',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_members",
        verbose_name="Biriktirilgan hudud (mas'ul xodimlar uchun)"
    )

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.get_display_name()} ({self.get_role_display()})"

    def get_display_name(self):
        if self.full_name:
            return self.full_name
        return self.username

    @property
    def is_citizen(self):
        return self.role == self.ROLE_CITIZEN

    @property
    def is_staff_member(self):
        return self.role in [self.ROLE_SPECIALIST, self.ROLE_REGIONAL_STAFF, self.ROLE_ADMIN, self.ROLE_SUPERADMIN] or self.is_staff or self.is_superuser

    @property
    def is_admin_or_superadmin(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_SUPERADMIN] or self.is_superuser
