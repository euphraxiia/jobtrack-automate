"""
API serializers for the applications app.

Convert our Django models to and from JSON for the REST API.
Used by the mobile app and Chrome extension to talk to the backend.
"""
from rest_framework import serializers

from applications.models import (
    Company, Job, Application, ApplicationActivity,
    AutomationRule, Reminder
)
from documents.models import Document


class CompanySerializer(serializers.ModelSerializer):
    """Serialise company data for the API."""

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'industry', 'location', 'website',
            'company_size', 'glassdoor_rating', 'notes',
            'is_blacklisted', 'date_added'
        ]
        read_only_fields = ['id', 'date_added']


class JobSerializer(serializers.ModelSerializer):
    """Serialise job listing data for the API."""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'company', 'company_name', 'title', 'description',
            'requirements', 'salary_range', 'location', 'work_type',
            'posted_date', 'closing_date', 'job_url', 'source_platform',
            'is_expired', 'date_added'
        ]
        read_only_fields = ['id', 'date_added', 'is_expired']


class ApplicationActivitySerializer(serializers.ModelSerializer):
    """Serialise application activity log entries."""

    class Meta:
        model = ApplicationActivity
        fields = [
            'id', 'activity_type', 'description', 'timestamp', 'created_by'
        ]
        read_only_fields = ['id', 'timestamp']


class ApplicationSerializer(serializers.ModelSerializer):
    """Serialise application data for the API."""
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    activities = ApplicationActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'user', 'job', 'job_title', 'company', 'company_name',
            'status', 'applied_date', 'application_method', 'job_board_url',
            'cover_letter', 'cv_used', 'notes', 'priority',
            'follow_up_date', 'last_contact_date', 'rejection_reason',
            'salary_offered', 'interview_dates', 'automated_application_log',
            'created_at', 'updated_at', 'activities'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Serialiser for creating a new application.
    Simpler than the full serialiser since we do not need all the fields.
    """
    company_name = serializers.CharField(write_only=True, required=False)
    job_title = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Application
        fields = [
            'job', 'company', 'company_name', 'job_title',
            'status', 'application_method', 'job_board_url',
            'cover_letter', 'cv_used', 'notes', 'priority',
        ]

    def create(self, validated_data):
        """Create the application and set the user from the request."""
        # Pop out extra fields that are not on the model
        validated_data.pop('company_name', None)
        validated_data.pop('job_title', None)
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class StatusUpdateSerializer(serializers.Serializer):
    """Serialiser for updating just the status of an application."""
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class AutomationRuleSerializer(serializers.ModelSerializer):
    """Serialise automation rule settings."""

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'job_board', 'search_keywords', 'location_filter',
            'salary_min', 'apply_automatically', 'max_applications_per_day',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReminderSerializer(serializers.ModelSerializer):
    """Serialise reminder data."""

    class Meta:
        model = Reminder
        fields = [
            'id', 'application', 'reminder_type', 'reminder_date',
            'message', 'is_sent', 'sent_date', 'created_at'
        ]
        read_only_fields = ['id', 'is_sent', 'sent_date', 'created_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Serialiser for the dashboard statistics response."""
    total_applications = serializers.IntegerField()
    this_month = serializers.IntegerField()
    response_rate = serializers.FloatField()
    interview_rate = serializers.FloatField()
    avg_response_days = serializers.FloatField(allow_null=True)
    status_breakdown = serializers.ListField()
    top_companies = serializers.ListField()
    board_stats = serializers.ListField()


class AutomationRequestSerializer(serializers.Serializer):
    """Serialiser for triggering an automated application."""
    job_url = serializers.URLField()
    job_board = serializers.ChoiceField(
        choices=['pnet', 'careers24', 'linkedin', 'indeed']
    )
    cv_id = serializers.IntegerField(required=False)
    cover_letter_id = serializers.IntegerField(required=False)
    dry_run = serializers.BooleanField(default=False)


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serialiser for uploading documents via the API."""

    class Meta:
        model = Document
        fields = ['id', 'doc_type', 'title', 'file', 'version', 'tags']
        read_only_fields = ['id']
