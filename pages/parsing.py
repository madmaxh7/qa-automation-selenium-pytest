"""Parsing of the money and odds strings the UI renders.

One shared helper rather than a copy in every page object: the application prints
amounts in several shapes ("€15.25", "Odds: 3.05", "Balance: €120.00") and each
page object needs the same number out of them.
"""
import re

# The sign is part of the number: a negative balance ("Balance: €-80.00") must not be
# read back as positive, or an overdraft assertion would silently pass.
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def to_amount(text: str) -> float:
    """Return the first numeric value in UI text such as '€15.25' or 'Balance: €120.00'."""
    match = _NUMBER.search(text.replace(",", ""))
    if match is None:
        raise ValueError(f"no numeric value in UI text: {text!r}")
    return float(match.group())
