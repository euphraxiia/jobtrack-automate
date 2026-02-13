"""
Models for the accounts app.

Extends the default Django user with a profile that stores
job-seeking preferences and personal details needed for
filling in application forms.
"""
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extra information about the user beyond what Django provides.
    Stores job preferences, contact details, and skills.
    """

    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
        ('any', 'Any'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text='City or area, e.g. Johannesburg, Cape Town'
    )
    job_title_target = models.CharField(
        max_length=255,
        blank=True,
        help_text='The type of job you are looking for'
    )
    industries_interested = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated list of industries'
    )
    salary_expectation_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum salary expectation (ZAR per annum)'
    )
    salary_expectation_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum salary expectation (ZAR per annum)'
    )
    willing_to_relocate = models.BooleanField(default=False)
    work_type_preference = models.CharField(
        max_length=10,
        choices=WORK_TYPE_CHOICES,
        default='any'
    )
    years_experience = models.IntegerField(
        null=True,
        blank=True,
        help_text='Total years of work experience'
    )
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text='List of skills as a JSON array'
    )

    # Automation consent - important for POPIA compliance
    automation_consent = models.BooleanField(
        default=False,
        help_text='User has agreed to automation terms'
    )
    automation_consent_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'Profile for {self.user.username}'

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f'{self.user.first_name} {self.user.last_name}'.strip()

    def get_profile_data(self) -> dict:
        """
        Get all the profile data in a dict format.
        Useful for passing to the form filler.
        """
        return {
            'full_name': self.full_name,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'phone_number': self.phone_number,
            'location': self.location,
            'job_title': self.job_title_target,
            'years_experience': self.years_experience,
            'skills': self.skills,
        }


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a profile when a new user signs up."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile whenever the user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
