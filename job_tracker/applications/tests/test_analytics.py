import pytest
from datetime import timedelta
from django.utils import timezone

from applications.services.analytics_engine import AnalyticsEngine
from applications.services.status_tracker import StatusTracker
from applications.services.application_manager import ApplicationManager
from applications.services.reminder_service import ReminderService
from applications.tests.factories import (
    ApplicationFactory,
    ReminderFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestAnalyticsEngine:
    """Tests for the analytics engine calculations."""

    def setup_method(self):
        """Create a test user with some applications for analytics."""
        self.user = UserFactory()

    def test_response_rate_no_applications(self):
        rate = AnalyticsEngine.calculate_response_rate(self.user)
        assert rate == 0

    def test_response_rate_with_data(self):
        # 2 out of 4 got a positive response (screening/interview/offer/accepted)
        ApplicationFactory(user=self.user, status='applied')
        ApplicationFactory(user=self.user, status='applied')
        ApplicationFactory(user=self.user, status='interview_scheduled')
        ApplicationFactory(user=self.user, status='screening')
        rate = AnalyticsEngine.calculate_response_rate(self.user)
        assert rate == 50.0

    def test_interview_rate_no_applications(self):
        rate = AnalyticsEngine.calculate_interview_rate(self.user)
        assert rate == 0

    def test_interview_rate_with_data(self):
        ApplicationFactory(user=self.user, status='applied')
        ApplicationFactory(user=self.user, status='interview_scheduled')
        ApplicationFactory(user=self.user, status='interview_scheduled')
        ApplicationFactory(user=self.user, status='rejected')
        rate = AnalyticsEngine.calculate_interview_rate(self.user)
        assert rate == 50.0

    def test_applications_by_status(self):
        ApplicationFactory(user=self.user, status='applied')
        ApplicationFactory(user=self.user, status='applied')
        ApplicationFactory(user=self.user, status='interview_scheduled')
        result = AnalyticsEngine.get_applications_by_status(self.user)
        assert isinstance(result, list)

    def test_monthly_trend(self):
        ApplicationFactory(user=self.user)
        result = AnalyticsEngine.get_monthly_trend(self.user, months=6)
        assert isinstance(result, list)
        assert len(result) == 6

    def test_top_companies(self):
        # apply to the same company multiple times
        from applications.tests.factories import CompanyFactory, JobFactory
        company = CompanyFactory(name='FNB')
        job1 = JobFactory(company=company)
        job2 = JobFactory(company=company)
        ApplicationFactory(user=self.user, job=job1, company=company)
        ApplicationFactory(user=self.user, job=job2, company=company)
        result = AnalyticsEngine.get_top_companies(self.user, limit=5)
        assert isinstance(result, list)


@pytest.mark.django_db
class TestStatusTracker:
    """Tests for the application status state machine."""

    def test_valid_transition_from_applied(self):
        assert StatusTracker.is_valid_transition('applied', 'screening') is True
        assert StatusTracker.is_valid_transition('applied', 'interview_scheduled') is True
        assert StatusTracker.is_valid_transition('applied', 'rejected') is True
        assert StatusTracker.is_valid_transition('applied', 'withdrawn') is True

    def test_invalid_transition(self):
        # cant go from saved to offer directly
        assert StatusTracker.is_valid_transition('saved', 'offer') is False
        # cant go from rejected to interview_scheduled
        assert StatusTracker.is_valid_transition('rejected', 'interview_scheduled') is False

    def test_get_available_transitions(self):
        transitions = StatusTracker.get_available_transitions('applied')
        assert isinstance(transitions, list)
        assert 'screening' in transitions
        assert 'rejected' in transitions

    def test_transition_success(self):
        app = ApplicationFactory(status='applied')
        result = StatusTracker.transition(app, 'interview_scheduled')
        assert result is True
        app.refresh_from_db()
        assert app.status == 'interview_scheduled'

    def test_transition_failure(self):
        app = ApplicationFactory(status='saved')
        result = StatusTracker.transition(app, 'offer')
        assert result is False
        app.refresh_from_db()
        assert app.status == 'saved'

    def test_status_summary(self):
        user = UserFactory()
        ApplicationFactory(user=user, status='applied')
        ApplicationFactory(user=user, status='interview_scheduled')
        summary = StatusTracker.get_status_summary(user)
        assert isinstance(summary, dict)


@pytest.mark.django_db
class TestApplicationManager:
    """Tests for the application manager service."""

    def test_check_duplicate_match(self):
        user = UserFactory()
        app = ApplicationFactory(user=user)
        # same user same job should be a duplicate
        assert ApplicationManager.check_duplicate(user, app.job) is True

    def test_check_duplicate_different_job(self):
        user = UserFactory()
        from applications.tests.factories import JobFactory
        job = JobFactory()
        assert ApplicationManager.check_duplicate(user, job) is False

    def test_get_daily_application_count(self):
        user = UserFactory()
        from django.utils import timezone
        ApplicationFactory(
            user=user,
            application_method='automated',
            applied_date=timezone.now()
        )
        ApplicationFactory(
            user=user,
            application_method='automated',
            applied_date=timezone.now()
        )
        count = ApplicationManager.get_daily_application_count(user)
        assert count == 2


@pytest.mark.django_db
class TestReminderService:
    """Tests for the reminder service."""

    def test_get_due_reminders(self):
        app = ApplicationFactory()
        # create a reminder that is due (past date)
        ReminderFactory(
            application=app,
            reminder_date=timezone.now().date() - timedelta(days=1),
            is_sent=False
        )
        # create a future reminder
        ReminderFactory(
            application=app,
            reminder_date=timezone.now().date() + timedelta(days=10),
            is_sent=False
        )
        due = ReminderService.get_due_reminders()
        assert len(due) >= 1

    def test_create_interview_reminder(self):
        app = ApplicationFactory()
        interview_date = timezone.now() + timedelta(days=3)
        reminder = ReminderService.create_interview_reminder(app, interview_date)
        assert reminder is not None
        assert reminder.reminder_type == 'interview'
