"""
Form filler for automated job applications.

Handles filling in job application forms automatically.
Works with different job board layouts by using flexible
field detection strategies.
"""
import logging
import time
from typing import Dict, Optional, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, ElementNotInteractableException
)

logger = logging.getLogger('automation')


class FormFiller:
    """
    Handle filling in job application forms automatically.
    Works with different job board layouts.
    """

    def __init__(self, driver: WebDriver, user_profile: Dict[str, Any]) -> None:
        self.driver = driver
        self.profile = user_profile

    def fill_personal_info(self, form_fields: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """
        Fill in the basic personal details on the form.
        Maps our database fields to form fields. Returns a dict
        showing which fields were filled successfully.
        """
        field_mapping = {
            'name': self.profile.get('full_name', ''),
            'first_name': self.profile.get('first_name', ''),
            'last_name': self.profile.get('last_name', ''),
            'email': self.profile.get('email', ''),
            'phone': self.profile.get('phone_number', ''),
            'location': self.profile.get('location', ''),
        }

        # Override with custom field mappings if provided
        if form_fields:
            field_mapping.update(form_fields)

        results = {}
        for field_name, value in field_mapping.items():
            if not value:
                continue

            try:
                element = self._find_form_field(field_name)
                if element:
                    element.clear()
                    element.send_keys(value)
                    results[field_name] = True
                    logger.info('Filled field: %s', field_name)
                else:
                    results[field_name] = False
            except (ElementNotInteractableException, Exception) as e:
                logger.warning('Could not fill field %s: %s', field_name, e)
                results[field_name] = False

        return results

    def _find_form_field(self, field_name: str) -> Optional[Any]:
        """
        Try different strategies to find a form field.
        Job boards all have different HTML structures, so we try
        multiple selectors to find the right element.
        """
        # Common patterns for form field selectors
        selectors = [
            (By.NAME, field_name),
            (By.ID, field_name),
            (By.CSS_SELECTOR, f"input[name*='{field_name}']"),
            (By.CSS_SELECTOR, f"input[id*='{field_name}']"),
            (By.CSS_SELECTOR, f"input[placeholder*='{field_name}']"),
            (By.XPATH, f"//label[contains(text(), '{field_name}')]/following::input[1]"),
        ]

        for by, selector in selectors:
            try:
                element = self.driver.find_element(by, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except NoSuchElementException:
                continue

        return None

    def upload_cv(self, cv_path: str) -> bool:
        """
        Find the CV upload button and attach the file.
        Looks for common file input patterns used by job boards.
        """
        # Common selectors for file upload inputs on job sites
        upload_selectors = [
            "input[type='file'][name*='cv']",
            "input[type='file'][name*='resume']",
            "input[type='file'][name*='document']",
            "input[type='file'][name*='attachment']",
            "input[type='file'][accept*='.pdf']",
            "input[type='file']",
        ]

        for selector in upload_selectors:
            try:
                upload_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                upload_element.send_keys(cv_path)
                time.sleep(2)  # Wait for the upload to process
                logger.info('CV uploaded using selector: %s', selector)
                return True
            except (NoSuchElementException, ElementNotInteractableException):
                continue

        logger.error('Could not find CV upload field')
        return False

    def fill_dropdown(self, field_name: str, value: str) -> bool:
        """Fill in a dropdown (select) field."""
        try:
            element = self._find_form_field(field_name)
            if element and element.tag_name == 'select':
                select = Select(element)
                # Try matching by visible text first, then by value
                try:
                    select.select_by_visible_text(value)
                except NoSuchElementException:
                    select.select_by_value(value)
                return True
        except Exception as e:
            logger.warning('Could not fill dropdown %s: %s', field_name, e)

        return False

    def fill_textarea(self, field_name: str, text: str) -> bool:
        """Fill in a textarea field (like cover letter or notes)."""
        selectors = [
            (By.NAME, field_name),
            (By.CSS_SELECTOR, f"textarea[name*='{field_name}']"),
            (By.CSS_SELECTOR, f"textarea[id*='{field_name}']"),
        ]

        for by, selector in selectors:
            try:
                element = self.driver.find_element(by, selector)
                element.clear()
                element.send_keys(text)
                logger.info('Filled textarea: %s', field_name)
                return True
            except (NoSuchElementException, ElementNotInteractableException):
                continue

        logger.warning('Could not find textarea: %s', field_name)
        return False

    def click_submit(self) -> bool:
        """
        Find and click the submit button on the form.
        Tries various common button selectors.
        """
        submit_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Submit')]"),
            (By.XPATH, "//button[contains(text(), 'Apply')]"),
            (By.XPATH, "//input[@value='Submit']"),
            (By.XPATH, "//input[@value='Apply']"),
        ]

        for by, selector in submit_selectors:
            try:
                button = self.driver.find_element(by, selector)
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    logger.info('Clicked submit button')
                    return True
            except (NoSuchElementException, ElementNotInteractableException):
                continue

        logger.error('Could not find submit button')
        return False

    def wait_for_element(self, by: By, selector: str, timeout: int = 10) -> Optional[Any]:
        """Wait for an element to appear on the page."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            logger.warning('Timed out waiting for element: %s', selector)
            return None
