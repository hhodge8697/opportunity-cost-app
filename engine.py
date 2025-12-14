from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

def monthly_rate(annual_rate: float) -> float:
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0

def money(x: float) -> str:
    return f"${x:,.2f}"

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def fra_months_for_birth_year(birth_year: int) -> int:
    if birth_year <= 1937:
        return 65 * 12
    if 1943 <= birth_year <= 1954:
        return 66 * 12
    if birth_year == 1955:
        return 66 * 12 + 2
    if birth_year == 1956:
        return 66 * 12 + 4
    if birth_year == 1957:
        return 66 * 12 + 6
    if birth_year == 1958:
        return 66 * 12 + 8
    if birth_year == 1959:
        return 66 * 12 + 10
    return 67 * 12

def drc_rate_per_year(birth_year: int) -> float:
    return 0.08 if birth_year >= 1943 else 0.06

def ss_monthly_benefit_from_pia(
    pia_at_fra: float,
    birth_year: int,
    claim_age_years: int,
    claim_age_months: int = 0
) -> Tuple[float, int, int]:
    fra_m = fra_months_for_birth_year(birth_year)
    claim_m = claim_age_years * 12 + claim_age_months
    diff = claim_m - fra_m
    if diff == 0:
        return pia_at_fra, fra_m, diff
    if diff < 0:
        early_months = -diff
        first = min(36, early_months)
        rest = max(0, early_months - 36)
        reduction = first * (5/9/100) + rest * (5/12/100)
        reduction = clamp(reduction, 0.0, 1.0)
        return pia_at_fra * (1.0 - reduction), fra_m, diff
    max_delay = max(0, 70 * 12 - fra_m)
    delay_months = min(diff, max_delay)
    drc_per_month = drc_rate_per_year(birth_year) / 12.0
    increase = delay_months * drc_per_month
    return pia_at_fra * (1.0 + increase), fra_m, diff

@dataclass
class Debt:
    name: str
    balance: float
    apr: float
    min_payment: float

@dataclass
class Profile:
    current_age_years: int
    current_age_months: int = 0
    life_expectancy_age_years: int = 90
    retirement_age_years: int = 67
    monthly_income_after_tax: float = 8500.0
    post_retirement_monthly_income: float = 3000.0
    annual_income_growth: float = 0.03
    base_expenses: Dict[str, float] = None
    annual_expense_inflation: float = 0.025
    cash_savings: float = 6000.0
    investment_balance: float = 25000.0
    debts: List[Debt] = None
    invest_annual_return: float = 0.08
    discount_rate: float = 0.04
    emergency_fund_target_months: float = 4.0
    essential_expense_categories: Optional[List[str]] = None
    birth_year: int = 1985
    ss_pia_at_fra_monthly: float = 2800.0

    def __post_init__(self):
        if self.base_expenses is None:
            self.base_expenses = {}
        if self.debts is None:
            self.debts = []

@dataclass
class Scenario:
    name: str
    tithe_enabled: bool = False
    tithe_rate: float = 0.10
    tithe_on_income: bool = True
    tithe_fixed_monthly: float = 0.0
    tithe_start_rule: str = "now"  # now, after_debt_free, after_emergency_fund
    ss_claim_age_years: int = 67
    ss_claim_age_months: int = 0
    invest_after: str = "debt_free"  # always, debt_free

def total_base_expenses(profile: Profile, month: int) -> float:
    inflation_factor = (1 + profile.annual_expense_inflation / 12) ** month
    return sum(profile.base_expenses.values()) * inflation_factor

def essential_expenses(profile: Profile, month: int) -> float:
    inflation_factor = (1 + profile.annual_expense_inflation / 12) ** month
    if profile.essential_expense_categories:
        return sum(profile.base_expenses.get(k, 0.0) for k in profile.essential_expense_categories) * inflation_factor
    return total_base_expenses(profile, month)

def emergency_target(profile: Profile, month: int) -> float:
    return essential_expenses(profile, month) * profile.emergency_fund_target_months

def month_index(age_y: int, age_m: int) -> int:
    return age_y * 12 + age_m

def copy_debts(debts: List[Debt]) -> List[Debt]:
    return [Debt(d.name, d.balance, d.apr, d.min_payment) for d in debts]

def sum_debt_balance(debts: List[Debt]) -> float:
    return sum(max(0.0, d.balance) for d in debts)

def apply_interest(debts: List[Debt]) -> float:
    total = 0.0
    for d in debts:
        if d.balance > 0:
            r = monthly_rate(d.apr)
            interest = d.balance * r
            d.balance += interest
            total += interest
    return total

def pay_minimums(debts: List[Debt]) -> float:
    paid = 0.0
    for d in debts:
        if d.balance > 0:
            amt = min(d.min_payment, d.balance)
            d.balance -= amt
            paid += amt
    return paid

def pay_extra_avalanche(debts: List[Debt], extra: float) -> float:
    if extra <= 0 or not any(d.balance > 0 for d in debts):
        return 0.0
    active = [d for d in debts if d.balance > 0]
    active.sort(key=lambda x: x.apr, reverse=True)
    amt = min(extra, active[0].balance)
    active[0].balance -= amt
    return amt

def pv(amount: float, annual_discount: float, months: int) -> float:
    r = monthly_rate(annual_discount)
    return amount / ((1 + r) ** months) if r > 0 else amount

def simulate(profile: Profile, scenario: Scenario) -> Dict:
    inv_r = monthly_rate(profile.invest_annual_return)
    debts = copy_debts(profile.debts)
    cash = profile.cash_savings
    inv = profile.investment_balance
    start_m = month_index(profile.current_age_years, profile.current_age_months)
    end_m = profile.life_expectancy_age_years * 12
    retirement_m = profile.retirement_age_years * 12
    ss_monthly, _, _ = ss_monthly_benefit_from_pia(profile.ss_pia_at_fra_monthly, profile.birth_year,
                                                   scenario.ss_claim_age_years, scenario.ss_claim_age_months)
    claim_m = scenario.ss_claim_age_years * 12 + scenario.ss_claim_age_months

    debt_free_month = None
    ef_filled_month = None
    total_interest = 0.0
    total_ss = 0.0
    pv_ss = 0.0

    for t in range(start_m, end_m):
        months_from_now = t - start_m
        inv *= (1 + inv_r)

        # Income
        if t < retirement_m:
            growth = (1 + profile.annual_income_growth / 12) ** months_from_now
            income = profile.monthly_income_after_tax * growth
        else:
            income = profile.post_retirement_monthly_income

        ss_income = ss_monthly if t >= claim_m else 0.0
        total_ss += ss_income
        pv_ss += pv(ss_income, profile.discount_rate, months_from_now)

        # Tithe
        tithe = 0.0
        if scenario.tithe_enabled:
            start_ok = True
            if scenario.tithe_start_rule == "after_debt_free":
                start_ok = sum_debt_balance(debts) <= 0.01
            elif scenario.tithe_start_rule == "after_emergency_fund":
                start_ok = cash >= emergency_target(profile, months_from_now)
            if start_ok:
                if scenario.tithe_on_income:
                    tithe = (income + ss_income) * scenario.tithe_rate
                else:
                    tithe = scenario.tithe_fixed_monthly

        # Expenses & Debt
        expenses = total_base_expenses(profile, months_from_now)
        total_interest += apply_interest(debts)
        min_paid = pay_minimums(debts)
        surplus = income + ss_income - expenses - tithe - min_paid

        # Emergency Fund
        ef_target = emergency_target(profile, months_from_now)
        if cash < ef_target and surplus > 0:
            add = min(surplus, ef_target - cash)
            cash += add
            surplus -= add
            if cash >= ef_target and ef_filled_month is None:
                ef_filled_month = months_from_now

        # Surplus allocation
        if surplus > 0 and sum_debt_balance(debts) > 0.01:
            paid = pay_extra_avalanche(debts, surplus)
            surplus -= paid
        elif surplus > 0:
            if debt_free_month is None:
                debt_free_month = months_from_now
            if scenario.invest_after in ("always", "debt_free"):
                inv += surplus
                surplus = 0.0

        if surplus > 0:
            cash += surplus
        elif surplus < 0:
            deficit = -surplus
            cash -= min(cash, deficit)
            deficit -= min(cash + deficit, deficit)
            if deficit > 0:
                inv -= min(inv, deficit)

        if sum_debt_balance(debts) <= 0.01 and debt_free_month is None:
            debt_free_month = months_from_now

    net_worth = cash + inv - sum_debt_balance(debts)
    return {
        "ss_monthly_at_claim": ss_monthly,
        "final_net_worth": net_worth,
        "final_cash": cash,
        "final_investments": inv,
        "final_debt": sum_debt_balance(debts),
        "total_interest_paid": total_interest,
        "total_ss_received": total_ss,
        "pv_ss_received": pv_ss,
        "months_to_debt_free": debt_free_month - start_m + 1 if debt_free_month else -1,
        "months_to_emergency_fund": ef_filled_month - start_m + 1 if ef_filled_month else -1,
    }
