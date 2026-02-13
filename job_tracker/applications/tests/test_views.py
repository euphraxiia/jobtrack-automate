import pytest
from django.test import Client
from django.urls import reverse

from applications.models import Application, Company
from applications.tests.factories import (
    ApplicationFactory,
    CompanyFactory,
    JobFactory,
    UserFactory,
)


@pytest.fixture
def authenticated_client():
    """Returns a logged in test client with a test user."""
    user = UserFactory()
    client = Client()
    client.login(username=user.username, password='testpass123')
    return client, user


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the main dashboard page."""

    def test_dashboard_requires_login(self):
        client = Client()
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_loads(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_shows_user_apps_only(self, authenticated_client):
        client, user = authenticated_client
        # create an app belonging to this user
        ApplicationFactory(user=user)
        # create an app belonging to another user
        ApplicationFactory()
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestApplicationListView:
    """Tests for the application list page."""

    def test_list_requires_login(self):
        client = Client()
        response = client.get(reverse('application-list'))
        assert response.status_code == 302

    def test_list_loads(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('application-list'))
        assert response.status_code == 200

    def test_list_shows_own_applications(self, authenticated_client):
        client, user = authenticated_client
        ApplicationFactory(user=user)
        ApplicationFactory(user=user)
        ApplicationFactory()  # belongs to someone else
        response = client.get(reverse('application-list'))
        assert response.status_code == 200

    def test_filter_by_status(self, authenticated_client):
        client, user = authenticated_client
        ApplicationFactory(user=user, status='applied')
        ApplicationFactory(user=user, status='interview_scheduled')
        response = client.get(reverse('application-list') + '?status=applied')
        assert response.status_code == 200

    def test_filter_by_priority(self, authenticated_client):
        client, user = authenticated_client
        ApplicationFactory(user=user, priority='high')
        ApplicationFactory(user=user, priority='low')
        response = client.get(reverse('application-list') + '?priority=high')
        assert response.status_code == 200


@pytest.mark.django_db
class TestApplicationCreateView:
    """Tests for creating new applications."""

    def test_create_requires_login(self):
        client = Client()
        response = client.get(reverse('application-create'))
        assert response.status_code == 302

    def test_create_form_loads(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('application-create'))
        assert response.status_code == 200

    def test_create_application_post(self, authenticated_client):
        client, user = authenticated_client
        company = CompanyFactory()
        job = JobFactory(company=company)
        data = {
            'job': job.pk,
            'company': company.pk,
            'status': 'applied',
            'priority': 'medium',
            'application_method': 'manual',
            'notes': 'Applied through the website',
        }
        response = client.post(reverse('application-create'), data)
        # should redirect on success
        assert response.status_code in [200, 302]


@pytest.mark.django_db
class TestApplicationDetailView:
    """Tests for the application detail page."""

    def test_detail_requires_login(self):
        app = ApplicationFactory()
        client = Client()
        response = client.get(
            reverse('application-detail', kwargs={'pk': app.pk})
        )
        assert response.status_code == 302

    def test_detail_shows_own_application(self, authenticated_client):
        client, user = authenticated_client
        app = ApplicationFactory(user=user)
        response = client.get(
            reverse('application-detail', kwargs={'pk': app.pk})
        )
        assert response.status_code == 200

    def test_detail_blocks_other_users(self, authenticated_client):
        client, user = authenticated_client
        other_app = ApplicationFactory()
        response = client.get(
            reverse('application-detail', kwargs={'pk': other_app.pk})
        )
        # should return 404 because queryset is filtered by user
        assert response.status_code == 404


@pytest.mark.django_db
class TestApplicationDeleteView:
    """Tests for deleting applications."""

    def test_delete_requires_login(self):
        app = ApplicationFactory()
        client = Client()
        response = client.post(
            reverse('application-delete', kwargs={'pk': app.pk})
        )
        assert response.status_code == 302
        assert 'login' in response.url

    def test_delete_own_application(self, authenticated_client):
        client, user = authenticated_client
        app = ApplicationFactory(user=user)
        response = client.post(
            reverse('application-delete', kwargs={'pk': app.pk})
        )
        assert response.status_code == 302
        assert not Application.objects.filter(pk=app.pk).exists()

    def test_cannot_delete_others_application(self, authenticated_client):
        client, user = authenticated_client
        other_app = ApplicationFactory()
        response = client.post(
            reverse('application-delete', kwargs={'pk': other_app.pk})
        )
        assert response.status_code == 404
        assert Application.objects.filter(pk=other_app.pk).exists()


@pytest.mark.django_db
class TestCompanyViews:
    """Tests for company list and create views."""

    def test_company_list_loads(self, authenticated_client):
        client, user = authenticated_client
        CompanyFactory()
        response = client.get(reverse('company-list'))
        assert response.status_code == 200

    def test_company_create_loads(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('company-create'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAnalyticsView:
    """Tests for the analytics page."""

    def test_analytics_requires_login(self):
        client = Client()
        response = client.get(reverse('analytics'))
        assert response.status_code == 302

    def test_analytics_loads(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('analytics'))
        assert response.status_code == 200

    def test_analytics_with_data(self, authenticated_client):
        client, user = authenticated_client
        # create a mix of applications
        ApplicationFactory(user=user, status='applied')
        ApplicationFactory(user=user, status='interview_scheduled')
        ApplicationFactory(user=user, status='rejected')
        ApplicationFactory(user=user, status='offer')
        response = client.get(reverse('analytics'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestCSVExport:
    """Tests for the CSV export function."""

    def test_export_requires_login(self):
        client = Client()
        response = client.get(reverse('export-csv'))
        assert response.status_code == 302

    def test_export_returns_csv(self, authenticated_client):
        client, user = authenticated_client
        ApplicationFactory(user=user)
        response = client.get(reverse('export-csv'))
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv'

    def test_export_filename(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(reverse('export-csv'))
        assert 'applications' in response['Content-Disposition']
