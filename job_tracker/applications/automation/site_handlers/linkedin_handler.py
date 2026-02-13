"""
LinkedIn job board handler.

Handles automation for LinkedIn job applications.
LinkedIn has a more complex application flow so this handler
needs to deal with Easy Apply and external redirects.
"""
import logging
from typing import Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_handler import BaseSiteHandler
from applications.automation.browser_manager import BrowserManager

logger = logging.getLogger('automation')


class LinkedInHandler(BaseSiteHandler):
    """
    Handle automation for LinkedIn job applications.
    Supports both Easy Apply and standard application flows.
    """

    BASE_URL = 'https://www.linkedin.com'
    LOGIN_URL = 'https://www.linkedin.com/login'
    JOBS_URL = 'https://www.linkedin.com/jobs/search'

    def __init__(self, driver: WebDriver, user_data: Dict[str, Any]) -> None:
        super().__init__(driver, user_data)

    def login(self, email: str, password: str) -> bool:
        """Log in to LinkedIn."""
        try:
            self.navigate_to(self.LOGIN_URL)

            email_field = self.wait_and_find(By.ID, 'username')
            if email_field:
                email_field.clear()
                email_field.send_keys(email)

            BrowserManager.random_delay()

            password_field = self.wait_and_find(By.ID, 'password')
            if password_field:
                password_field.clear()
                password_field.send_keys(password)

            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit']")
            BrowserManager.random_delay(3, 5)

            # LinkedIn might ask for verification - check for that
            if 'checkpoint' in self.driver.current_url.lower():
                logger.warning('LinkedIn requires verification - manual intervention needed')
                return False

            if 'feed' in self.driver.current_url.lower():
                logger.info('LinkedIn login successful')
                return True

            return False

        except Exception as e:
            logger.error('LinkedIn login failed: %s', e)
            return False

    def search_jobs(self, keywords: str, location: str = '') -> List[Dict[str, str]]:
        """
        Search for jobs on LinkedIn.
        Filters for South African jobs by default if no location given.
        """
        try:
            search_url = f'{self.JOBS_URL}?keywords={keywords}'
            if location:
                search_url += f'&location={location}'
            else:
                search_url += '&location=South%20Africa'

            self.navigate_to(search_url)
            BrowserManager.random_delay(2, 4)

            jobs = []
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, '.job-card-container, .jobs-search-results__list-item'
            )

            for card in job_cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, 'a.job-card-list__title, a.job-card-container__link')
                    jobs.append({
                        'title': link.text.strip(),
                        'url': link.get_attribute('href'),
                    })
                except Exception:
                    continue

            logger.info('Found %d jobs on LinkedIn for "%s"', len(jobs), keywords)
            return jobs

        except Exception as e:
            logger.error('LinkedIn job search failed: %s', e)
            return []

    def apply_to_job(self, job_url: str, cv_path: str) -> bool:
        """
        Apply to a job on LinkedIn.
        Handles Easy Apply where possible. External applications
        are flagged for manual handling.
        """
        try:
            self.navigate_to(job_url)
            BrowserManager.random_delay(1, 3)

            # Check if this is an Easy Apply job
            easy_apply_btn = self.wait_and_find(
                By.CSS_SELECTOR,
                '.jobs-apply-button, button[data-control-name="jobdetails_topcard_inapply"]',
                timeout=5
            )

            if not easy_apply_btn:
                logger.info('Not an Easy Apply job - flagging for manual application')
                return False

            easy_apply_btn.click()
            BrowserManager.random_delay(1, 3)

            # Work through the Easy Apply steps
            return self._complete_easy_apply(cv_path)

        except Exception as e:
            logger.error('LinkedIn application failed for %s: %s', job_url, e)
            return False

    def _complete_easy_apply(self, cv_path: str) -> bool:
        """
        Work through the LinkedIn Easy Apply multi-step form.
        LinkedIn breaks the application into several pages.
        """
        max_steps = 5
        for step in range(max_steps):
            BrowserManager.random_delay(1, 2)

            # Fill in any visible form fields
            self.fill_form()

            # Try to upload CV if there is a file input
            self.upload_document(cv_path)

            # Look for the next button or submit
            next_btn = self.wait_and_find(
                By.CSS_SELECTOR,
                'button[aria-label="Continue to next step"], '
                'button[aria-label="Review your application"], '
                'button[aria-label="Submit application"]',
                timeout=5
            )

            if not next_btn:
                break

            button_text = next_btn.get_attribute('aria-label') or ''

            if 'submit' in button_text.lower():
                next_btn.click()
                BrowserManager.random_delay(2, 4)
                logger.info('LinkedIn Easy Apply submitted')
                return True

            next_btn.click()
            BrowserManager.random_delay(1, 3)

        logger.warning('LinkedIn Easy Apply did not complete within expected steps')
        return False
