"""Shared fixtures and reporting hooks.

Money-spending tests get a clean balance and always restore it. Browser tests attach
a screenshot and the page source to the Allure report whenever they fail, because a
UI failure without a picture of the page is a failure you have to reproduce by hand
before you can read it.
"""
import shutil
import subprocess
from datetime import datetime, timezone

import allure
import pytest

from api.client import BettingApiClient


def pytest_sessionstart(session):
    """Delete the stale HTML report at the start of every run."""
    shutil.rmtree(session.config.rootpath / "allure-report", ignore_errors=True)


def pytest_sessionfinish(session):
    """Regenerate the HTML report from this run's results, best effort."""
    root = session.config.rootpath
    results = root / "allure-results"
    if not results.is_dir() or not any(results.iterdir()):
        return
    cli = shutil.which("allure")
    if cli is None:
        print("\n[allure] CLI not found on PATH, HTML report not generated "
              "(results are in allure-results/, view them with `allure serve`)")
        return
    try:
        done = subprocess.run(
            [cli, "generate", str(results), "-o", str(root / "allure-report"), "--clean"],
            capture_output=True, text=True, timeout=120,
        )
        if done.returncode == 0:
            print(f"\n[allure] report regenerated: {root / 'allure-report'}")
        else:
            print(f"\n[allure] generate failed ({done.returncode}): {done.stderr.strip()[:200]}")
    except Exception as exc:  # noqa: BLE001 - reporting must never fail the run
        print(f"\n[allure] generate skipped: {exc}")


def _attach_browser_evidence(driver, label: str):
    """Attach a screenshot and the rendered DOM to the current Allure test."""
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=f"screenshot {label}",
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(
            driver.page_source,
            name=f"page source {label}",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception:  # noqa: BLE001 - diagnostics must never mask the real failure
        pass


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item):
    """Capture the browser state for failing and expected-failing UI tests.

    Expected failures are included on purpose: the strict-xfail tests are the
    running record of BUG-05 (receipt payout) and BUG-07 (receipt team order), so
    their screenshots are evidence rather than noise. The hook runs before fixture
    teardown, so the browser is still alive.
    """
    report = yield
    # Only the test-body phase matters (the hook also fires for setup and teardown),
    # and only when the test failed for real or failed expectedly (xfail is not
    # "failed" for pytest, it carries the wasxfail attribute instead).
    if report.when == "call" and (report.failed or getattr(report, "wasxfail", None)):
        driver = item.funcargs.get("driver")  # absent for API tests: no browser, no shot
        if driver is not None:
            _attach_browser_evidence(driver, "at failure")
    return report  # a wrapper must hand the report back, or pytest loses it


@pytest.fixture(scope="session")
def api_client() -> BettingApiClient:
    return BettingApiClient()


@pytest.fixture()
def fresh_balance(api_client):
    """Reset balance and return (client, actual_balance).

    Baseline comes from GET /api/balance, not from the reset response:
    the reset response reports 125.50 while the persisted value differs
    (BUG-06 in bug-reports.md), so the read endpoint is the
    only trustworthy source of the starting state.
    """
    with allure.step("Setup: reset balance, then read the persisted baseline"):
        response = api_client.reset_balance()
        assert response.status_code == 200, f"reset-balance failed: {response.status_code}"
        actual = api_client.get_balance().json()["balance"]
    yield api_client, actual
    with allure.step("Teardown: reset balance"):
        api_client.reset_balance()  # guaranteed cleanup regardless of test outcome


@pytest.fixture()
def driver():
    """Chrome per test, headless switchable via HEADLESS env var."""
    import os

    from selenium import webdriver

    options = webdriver.ChromeOptions()
    if os.getenv("HEADLESS", "1") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    # No driver path: Selenium Manager (bundled since Selenium 4.6) resolves and caches
    # the chromedriver matching the installed Chrome.
    drv = webdriver.Chrome(options=options)
    yield drv
    drv.quit()  # guaranteed even on failure


@pytest.fixture(scope="session")
def upcoming_match(api_client):
    """Pick a match with a future kickoff date so the test targets a valid bettable event.

    "Today" is taken in UTC rather than local time, so a CI runner and a developer
    machine in different zones select the same fixture near a day boundary.
    """
    with allure.step("Setup: pick a match with a future kickoff date"):
        matches = api_client.get_matches().json()
        today = datetime.now(timezone.utc).date().isoformat()
        # Odds of exactly 2.00 are excluded on top of the date filter: at that value
        # stake x odds equals stake x 2, so the receipt payout defect (BUG-05) would be
        # invisible and its strict xfail would XPASS for the wrong reason.
        future = [
            m for m in matches
            if m["kickoffDate"] > today and 2.0 not in m["odds"].values()
        ]
        assert future, "No upcoming matches with non-degenerate odds in catalog"
        match = future[0]
        allure.attach(
            f"{match['id']}\n{match['homeTeam']} vs {match['awayTeam']}\n"
            f"kickoff {match['kickoffDate']}\nodds {match['odds']}",
            name="selected match",
            attachment_type=allure.attachment_type.TEXT,
        )
        return match
