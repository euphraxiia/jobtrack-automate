"""
Careers24.com job board handler.

Handles automation for Careers24, another popular South African
job board. Knows the form structure and application flow.
"""
import logging
from typing import Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_handler import BaseSiteHandler
from applications.automation.browser_manager import BrowserManager

logger = logging.getLogger('automation')


class Careers24Handler(BaseSiteHandler):
    """
    Handle automation for Careers24.com applications.
    Follows the Careers24-specific application flow.
    """

    BASE_URL = 'https://www.careers24.com'
    LOGIN_URL = 'https://www.careers24.com/auth/login'
    SEARCH_URL = 'https://www.careers24.com/jobs'

    def __init__(self, driver: WebDriver, user_data: Dict[str, Any]) -> None:
        super().__init__(driver, user_data)

    def login(self, email: str, password: str) -> bool:
        """Log in to Careers24."""
        try:
            self.navigate_to(self.LOGIN_URL)
            self.dismiss_popups()

            email_field = self.wait_and_find(By.CSS_SELECTOR, "input[name='email'], #email")
            if email_field:
                email_field.clear()
                email_field.send_keys(email)

            BrowserManager.random_delay()

            password_field = self.wait_and_find(By.CSS_SELECTOR, "input[name='password'], #password")
            if password_field:
                password_field.clear()
                password_field.send_keys(password)

            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit'], .login-btn")
            BrowserManager.random_delay(2, 4)

            if 'login' not in self.driver.current_url.lower():
                logger.info('Careers24 login successful')
                return True

            logger.warning('Careers24 login may have failed')
            return False

        except Exception as e:
            logger.error('Careers24 login failed: %s', e)
            return False

    def search_jobs(self, keywords: str, location: str = '') -> List[Dict[str, str]]:
        """Search for jobs on Careers24."""
        try:
            search_url = f'{self.SEARCH_URL}?keyword={keywords}'
            if location:
                search_url += f'&location={location}'

            self.navigate_to(search_url)
            self.dismiss_popups()
            BrowserManager.random_delay(2, 4)

            jobs = []
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, '.job-result, .job-card'
            )

            for card in job_cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, 'a.job-title, h2 a, h3 a')
                    jobs.append({
                        'title': link.text,
                        'url': link.get_attribute('href'),
                    })
                except Exception:
                    continue

            logger.info('Found %d jobs on Careers24 for "%s"', len(jobs), keywords)
            return jobs

        except Exception as e:
            logger.error('Careers24 job search failed: %s', e)
            return []

    def apply_to_job(self, job_url: str, cv_path: str) -> bool:
        """Apply to a job on Careers24."""
        try:
            self.navigate_to(job_url)
            self.dismiss_popups()
            BrowserManager.random_delay()

            # Click the apply button
            applied = self.wait_and_click(
                By.CSS_SELECTOR, '.apply-btn, #apply-now, [data-action="apply"]'
            )
            if not applied:
                logger.warning('Could not find apply button on Careers24')
                return False

            BrowserManager.random_delay(1, 3)

            if self.is_login_page():
                email = self.user_data.get('email', '')
                password = self.user_data.get('password', '')
                if not self.login(email, password):
                    return False

            # Fill the form and upload CV
            self.fill_form()
            BrowserManager.random_delay()
            self.upload_document(cv_path)
            BrowserManager.random_delay()

            # Submit
            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit']")
            BrowserManager.random_delay(2, 4)

            success = self.verify_submission()
            if success:
                logger.info('Careers24 application submitted for: %s', job_url)

            return success

        except Exception as e:
            logger.error('Careers24 application failed for %s: %s', job_url, e)
            return False
