"""
Status tracker service.

Manages the state machine for application statuses.
Makes sure transitions are valid and logs everything properly.
"""
import logging
from typing import List, Dict, Optional

from applications.models import Application, ApplicationActivity

logger = logging.getLogger('applications')

# Define which status transitions are allowed
VALID_TRANSITIONS: Dict[str, List[str]] = {
    'saved': ['applied', 'withdrawn'],
    'applied': ['screening', 'interview_scheduled', 'rejected', 'withdrawn'],
    'screening': ['interview_scheduled', 'rejected', 'withdrawn'],
    'interview_scheduled': ['interviewed', 'rejected', 'withdrawn'],
    'interviewed': ['offer', 'rejected', 'withdrawn'],
    'offer': ['accepted', 'rejected', 'withdrawn'],
    'rejected': [],
    'accepted': ['withdrawn'],
    'withdrawn': [],
}


class StatusTracker:
    """
    Handle all status-related operations for applications.
    Keeps track of what transitions are valid and enforces them.
    """

    @staticmethod
    def is_valid_transition(current_status: str, new_status: str) -> bool:
        """Check if moving from one status to another is allowed."""
        if current_status == new_status:
            return True
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    @staticmethod
    def get_available_transitions(current_status: str) -> List[str]:
        """Get a list of statuses we can move to from the current one."""
        return VALID_TRANSITIONS.get(current_status, [])

    @staticmethod
    def transition(
        application: Application,
        new_status: str,
        user=None,
        notes: str = ''
    ) -> bool:
        """
        Try to move an application to a new status.
        Returns True if successful, False if the transition is not allowed.
        """
        current = application.status

        if not StatusTracker.is_valid_transition(current, new_status):
            logger.warning(
                'Invalid status transition attempted: %s -> %s for application %s',
                current, new_status, application.pk
            )
            return False

        old_status = application.status
        application.status = new_status
        application.save()

        # Log the transition
        description = f'Status changed from {old_status} to {new_status}'
        if notes:
            description += f'. Notes: {notes}'

        ApplicationActivity.objects.create(
            application=application,
            activity_type='status_change',
            description=description,
            created_by=user,
        )

        logger.info(
            'Application %s transitioned: %s -> %s',
            application.pk, old_status, new_status
        )

        return True

    @staticmethod
    def get_status_summary(user_or_queryset) -> Dict[str, int]:
        """
        Count how many applications are in each status.
        Handy for the dashboard overview.
        Accepts a User object or a queryset of applications.
        """
        from django.contrib.auth.models import User

        if isinstance(user_or_queryset, User):
            applications = Application.objects.filter(user=user_or_queryset)
        else:
            applications = user_or_queryset

        summary = {}
        for status, label in Application.STATUS_CHOICES:
            count = applications.filter(status=status).count()
            summary[status] = count
        return summary

    @staticmethod
    def get_status_display_info() -> List[Dict[str, str]]:
        """
        Get status labels with their display colours for the frontend.
        Used by the kanban board and status badges.
        """
        colour_map = {
            'saved': '#6c757d',
            'applied': '#007bff',
            'screening': '#17a2b8',
            'interview_scheduled': '#ffc107',
            'interviewed': '#fd7e14',
            'offer': '#28a745',
            'rejected': '#dc3545',
            'accepted': '#155724',
            'withdrawn': '#495057',
        }

        return [
            {
                'value': status,
                'label': label,
                'colour': colour_map.get(status, '#6c757d'),
            }
            for status, label in Application.STATUS_CHOICES
        ]
