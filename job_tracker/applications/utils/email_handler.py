"""
Email handler utility.

Manages sending emails for notifications, reminders, and
application-related communications. Wraps Django's email
functionality with our specific templates.
"""
import logging
from typing import List, Optional

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger('applications')


class EmailHandler:
    """Handle sending all types of emails for the application."""

    @staticmethod
    def send_reminder_email(
        to_email: str,
        user_name: str,
        reminder_type: str,
        job_title: str,
        company_name: str,
        message: str
    ) -> bool:
        """Send a reminder email to the user."""
        try:
            subject = f'JobTrack Reminder: {reminder_type} - {job_title}'
            body = (
                f'Hi {user_name},\n\n'
                f'This is a reminder about your application for '
                f'{job_title} at {company_name}.\n\n'
                f'{message}\n\n'
                f'Log in to JobTrack to see more details.\n\n'
                f'Cheers,\nJobTrack Automate'
            )

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER or 'noreply@jobtrack.co.za',
                recipient_list=[to_email],
                fail_silently=False,
            )

            logger.info('Reminder email sent to %s', to_email)
            return True

        except Exception as e:
            logger.error('Failed to send reminder email to %s: %s', to_email, e)
            return False

    @staticmethod
    def send_automation_summary(
        to_email: str,
        user_name: str,
        applications_made: int,
        successful: int,
        failed: int,
        details: List[dict]
    ) -> bool:
        """
        Send a summary email after running automated applications.
        Lets the user know what happened without them having to check.
        """
        try:
            subject = f'JobTrack Automation Summary: {applications_made} applications processed'
            body = (
                f'Hi {user_name},\n\n'
                f'Here is a summary of your automated applications:\n\n'
                f'Total processed: {applications_made}\n'
                f'Successful: {successful}\n'
                f'Failed: {failed}\n\n'
            )

            if details:
                body += 'Details:\n'
                for detail in details:
                    status_text = 'Submitted' if detail.get('success') else 'Failed'
                    body += f"  - {detail.get('title', 'Unknown')} at {detail.get('company', 'Unknown')}: {status_text}\n"

            body += (
                '\nLog in to JobTrack to review and add notes to your applications.\n\n'
                'Cheers,\nJobTrack Automate'
            )

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER or 'noreply@jobtrack.co.za',
                recipient_list=[to_email],
                fail_silently=False,
            )

            logger.info('Automation summary sent to %s', to_email)
            return True

        except Exception as e:
            logger.error('Failed to send automation summary to %s: %s', to_email, e)
            return False

    @staticmethod
    def send_status_update_email(
        to_email: str,
        user_name: str,
        job_title: str,
        company_name: str,
        old_status: str,
        new_status: str
    ) -> bool:
        """Notify the user when an application status changes."""
        try:
            subject = f'Application Update: {job_title} at {company_name}'
            body = (
                f'Hi {user_name},\n\n'
                f'Your application for {job_title} at {company_name} '
                f'has been updated.\n\n'
                f'Previous status: {old_status}\n'
                f'New status: {new_status}\n\n'
                f'Cheers,\nJobTrack Automate'
            )

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER or 'noreply@jobtrack.co.za',
                recipient_list=[to_email],
                fail_silently=False,
            )

            return True

        except Exception as e:
            logger.error('Failed to send status update email: %s', e)
            return False
