"""
Admin configuration for the applications app.

Register all the models so they show up in the Django admin panel
and can be managed from there.
"""
from django.contrib import admin

from .models import (
    Company, Job, Application, ApplicationActivity,
    AutomationRule, Reminder
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'location', 'company_size', 'is_blacklisted']
    list_filter = ['industry', 'company_size', 'is_blacklisted']
    search_fields = ['name', 'industry', 'location']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'work_type', 'source_platform', 'posted_date']
    list_filter = ['work_type', 'source_platform']
    search_fields = ['title', 'company__name', 'description']
    raw_id_fields = ['company']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'job', 'company', 'user', 'status', 'priority',
        'applied_date', 'application_method'
    ]
    list_filter = ['status', 'priority', 'application_method']
    search_fields = ['job__title', 'company__name', 'notes']
    raw_id_fields = ['user', 'job', 'company', 'cover_letter', 'cv_used']
    date_hierarchy = 'created_at'


@admin.register(ApplicationActivity)
class ApplicationActivityAdmin(admin.ModelAdmin):
    list_display = ['application', 'activity_type', 'timestamp', 'created_by']
    list_filter = ['activity_type']
    search_fields = ['description']
    raw_id_fields = ['application', 'created_by']


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'job_board', 'search_keywords',
        'apply_automatically', 'is_active'
    ]
    list_filter = ['job_board', 'is_active', 'apply_automatically']
    search_fields = ['search_keywords']
    raw_id_fields = ['user']


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'application', 'reminder_type', 'reminder_date',
        'is_sent', 'sent_date'
    ]
    list_filter = ['reminder_type', 'is_sent']
    search_fields = ['message']
    raw_id_fields = ['application']
