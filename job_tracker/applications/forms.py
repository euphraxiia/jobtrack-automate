"""
Forms for the applications app.

Django forms for creating and updating applications, companies,
jobs, and automation rules. Handles validation and cleaning.
"""
from django import forms
from django.utils import timezone

from .models import Application, Company, Job, AutomationRule, Reminder


class CompanyForm(forms.ModelForm):
    """Form for adding or editing a company."""

    class Meta:
        model = Company
        fields = [
            'name', 'industry', 'location', 'website',
            'company_size', 'glassdoor_rating', 'notes', 'is_blacklisted'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class JobForm(forms.ModelForm):
    """Form for adding or editing a job listing."""

    class Meta:
        model = Job
        fields = [
            'company', 'title', 'description', 'requirements',
            'salary_range', 'location', 'work_type',
            'posted_date', 'closing_date', 'job_url', 'source_platform'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
            'posted_date': forms.DateInput(attrs={'type': 'date'}),
            'closing_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ApplicationForm(forms.ModelForm):
    """Form for creating or updating a job application."""

    class Meta:
        model = Application
        fields = [
            'job', 'company', 'status', 'application_method',
            'job_board_url', 'cover_letter', 'cv_used', 'notes',
            'priority', 'follow_up_date', 'salary_offered',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        """Check that the status transition is valid."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')

        # If editing an existing application, check the transition
        if self.instance.pk and status:
            old_status = Application.objects.get(pk=self.instance.pk).status
            if not self._is_valid_transition(old_status, status):
                raise forms.ValidationError(
                    f'Cannot change status from {old_status} to {status}.'
                )

        return cleaned_data

    @staticmethod
    def _is_valid_transition(old_status: str, new_status: str) -> bool:
        """
        Check if moving from one status to another is allowed.
        You can always withdraw, and rejected is mostly final.
        """
        # Allowed transitions for each status
        valid_transitions = {
            'saved': ['applied', 'withdrawn'],
            'applied': ['screening', 'interview_scheduled', 'rejected', 'withdrawn'],
            'screening': ['interview_scheduled', 'rejected', 'withdrawn'],
            'interview_scheduled': ['interviewed', 'rejected', 'withdrawn'],
            'interviewed': ['offer', 'rejected', 'withdrawn'],
            'offer': ['accepted', 'rejected', 'withdrawn'],
            'rejected': [],  # Final state
            'accepted': ['withdrawn'],
            'withdrawn': [],  # Final state
        }

        allowed = valid_transitions.get(old_status, [])
        return new_status in allowed or old_status == new_status


class ApplicationFilterForm(forms.Form):
    """Form for filtering applications on the list page."""

    STATUS_CHOICES = [('', 'All Statuses')] + Application.STATUS_CHOICES
    PRIORITY_CHOICES = [('', 'All Priorities')] + Application.PRIORITY_CHOICES

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    search = forms.CharField(max_length=255, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


class AutomationRuleForm(forms.ModelForm):
    """Form for setting up automation rules."""

    class Meta:
        model = AutomationRule
        fields = [
            'job_board', 'search_keywords', 'location_filter',
            'salary_min', 'apply_automatically',
            'max_applications_per_day', 'is_active'
        ]
        widgets = {
            'search_keywords': forms.TextInput(
                attrs={'placeholder': 'e.g. Python Developer, Data Analyst'}
            ),
        }


class ReminderForm(forms.ModelForm):
    """Form for creating a new reminder."""

    class Meta:
        model = Reminder
        fields = ['reminder_type', 'reminder_date', 'message']
        widgets = {
            'reminder_date': forms.DateInput(attrs={'type': 'date'}),
            'message': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_reminder_date(self):
        """Make sure the reminder date is in the future."""
        date = self.cleaned_data.get('reminder_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError('Reminder date must be in the future.')
        return date
