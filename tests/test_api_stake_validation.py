"""API test: stake validation business rules on POST /api/place-bet.

Why this test: stake limits are a direct money-handling rule, cheapest to verify
at the API layer, and the UI cannot cover precision at all (the input masks the
third decimal digit), so the API is the only layer where this rule is testable.
"""
import allure
import pytest

VALID_SELECTION = "HOME"

# Severity is a property of the individual boundary, not of the test function, so it is
# declared per case. Most of these guard input correctness and are normal severity.
# Critical is reserved for the two whose failure costs the operator money: accepting a
# stake above the exposure cap, and accepting one the balance cannot cover.
#
# Note: allure keeps the FIRST severity mark it finds, and a function-level
# @allure.severity decorator is found before a per-param mark, which would silently
# override every case here. That is why the decorator is deliberately absent.
NORMAL = allure.severity(allure.severity_level.NORMAL)
CRITICAL = allure.severity(allure.severity_level.CRITICAL)

MIN_BOUNDARY = (
    "minimum boundary (spec tables disagree: 1.00 vs 1.01; "
    "actual behavior accepts 1.00)"
)


@allure.feature("Single Bet Placement")
@allure.story("TC-05: stake boundary grid and decimal precision")
@allure.title("Stake {stake}: {case}")
@pytest.mark.parametrize(
    "stake, expect_success, error_code, case",
    [
        pytest.param(
            0.99, False, "invalid_stake_min", "below minimum",
            id="below-min-0.99", marks=NORMAL,
        ),
        pytest.param(
            1.00, True, None, MIN_BOUNDARY,
            id="min-boundary-1.00", marks=NORMAL,
        ),
        pytest.param(
            100.00, True, None, "maximum boundary",
            id="max-boundary-100.00", marks=NORMAL,
        ),
        pytest.param(
            100.01, False, "invalid_stake_max", "above maximum",
            id="above-max-100.01", marks=CRITICAL,
        ),
        pytest.param(
            5.234, False, "invalid_stake_precision", "invalid precision, 3 decimal places",
            id="precision-5.234", marks=NORMAL,
        ),
        pytest.param(
            200.00, False, "invalid_stake_max", "exceeds both max and balance",
            id="exceeds-balance-200", marks=CRITICAL,
        ),
    ],
)
def test_place_bet_stake_validation(
    fresh_balance, upcoming_match, stake, expect_success, error_code, case
):
    """Chosen because stake limits are the one control on per-bet exposure, and the
    precision rule is testable only here: the UI input masks a third decimal."""
    client, balance_before = fresh_balance
    response = client.place_bet(upcoming_match["id"], VALID_SELECTION, stake)

    if expect_success:
        with allure.step("Accepted and the stake is deducted"):
            assert response.status_code == 200, (
                f"{case}: expected acceptance, got "
                f"{response.status_code}: {response.text}"
            )
            body = response.json()
            # One test, one rule: this test owns the stake boundaries only.
            # Payout arithmetic is owned by the receipt test; the backend payout
            # was verified manually (stake 10 at odds 2.2 -> payout 22.00 exact).
            assert body["balance"] == round(balance_before - stake, 2), (
                f"{case}: stake must be deducted from balance"
            )
    else:
        with allure.step("Rejected as a semantic validation failure"):
            assert response.status_code == 422, (
                f"{case}: expected 422 rejection, got "
                f"{response.status_code}: {response.text}"
            )
            # The stable error code is part of the contract; the human-readable
            # message is not asserted because wording changes must not fail this test.
            assert response.json()["error"] == error_code, (
                f"{case}: expected error code {error_code!r}, got {response.text}"
            )
