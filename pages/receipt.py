"""Success receipt modal (`modal-success-*` fields).

Trap for anyone extending this: the date filter popover is always in the DOM with
`role="dialog"`, so a generic modal or dialog selector matches it instead of the
receipt. Address the receipt by its id.
"""
import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class SuccessReceipt(BasePage):
    MODAL = (By.ID, "modal-success")
    BET_ID = (By.ID, "modal-success-bet-id")
    MATCH = (By.ID, "modal-success-match")
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    PAYOUT = (By.ID, "modal-success-payout")
    PLACED_AT = (By.ID, "modal-success-placed-at")
    CLOSE = (By.ID, "modal-success-close")

    @allure.step("Wait for the success receipt")
    def wait_until_visible(self) -> "SuccessReceipt":
        self._visible(self.MODAL)
        return self

    def bet_id(self) -> str:
        return self._text(self.BET_ID)

    def match(self) -> str:
        return self._text(self.MATCH)

    def placed_at(self) -> str:
        return self._text(self.PLACED_AT)

    def stake(self) -> float:
        return self._amount(self.STAKE)

    def odds(self) -> float:
        return self._amount(self.ODDS)

    def payout(self) -> float:
        return self._amount(self.PAYOUT)

    @allure.step("Close the receipt")
    def close(self) -> None:
        self._click(self.CLOSE)
