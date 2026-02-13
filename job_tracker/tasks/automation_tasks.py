"""
Celery tasks for automation and background processing.

These tasks run asynchronously via Celery workers.
They handle things like automated applications, sending
reminders, and running scheduled job searches.
"""
import logging
import os
from datetime import timedelta

from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger('automation')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def apply_to_job_task(self, user_id: int, job_url: str, job_board: str,
                      cv_id: int = None, dry_run: bool = False) -> dict:
    """
    Apply to a single job using Selenium automation.
    This runs as a background Celery task so it does not
    block the web request.
    """
    from applications.automation.browser_manager import BrowserManager
    from applications.services.application_manager import ApplicationManager
    from accounts.models import UserProfile
    from documents.models import Document

    result = {
        'success': False,
        'job_url': job_url,
        'job_board': job_board,
        'message': '',
    }

    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
        user_data = profile.get_profile_data()

        # Check if we have already applied to this job
        manager = ApplicationManager()
        if manager.check_duplicate(user, job_url):
            result['message'] = 'Already applied to this job'
            logger.info('Duplicate application skipped: %s', job_url)
            return result

        # Check daily application limit
        daily_count = manager.get_daily_application_count(user)
        from django.conf import settings
        max_daily = settings.MAX_DAILY_APPLICATIONS

        if daily_count >= max_daily:
            result['message'] = f'Daily limit reached ({max_daily} applications)'
            logger.info('Daily limit reached for user %s', user.username)
            return result

        # Get the CV file path
        cv_path = None
        if cv_id:
            try:
                doc = Document.objects.get(id=cv_id, user=user, doc_type='cv')
                cv_path = doc.file.path
            except Document.DoesNotExist:
                pass

        if not cv_path:
            # Use the active CV
            active_cv = Document.objects.filter(
                user=user, doc_type='cv', is_active=True
            ).first()
            if active_cv:
                cv_path = active_cv.file.path

        if not cv_path:
            result['message'] = 'No CV found. Upload a CV first.'
            return result

        if dry_run:
            result['success'] = True
            result['message'] = 'Dry run completed - no application submitted'
            logger.info('Dry run for %s', job_url)
            return result

        # Pick the right handler for the job board
        handler = _get_site_handler(job_board, user_data)
        if not handler:
            result['message'] = f'Unsupported job board: {job_board}'
            return result

        # Run the automation
        with BrowserManager(headless=True) as browser:
            driver = browser.driver
            handler.driver = driver
            handler.form_filler.driver = driver

            success = handler.apply_to_job(job_url, cv_path)

            if success:
                result['success'] = True
                result['message'] = 'Application submitted successfully'
                logger.info('Automated application submitted: %s', job_url)
            else:
                result['message'] = 'Application submission could not be verified'
                browser.take_screenshot('failed_application')

        return result

    except User.DoesNotExist:
        result['message'] = 'User not found'
        return result

    except Exception as exc:
        logger.error('Automation task failed: %s', exc)
        result['message'] = f'Task failed: {str(exc)}'

        # Retry the task if we have retries left
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return result


@shared_task
def check_and_send_reminders() -> dict:
    """
    Check for due reminders and send email notifications.
    Runs daily via Celery beat at 8am.
    """
    from applications.services.reminder_service import ReminderService

    sent_count = ReminderService.check_and_send_all()

    return {
        'reminders_sent': sent_count,
        'timestamp': timezone.now().isoformat(),
    }


@shared_task
def run_automated_searches() -> dict:
    """
    Run all active automation rules to search for new jobs.
    Checks each rule, searches the relevant job board,
    and optionally applies to matching jobs.
    """
    from applications.models import AutomationRule
    from applications.services.application_manager import ApplicationManager
    from applications.automation.browser_manager import BrowserManager

    active_rules = AutomationRule.objects.filter(is_active=True).select_related('user')
    results = []

    for rule in active_rules:
        try:
            # Get the right handler for this job board
            user_profile = rule.user.profile
            user_data = user_profile.get_profile_data()
            handler = _get_site_handler(rule.job_board, user_data)

            if not handler:
                continue

            # Search for jobs
            with BrowserManager(headless=True) as browser:
                handler.driver = browser.driver
                jobs_found = handler.search_jobs(
                    rule.search_keywords,
                    rule.location_filter
                )

            results.append({
                'rule_id': rule.id,
                'job_board': rule.job_board,
                'keywords': rule.search_keywords,
                'jobs_found': len(jobs_found),
            })

            # Auto-apply if enabled (queue individual tasks)
            if rule.apply_automatically and jobs_found:
                daily_limit = rule.max_applications_per_day
                for job in jobs_found[:daily_limit]:
                    manager = ApplicationManager()
                    if not manager.check_duplicate(rule.user, job.get('url', '')):
                        apply_to_job_task.delay(
                            user_id=rule.user.id,
                            job_url=job['url'],
                            job_board=rule.job_board,
                        )

        except Exception as e:
            logger.error('Automated search failed for rule %s: %s', rule.id, e)
            results.append({
                'rule_id': rule.id,
                'error': str(e),
            })

    return {'rules_processed': len(results), 'results': results}


@shared_task
def cleanup_old_screenshots() -> dict:
    """
    Remove screenshots older than 7 days.
    Runs weekly to stop the screenshots folder getting too big.
    """
    screenshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'media', 'screenshots'
    )

    if not os.path.exists(screenshot_dir):
        return {'deleted': 0}

    cutoff = timezone.now() - timedelta(days=7)
    deleted_count = 0

    for filename in os.listdir(screenshot_dir):
        filepath = os.path.join(screenshot_dir, filename)
        if os.path.isfile(filepath):
            file_time = os.path.getmtime(filepath)
            if timezone.datetime.fromtimestamp(file_time, tz=timezone.utc) < cutoff:
                os.remove(filepath)
                deleted_count += 1

    logger.info('Cleaned up %d old screenshots', deleted_count)
    return {'deleted': deleted_count}


def _get_site_handler(job_board: str, user_data: dict):
    """
    Get the right site handler for a given job board.
    Returns None if the board is not supported.
    """
    from applications.automation.site_handlers.pnet_handler import PNetHandler
    from applications.automation.site_handlers.careers24_handler import Careers24Handler
    from applications.automation.site_handlers.linkedin_handler import LinkedInHandler
    from applications.automation.site_handlers.indeed_handler import IndeedHandler

    handlers = {
        'pnet': PNetHandler,
        'careers24': Careers24Handler,
        'linkedin': LinkedInHandler,
        'indeed': IndeedHandler,
    }

    handler_class = handlers.get(job_board)
    if handler_class:
        # Pass None as driver - it gets set later when the browser starts
        return handler_class(driver=None, user_data=user_data)

    return None
