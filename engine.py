def fv_monthly(pmt: float, rate: float, months: int) -> float:
    if rate == 0:
        return pmt * months
    return pmt * ((1 + rate) ** months - 1) / rate

def monthly_rate(annual: float) -> float:
    return (1 + annual) ** (1/12) - 1

def months_to_payoff(balance: float, apr: float, min_payment: float, extra: float = 0) -> int:
    payment = min_payment + extra
    if payment <= balance * monthly_rate(apr):
        return float('inf')  # Never pays off
    months = 0
    while balance > 0:
        interest = balance * monthly_rate(apr)
        balance += interest - payment
        months += 1
        if months > 1200: return float('inf')
    return months

def total_interest_paid(balance: float, apr: float, min_payment: float, extra: float = 0) -> float:
    payment = min_payment + extra
    total_interest = 0
    current = balance
    while current > 0:
        interest = current * monthly_rate(apr)
        total_interest += interest
        current += interest - payment
        if current < 0: current = 0
    return total_interest
