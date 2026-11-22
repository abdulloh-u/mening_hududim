from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'email', 'phone', 'role', 'region', 'is_active', 'date_joined')
    list_filter = ('role', 'region', 'is_active', 'is_staff')
    search_fields = ('username', 'full_name', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('Platforma roli va ma\'lumotlar', {
            'fields': ('full_name', 'phone', 'role', 'region')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('full_name', 'phone', 'role', 'region')
        }),
    )
