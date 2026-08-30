"""Bet slip panel: the selection summary, the stake field and placement.

Every element is addressed by its own id (`bet-slip-*`). A bare `input` selector is
wrong on this page: the first input in the DOM is the odds filter range slider,
not the stake field.
"""
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class BetSlip(BasePage):
    # The selection card carries no ids, only classes, so these two are XPath by class.
    # contains() rather than an exact @class match keeps the same token semantics CSS
    # had: the locator survives the element gaining a second class.
    SELECTION_TEAMS = (By.XPATH, "//div[contains(@class, 'betSelectionTeams')]")
    SELECTION_ODDS = (By.XPATH, "//span[contains(@class, 'betSelectionOdds')]")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET = (By.ID, "bet-slip-place-bet")
    BET_COUNT = (By.ID, "bet-slip-count")

    def selection_teams(self) -> str:
        return self._text(self.SELECTION_TEAMS)

    def selection_odds(self) -> float:
        return self._amount(self.SELECTION_ODDS)

    def potential_payout(self) -> float:
        return self._amount(self.POTENTIAL_PAYOUT)

    def is_empty(self) -> bool:
        """True when the slip holds no selection: its counter badge reads 0."""
        return self._text(self.BET_COUNT) == "0"

    @allure.step("Enter stake {amount}")
    def enter_stake(self, amount: str) -> None:
        field = self.wait.until(EC.element_to_be_clickable(self.STAKE_INPUT))
        field.clear()
        field.send_keys(amount)

    @allure.step("Place the bet")
    def place_bet(self) -> None:
        """Click Place Bet.

        The button is rendered disabled until a valid stake is present, so waiting
        for it to be clickable also waits out the stake validation.
        """
        self._click(self.PLACE_BET)
