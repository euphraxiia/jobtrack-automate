"""Admin configuration for the accounts app."""
from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'phone_number', 'location',
        'job_title_target', 'work_type_preference'
    ]
    search_fields = ['user__username', 'user__email', 'location']
    list_filter = ['work_type_preference', 'willing_to_relocate']
