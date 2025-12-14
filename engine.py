# engine.py
from __future__ import annotations

import math


def monthly_rate(annual: float) -> float:
    """
    Convert annual rate (e.g., 0.07 for 7%) to effective monthly rate.
    """
    return (1.0 + float(annual)) ** (1.0 / 12.0) - 1.0


def fv_monthly(pmt: float, r_monthly: float, months: int) -> float:
    """
    Future value of a monthly contribution stream (end-of-month contributions).
    pmt: monthly contribution (>=0)
    r_monthly: monthly rate (e.g., 0.005)
    months: number of months
    """
    months = int(months)
    if months <= 0 or pmt == 0:
        return 0.0

    r = float(r_monthly)
    pmt = float(pmt)

    if abs(r) < 1e-12:
        return pmt * months

    return pmt * (((1.0 + r) ** months - 1.0) / r)


def months_to_payoff(balance: float, apr: float, min_payment: float, extra_payment: float = 0.0) -> int:
    """
    Simulate months to pay off a balance with (min_payment + extra_payment).
    Returns a large number (1e9) if it will not pay off (payment <= interest).
    """
    b = float(balance)
    if b <= 0:
        return 0

    payment = max(0.0, float(min_payment) + float(extra_payment))
    r = monthly_rate(float(apr))

    # If payment doesn't cover interest, payoff never happens
    if payment <= b * r + 1e-9:
        return 10**9

    months = 0
    # cap to prevent infinite loops
    while b > 0.01 and months < 1_000_000:
        months += 1
        b += b * r
        b -= min(payment, b)

    return months if b <= 0.01 else 10**9


def total_interest_paid(balance: float, apr: float, min_payment: float, extra_payment: float = 0.0) -> float:
    """
    Simulate total interest paid until payoff using (min_payment + extra_payment).
    Returns math.inf if payoff never occurs.
    """
    b = float(balance)
    if b <= 0:
        return 0.0

    payment = max(0.0, float(min_payment) + float(extra_payment))
    r = monthly_rate(float(apr))

    if payment <= b * r + 1e-9:
        return math.inf

    total_int = 0.0
    months = 0
    while b > 0.01 and months < 1_000_000:
        months += 1
        interest = b * r
        total_int += interest
        b += interest
        b -= min(payment, b)

    return total_int
