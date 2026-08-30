# Strategy and Recommendations

## Why these two tests

**E2E: place a bet on an upcoming match.** It is the only path where money moves: pick
an outcome, enter a stake, place it, get debited, get a receipt. If a filter breaks the
product is worse; if this breaks there is no product. The test reads its baseline from
`GET /api/balance` after a reset, picks the match by kickoff date so it never lands on a
PAST fixture, and compares the slip, the receipt and the server balance against the same
recorded values.

**API: stake validation grid.** Stake limits are the one control on per-bet exposure and
they are cheapest to check at the API. One of the rules cannot be tested anywhere else:
the UI input masks a third decimal, so precision is only reachable by calling the
endpoint. Six cases: 0.99, 1.00, 100.00, 100.01, 5.234, 200.00. Every rejection also
checks the stable error code, never the message text.

The API test paid for itself on its first run. It failed because `POST /api/reset-balance`
answers 125.50 and stores 120 (BUG-06). A browser never shows those two numbers side by
side, so manual testing would not have caught it. The fix became a rule for the whole
framework: never trust the response of a mutating call, read the state back.

**Three strict xfails.** Receipt payout (BUG-05), receipt team order (BUG-07) and
place-bet currency (BUG-08) are known defects. Each has a test in
`tests/test_known_defects.py` marked `xfail(strict=True)` with the bug id in the reason.
Today they report as expected failures; the day a bug is fixed the suite goes red until
the marker is removed. They are bug reports that execute, a demonstration on top of the
brief: delete that file and the two required tests remain. Suite state:
`7 passed, 3 xfailed`.

## What stays manual

- **Double-click double debit (BUG-04).** The assignment e-mail calls this "not a real-time scenario".
  Reproducing it reliably in automation needs controlled request timing, which belongs in a lower-level test
  that controls request ordering, not in a browser suite.
- **Stale header balance (BUG-11).** A test for "the value does not update" is a flaky
  negative by construction. A human check covers it reliably.
- **Filter UX (BUG-09, BUG-10, BUG-12).** Whether feedback is "clear" is a judgement call,
  cheaper with eyes than with pixel assertions.
- **Error modal and Rebet.** No deterministic trigger from outside yet. Next candidate:
  Chrome's offline mode driven from Selenium fails the request without any server hook,
  and Rebet then has to resubmit identical values.

## Data protection

The candidate id is treated as a secret. It lives in `.env` (`.env.example` is the
template), travels in the `x-user-id` header for the API and appears in a URL only where
the assignment forces it. One leak was found and closed: Allure serializes every argument
of a step-decorated method, so the id was removed from step signatures and is read from
config at the last moment; the regenerated results were grepped for the id fragment.
Screenshots never show the address bar. The full git history was grepped too. Zero hits
everywhere.

## Recommendations at scale

1. **CI gated by cost, not by layer.** Every run places real bets on a shared account,
   so a plain push runs only lint and `pytest --collect-only`. The API suite runs on
   pull requests and on each deploy of the app to a test environment (a minute, three bets).
   E2E runs nightly and on release candidates, headless, with Allure history. Parallel
   runs need one user id per run (point 3).
2. **A contract layer.** A JSON-schema check of our own on every response, with
   `currency` as an enum (the shipped OpenAPI types it as a free string), would have
   caught the USD currency (BUG-08) for free and guards the payout-arithmetic class of
   defects. The cheapest net under the money math.
3. **Trustworthy test data.** Per-user isolation through `x-user-id` is the natural
   mechanism, but reset-balance must tell the truth first (BUG-06), and the catalog needs
   a fixture that cannot age into the past (72 of 103 matches are already played). The
   open spec questions in bug-reports.md need answers before the boundaries they touch are
   automated deeper.
