import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from applications.models import (
    Application,
    ApplicationActivity,
    AutomationRule,
    Company,
    Job,
    Reminder,
)


class UserFactory(DjangoModelFactory):
    """Creates test users with sequential usernames."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class CompanyFactory(DjangoModelFactory):
    """Creates test company records."""

    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f'Test Company {n}')
    website = factory.LazyAttribute(
        lambda obj: f'https://www.{obj.name.lower().replace(" ", "")}.co.za'
    )
    industry = 'Technology'
    company_size = 'medium'
    location = 'Johannesburg'
    glassdoor_rating = factory.Faker(
        'pydecimal', left_digits=1, right_digits=1,
        min_value=1, max_value=5
    )
    is_blacklisted = False


class JobFactory(DjangoModelFactory):
    """Creates test job records linked to a company."""

    class Meta:
        model = Job

    company = factory.SubFactory(CompanyFactory)
    title = factory.Sequence(lambda n: f'Software Developer {n}')
    description = 'Looking for a skilled developer to join our team.'
    requirements = 'Python, Django, 3 years experience'
    job_url = factory.LazyAttribute(
        lambda obj: f'https://www.pnet.co.za/jobs/{obj.title.lower().replace(" ", "-")}'
    )
    source_platform = 'pnet'
    work_type = 'hybrid'
    salary_range = 'R25 000 - R45 000'


class ApplicationFactory(DjangoModelFactory):
    """Creates test application records with linked job and user."""

    class Meta:
        model = Application

    user = factory.SubFactory(UserFactory)
    job = factory.SubFactory(JobFactory)
    company = factory.LazyAttribute(lambda obj: obj.job.company)
    status = 'applied'
    priority = 'medium'
    application_method = 'manual'
    notes = 'Test application notes'


class ApplicationActivityFactory(DjangoModelFactory):
    """Creates test activity log entries."""

    class Meta:
        model = ApplicationActivity

    application = factory.SubFactory(ApplicationFactory)
    activity_type = 'status_change'
    description = 'Status changed to applied'


class AutomationRuleFactory(DjangoModelFactory):
    """Creates test automation rule configurations."""

    class Meta:
        model = AutomationRule

    user = factory.SubFactory(UserFactory)
    job_board = 'pnet'
    search_keywords = 'python developer'
    location_filter = 'Johannesburg'
    is_active = True
    max_applications_per_day = 5


class ReminderFactory(DjangoModelFactory):
    """Creates test reminder records."""

    class Meta:
        model = Reminder

    application = factory.SubFactory(ApplicationFactory)
    reminder_type = 'follow_up'
    message = 'Remember to follow up on this application'
    reminder_date = factory.Faker('future_date', end_date='+30d')
    is_sent = False
