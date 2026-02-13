"""
Indeed.co.za job board handler.

Handles automation for Indeed South Africa.
Follows the Indeed-specific application and search flow.
"""
import logging
from typing import Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_handler import BaseSiteHandler
from applications.automation.browser_manager import BrowserManager

logger = logging.getLogger('automation')


class IndeedHandler(BaseSiteHandler):
    """
    Handle automation for Indeed.co.za applications.
    Indeed has a fairly straightforward application process.
    """

    BASE_URL = 'https://za.indeed.com'
    SEARCH_URL = 'https://za.indeed.com/jobs'

    def __init__(self, driver: WebDriver, user_data: Dict[str, Any]) -> None:
        super().__init__(driver, user_data)

    def login(self, email: str, password: str) -> bool:
        """Log in to Indeed."""
        try:
            self.navigate_to(f'{self.BASE_URL}/account/login')
            self.dismiss_popups()

            email_field = self.wait_and_find(By.ID, 'ifl-InputFormField-3')
            if not email_field:
                email_field = self.wait_and_find(By.CSS_SELECTOR, "input[type='email']")

            if email_field:
                email_field.clear()
                email_field.send_keys(email)

            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit']")
            BrowserManager.random_delay(2, 3)

            # Indeed sometimes uses a two-step login
            password_field = self.wait_and_find(
                By.CSS_SELECTOR, "input[type='password']", timeout=5
            )
            if password_field:
                password_field.clear()
                password_field.send_keys(password)
                self.wait_and_click(By.CSS_SELECTOR, "button[type='submit']")
                BrowserManager.random_delay(2, 4)

            logger.info('Indeed login attempted')
            return True

        except Exception as e:
            logger.error('Indeed login failed: %s', e)
            return False

    def search_jobs(self, keywords: str, location: str = '') -> List[Dict[str, str]]:
        """Search for jobs on Indeed South Africa."""
        try:
            search_url = f'{self.SEARCH_URL}?q={keywords}'
            if location:
                search_url += f'&l={location}'

            self.navigate_to(search_url)
            self.dismiss_popups()
            BrowserManager.random_delay(2, 4)

            jobs = []
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, '.job_seen_beacon, .jobsearch-ResultsList .result'
            )

            for card in job_cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, 'a.jcs-JobTitle, h2 a')
                    jobs.append({
                        'title': link.text.strip(),
                        'url': link.get_attribute('href'),
                    })
                except Exception:
                    continue

            logger.info('Found %d jobs on Indeed for "%s"', len(jobs), keywords)
            return jobs

        except Exception as e:
            logger.error('Indeed job search failed: %s', e)
            return []

    def apply_to_job(self, job_url: str, cv_path: str) -> bool:
        """Apply to a job on Indeed."""
        try:
            self.navigate_to(job_url)
            self.dismiss_popups()
            BrowserManager.random_delay()

            # Look for the apply button
            apply_clicked = self.wait_and_click(
                By.CSS_SELECTOR,
                '#indeedApplyButton, .jobsearch-IndeedApplyButton-newDesign, '
                'button[id*="apply"], .indeed-apply-button'
            )

            if not apply_clicked:
                logger.warning('Could not find apply button on Indeed')
                return False

            BrowserManager.random_delay(1, 3)

            if self.is_login_page():
                email = self.user_data.get('email', '')
                password = self.user_data.get('password', '')
                if not self.login(email, password):
                    return False

            # Fill form fields
            self.fill_form()
            BrowserManager.random_delay()

            # Upload CV
            self.upload_document(cv_path)
            BrowserManager.random_delay()

            # Submit the application
            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit'], .indeed-apply-submit")
            BrowserManager.random_delay(2, 4)

            success = self.verify_submission()
            if success:
                logger.info('Indeed application submitted for: %s', job_url)

            return success

        except Exception as e:
            logger.error('Indeed application failed for %s: %s', job_url, e)
            return False
