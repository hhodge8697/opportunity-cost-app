import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine import fv_monthly, monthly_rate, months_to_payoff, total_interest_paid

st.set_page_config(page_title="Opportunity Cost Calculator", layout="centered")
st.title("💰 Opportunity Cost Calculator")
st.markdown("See how small changes in spending can lead to **big future gains**.")

tab1, tab2 = st.tabs(["📊 Inputs", "📈 Results"])

with tab1:
    st.header("Your Basics")
    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input("Monthly Take-Home Income", value=6000)
        total_expenses = st.number_input("Essential Monthly Expenses", value=4000)
    with col2:
        current_savings_inv = st.number_input("Current Savings/Investments", value=10000)
        expected_return = st.number_input("Expected Annual Return (%)", value=7.0) / 100

    discretionary = monthly_income - total_expenses
    if discretionary < 0:
        st.error("Expenses exceed income—adjust for realistic results.")
        discretionary = 0
    st.success(f"**Monthly Discretionary (Surplus): ${discretionary:,.0f}**")

    st.header("Debt (Optional)")
    has_debt = st.checkbox("I have high-interest debt")
    if has_debt:
        col1, col2, col3 = st.columns(3)
        with col1:
            debt_balance = st.number_input("Total Debt Balance", value=15000)
        with col2:
            debt_apr = st.number_input("Average APR (%)", value=18.0) / 100
        with col3:
            min_payment = st.number_input("Current Min Payment", value=400)

    st.header("Time Horizon")
    years = st.slider("Years into the Future", 5, 30, 15)

with tab2:
    if discretionary <= 0:
        st.warning("No surplus—focus on increasing income or cutting essentials first!")
    else:
        months = years * 12
        r_monthly = monthly_rate(expected_return)

        # Scenario 1: Current (spend discretionary)
        fv_current = current_savings_inv * (1 + r_monthly)**months + fv_monthly(0, r_monthly, months)

        # Scenario 2: Optimized (redirect discretionary to debt then invest)
        if has_debt and 'debt_balance' in locals():
            extra = discretionary
            interest_saved = total_interest_paid(debt_balance, debt_apr, min_payment, 0) - total_interest_paid(debt_balance, debt_apr, min_payment, extra)
            payoff_months_opt = months_to_payoff(debt_balance, debt_apr, min_payment, extra)
            payoff_months_cur = months_to_payoff(debt_balance, debt_apr, min_payment, 0)

            if payoff_months_opt < months:
                remaining_months = months - payoff_months_opt
                fv_opt = fv_monthly(discretionary, r_monthly, remaining_months) + current_savings_inv * (1 + r_monthly)**months
            else:
                fv_opt = current_savings_inv * (1 + r_monthly)**months
            opportunity = fv_opt - fv_current + interest_saved
            st.metric("Interest Saved by Paying Debt Faster", f"${interest_saved:,.0f}")
        else:
            fv_opt = current_savings_inv * (1 + r_monthly)**months + fv_monthly(discretionary, r_monthly, months)
            opportunity = fv_opt - fv_current

        col1, col2, col3 = st.columns(3)
        col1.metric("Current Path Future Value", f"${fv_current:,.0f}")
        col2.metric("Optimized Path Future Value", f"${fv_opt:,.0f}")
        col3.metric("**Opportunity Gain**", f"**${opportunity:,.0f}**", delta=f"+${opportunity:,.0f}")

        # Chart
        data = pd.DataFrame({
            "Scenario": ["Current Spending", "Optimized (Invest Surplus)"],
            "Future Wealth": [fv_current, fv_opt]
        })
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(data["Scenario"], data["Future Wealth"], color=["#ff9999", "#66b3ff"])
        ax.set_ylabel("Future Value ($)")
        ax.bar_label(bars, fmt="$%,.0f")
        st.pyplot(fig)

        st.info("**Key Insight**: By redirecting your discretionary spending to debt/investments, you could gain the amount shown above over the selected years.")

st.caption("Not financial advice • Simple math tool for illustration • Assumptions: constant returns, no taxes/inflation adjustments")
