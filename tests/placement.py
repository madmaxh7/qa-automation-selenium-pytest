"""One bet placement driven through the UI, shared by the E2E test and the
known-defect demonstrations.

The fixture under test comes from the API catalog rather than from the rendered list.
The catalog holds 103 fixtures with the past ones first and the date filter defaults
to All, so "click the first match" would select a played fixture, and a lookup by team
name is ambiguous because a club appears in several fixtures. The card is therefore
addressed by the match id the API returns.
"""
from dataclasses import dataclass

import allure

import config
from pages.bet_slip import BetSlip
from pages.main_page import MainPage
from pages.receipt import SuccessReceipt

STAKE = 5.00
SELECTION = "away"


@dataclass
class Placement:
    """What the UI showed at each stage of one placement."""

    main: MainPage
    slip: BetSlip
    receipt: SuccessReceipt
    button_odds: float
    slip_teams: str
    slip_odds: float
    slip_payout: float


def place_bet(driver, match) -> Placement:
    """Drive one placement end to end and capture what the UI displayed on the way."""
    main, slip, receipt = MainPage(driver), BetSlip(driver), SuccessReceipt(driver)

    with allure.step("Open the app and select an outcome on an upcoming fixture"):
        main.open(config.BASE_URL)
        # Precondition, not an assertion: must not be swallowed by xfail(raises=AssertionError).
        if main.is_marked_past(match["id"]):
            raise RuntimeError(
                f"{match['id']} is marked PAST, the test needs an upcoming fixture"
            )
        button_odds = main.select_odds(match["id"], SELECTION)

    with allure.step("Enter the stake and capture the slip before placement"):
        slip.enter_stake(f"{STAKE:.2f}")
        capture = Placement(
            main=main,
            slip=slip,
            receipt=receipt,
            button_odds=button_odds,
            slip_teams=slip.selection_teams(),
            slip_odds=slip.selection_odds(),
            slip_payout=slip.potential_payout(),
        )

    slip.place_bet()
    receipt.wait_until_visible()
    # Captured on every run, not only on failure: the receipt is the artefact the
    # receipt checks are about, and by the time a failure is reported it has been
    # closed and the page has moved on.
    allure.attach(
        driver.get_screenshot_as_png(),
        name="success receipt",
        attachment_type=allure.attachment_type.PNG,
    )
    return capture
