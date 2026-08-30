"""Page objects for the app's single screen, one module per zone:

- main_page.py : header balance + the match list (cards, PAST badges, odds buttons)
- bet_slip.py  : the right-hand slip (selection summary, stake field, Place Bet)
- receipt.py   : the success modal with the receipt fields

base_page.py is not a page but the shared skeleton (driver, one wait policy, element
access); parsing.py turns rendered strings like "Balance: €120.00" into numbers and
lives here because page objects are its only callers.
"""
