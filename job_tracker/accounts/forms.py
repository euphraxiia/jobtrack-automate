"""Forms for the accounts app."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    """Form for new user sign-up."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    """Form for editing the user profile."""

    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'location', 'job_title_target',
            'industries_interested', 'salary_expectation_min',
            'salary_expectation_max', 'willing_to_relocate',
            'work_type_preference', 'years_experience', 'skills',
            'automation_consent',
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+27 XX XXX XXXX'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Johannesburg'}),
            'job_title_target': forms.TextInput(attrs={'placeholder': 'e.g. Software Developer'}),
            'industries_interested': forms.TextInput(
                attrs={'placeholder': 'e.g. Tech, Finance, Consulting'}
            ),
        }
