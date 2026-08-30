"""Known-defect demonstrations. Not part of the two required tests.

Each test encodes one specification rule the application currently violates and is
marked ``xfail(strict=True)`` with the bug id in the reason: a bug report that
executes. Today they report as expected failures; the day a defect is fixed the suite
goes red until the marker is removed, so a marker cannot outlive its bug.
``raises=AssertionError`` keeps the marker honest: a Selenium timeout or an HTTP
error is a real failure, not an expected one.

Delete this file and the suite is exactly the two tests the assignment asks for.
"""
import allure
import pytest

from tests.placement import place_bet

KNOWN_DEFECT = dict(strict=True, raises=AssertionError)


@allure.feature("Single Bet Placement")
@allure.story("TC-01: Place a bet on an upcoming match, stake debited, receipt issued")
@allure.severity(allure.severity_level.CRITICAL)  # bug-reports.md: High
@allure.title("Receipt payout must equal stake * odds, not stake * 2")
@pytest.mark.xfail(
    **KNOWN_DEFECT,
    reason=(
        "BUG-05: receipt renders payout as a flat stake * 2, ignoring odds "
        "(receipt fields: Spec 2.4; consistency and payout = stake * odds: Domain Context)."
    ),
)
@pytest.mark.usefixtures("fresh_balance")  # for its reset side effect only
def test_receipt_payout_matches_odds(driver, upcoming_match):
    placement = place_bet(driver, upcoming_match)
    assert placement.receipt.payout() == placement.slip_payout, (
        f"receipt payout {placement.receipt.payout()} must equal stake * odds "
        f"{placement.slip_payout} (odds {placement.slip_odds}), not stake * 2 (BUG-05)"
    )


@allure.feature("Single Bet Placement")
@allure.story("TC-01: Place a bet on an upcoming match, stake debited, receipt issued")
@allure.severity(allure.severity_level.NORMAL)  # bug-reports.md: Medium
@allure.title("Receipt must carry the home-first team order")
@pytest.mark.xfail(
    **KNOWN_DEFECT,
    reason=(
        "BUG-07: receipt renders away vs home (Domain Context: home team listed "
        "first, convention carries through to the receipt)."
    ),
)
@pytest.mark.usefixtures("fresh_balance")  # for its reset side effect only
def test_receipt_team_order(driver, upcoming_match):
    home, away = upcoming_match["homeTeam"], upcoming_match["awayTeam"]
    placement = place_bet(driver, upcoming_match)
    assert placement.receipt.match() == f"{home} vs {away}", (
        f"receipt shows {placement.receipt.match()!r}, "
        f"expected {home!r} vs {away!r} home-first (BUG-07)"
    )


@allure.feature("Single Bet Placement")
@allure.story("TC-02: API rejects negative stakes and stakes beyond available funds")
@allure.severity(allure.severity_level.NORMAL)  # bug-reports.md: Medium
@allure.title("place-bet must return currency EUR, not USD")
@pytest.mark.xfail(
    **KNOWN_DEFECT,
    reason=(
        "BUG-08: POST /api/place-bet returns currency 'USD' while the contract and "
        "GET /api/balance use 'EUR' (Spec 5.3 place-bet response: currency EUR)."
    ),
)
def test_place_bet_currency_is_eur(fresh_balance, upcoming_match):
    client, _ = fresh_balance
    response = client.place_bet(upcoming_match["id"], "HOME", 5.00)
    # A 4xx/5xx here is a real error, not the expected currency defect: HTTPError is
    # outside raises=AssertionError, so it fails the test instead of counting as xfail.
    response.raise_for_status()
    assert response.json()["currency"] == "EUR", (
        f"place-bet returned {response.json()['currency']!r}, contract requires 'EUR' (BUG-08)"
    )
