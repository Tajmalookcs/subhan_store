"""
Admin panel configuration for CustomUser.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Extended admin for CustomUser with role support."""

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    list_per_page = 25

    fieldsets = UserAdmin.fieldsets + (
        ('Store Info', {
            'fields': ('role', 'phone', 'address', 'profile_picture', 'date_of_birth', 'is_verified'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Store Info', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name'),
        }),
    )
