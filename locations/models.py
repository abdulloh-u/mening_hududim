from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Viloyat / Shahar nomi")
    code = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Kodi")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")
    latitude = models.FloatField(default=41.2995, verbose_name="Markaz kenglik (Lat)")
    longitude = models.FloatField(default=69.2401, verbose_name="Markaz uzunlik (Lng)")
    zoom_level = models.PositiveSmallIntegerField(default=9, verbose_name="Xarita masshtabi (Zoom)")

    class Meta:
        verbose_name = "Viloyat / Hudud"
        verbose_name_plural = "Viloyatlar va Hududlar"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(max_length=150, verbose_name="Tuman / Shahar nomi")
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="districts",
        verbose_name="Hudud"
    )
    latitude = models.FloatField(null=True, blank=True, verbose_name="Kenglik (Lat)")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Uzunlik (Lng)")

    class Meta:
        verbose_name = "Tuman / Shahar"
        verbose_name_plural = "Tumanlar va Shaharlar"
        ordering = ['region__name', 'name']
        unique_together = ('name', 'region')

    def __str__(self):
        return f"{self.name} ({self.region.name})"
