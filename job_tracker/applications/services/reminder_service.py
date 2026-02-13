"""
Reminder service.

Handles checking for due reminders and sending out email
notifications. Called by the Celery beat scheduler daily.
"""
import logging
from datetime import timedelta
from typing import List

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from applications.models import Reminder

logger = logging.getLogger('applications')


class ReminderService:
    """Handle all reminder-related operations."""

    @staticmethod
    def get_due_reminders() -> List[Reminder]:
        """Find all reminders that need to be sent today."""
        today = timezone.now().date()
        return list(
            Reminder.objects.filter(
                reminder_date__lte=today,
                is_sent=False
            ).select_related('application__user', 'application__job', 'application__company')
        )

    @staticmethod
    def send_reminder(reminder: Reminder) -> bool:
        """
        Send out a single reminder via email.
        Marks it as sent once the email goes through.
        """
        try:
            application = reminder.application
            user = application.user
            job = application.job
            company = application.company

            subject = f'JobTrack Reminder: {reminder.get_reminder_type_display()}'
            body = (
                f'Hi {user.first_name},\n\n'
                f'This is a reminder about your application for '
                f'{job.title} at {company.name}.\n\n'
                f'{reminder.message}\n\n'
                f'Type: {reminder.get_reminder_type_display()}\n'
                f'Current Status: {application.get_status_display()}\n\n'
                f'Cheers,\nJobTrack Automate'
            )

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER or 'noreply@jobtrack.co.za',
                recipient_list=[user.email],
                fail_silently=False,
            )

            # Mark the reminder as sent
            reminder.is_sent = True
            reminder.sent_date = timezone.now()
            reminder.save()

            logger.info(
                'Sent %s reminder to %s for application %s',
                reminder.reminder_type, user.email, application.pk
            )

            return True

        except Exception as e:
            logger.error('Failed to send reminder %s: %s', reminder.pk, e)
            return False

    @staticmethod
    def check_and_send_all() -> int:
        """
        Check for all due reminders and send them.
        Returns the number of reminders sent successfully.
        """
        due_reminders = ReminderService.get_due_reminders()
        sent_count = 0

        for reminder in due_reminders:
            if ReminderService.send_reminder(reminder):
                sent_count += 1

        logger.info(
            'Reminder check complete: %d of %d sent',
            sent_count, len(due_reminders)
        )

        return sent_count

    @staticmethod
    def create_interview_reminder(application, interview_date, message: str = '') -> Reminder:
        """
        Set up a reminder the day before an interview.
        Helps the user prepare in advance.
        """
        reminder_date = interview_date - timedelta(days=1)

        if not message:
            message = (
                f'Your interview for {application.job.title} at '
                f'{application.company.name} is tomorrow. Good luck!'
            )

        return Reminder.objects.create(
            application=application,
            reminder_type='interview',
            reminder_date=reminder_date,
            message=message,
        )
