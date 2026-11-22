from django.contrib import admin
from .models import Region, District

class DistrictInline(admin.TabularInline):
    model = District
    extra = 1

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'district_count')
    search_fields = ('name', 'code')
    inlines = [DistrictInline]

    def district_count(self, obj):
        return obj.districts.count()
    district_count.short_description = "Tumanlar soni"

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region')
    list_filter = ('region',)
    search_fields = ('name', 'region__name')
