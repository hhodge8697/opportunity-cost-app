# streamlit_app.py
from __future__ import annotations

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from engine import fv_monthly, monthly_rate, months_to_payoff, total_interest_paid


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Opportunity Cost Optimizer", layout="centered")
st.title("💰 Opportunity Cost Optimizer")
st.markdown(
    "See how small changes in spending can lead to **big future gains**.\n\n"
    "This is a **math simulator** (not financial advice). Assumes constant returns, no taxes/inflation."
)

tab1, tab2 = st.tabs(["📊 Inputs", "📈 Results"])


# -----------------------------
# Inputs
# -----------------------------
with tab1:
    st.header("Your Basics")

    c1, c2 = st.columns(2)
    with c1:
        monthly_income = st.number_input(
            "Monthly Take-Home Income ($)",
            min_value=0.0,
            value=6000.0,
            step=100.0,
        )
        total_expenses = st.number_input(
            "Essential Monthly Expenses ($)",
            min_value=0.0,
            value=4000.0,
            step=100.0,
        )

    with c2:
        current_savings_inv = st.number_input(
            "Current Savings / Investments ($)",
            min_value=0.0,
            value=10000.0,
            step=500.0,
        )
        expected_return = st.number_input(
            "Expected Annual Return (%)",
            min_value=0.0,
            value=7.0,
            step=0.25,
        ) / 100.0

    discretionary = monthly_income - total_expenses
    if discretionary < 0:
        st.error("Expenses exceed income — adjust inputs for realistic results.")
        discretionary = 0.0

    st.success(f"**Monthly Discretionary (Surplus): ${discretionary:,.0f}**")

    st.divider()

    st.header("Debt (Optional)")
    has_debt = st.checkbox("I have high-interest debt", value=False)

    debt_balance = 0.0
    debt_apr = 0.0
    min_payment = 0.0

    if has_debt:
        d1, d2, d3 = st.columns(3)
        with d1:
            debt_balance = st.number_input(
                "Total Debt Balance ($)",
                min_value=0.0,
                value=15000.0,
                step=500.0,
            )
        with d2:
            debt_apr = st.number_input(
                "Average APR (%)",
                min_value=0.0,
                value=18.0,
                step=0.5,
            ) / 100.0
        with d3:
            min_payment = st.number_input(
                "Current Minimum Payment ($/mo)",
                min_value=0.0,
                value=400.0,
                step=50.0,
            )

        if debt_balance <= 0:
            st.warning("Debt balance is 0 — debt calculations will be skipped.")
        if min_payment <= 0 and debt_balance > 0:
            st.warning("Minimum payment is 0 — payoff math will not work. Increase it.")

    st.divider()

    st.header("Time Horizon")
    years = st.slider("Years into the Future", min_value=5, max_value=30, value=15)
    st.caption("Tip: Use 10–20 years to see the compounding effect clearly.")


# -----------------------------
# Results
# -----------------------------
with tab2:
    st.subheader("Run your results")

    run = st.button("🚀 Run Simulation", type="primary", use_container_width=True)

    if not run:
        st.info("Enter your numbers on the **Inputs** tab, then click **Run Simulation**.")
        st.stop()

    if discretionary <= 0:
        st.warning("No surplus available. Focus on increasing income or reducing essentials first.")
        st.stop()

    months = int(years * 12)
    r_monthly = monthly_rate(expected_return)

    # Scenario 1: Current path (you do NOT invest the surplus)
    fv_current = current_savings_inv * (1 + r_monthly) ** months + fv_monthly(0.0, r_monthly, months)

    # Scenario 2: Optimized path
    fv_opt = 0.0
    interest_saved = 0.0

    if has_debt and debt_balance > 0 and min_payment > 0:
        extra = discretionary

        # Interest saved: min-only interest minus (min + extra) interest
        int_min_only = total_interest_paid(debt_balance, debt_apr, min_payment, 0.0)
        int_with_extra = total_interest_paid(debt_balance, debt_apr, min_payment, extra)

        # If either is infinite, handle gracefully
        if int_min_only == float("inf") or int_with_extra == float("inf"):
            interest_saved = 0.0
        else:
            interest_saved = max(0.0, float(int_min_only - int_with_extra))

        payoff_months_opt = months_to_payoff(debt_balance, debt_apr, min_payment, extra)
        payoff_months_cur = months_to_payoff(debt_balance, debt_apr, min_payment, 0.0)

        st.markdown("### Debt Payoff Comparison")
        c1, c2, c3 = st.columns(3)
        c1.metric("Payoff (Min Only)", "Never" if payoff_months_cur >= 10**9 else f"{payoff_months_cur} months")
        c2.metric("Payoff (Min + Surplus)", "Never" if payoff_months_opt >= 10**9 else f"{payoff_months_opt} months")
        c3.metric("Interest Saved", f"${interest_saved:,.0f}")

        # If debt is paid off before the horizon, invest surplus after payoff
        if payoff_months_opt < 10**9 and payoff_months_opt < months:
            remaining_months = months - payoff_months_opt
            fv_opt = (
                current_savings_inv * (1 + r_monthly) ** months
                + fv_monthly(discretionary, r_monthly, remaining_months)
            )
        else:
            # If not paid off within horizon, only investment growth on existing savings/investments
            fv_opt = current_savings_inv * (1 + r_monthly) ** months

        opportunity = (fv_opt - fv_current) + interest_saved

    else:
        # No debt case: simply invest surplus monthly
        fv_opt = current_savings_inv * (1 + r_monthly) ** months + fv_monthly(discretionary, r_monthly, months)
        opportunity = fv_opt - fv_current

    st.divider()

    st.markdown("### Future Wealth Outcomes")

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Path Future Value", f"${fv_current:,.0f}")
    m2.metric("Optimized Path Future Value", f"${fv_opt:,.0f}")
    m3.metric("Opportunity Gain", f"${opportunity:,.0f}", delta=f"+${opportunity:,.0f}")

    # Table
    df = pd.DataFrame(
        {
            "Scenario": ["Current Spending", "Optimized (Debt/Invest)"],
            "Future Wealth": [fv_current, fv_opt],
        }
    )

    st.dataframe(
        df.style.format({"Future Wealth": "${:,.0f}"}),
        use_container_width=True,
    )

    # Chart
    st.markdown("### Chart")
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(df["Scenario"], df["Future Wealth"])
    ax.set_ylabel("Future Value ($)")
    ax.bar_label(bars, fmt="$%,.0f")
    st.pyplot(fig)

    st.info(
        "**Key Insight:** Redirecting discretionary spending into debt payoff and/or investing can create a large "
        "difference over time due to compounding."
    )

st.caption("Not financial advice • Simple math tool • Assumes constant returns • No taxes/inflation adjustments")
