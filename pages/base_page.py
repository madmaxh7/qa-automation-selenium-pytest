"""Shared behaviour for every page object: the driver, one wait policy, element access.

The wait policy is defined once here, so changing it is one edit, not one per page.
The helpers are underscore-prefixed on purpose: a test calls `slip.potential_payout()`,
never `slip._text(...)`, which is what keeps selectors out of test bodies.
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.parsing import to_amount

DEFAULT_WAIT = 15


class BasePage:
    """Base for page objects. Holds no locators of its own and makes no assertions."""

    def __init__(self, driver: WebDriver, wait: int = DEFAULT_WAIT) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, wait)

    def _visible(self, locator) -> WebElement:
        """Wait for the element to be visible and return it."""
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _present(self, locator) -> WebElement:
        """Wait for the element to exist in the DOM, visible or not."""
        return self.wait.until(EC.presence_of_element_located(locator))

    def _text(self, locator) -> str:
        """Text of a visible element, as the user reads it."""
        return self._visible(locator).text

    def _amount(self, locator) -> float:
        """Numeric value parsed out of a rendered money or odds string."""
        return to_amount(self._text(locator))

    def _click(self, locator) -> None:
        """Wait for the element to be clickable, then click it."""
        self.wait.until(EC.element_to_be_clickable(locator)).click()
