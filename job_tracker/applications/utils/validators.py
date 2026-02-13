"""
Validators for the applications app.

Custom validation logic for file uploads, URLs, and other
input data that needs checking before we save it.
"""
import os
from typing import List

from django.core.exceptions import ValidationError


# File types we allow for uploads
ALLOWED_CV_EXTENSIONS = ['.pdf', '.docx', '.doc']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_CERTIFICATE_EXTENSIONS = ALLOWED_CV_EXTENSIONS + ALLOWED_IMAGE_EXTENSIONS

# Max file size in bytes (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_extension(value, allowed_extensions: List[str] = None) -> None:
    """
    Check that the uploaded file has an allowed extension.
    Raises a ValidationError if the file type is not supported.
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_CV_EXTENSIONS

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type {ext} is not supported. '
            f'Allowed types: {", ".join(allowed_extensions)}'
        )


def validate_file_size(value) -> None:
    """
    Check that the uploaded file is not too large.
    We do not want people uploading massive files.
    """
    if value.size > MAX_FILE_SIZE:
        size_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f'File is too large. Maximum size is {size_mb} MB.'
        )


def validate_cv_file(value) -> None:
    """Validate a CV upload (check both extension and size)."""
    validate_file_extension(value, ALLOWED_CV_EXTENSIONS)
    validate_file_size(value)


def validate_certificate_file(value) -> None:
    """Validate a certificate upload."""
    validate_file_extension(value, ALLOWED_CERTIFICATE_EXTENSIONS)
    validate_file_size(value)


def validate_job_url(url: str) -> bool:
    """
    Check if a job URL looks like it is from a supported board.
    Returns True if the URL matches one of our supported sites.
    """
    supported_domains = [
        'pnet.co.za',
        'careers24.com',
        'linkedin.com',
        'indeed.co.za',
        'za.indeed.com',
        'careerjunction.co.za',
        'gumtree.co.za',
    ]

    url_lower = url.lower()
    return any(domain in url_lower for domain in supported_domains)


def validate_salary_range(salary_min: float, salary_max: float) -> None:
    """Check that the salary range makes sense."""
    if salary_min and salary_max and salary_min > salary_max:
        raise ValidationError(
            'Minimum salary cannot be more than maximum salary.'
        )

    if salary_min and salary_min < 0:
        raise ValidationError('Salary cannot be negative.')
