"""
Selenium WebDriver configuration for the automation features.

Keeps all the browser settings in one place so we do not
have to repeat ourselves across the different site handlers.
"""
import os
from dataclasses import dataclass, field
from typing import List

from decouple import config


@dataclass
class SeleniumConfig:
    """Hold all the Selenium-related settings."""

    # Browser options
    headless: bool = config('SELENIUM_HEADLESS', default=True, cast=bool)
    browser: str = 'chrome'
    window_width: int = 1920
    window_height: int = 1080

    # Timeouts (in seconds)
    implicit_wait: int = 10
    page_load_timeout: int = 30
    script_timeout: int = 30

    # Safety settings to avoid getting flagged
    min_delay: int = config('APPLICATION_DELAY_MIN', default=2, cast=int)
    max_delay: int = config('APPLICATION_DELAY_MAX', default=5, cast=int)
    max_daily_applications: int = config('MAX_DAILY_APPLICATIONS', default=10, cast=int)

    # Screenshot directory for debugging
    screenshot_dir: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'job_tracker', 'media', 'screenshots'
    )

    # User agents to rotate through so we look like a real browser
    user_agents: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ])

    # Chrome-specific options
    chrome_arguments: List[str] = field(default_factory=lambda: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-gpu',
        '--disable-infobars',
    ])

    def get_chrome_options(self):
        """Build the Chrome options object with all our settings."""
        from selenium import webdriver

        options = webdriver.ChromeOptions()

        if self.headless:
            options.add_argument('--headless=new')

        for arg in self.chrome_arguments:
            options.add_argument(arg)

        options.add_argument(f'--window-size={self.window_width},{self.window_height}')

        # Remove the "Chrome is being controlled by automated test software" bar
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        return options


# Default config instance
default_config = SeleniumConfig()
