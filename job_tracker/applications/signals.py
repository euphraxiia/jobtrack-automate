"""
Django signals for the applications app.

Automatically log activities whenever an application is
created or its status changes. Keeps the activity trail
up to date without having to do it manually everywhere.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Application, ApplicationActivity


@receiver(post_save, sender=Application)
def log_application_created(sender, instance, created, **kwargs):
    """Log when a new application is created."""
    if created:
        ApplicationActivity.objects.create(
            application=instance,
            activity_type='status_change',
            description=f'Application created with status: {instance.status}',
            created_by=instance.user
        )


@receiver(pre_save, sender=Application)
def log_status_change(sender, instance, **kwargs):
    """Log when the status of an application changes."""
    if not instance.pk:
        # New record, skip - the post_save signal will handle it
        return

    try:
        old_instance = Application.objects.get(pk=instance.pk)
    except Application.DoesNotExist:
        return

    if old_instance.status != instance.status:
        ApplicationActivity.objects.create(
            application=instance,
            activity_type='status_change',
            description=(
                f'Status changed from {old_instance.status} '
                f'to {instance.status}'
            ),
            created_by=instance.user
        )
