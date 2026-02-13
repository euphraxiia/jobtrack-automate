"""
Models for the documents app.

Stores CVs, cover letters, certificates, and other documents
that users upload. Each document is versioned so users can
keep track of different versions of their CV.
"""
from django.db import models
from django.conf import settings

from applications.utils.validators import validate_cv_file, validate_certificate_file


def document_upload_path(instance, filename: str) -> str:
    """
    Work out where to save the uploaded file.
    Organises files by user and document type.
    """
    doc_type = instance.doc_type
    user_id = instance.user_id
    return f'{doc_type}s/user_{user_id}/{filename}'


class Document(models.Model):
    """
    Store uploaded documents like CVs, cover letters, and certificates.
    Keeps different versions so users can pick the right one for each application.
    """

    DOC_TYPE_CHOICES = [
        ('cv', 'CV / Resume'),
        ('cover_letter', 'Cover Letter'),
        ('certificate', 'Certificate'),
        ('portfolio', 'Portfolio'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    doc_type = models.CharField(max_length=15, choices=DOC_TYPE_CHOICES)
    title = models.CharField(
        max_length=255,
        help_text='Give it a descriptive name, e.g. "Senior Dev CV v3"'
    )
    file = models.FileField(upload_to=document_upload_path)
    version = models.CharField(
        max_length=20,
        blank=True,
        default='1.0',
        help_text='Version number for this document'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this the version you want to use for new applications?'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Tags for categorising, e.g. ["tech", "senior", "python"]'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self) -> str:
        return f'{self.title} ({self.get_doc_type_display()}) v{self.version}'

    @property
    def file_extension(self) -> str:
        """Get the file extension."""
        if self.file and self.file.name:
            return self.file.name.rsplit('.', 1)[-1].lower()
        return ''

    @property
    def file_size_mb(self) -> float:
        """Get the file size in megabytes."""
        if self.file:
            try:
                return round(self.file.size / (1024 * 1024), 2)
            except Exception:
                return 0.0
        return 0.0


class CoverLetterTemplate(models.Model):
    """
    Reusable cover letter templates with variable placeholders.
    Users can create templates and customise them per application.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cover_letter_templates'
    )
    name = models.CharField(max_length=255)
    content = models.TextField(
        help_text=(
            'Use placeholders like {company_name}, {job_title}, '
            '{your_skills} for auto-filling'
        )
    )
    job_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='What kind of jobs is this template for?'
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']

    def __str__(self) -> str:
        return self.name

    def render(self, context: dict) -> str:
        """
        Fill in the template placeholders with actual values.
        Uses Python string formatting with the context dict.
        """
        try:
            return self.content.format(**context)
        except KeyError as e:
            return self.content  # Return unformatted if a key is missing
