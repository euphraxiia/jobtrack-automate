"""
Base handler that all site-specific handlers inherit from.

Provides common methods for navigating pages, filling forms,
and handling the standard bits of the application process.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException
)

from applications.automation.form_filler import FormFiller
from applications.automation.browser_manager import BrowserManager

logger = logging.getLogger('automation')


class BaseSiteHandler(ABC):
    """
    Base class for all job board handlers.
    Each supported site gets its own handler that inherits from this.
    """

    def __init__(self, driver: WebDriver, user_data: Dict[str, Any]) -> None:
        self.driver = driver
        self.user_data = user_data
        self.form_filler = FormFiller(driver, user_data)
        self.wait = WebDriverWait(driver, 10)

    @abstractmethod
    def apply_to_job(self, job_url: str, cv_path: str) -> bool:
        """Apply to a job on this specific site. Must be implemented by each handler."""
        pass

    @abstractmethod
    def login(self, email: str, password: str) -> bool:
        """Log in to the job board. Must be implemented by each handler."""
        pass

    @abstractmethod
    def search_jobs(self, keywords: str, location: str = '') -> list:
        """Search for jobs on this site. Must be implemented by each handler."""
        pass

    def navigate_to(self, url: str) -> bool:
        """Go to a URL and wait for the page to load."""
        try:
            self.driver.get(url)
            BrowserManager.random_delay(1, 2)
            return True
        except Exception as e:
            logger.error('Failed to navigate to %s: %s', url, e)
            return False

    def wait_and_find(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """Wait for an element to appear, then return it."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            logger.warning('Timed out waiting for element: %s=%s', by, value)
            return None

    def wait_and_click(self, by: By, value: str, timeout: int = 10) -> bool:
        """Wait for a clickable element and click it."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            element.click()
            BrowserManager.random_delay()
            return True
        except (TimeoutException, Exception) as e:
            logger.warning('Could not click element %s=%s: %s', by, value, e)
            return False

    def is_login_page(self) -> bool:
        """Check if we have been redirected to a login page."""
        login_indicators = ['login', 'sign-in', 'signin', 'log-in']
        current_url = self.driver.current_url.lower()
        return any(indicator in current_url for indicator in login_indicators)

    def verify_submission(self) -> bool:
        """
        Check if the application was submitted successfully.
        Looks for common success messages on the page.
        """
        BrowserManager.random_delay(2, 4)
        page_source = self.driver.page_source.lower()

        success_phrases = [
            'application submitted',
            'successfully applied',
            'thank you for applying',
            'application received',
            'your application has been sent',
        ]

        for phrase in success_phrases:
            if phrase in page_source:
                logger.info('Application submission verified: found "%s"', phrase)
                return True

        logger.warning('Could not verify submission - no success message found')
        return False

    def dismiss_popups(self) -> None:
        """Try to close any cookie banners or popup overlays."""
        popup_selectors = [
            "button[id*='cookie']",
            "button[class*='cookie']",
            "button[class*='dismiss']",
            "button[class*='close']",
            ".modal-close",
        ]

        for selector in popup_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    element.click()
                    time.sleep(0.5)
            except (NoSuchElementException, Exception):
                continue

    def upload_document(self, file_path: str) -> bool:
        """Upload a CV or cover letter to the form."""
        return self.form_filler.upload_cv(file_path)

    def fill_form(self, custom_fields: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """Fill in the application form with user data."""
        return self.form_filler.fill_personal_info(custom_fields)
