"""Match list page: match cards and odds selection. Locators and actions only, no assertions.

Locators are anchored on the ids the application renders for every fixture,
`match-card-<matchId>` and `odds-<matchId>-<home|draw|away>`, where `<matchId>` is the
same id `GET /api/matches` returns. Locating a card by team name is not safe here: a club
appears in several fixtures, so a name lookup silently selects the wrong card.
"""
import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import config
from pages.base_page import BasePage
from pages.parsing import to_amount


class MainPage(BasePage):
    # Two elements print the balance, the header and the bet slip, because the application
    # shares one value between them. The header one is anchored on its container id and
    # then on the text, not on a positional span[2]: an icon span sits first inside the
    # container, and positions shift the moment the markup gains or loses one.
    HEADER_BALANCE = (By.XPATH, "//*[@id='header-balance']/span[contains(text(), 'Balance:')]")

    # ODDS_VALUE and PAST_BADGE are never searched from the driver: select_odds() calls
    # button.find_element(...) and is_marked_past() calls card.find_elements(...). XPath
    # does not scope itself to the element it is called on: a bare '//span' still searches
    # the whole document and would return the first of 300 odds values on the page, not
    # this button's. The leading dot ('.//') is what restricts the search to the element.
    ODDS_VALUE = (By.XPATH, ".//span[contains(@class, 'oddsButtonValue')]")
    PAST_BADGE = (By.XPATH, ".//span[contains(@class, 'badge')]")

    @staticmethod
    def card_locator(match_id: str):
        return By.ID, f"match-card-{match_id}"

    @staticmethod
    def odds_locator(match_id: str, selection: str):
        return By.ID, f"odds-{match_id}-{selection}"

    @allure.step("Open the match list")
    def open(self, base_url: str) -> None:
        """Navigate to the app, authenticating with the configured user id.

        The id is deliberately NOT a method parameter: allure.step serializes every
        argument into the report, which would leak the real id. It is read from
        config here, at the last moment.
        """
        self.driver.get(f"{base_url}/?user-id={config.USER_ID}")
        self._visible(self.HEADER_BALANCE)

    def header_balance(self) -> float:
        """Return the balance as the header currently prints it, without waiting."""
        return self._amount(self.HEADER_BALANCE)

    def settled_header_balance(self, expected: float) -> float:
        """Return the header balance once it settles, or its value at timeout.

        The header shows a 0.00 placeholder until GET /api/balance resolves; the wait
        removes that race. On timeout the current value is returned, so the caller's
        assertion reports the real number, not a TimeoutException. For the unsettled
        value use header_balance().
        """
        try:
            self.wait.until(
                EC.text_to_be_present_in_element(self.HEADER_BALANCE, f"{expected:.2f}")
            )
        except TimeoutException:
            pass
        return self.header_balance()

    def match_card(self, match_id: str):
        return self._present(self.card_locator(match_id))

    def is_marked_past(self, match_id: str) -> bool:
        """True when the card carries the PAST badge the application renders itself."""
        badges = self.match_card(match_id).find_elements(*self.PAST_BADGE)
        return any(b.text.strip().upper() == "PAST" for b in badges)

    @allure.step("Select the {selection} outcome on match {match_id}")
    def select_odds(self, match_id: str, selection: str) -> float:
        """Click one outcome button and return the odds it displayed.
        The catalog holds over a hundred fixtures, so the target is scrolled into
        view first; without it the click can land on a sticky element.
        """
        locator = self.odds_locator(match_id, selection)
        button = self._present(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        odds = to_amount(button.find_element(*self.ODDS_VALUE).text)
        self._click(locator)
        return odds
