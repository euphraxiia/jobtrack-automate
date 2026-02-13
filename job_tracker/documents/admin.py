"""Admin configuration for the documents app."""
from django.contrib import admin

from .models import Document, CoverLetterTemplate


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'doc_type', 'version', 'is_active', 'created_date']
    list_filter = ['doc_type', 'is_active']
    search_fields = ['title', 'user__username']


@admin.register(CoverLetterTemplate)
class CoverLetterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'job_type', 'is_default', 'updated_at']
    list_filter = ['is_default']
    search_fields = ['name', 'content']
