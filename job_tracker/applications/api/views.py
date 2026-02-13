"""
API views for the applications app.

Provides REST endpoints for the mobile app and Chrome extension.
All endpoints require authentication via JWT tokens.
"""
import logging
from typing import Any

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone

from applications.models import (
    Application, Company, Job, AutomationRule, Reminder
)
from applications.services.analytics_engine import AnalyticsEngine
from applications.services.status_tracker import StatusTracker
from .serializers import (
    ApplicationSerializer, ApplicationCreateSerializer,
    CompanySerializer, JobSerializer,
    StatusUpdateSerializer, AutomationRuleSerializer,
    ReminderSerializer, DashboardStatsSerializer,
    AutomationRequestSerializer, DocumentUploadSerializer,
)

logger = logging.getLogger('applications')


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for job applications.
    Each user can only see and manage their own applications.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        return (
            Application.objects.filter(user=self.request.user)
            .select_related('job', 'company')
            .prefetch_related('activities')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update just the status of an application."""
        application = self.get_object()
        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        tracker = StatusTracker()
        success = tracker.transition(
            application, new_status,
            user=request.user, notes=notes
        )

        if success:
            return Response(
                ApplicationSerializer(application).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': f'Cannot transition from {application.status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CompanyViewSet(viewsets.ModelViewSet):
    """CRUD for companies."""
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    queryset = Company.objects.all()
    filterset_fields = ['industry', 'company_size', 'is_blacklisted']
    search_fields = ['name', 'industry', 'location']


class JobViewSet(viewsets.ModelViewSet):
    """CRUD for job listings."""
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.select_related('company').all()
    filterset_fields = ['work_type', 'source_platform', 'company']
    search_fields = ['title', 'description', 'company__name']


class DashboardStatsView(APIView):
    """Get all the dashboard statistics in one go."""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        user = request.user
        engine = AnalyticsEngine()

        data = {
            'total_applications': Application.objects.filter(user=user).count(),
            'this_month': engine.get_monthly_count(user),
            'response_rate': engine.calculate_response_rate(user),
            'interview_rate': engine.calculate_interview_rate(user),
            'avg_response_days': engine.calculate_avg_response_time(user),
            'status_breakdown': engine.get_applications_by_status(user),
            'top_companies': engine.get_top_companies(user),
            'board_stats': engine.get_success_by_board(user),
        }

        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


class AutomationApplyView(APIView):
    """Trigger an automated job application."""
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        serializer = AutomationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Queue the automation task with Celery
        from tasks.automation_tasks import apply_to_job_task

        task = apply_to_job_task.delay(
            user_id=request.user.id,
            job_url=serializer.validated_data['job_url'],
            job_board=serializer.validated_data['job_board'],
            cv_id=serializer.validated_data.get('cv_id'),
            dry_run=serializer.validated_data.get('dry_run', False),
        )

        return Response(
            {'task_id': task.id, 'status': 'queued'},
            status=status.HTTP_202_ACCEPTED
        )


class JobSearchView(APIView):
    """Search for available jobs across supported boards."""
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        keywords = request.query_params.get('keywords', '')
        location = request.query_params.get('location', '')
        board = request.query_params.get('board', '')

        if not keywords:
            return Response(
                {'error': 'Keywords parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For now, return jobs from our database that match
        jobs = Job.objects.filter(
            title__icontains=keywords
        ).select_related('company')

        if location:
            jobs = jobs.filter(location__icontains=location)

        if board:
            jobs = jobs.filter(source_platform=board)

        serializer = JobSerializer(jobs[:50], many=True)
        return Response(serializer.data)


class ReminderViewSet(viewsets.ModelViewSet):
    """CRUD for reminders."""
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Reminder.objects.filter(application__user=self.request.user)
            .select_related('application')
            .order_by('reminder_date')
        )


class DocumentUploadView(APIView):
    """Handle document uploads via the API."""
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
