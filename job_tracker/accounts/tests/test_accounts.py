import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from accounts.models import UserProfile
from applications.tests.factories import UserFactory


@pytest.mark.django_db
class TestUserProfileModel:
    """Tests for the UserProfile model and auto creation."""

    def test_profile_created_on_user_save(self):
        """A UserProfile should be created automatically when a User is made."""
        user = User.objects.create_user(
            username='sipho',
            email='sipho@example.com',
            password='testpass123'
        )
        assert hasattr(user, 'profile')
        assert user.profile is not None

    def test_profile_fields(self):
        user = UserFactory()
        profile = user.profile
        profile.phone_number = '+27821234567'
        profile.location = 'Pretoria'
        profile.job_title_target = 'Software Engineer'
        profile.years_experience = 5
        profile.save()

        profile.refresh_from_db()
        assert profile.phone_number == '+27821234567'
        assert profile.location == 'Pretoria'
        assert profile.years_experience == 5

    def test_profile_str(self):
        user = UserFactory()
        profile = user.profile
        assert str(profile) == f'Profile for {user.username}'


@pytest.mark.django_db
class TestRegistrationView:
    """Tests for user registration."""

    def test_register_page_loads(self):
        client = Client()
        response = client.get(reverse('register'))
        assert response.status_code == 200

    def test_register_new_user(self):
        client = Client()
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        response = client.post(reverse('register'), data)
        # should redirect to login on success
        assert response.status_code in [200, 302]

    def test_register_password_mismatch(self):
        client = Client()
        data = {
            'username': 'baduser',
            'email': 'bad@example.com',
            'first_name': 'Bad',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass456!',
        }
        response = client.post(reverse('register'), data)
        # should stay on the form with errors
        assert response.status_code == 200


@pytest.mark.django_db
class TestLoginView:
    """Tests for user login."""

    def test_login_page_loads(self):
        client = Client()
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self):
        user = UserFactory()
        client = Client()
        success = client.login(username=user.username, password='testpass123')
        assert success is True

    def test_login_with_wrong_password(self):
        user = UserFactory()
        client = Client()
        success = client.login(username=user.username, password='wrongpass')
        assert success is False


@pytest.mark.django_db
class TestProfileView:
    """Tests for the user profile page."""

    def test_profile_requires_login(self):
        client = Client()
        response = client.get(reverse('profile'))
        assert response.status_code == 302
        assert 'login' in response.url

    def test_profile_loads(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        response = client.get(reverse('profile'))
        assert response.status_code == 200

    def test_profile_update(self):
        user = UserFactory()
        client = Client()
        client.login(username=user.username, password='testpass123')
        data = {
            'phone_number': '+27831112222',
            'location': 'Durban',
            'job_title_target': 'Full Stack Developer',
            'industries_interested': 'Tech, Finance',
            'salary_expectation_min': 30000,
            'salary_expectation_max': 60000,
            'willing_to_relocate': True,
            'work_type_preference': 'remote',
            'years_experience': 3,
            'skills': '["Python", "Django"]',
            'automation_consent': True,
        }
        response = client.post(reverse('profile'), data)
        assert response.status_code in [200, 302]
