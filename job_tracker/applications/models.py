"""
Models for the applications app.

These are the core data models that keep track of every job
application, the companies involved, and all the related info.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Company(models.Model):
    """
    Store details about companies we have applied to.
    Keeps a record so we do not lose track of who is who.
    """

    COMPANY_SIZE_CHOICES = [
        ('startup', 'Startup (1-10)'),
        ('small', 'Small (11-50)'),
        ('medium', 'Medium (51-200)'),
        ('large', 'Large (201-1000)'),
        ('enterprise', 'Enterprise (1000+)'),
    ]

    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    company_size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True
    )
    glassdoor_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    notes = models.TextField(blank=True)
    is_blacklisted = models.BooleanField(
        default=False,
        help_text='Flag companies you do not want to apply to again'
    )
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Job(models.Model):
    """
    Store the details of a specific job listing.
    Linked to a company so we can see all jobs at one place.
    """

    WORK_TYPE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
    ]

    SOURCE_PLATFORM_CHOICES = [
        ('pnet', 'PNet'),
        ('careers24', 'Careers24'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('careerjunction', 'CareerJunction'),
        ('gumtree', 'Gumtree'),
        ('company_site', 'Company Website'),
        ('referral', 'Referral'),
        ('other', 'Other'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    work_type = models.CharField(
        max_length=10,
        choices=WORK_TYPE_CHOICES,
        default='onsite'
    )
    posted_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    job_url = models.URLField(blank=True)
    source_platform = models.CharField(
        max_length=20,
        choices=SOURCE_PLATFORM_CHOICES,
        default='other'
    )
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name}"

    @property
    def is_expired(self) -> bool:
        """Check if the closing date has passed."""
        if self.closing_date:
            return self.closing_date < timezone.now().date()
        return False


class Application(models.Model):
    """
    The main model - tracks a single job application from start to finish.
    Links together the user, the job, and all the related bits and pieces.
    """

    STATUS_CHOICES = [
        ('saved', 'Saved'),
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer', 'Offer Received'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
        ('withdrawn', 'Withdrawn'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    METHOD_CHOICES = [
        ('manual', 'Manual'),
        ('automated', 'Automated'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='saved'
    )
    applied_date = models.DateTimeField(null=True, blank=True)
    application_method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        default='manual'
    )
    job_board_url = models.URLField(blank=True)
    cover_letter = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications_as_cover_letter'
    )
    cv_used = models.ForeignKey(
        'documents.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications_as_cv'
    )
    notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    follow_up_date = models.DateField(null=True, blank=True)
    last_contact_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    salary_offered = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    interview_dates = models.JSONField(default=list, blank=True)
    automated_application_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.job.title} at {self.company.name} ({self.status})"

    def mark_as_applied(self) -> None:
        """Set the status to applied and record the date."""
        self.status = 'applied'
        self.applied_date = timezone.now()
        self.save()


class ApplicationActivity(models.Model):
    """
    Log every action taken on an application so we have a full history.
    Useful for seeing what happened and when.
    """

    ACTIVITY_TYPE_CHOICES = [
        ('status_change', 'Status Changed'),
        ('email_sent', 'Email Sent'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('note_added', 'Note Added'),
        ('follow_up', 'Follow-up'),
        ('document_attached', 'Document Attached'),
        ('automated_action', 'Automated Action'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=25,
        choices=ACTIVITY_TYPE_CHOICES
    )
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name_plural = 'application activities'
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"{self.activity_type} on {self.application}"


class AutomationRule(models.Model):
    """
    Define rules for automated job searching and applying.
    Each user can set up multiple rules for different job boards.
    """

    JOB_BOARD_CHOICES = [
        ('pnet', 'PNet'),
        ('careers24', 'Careers24'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('careerjunction', 'CareerJunction'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='automation_rules'
    )
    job_board = models.CharField(max_length=20, choices=JOB_BOARD_CHOICES)
    search_keywords = models.CharField(max_length=500)
    location_filter = models.CharField(max_length=255, blank=True)
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    apply_automatically = models.BooleanField(
        default=False,
        help_text='Apply without user confirmation (use with caution)'
    )
    max_applications_per_day = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.job_board} - {self.search_keywords}"


class Reminder(models.Model):
    """
    Track reminders for follow-ups, interviews, and deadlines.
    The Celery beat scheduler checks these daily and sends emails.
    """

    REMINDER_TYPE_CHOICES = [
        ('follow_up', 'Follow-up'),
        ('interview', 'Interview'),
        ('deadline', 'Deadline'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_type = models.CharField(
        max_length=15,
        choices=REMINDER_TYPE_CHOICES
    )
    reminder_date = models.DateField()
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_date']

    def __str__(self) -> str:
        return f"{self.reminder_type} for {self.application} on {self.reminder_date}"
