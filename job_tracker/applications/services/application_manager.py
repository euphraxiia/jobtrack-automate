"""
Application manager service.

Handles the core business logic for creating, updating,
and managing job applications. Keeps the views clean by
putting the heavy lifting here.
"""
import logging
from datetime import timedelta
from typing import Optional, Dict, Any, List

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from applications.models import (
    Application, Company, Job, ApplicationActivity, Reminder
)

logger = logging.getLogger('applications')


class ApplicationManager:
    """
    Core service for managing job applications.
    All the business logic for applications lives here.
    """

    @staticmethod
    @transaction.atomic
    def create_application(
        user: User,
        job_data: Dict[str, Any],
        company_data: Dict[str, Any],
        application_data: Optional[Dict[str, Any]] = None
    ) -> Application:
        """
        Create a new application with its related job and company.
        Wraps everything in a transaction so nothing is left half done.
        """
        # Get or create the company
        company, _ = Company.objects.get_or_create(
            name=company_data['name'],
            defaults={
                'industry': company_data.get('industry', ''),
                'location': company_data.get('location', ''),
                'website': company_data.get('website', ''),
            }
        )

        # Create the job listing
        job = Job.objects.create(
            company=company,
            title=job_data['title'],
            description=job_data.get('description', ''),
            requirements=job_data.get('requirements', ''),
            salary_range=job_data.get('salary_range', ''),
            location=job_data.get('location', ''),
            work_type=job_data.get('work_type', 'onsite'),
            job_url=job_data.get('job_url', ''),
            source_platform=job_data.get('source_platform', 'other'),
        )

        # Create the application record
        app_defaults = application_data or {}
        application = Application.objects.create(
            user=user,
            job=job,
            company=company,
            status=app_defaults.get('status', 'saved'),
            priority=app_defaults.get('priority', 'medium'),
            notes=app_defaults.get('notes', ''),
            application_method=app_defaults.get('application_method', 'manual'),
        )

        logger.info(
            'Created application %s for user %s - %s at %s',
            application.pk, user.username, job.title, company.name
        )

        return application

    @staticmethod
    def update_status(
        application: Application,
        new_status: str,
        user: User,
        notes: str = ''
    ) -> Application:
        """
        Update the status of an application.
        Also logs the change as an activity.
        """
        old_status = application.status
        application.status = new_status

        # Record the applied date if moving to applied status
        if new_status == 'applied' and not application.applied_date:
            application.applied_date = timezone.now()

        application.save()

        # Log the status change
        ApplicationActivity.objects.create(
            application=application,
            activity_type='status_change',
            description=f'Status changed from {old_status} to {new_status}. {notes}'.strip(),
            created_by=user,
        )

        logger.info(
            'Application %s status: %s -> %s',
            application.pk, old_status, new_status
        )

        return application

    @staticmethod
    def check_duplicate(user: User, job_or_url) -> bool:
        """
        Check if the user has already applied to this job.
        Accepts a Job object or a job URL string.
        Useful for avoiding duplicate applications in automation.
        """
        if isinstance(job_or_url, str):
            # It is a URL string
            if not job_or_url:
                return False
            return Application.objects.filter(
                user=user,
                job__job_url=job_or_url
            ).exists()
        else:
            # It is a Job object
            return Application.objects.filter(
                user=user,
                job=job_or_url
            ).exists()

    @staticmethod
    def get_daily_application_count(user: User) -> int:
        """Work out how many applications were made today."""
        today = timezone.now().date()
        return Application.objects.filter(
            user=user,
            applied_date__date=today,
            application_method='automated'
        ).count()

    @staticmethod
    def create_follow_up_reminder(
        application: Application,
        days_from_now: int = 7,
        message: str = ''
    ) -> Reminder:
        """
        Set a follow-up reminder for an application.
        Defaults to one week from now if no date given.
        """
        reminder_date = timezone.now().date() + timedelta(days=days_from_now)

        if not message:
            message = (
                f'Follow up on your application for '
                f'{application.job.title} at {application.company.name}'
            )

        reminder = Reminder.objects.create(
            application=application,
            reminder_type='follow_up',
            reminder_date=reminder_date,
            message=message,
        )

        logger.info(
            'Created follow-up reminder for application %s on %s',
            application.pk, reminder_date
        )

        return reminder

    @staticmethod
    def get_applications_needing_follow_up(user: User) -> List[Application]:
        """
        Find applications where a follow-up is overdue.
        Looks for applied applications with no recent contact.
        """
        week_ago = timezone.now().date() - timedelta(days=7)

        return list(
            Application.objects.filter(
                user=user,
                status__in=['applied', 'screening'],
                follow_up_date__lte=timezone.now().date()
            ).select_related('job', 'company')
        )
