# Single Bet Placement: QA Test Plan, Defect Reports and Automation

QA take-home for the Single Bet Placement feature of a sports betting demo application.
The repository holds the manual test design, the defects found while executing it, and a
small Selenium plus pytest framework that runs against the live application.

## Deliverables

| Document | Contents |
|----------|----------|
| [test-plan.md](deliverables/test-plan.md) | Six prioritised scenarios with risk rationale, steps and expected results |
| [bug-reports.md](deliverables/bug-reports.md) | Execution results, fifteen defects with severity, repro steps, business impact and evidence, spec and contract notes, open questions for the PO |
| [strategy.md](deliverables/strategy.md) | Why these two tests, what stays manual, data protection, three scaling recommendations |
| Automation framework and 2 tests | [tests/test_e2e_place_bet.py](tests/test_e2e_place_bet.py) (E2E UI journey), [tests/test_api_stake_validation.py](tests/test_api_stake_validation.py) (API business rule); framework in `api/`, `pages/`, [conftest.py](conftest.py), [config.py](config.py) |
| `evidence/` | Raw API captures and screenshots referenced from the bug reports |

Additive, on top of the required two tests: the known-defects xfail suite
([tests/test_known_defects.py](tests/test_known_defects.py)) and Allure reporting.

## Required stack and extra tooling

- Python 3.10 or newer (run on 3.13), Selenium WebDriver + pytest for UI, `requests` for
  API, latest desktop Chrome. This is the stack fixed by the assignment.
- Extras: **Allure** (`allure-pytest`) for reporting, **python-dotenv** for configuration
  so the candidate id never appears in the repository.
- Java 8 or newer plus npm, only if you want the rendered Allure report. The tests do not
  need either.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS and Linux

pip install -r requirements.txt

cp .env.example .env          # macOS and Linux, then fill in USER_ID
copy .env.example .env        # Windows
```

`.env` holds `USER_ID` (sent as the `x-user-id` header on every API call and as the
`user-id` query parameter in the UI) and, optionally, `BASE_URL` and `HEADLESS`. `.env` is
gitignored; [.env.example](.env.example) is the committed template. [config.py](config.py)
fails fast with one clear message when `USER_ID` is missing or still the placeholder.

## Running the tests

```bash
pytest                                       # the whole suite
pytest tests/test_api_stake_validation.py    # API only, no browser needed
pytest tests/test_e2e_place_bet.py           # UI only
pytest tests/test_known_defects.py           # the three known-defect xfails
HEADLESS=0 pytest tests/test_e2e_place_bet.py   # watch the browser (bash)
$env:HEADLESS="0"; pytest tests/test_e2e_place_bet.py   # same, PowerShell
```

Expected result: `7 passed, 3 xfailed`.

The two required tests are `test_e2e_place_bet.py` and `test_api_stake_validation.py`
(seven green items, the API test is a six-case grid). The three expected failures come
from `test_known_defects.py`, a demonstration on top of the brief: one strict xfail per
known defect (receipt payout, receipt team order, place-bet currency) with the bug id in
the reason, so the suite goes red the day a defect is fixed and the marker cannot outlive
its bug. Delete that file and exactly the two tests remain.

The API tests need no browser: selenium is imported inside the `driver` fixture. The suite
places real bets on the live application, so every money-spending test resets the balance
in setup and again in teardown, and no test depends on another's state.

## Allure report

Raw results go to `allure-results/` on every run (`pytest.ini` wires it in). Rendering the
HTML needs the Allure CLI, a Java application:

```bash
npm install -g allure-commandline    # one time
allure serve allure-results          # generate and open
```

`allure-report/` is regenerated after every pytest session when the `allure` CLI is on
PATH (a missing CLI prints a note and nothing else), so the folder always matches the last
run, even a single test started from the IDE. Both folders are gitignored.

Why Allure: every client call is a step with its request and response attached, every page
action is a step, and a hook attaches a screenshot and the rendered DOM when a UI test
fails or xfails. The receipt is captured on every run, because by the time a failure is
reported the modal has been closed. The user id is never a step parameter, since Allure
serializes step arguments into its output.

## Project structure

```
.
├── api/
│   └── client.py          # BettingApiClient: owns HTTP, headers, timeouts, Allure steps
├── pages/
│   ├── base_page.py       # driver, one wait policy, shared element access
│   ├── main_page.py       # match list: cards and odds selection
│   ├── bet_slip.py        # slip: selection summary, stake field, placement
│   ├── receipt.py         # success modal: the receipt fields
│   └── parsing.py         # shared parsing of rendered money and odds strings
├── tests/
│   ├── placement.py                   # one bet placement, shared by the E2E and known-defect tests
│   ├── test_api_stake_validation.py   # required API test: the stake boundary grid
│   ├── test_e2e_place_bet.py          # required E2E test: the placement journey
│   └── test_known_defects.py          # demonstration: three strict xfails, one bug each
├── deliverables/          # test-plan.md, bug-reports.md, strategy.md
├── evidence/              # raw API captures and screenshots for the bug reports
├── config.py              # environment-driven configuration, fails fast
├── conftest.py            # shared fixtures with guaranteed teardown, reporting hooks
├── pytest.ini
└── requirements.txt
```

Packaging `__init__.py` files and the dotfiles (`.env.example`, `.gitignore`,
`.gitattributes`) are omitted from the tree.

## Design notes

- **Tests carry intent, never transport.** No raw URLs, headers or `requests` calls in a
  test body. `BettingApiClient` owns the session, the auth header and the timeout in one
  private `_request`, so a new endpoint cannot be added without a timeout.
- **Isolation is a fixture.** `fresh_balance` resets the balance before the test and again
  in teardown.
- **Never trust a mutating response for state.** The baseline comes from
  `GET /api/balance`, not from the reset response: the reset reports a balance it does
  not persist (BUG-06), which this discipline surfaced on the suite's first run.
- **One test, one rule.** The stake test owns boundaries; each known-defect test owns a
  single spec rule, so fixes flip tests independently.
- **Elements are addressed by their own ids** (`match-card-<matchId>`,
  `odds-<matchId>-<selection>`), keyed to the ids `GET /api/matches` returns, because the
  catalog lists played fixtures first and club names repeat across fixtures.
- **Waits are conditions, never sleeps.** The header prints a placeholder balance until
  the balance request resolves, so the page object waits for the value to settle and
  returns what it finds on timeout, letting the assertion report the real number.
- **Allure severity is a mapping.** Allure has its own scale, so a bug rated High in
  bug-reports.md maps to Allure CRITICAL and Medium to NORMAL; bug-reports.md is the
  canonical scale.
- **Amounts are floats, on purpose.** Every value in the product has two decimals and is
  compared after `round(..., 2)`; the parser keeps the sign so a negative balance reads
  as negative.

## Current status

`7 passed, 3 xfailed` against the live application. Executing the plan and the exploratory
sessions surfaced fifteen defects, four of them Critical; the most severe are a negative
stake that credits the account and a balance that can be driven negative. The full list is in
[bug-reports.md](deliverables/bug-reports.md), the reasoning in
[strategy.md](deliverables/strategy.md).
