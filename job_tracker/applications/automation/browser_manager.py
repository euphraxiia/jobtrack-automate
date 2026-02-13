"""
Browser manager for Selenium automation.

Sets up and manages the Chrome WebDriver instance.
Handles all the browser options, lifecycle, and safety features
like random delays and screenshot capture.
"""
import logging
import os
import random
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger('automation')


class BrowserManager:
    """
    Set up and manage the Selenium WebDriver instance.
    Handles browser options and driver lifecycle.
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.options = self._build_options()

    def _build_options(self) -> webdriver.ChromeOptions:
        """Put together the Chrome options with all our settings."""
        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless=new')

        # Standard options that make Chrome behave nicely
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--window-size=1920,1080')

        # Pick a random user agent so we look like a normal browser
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')

        # Hide the automation flags
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def start_browser(self) -> webdriver.Chrome:
        """
        Start up the Chrome browser.
        Uses webdriver-manager to sort out the driver automatically.
        """
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            # Remove the webdriver flag from navigator
            self.driver.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'}
            )

            logger.info('Browser started successfully')
            return self.driver

        except Exception as e:
            logger.error('Failed to start browser: %s', e)
            raise

    def close_browser(self) -> None:
        """Shut down the browser properly."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info('Browser closed')
            except Exception as e:
                logger.warning('Error closing browser: %s', e)
            finally:
                self.driver = None

    def take_screenshot(self, name: str, directory: str = 'screenshots') -> Optional[str]:
        """
        Take a screenshot for debugging purposes.
        Saves it with a descriptive filename.
        """
        if not self.driver:
            return None

        os.makedirs(directory, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(directory, f'{name}_{timestamp}.png')

        try:
            self.driver.save_screenshot(filepath)
            logger.info('Screenshot saved: %s', filepath)
            return filepath
        except Exception as e:
            logger.error('Failed to take screenshot: %s', e)
            return None

    @staticmethod
    def random_delay(min_seconds: int = 1, max_seconds: int = 3) -> None:
        """
        Wait a random amount of time between actions.
        Helps avoid detection by making our behaviour less predictable.
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def get_wait(self, timeout: int = 10) -> WebDriverWait:
        """Get a WebDriverWait instance for explicit waits."""
        if not self.driver:
            raise RuntimeError('Browser not started. Call start_browser() first.')
        return WebDriverWait(self.driver, timeout)

    def __enter__(self):
        """Support using BrowserManager as a context manager."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the browser when exiting the context."""
        self.close_browser()
        return False
