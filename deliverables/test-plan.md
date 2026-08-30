# Test Plan: Single Bet Placement

Feature under test: single bet placement on upcoming football matches, desktop web.
Source of truth: the Single Bet Placement Feature Specification (cited by section) and the
Domain Context of the assignment brief. Out of scope per spec 1: live betting,
accumulators, other sports, mobile UX.

## Global preconditions

- Latest desktop Chrome, application at `<BASE_URL>/?user-id=<USER_ID>`; API calls carry
  `x-user-id: <USER_ID>` (spec 5.1). The real id lives in `.env` only and is never written
  into this repository.
- Balance reset with `POST /api/reset-balance` before each scenario, then read back with
  `GET /api/balance`. TC-04 exists because the reset itself is suspect, so no scenario
  trusts the documented starting figure without reading it back.
- Odds are static for the session (spec 3), so odds recorded at selection must still hold
  at placement.

## Priority model

Priority is how likely the defect is, times what it costs if it reaches production. Each
scenario names the risk it controls: **money loss** (wrong payout, unpriced exposure, or
no charge), **data integrity** (stored and displayed state disagree), **user trust**
(figures that change or contradict each other), **spec compliance** (a written rule,
including regulatory-shaped ones such as pre-match only, is not honoured).

## Scenario summary

| ID | Title | Priority | Type | Primary risk | Defects covered |
|----|-------|----------|------|--------------|-----------------|
| TC-01 | Place a bet on an upcoming match, stake debited, receipt issued | Critical | Happy path (E2E) | Money loss | Regression gate; surfaces BUG-05, BUG-07, BUG-11 |
| TC-02 | API rejects negative stakes and stakes beyond available funds | Critical | Negative (API) | Money loss, data integrity | BUG-01, BUG-02, BUG-08 |
| TC-03 | Betting on a non-upcoming (PAST) match is rejected | Critical | Negative | Money loss, spec compliance | BUG-03 |
| TC-04 | reset-balance response body agrees with the persisted balance | High | Consistency (API) | Data integrity | BUG-06 |
| TC-05 | Stake boundary grid and decimal precision | High | Boundary | Money loss, spec compliance | Surfaces the min-stake spec inconsistency |
| TC-06 | Odds filter honours inclusive bounds and rejects invalid ranges | Medium | Negative / boundary | User trust | BUG-09, BUG-10 |

**Top 3 executed** (Part A.2): TC-01, TC-02, TC-03. Together they cover the money path: a
legitimate bet works, an illegitimate stake cannot take money, an ineligible event cannot
be bet on at all. Results are in [bug-reports.md](bug-reports.md).

---

## TC-01: Place a bet on an upcoming match, stake debited, receipt issued

**Priority:** Critical

**Risk Rationale:** Money loss. This is the only revenue path: if placement breaks no bet
can be taken, if it succeeds without debiting the operator carries liability it never
charged for. It is also the regression gate; without it the results of TC-02, TC-05 and
TC-06 mean nothing. Running it end to end also exercises the receipt and balance rendering
rules, which is where BUG-05, BUG-07 and BUG-11 surface.

**Steps:**
1. Reset, read `GET /api/balance`, record it as baseline **B**.
2. Open the application; the header shows **B**.
3. Pick a match with a future `kickoffDate`. Record home team, away team and the odds on
   the outcome to be selected.
4. Click that outcome; the slip shows the same match, outcome and odds.
5. Enter stake `5.00`, record the potential payout the slip shows.
6. Click `Place Bet`, watch the button state.
7. Compare every receipt field with what was recorded in steps 3 to 5, close the receipt.
8. Read the header balance without reloading, reload, read again, compare both with
   `GET /api/balance`.

**Expected Result:**
- The slip holds one selection (spec 2.2) and shows payout = stake x odds (Domain Context).
- `Place Bet` shows `Placing...` and resolves to exactly one outcome, no stuck spinner, no
  two modals (spec 2.3).
- The receipt shows Bet ID, match, selection, stake, odds at placement, potential payout
  and timestamp (spec 2.4), the match as "home vs away" (Match Ordering), the payout equal
  to the slip figure (Bet Receipt: consistent with the pre-placement state).
- Balance falls by exactly €5.00 in the header, the slip and `GET /api/balance`, without
  a reload (spec 2.3; balance is shared per Domain Context).
- Closing the receipt returns to the list with no selection and an empty stake (spec 2.4).

---

## TC-02: API rejects negative stakes and stakes beyond available funds

**Priority:** Critical

**Risk Rationale:** Money loss and data integrity, the sharpest risk in the plan. A negative
or over-funds stake does not produce a wrong bet, it moves money in a direction the product
has no rule for. Both rules are declared at the API layer (spec 4.1), so they must hold when
the browser is bypassed, which is exactly what a retry path or an attacker does. Run against
the API directly because the UI cannot even express these inputs. The place-bet currency
contract (BUG-08) files under this scenario as the same class of API rule.

**Steps:**
1. Reset, read `GET /api/balance` as baseline **B**.
2. `POST /api/place-bet` with a valid upcoming `matchId`, a valid selection and stake
   `-10`. Record status, body and the balance afterwards.
3. Repeat with stake `0`.
4. Spend the balance down below 90.00 with valid bets, then send a stake larger than the
   remaining balance but within the €100.00 maximum (for example remaining + 10). Record
   status and the balance afterwards.
5. Repeat from a second, lower starting point.
6. After every attempt read `GET /api/balance` and compare with **B**.

**Expected Result:**
- A negative stake is rejected with 422: stake "must be a positive number" (Domain
  Context) and the minimum rule admits positive values only (spec 4.1, 5.3).
- A zero stake is rejected on the same rule.
- A stake above the available balance is rejected as insufficient balance (spec 4.1).
- No rejected attempt issues a Bet ID or changes `GET /api/balance`; the balance never
  goes negative.

---

## TC-03: Betting on a non-upcoming (PAST) match is rejected

**Priority:** Critical

**Risk Rationale:** Money loss and spec compliance. A fixture whose kickoff has passed may
already have a public result, so a wager on it is a guaranteed loss against an informed
customer, and the rule is stated twice in the spec and enforced on operators externally.
The catalog is mostly past fixtures, so this is the common case, not an edge case.

**Steps:**
1. `GET /api/matches`, classify every entry by `kickoffDate` against today; note whether
   upcoming fixtures exist at all (TC-01, TC-02 and TC-05 need them).
2. Open the application, widen the date filter to the full catalog, find a past fixture.
3. Try to select an outcome on it; if possible, enter stake `1.00` and click `Place Bet`.
4. Independently, `POST /api/place-bet` with the past `matchId`, a valid selection, stake
   `1.00`.
5. Read `GET /api/balance` after both attempts.

**Expected Result:**
- Past fixtures are absent from the bettable list or their odds buttons cannot be selected
  (spec 1 "Upcoming/Pre-match events only", spec 3 "Upcoming matches only").
- If a selection is still possible, placement is blocked before any request is sent.
- The API rejects a past `matchId` with 422 (spec 5.3).
- No Bet ID is issued and the balance is unchanged.

---

## TC-04: reset-balance response body agrees with the persisted balance

**Priority:** High

**Risk Rationale:** Data integrity, and it multiplies into every other scenario: the reset
is how the plan establishes a known state, so if it reports one figure and stores another,
every balance assertion is computed against a baseline that does not exist. The spec
states the property in a dedicated sentence, so this is a stated contract.

**Steps:**
1. `POST /api/reset-balance`, record `balance` from the response.
2. Immediately `GET /api/balance`, record `balance`.
3. Compare. Repeat once to tell a stable difference from a race.
4. Place a bet of a known stake and check which figure the resulting balance derives from.
5. Spend the balance down, reset again, confirm the reset recovers from a depleted state.

**Expected Result:**
- The two figures are identical: "Response body and persisted state must be consistent
  after reset" (spec 5.3), and both equal the documented €125.50 (Domain Context).
- `currency` is `"EUR"` in both responses (spec 3).
- After a bet the resulting balance derives from the figure the reset reported.

---

## TC-05: Stake boundary grid and decimal precision

**Priority:** High

**Risk Rationale:** Money loss and spec compliance. Stake bounds are the only control on
per-bet exposure, and boundaries are where off-by-one defects live. The scenario also
forces the spec's own contradiction into the open: its sections disagree on the minimum
(1.00 in two places, 1.01 in one),
so the true behaviour has to be recorded, not assumed. High rather than Critical because a
wrong boundary costs one cent per bet, not the whole balance, which is what separates it
from TC-02.

**Steps:**
1. Reset, read the baseline through `GET /api/balance`.
2. For each rejection candidate submit a placement and record status, body and balance:
   `0.99`, `100.01`, `5.234`, `200.00` (above both the maximum and the balance).
3. For each acceptance candidate place a real bet and close the receipt: `1.00`, `100.00`
   (reset before the `100.00` bet so funds are not the limiting factor).
4. Run the same grid through the UI stake field; record the message for each rejection
   and whether `Place Bet` is blocked.
5. Note which minimum each layer actually enforces.

**Expected Result:**
- `0.99` rejected below the minimum, `100.01` above the maximum, at both layers (spec 4.1).
- `100.00` accepted: the €100.00 maximum (spec 3) is inclusive.
- Three-decimal stakes rejected for invalid precision (spec 3, 4.1).
- The UI shows at least the copy of spec 4.4: `Minimum stake is €1.00`, `Maximum stake is
  €100.00`.
- Behaviour at `1.00` is identical in UI and API, and is recorded against the conflict:
  spec 3 and 4.4 say €1.00, the validation table in 4.1 says €1.01.
- No rejected attempt debits the balance or issues a Bet ID.

---

## TC-06: Odds filter honours inclusive bounds and rejects invalid ranges

**Priority:** Medium

**Risk Rationale:** User trust. A filter defect takes no money, which keeps it below the
money-path scenarios, but it hides inventory the operator is trying to sell: a customer who
filters for a price and sees nothing concludes the market does not exist. An empty list
looks like a legitimate answer, so the defect is unlikely to be reported and can persist.
Both halves are explicit spec requirements.

**Steps:**
1. From `GET /api/matches` pick a fixture priced at exactly some value **P** on one outcome.
2. Apply the odds filter with min = max = **P**, record the result.
3. Widen to **P** minus 0.01 up to **P** plus 0.01, compare.
4. Apply a range whose lower bound is exactly **P**, then one just below it; repeat for the
   upper bound.
5. Apply an inverted range, min above max.
6. Check that a match qualifies on any of home, draw or away, not only home.

**Expected Result:**
- A point range min = max = **P** returns the fixture priced at **P**; a fixture priced
  exactly at either bound is included ("min/max range (inclusive)", spec 2.6).
- An inverted range is rejected with clear feedback (spec 2.6). An empty list with no
  message does not qualify: it is indistinguishable from a valid range that matched
  nothing.
- Matching considers all three outcomes.
