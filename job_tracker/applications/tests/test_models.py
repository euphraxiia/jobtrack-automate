import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from applications.models import (
    Application,
    ApplicationActivity,
    AutomationRule,
    Company,
    Job,
    Reminder,
)
from applications.tests.factories import (
    ApplicationFactory,
    CompanyFactory,
    JobFactory,
    ReminderFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestCompanyModel:
    """Tests for the Company model."""

    def test_create_company(self):
        company = CompanyFactory()
        assert company.pk is not None
        assert company.name.startswith('Test Company')

    def test_company_str(self):
        company = CompanyFactory(name='Discovery Limited')
        assert str(company) == 'Discovery Limited'

    def test_company_defaults(self):
        company = Company.objects.create(name='Takealot')
        assert company.is_blacklisted is False
        assert company.company_size == ''
        assert company.glassdoor_rating is None

    def test_blacklisted_company(self):
        company = CompanyFactory(is_blacklisted=True)
        assert company.is_blacklisted is True

    def test_company_ordering(self):
        """Companies should be ordered by name by default."""
        CompanyFactory(name='Zando')
        CompanyFactory(name='Absa')
        CompanyFactory(name='MTN')
        companies = Company.objects.all()
        names = [c.name for c in companies]
        assert names == sorted(names)


@pytest.mark.django_db
class TestJobModel:
    """Tests for the Job model."""

    def test_create_job(self):
        job = JobFactory()
        assert job.pk is not None
        assert job.company is not None

    def test_job_str(self):
        company = CompanyFactory(name='Standard Bank')
        job = JobFactory(title='Data Analyst', company=company)
        assert str(job) == 'Data Analyst at Standard Bank'

    def test_job_source_platforms(self):
        """Check that all SA job board choices are valid."""
        valid_platforms = ['pnet', 'careers24', 'linkedin', 'indeed', 'other']
        for platform in valid_platforms:
            job = JobFactory(source_platform=platform)
            assert job.source_platform == platform

    def test_job_work_types(self):
        valid_types = ['remote', 'onsite', 'hybrid']
        for work_type in valid_types:
            job = JobFactory(work_type=work_type)
            assert job.work_type == work_type

    def test_job_salary_range(self):
        job = JobFactory(salary_range='R30 000 - R50 000')
        assert job.salary_range == 'R30 000 - R50 000'


@pytest.mark.django_db
class TestApplicationModel:
    """Tests for the Application model and its status workflow."""

    def test_create_application(self):
        app = ApplicationFactory()
        assert app.pk is not None
        assert app.user is not None
        assert app.job is not None
        assert app.company is not None

    def test_application_str(self):
        company = CompanyFactory(name='Vodacom')
        job = JobFactory(title='Backend Dev', company=company)
        app = ApplicationFactory(job=job, company=company)
        assert 'Backend Dev' in str(app)
        assert 'Vodacom' in str(app)

    def test_default_status(self):
        """The default status on the model is saved."""
        company = CompanyFactory()
        job = JobFactory(company=company)
        user = UserFactory()
        app = Application.objects.create(
            user=user, job=job, company=company
        )
        assert app.status == 'saved'

    def test_all_status_choices(self):
        valid_statuses = [
            'saved', 'applied', 'screening', 'interview_scheduled',
            'interviewed', 'offer', 'accepted', 'rejected', 'withdrawn'
        ]
        for status in valid_statuses:
            app = ApplicationFactory(status=status)
            assert app.status == status

    def test_priority_choices(self):
        for priority in ['low', 'medium', 'high']:
            app = ApplicationFactory(priority=priority)
            assert app.priority == priority

    def test_application_method_choices(self):
        for method in ['manual', 'automated']:
            app = ApplicationFactory(application_method=method)
            assert app.application_method == method

    def test_application_timestamps(self):
        app = ApplicationFactory()
        assert app.created_at is not None
        assert app.updated_at is not None

    def test_application_with_notes(self):
        app = ApplicationFactory(notes='Had a good feeling about this one')
        assert app.notes == 'Had a good feeling about this one'

    def test_mark_as_applied(self):
        app = ApplicationFactory(status='saved')
        app.mark_as_applied()
        app.refresh_from_db()
        assert app.status == 'applied'
        assert app.applied_date is not None


@pytest.mark.django_db
class TestApplicationActivityModel:
    """Tests for activity logging."""

    def test_create_activity(self):
        app = ApplicationFactory()
        activity = ApplicationActivity.objects.create(
            application=app,
            activity_type='note_added',
            description='Sent follow up email'
        )
        assert activity.pk is not None
        assert activity.application == app

    def test_activity_str(self):
        app = ApplicationFactory()
        activity = ApplicationActivity.objects.create(
            application=app,
            activity_type='status_change',
            description='Changed to interview'
        )
        assert 'status_change' in str(activity)

    def test_activity_ordering(self):
        """Activities should be ordered newest first."""
        app = ApplicationFactory()
        a1 = ApplicationActivity.objects.create(
            application=app,
            activity_type='note_added',
            description='First note'
        )
        a2 = ApplicationActivity.objects.create(
            application=app,
            activity_type='note_added',
            description='Second note'
        )
        activities = ApplicationActivity.objects.filter(application=app)
        # ordering is ['-timestamp'], newest first
        assert activities.first().description == 'Second note'


@pytest.mark.django_db
class TestReminderModel:
    """Tests for the Reminder model."""

    def test_create_reminder(self):
        reminder = ReminderFactory()
        assert reminder.pk is not None
        assert reminder.is_sent is False

    def test_reminder_types(self):
        for rtype in ['follow_up', 'interview', 'deadline']:
            reminder = ReminderFactory(reminder_type=rtype)
            assert reminder.reminder_type == rtype

    def test_reminder_str(self):
        reminder = ReminderFactory(reminder_type='follow_up')
        result = str(reminder)
        assert 'follow_up' in result

    def test_mark_reminder_sent(self):
        reminder = ReminderFactory(is_sent=False)
        reminder.is_sent = True
        reminder.save()
        reminder.refresh_from_db()
        assert reminder.is_sent is True


@pytest.mark.django_db
class TestAutomationRuleModel:
    """Tests for the AutomationRule model."""

    def test_create_rule(self):
        rule = AutomationRule.objects.create(
            user=UserFactory(),
            job_board='pnet',
            search_keywords='python developer',
            location_filter='Cape Town',
            is_active=True,
            max_applications_per_day=10
        )
        assert rule.pk is not None
        assert rule.job_board == 'pnet'

    def test_rule_defaults(self):
        rule = AutomationRule.objects.create(
            user=UserFactory(),
            job_board='linkedin',
            search_keywords='data scientist'
        )
        assert rule.is_active is True
        assert rule.max_applications_per_day == 5

    def test_rule_str(self):
        rule = AutomationRule.objects.create(
            user=UserFactory(),
            job_board='indeed',
            search_keywords='analyst'
        )
        assert 'indeed' in str(rule)
        assert 'analyst' in str(rule)
