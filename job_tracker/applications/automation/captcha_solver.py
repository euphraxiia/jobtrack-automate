"""
CAPTCHA solver utility.

Handles CAPTCHA detection and provides a manual fallback
when automated solving is not possible. We do not try to
bypass CAPTCHAs automatically - that would be dodgy.
"""
import logging
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger('automation')


class CaptchaSolver:
    """
    Detect CAPTCHAs and handle them with a manual fallback.
    We flag CAPTCHAs for the user to solve rather than trying
    to bypass them automatically.
    """

    # Common CAPTCHA indicators on web pages
    CAPTCHA_SELECTORS = [
        '#captcha',
        '.g-recaptcha',
        '.h-captcha',
        'iframe[src*="recaptcha"]',
        'iframe[src*="hcaptcha"]',
        '[data-sitekey]',
        '#captcha-container',
    ]

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def is_captcha_present(self) -> bool:
        """Check if there is a CAPTCHA on the current page."""
        for selector in self.CAPTCHA_SELECTORS:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    logger.info('CAPTCHA detected: %s', selector)
                    return True
            except NoSuchElementException:
                continue

        return False

    def wait_for_manual_solve(self, timeout: int = 120) -> bool:
        """
        Wait for the user to solve the CAPTCHA manually.
        Opens a visible browser window and pauses automation.
        Returns True if the CAPTCHA seems to be solved.
        """
        if not self.is_captcha_present():
            return True

        logger.info(
            'CAPTCHA detected - waiting up to %d seconds for manual solve',
            timeout
        )
        print(
            '\n[JobTrack] CAPTCHA detected! Please solve it in the browser window.\n'
            f'You have {timeout} seconds before we give up.\n'
        )

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.is_captcha_present():
                logger.info('CAPTCHA appears to be solved')
                return True
            time.sleep(2)

        logger.warning('CAPTCHA solve timed out after %d seconds', timeout)
        return False

    def get_captcha_type(self) -> Optional[str]:
        """Work out what type of CAPTCHA we are dealing with."""
        try:
            if self.driver.find_elements(By.CSS_SELECTOR, '.g-recaptcha, iframe[src*="recaptcha"]'):
                return 'recaptcha'
            if self.driver.find_elements(By.CSS_SELECTOR, '.h-captcha, iframe[src*="hcaptcha"]'):
                return 'hcaptcha'
            if self.driver.find_elements(By.CSS_SELECTOR, '#captcha'):
                return 'custom'
        except Exception:
            pass

        return None
