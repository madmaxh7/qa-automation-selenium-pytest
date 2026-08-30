"""E2E UI test: the critical revenue placement.

Why this journey: placing a single bet is the only money path in the product, the one
flow whose breakage stops the business rather than degrading it. Baseline from
GET /api/balance after a reset, fixture from the API catalog (see placement.py), and
the two known receipt defects are deliberately not asserted here: this is the
regression gate and must stay green; they live in test_known_defects.py.
"""
import allure

from tests.placement import SELECTION, STAKE, place_bet


@allure.feature("Single Bet Placement")
@allure.story("TC-01: Place a bet on an upcoming match, stake debited, receipt issued")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Placing a bet debits the stake and issues a receipt")
def test_place_bet_journey(driver, fresh_balance, upcoming_match):
    """Chosen because this is the only money path: if placement breaks, there is no product."""
    api, balance_before = fresh_balance
    expected_odds = upcoming_match["odds"][SELECTION]
    expected_payout = round(STAKE * expected_odds, 2)
    home, away = upcoming_match["homeTeam"], upcoming_match["awayTeam"]

    # Every check is recorded, none stops the test: one run reports every mismatch
    # instead of the first one hiding the rest.
    mismatches = []

    def expect(label, actual, expected):
        if actual != expected:
            mismatches.append(f"{label}: expected {expected!r}, got {actual!r}")

    placement = place_bet(driver, upcoming_match)

    with allure.step("The slip agreed with the catalog before placement"):
        expect("odds button", placement.button_odds, expected_odds)
        expect("slip teams, home first", placement.slip_teams, f"{home} vs {away}")
        expect("slip odds", placement.slip_odds, expected_odds)
        expect("slip payout, stake * odds", placement.slip_payout, expected_payout)

    with allure.step("The receipt identifies the bet and repeats its terms"):
        expect("receipt has a bet id", bool(placement.receipt.bet_id().strip()), True)
        expect("receipt has a timestamp", bool(placement.receipt.placed_at().strip()), True)
        expect("receipt stake", placement.receipt.stake(), STAKE)
        expect("receipt odds", placement.receipt.odds(), expected_odds)

    with allure.step("The stake left the account"):
        placement.receipt.close()
        expect("slip empty after closing the receipt (spec 2.4)", placement.slip.is_empty(), True)
        expected_balance = round(balance_before - STAKE, 2)
        expect("server balance", api.get_balance().json()["balance"], expected_balance)
        driver.refresh()
        expect(
            "header balance after reload",
            placement.main.settled_header_balance(expected_balance),
            expected_balance,
        )

    assert not mismatches, "placement mismatches:\n  " + "\n  ".join(mismatches)
