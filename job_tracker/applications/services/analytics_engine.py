"""
Analytics engine service.

Works out all the stats and metrics for the dashboard and
analytics pages. Keeps the calculation logic separate from
the views so it is easier to test and maintain.
"""
import logging
from datetime import timedelta
from typing import Dict, Any, List, Optional

from django.contrib.auth.models import User
from django.db.models import Count, Avg, F, Q
from django.utils import timezone

from applications.models import Application

logger = logging.getLogger('applications')


class AnalyticsEngine:
    """
    Work out all the stats and metrics for the dashboard.
    Each method calculates a specific metric.
    """

    @staticmethod
    def calculate_response_rate(user: User) -> float:
        """
        Work out what percentage of applications got a response.
        A response means any status beyond 'applied'.
        """
        total = Application.objects.filter(user=user).exclude(
            status='saved'
        ).count()

        responded = Application.objects.filter(
            user=user,
            status__in=[
                'screening', 'interview_scheduled',
                'interviewed', 'offer', 'accepted'
            ]
        ).count()

        if total == 0:
            return 0.0

        return round((responded / total) * 100, 1)

    @staticmethod
    def calculate_interview_rate(user: User) -> float:
        """
        Work out how many applications actually led to interviews.
        This is a good measure of how well the applications are doing.
        """
        total = Application.objects.filter(user=user).exclude(
            status='saved'
        ).count()

        interviews = Application.objects.filter(
            user=user,
            status__in=[
                'interview_scheduled', 'interviewed',
                'offer', 'accepted'
            ]
        ).count()

        if total == 0:
            return 0.0

        return round((interviews / total) * 100, 1)

    @staticmethod
    def calculate_avg_response_time(user: User) -> Optional[float]:
        """
        Work out the average number of days between applying
        and getting any kind of response.
        """
        responded_apps = Application.objects.filter(
            user=user,
            applied_date__isnull=False,
            status__in=[
                'screening', 'interview_scheduled',
                'interviewed', 'offer', 'accepted', 'rejected'
            ]
        )

        if not responded_apps.exists():
            return None

        total_days = 0
        count = 0

        for app in responded_apps:
            # Use the first activity after applied as response date
            first_response = app.activities.filter(
                activity_type='status_change',
                timestamp__gt=app.applied_date
            ).order_by('timestamp').first()

            if first_response and app.applied_date:
                days = (first_response.timestamp - app.applied_date).days
                total_days += days
                count += 1

        if count == 0:
            return None

        return round(total_days / count, 1)

    @staticmethod
    def get_applications_by_status(user: User) -> List[Dict[str, Any]]:
        """
        Count how many applications are in each status.
        Used for the pie chart on the dashboard.
        """
        return list(
            Application.objects.filter(user=user)
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

    @staticmethod
    def get_monthly_count(user: User) -> int:
        """Count how many applications were made this month."""
        now = timezone.now()
        return Application.objects.filter(
            user=user,
            created_at__year=now.year,
            created_at__month=now.month
        ).count()

    @staticmethod
    def get_monthly_trend(user: User, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get application counts per month for the last N months.
        Used for the line chart showing trends over time.
        """
        result = []
        now = timezone.now()

        for i in range(months - 1, -1, -1):
            # Work out the start and end of each month
            month_date = now - timedelta(days=i * 30)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0)

            if month_date.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)

            count = Application.objects.filter(
                user=user,
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()

            result.append({
                'month': month_start.strftime('%b %Y'),
                'count': count,
            })

        return result

    @staticmethod
    def get_top_companies(user: User, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the companies the user has applied to the most."""
        return list(
            Application.objects.filter(user=user)
            .values('company__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )

    @staticmethod
    def get_success_by_board(user: User) -> List[Dict[str, Any]]:
        """
        Work out the success rate for each job board.
        Helps the user figure out which boards work best for them.
        """
        boards = (
            Application.objects.filter(user=user)
            .values('job__source_platform')
            .annotate(
                total=Count('id'),
                responses=Count(
                    'id',
                    filter=Q(status__in=[
                        'screening', 'interview_scheduled',
                        'interviewed', 'offer', 'accepted'
                    ])
                )
            )
        )

        result = []
        for board in boards:
            total = board['total']
            responses = board['responses']
            rate = round((responses / total) * 100, 1) if total > 0 else 0

            result.append({
                'board': board['job__source_platform'],
                'total': total,
                'responses': responses,
                'response_rate': rate,
            })

        return result
