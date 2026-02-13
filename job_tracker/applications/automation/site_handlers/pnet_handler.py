"""
PNet.co.za job board handler.

Handles automation for PNet, which is one of the most popular
job boards in South Africa. Knows the specific form fields
and steps for the PNet application process.
"""
import logging
from typing import Dict, Any, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_handler import BaseSiteHandler
from applications.automation.browser_manager import BrowserManager

logger = logging.getLogger('automation')


class PNetHandler(BaseSiteHandler):
    """
    Handle automation for PNet.co.za applications.
    Knows the specific form fields and steps for PNet.
    """

    BASE_URL = 'https://www.pnet.co.za'
    LOGIN_URL = 'https://www.pnet.co.za/5/login.html'
    SEARCH_URL = 'https://www.pnet.co.za/5/job-search.html'

    def __init__(self, driver: WebDriver, user_data: Dict[str, Any]) -> None:
        super().__init__(driver, user_data)

    def login(self, email: str, password: str) -> bool:
        """
        Log in to PNet with the user's credentials.
        Returns True if the login was successful.
        """
        try:
            self.navigate_to(self.LOGIN_URL)
            self.dismiss_popups()

            # Fill in the email field
            email_field = self.wait_and_find(By.ID, 'email')
            if email_field:
                email_field.clear()
                email_field.send_keys(email)

            BrowserManager.random_delay()

            # Fill in the password field
            password_field = self.wait_and_find(By.ID, 'password')
            if password_field:
                password_field.clear()
                password_field.send_keys(password)

            BrowserManager.random_delay()

            # Click the login button
            self.wait_and_click(By.CSS_SELECTOR, "button[type='submit']")
            BrowserManager.random_delay(2, 4)

            # Check if we are now logged in
            if 'login' not in self.driver.current_url.lower():
                logger.info('PNet login successful')
                return True

            logger.warning('PNet login may have failed')
            return False

        except Exception as e:
            logger.error('PNet login failed: %s', e)
            return False

    def search_jobs(self, keywords: str, location: str = '') -> List[Dict[str, str]]:
        """
        Search for jobs on PNet matching the given criteria.
        Returns a list of job URLs and titles found.
        """
        try:
            self.navigate_to(self.SEARCH_URL)
            self.dismiss_popups()

            # Fill in the search keywords
            keyword_field = self.wait_and_find(By.ID, 'keywords-input')
            if keyword_field:
                keyword_field.clear()
                keyword_field.send_keys(keywords)

            # Fill in the location if given
            if location:
                location_field = self.wait_and_find(By.ID, 'location-input')
                if location_field:
                    location_field.clear()
                    location_field.send_keys(location)

            BrowserManager.random_delay()

            # Click search
            self.wait_and_click(By.CSS_SELECTOR, "button.search-btn")
            BrowserManager.random_delay(2, 4)

            # Collect the job listings from the results
            jobs = []
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, '.job-card, .search-result'
            )

            for card in job_cards:
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, 'a.job-title, h3 a')
                    jobs.append({
                        'title': title_element.text,
                        'url': title_element.get_attribute('href'),
                    })
                except Exception:
                    continue

            logger.info('Found %d jobs on PNet for "%s"', len(jobs), keywords)
            return jobs

        except Exception as e:
            logger.error('PNet job search failed: %s', e)
            return []

    def apply_to_job(self, job_url: str, cv_path: str) -> bool:
        """
        Go through the PNet application process step by step.
        Navigates to the job, clicks apply, fills the form, and submits.
        """
        try:
            # Go to the job page
            self.navigate_to(job_url)
            self.dismiss_popups()
            BrowserManager.random_delay()

            # Click the apply button
            applied = self.wait_and_click(By.CSS_SELECTOR, '#apply-button, .apply-btn, [data-action="apply"]')
            if not applied:
                logger.warning('Could not find apply button on PNet')
                return False

            BrowserManager.random_delay(1, 3)

            # Check if we need to log in first
            if self.is_login_page():
                email = self.user_data.get('email', '')
                password = self.user_data.get('password', '')
                if not self.login(email, password):
                    return False

            # Fill in the application form
            self.fill_form()
            BrowserManager.random_delay()

            # Upload the CV
            self.upload_document(cv_path)
            BrowserManager.random_delay()

            # Submit the application
            self.wait_and_click(By.CSS_SELECTOR, '#submit-application, button[type="submit"]')
            BrowserManager.random_delay(2, 4)

            # Check if it went through
            success = self.verify_submission()
            if success:
                logger.info('PNet application submitted for: %s', job_url)
            else:
                logger.warning('PNet application may not have submitted for: %s', job_url)

            return success

        except Exception as e:
            logger.error('PNet application failed for %s: %s', job_url, e)
            return False
