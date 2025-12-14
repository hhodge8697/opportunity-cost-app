import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine import fv_monthly, monthly_rate, months_to_payoff, total_interest_paid
import json

st.set_page_config(page_title="Opportunity Cost Calculator", layout="centered")
st.title("💰 Opportunity Cost Calculator")
st.markdown("**Discover your missed wealth — and how to capture it.**")

# Load Profile
uploaded_file = st.file_uploader("Load Saved Profile (JSON)", type="json")
if uploaded_file:
    profile = json.load(uploaded_file)
    st.success("Profile loaded successfully!")
else:
    profile = {}

tab1, tab2, tab3 = st.tabs(["📊 Your Numbers", "📈 Your Opportunity", "💡 Optimized Budget"])

with tab1:
    st.info("💡 Use real numbers for the most accurate insights.")

    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input("Monthly Take-Home Income", min_value=0, value=profile.get("income", 6000), step=100, key="income")
        essentials = st.number_input("Current Essential Expenses", min_value=0, value=profile.get("essentials", 4000), step=100, key="essentials")
    with col2:
        current_net_worth = st.number_input("Current Savings + Investments", min_value=0, value=profile.get("current_net_worth", 10000), step=1000)
        expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, value=profile.get("expected_return", 7.0), step=0.5) / 100

    surplus = income - essentials
    if surplus < 0:
        st.error("Warning: Expenses exceed income. Start by balancing this.")
        surplus = 0
    else:
        st.success(f"**Monthly Surplus: ${surplus:,.0f}**")

    st.divider()
    has_debt = st.checkbox("I have high-interest debt", value=profile.get("has_debt", False))
    if has_debt:
        col1, col2, col3 = st.columns(3)
        with col1:
            debt_balance = st.number_input("Debt Balance", min_value=0.0, value=profile.get("debt_balance", 15000.0))
        with col2:
            debt_apr = st.number_input("Average APR (%)", min_value=0.0, value=profile.get("debt_apr", 18.0)) / 100
        with col3:
            min_payment = st.number_input("Minimum Payment", min_value=0.0, value=profile.get("min_payment", 400.0))

    years = st.slider("Time Horizon (Years)", 5, 30, profile.get("years", 15))
    inflation = st.slider("Annual Inflation (%)", 0.0, 10.0, profile.get("inflation", 3.0)) / 100

    # Save Profile
    profile_data = {
        "income": income, "essentials": essentials, "current_net_worth": current_net_worth,
        "expected_return": expected_return * 100, "has_debt": has_debt,
        "debt_balance": debt_balance if has_debt else 0, "debt_apr": debt_apr * 100 if has_debt else 0,
        "min_payment": min_payment if has_debt else 0, "years": years, "inflation": inflation * 100
    }
    st.download_button("💾 Save Profile", data=json.dumps(profile_data), file_name="financial_profile.json", mime="application/json")

# Calculations (shared across tabs)
months = years * 12
r_inv = monthly_rate(expected_return)
r_inf = monthly_rate(inflation)

fv_current_nominal = current_net_worth * (1 + r_inv)**months
fv_current_real = fv_current_nominal / (1 + r_inf)**months

interest_saved = 0
payoff_months = months
if has_debt and debt_balance > 0:
    interest_saved = total_interest_paid(debt_balance, debt_apr, min_payment) - total_interest_paid(debt_balance, debt_apr, min_payment, surplus)
    payoff_months = months_to_payoff(debt_balance, debt_apr, min_payment, surplus)
    invest_months = max(0, months - payoff_months)
    fv_opt_nominal = current_net_worth * (1 + r_inv)**months + fv_monthly(surplus, r_inv, invest_months)
else:
    fv_opt_nominal = current_net_worth * (1 + r_inv)**months + fv_monthly(surplus, r_inv, months)

fv_opt_real = fv_opt_nominal / (1 + r_inf)**months
opportunity_real = fv_opt_real - fv_current_real + (interest_saved / (1 + r_inf)**months if interest_saved else 0)

with tab2:
    if surplus <= 0:
        st.warning("No surplus yet — your biggest opportunity is creating one!")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Path (Today's $)", f"${fv_current_real:,.0f}")
    col2.metric("Optimized Path (Today's $)", f"${fv_opt_real:,.0f}")
    col3.metric("Missed Opportunity", f"${opportunity_real:,.0f}", delta=f"+${opportunity_real:,.0f}")

    if interest_saved > 0:
        st.success(f"Save **${interest_saved:,.0f}** in interest by becoming debt-free faster.")

    # Personalized Insight
    insight = f"Redirecting **${surplus:,.0f}/month** could add **${opportunity_real:,.0f}** to your wealth in {years} years. "
    if opportunity_real > 300000:
        insight += "That’s life-changing — early retirement territory. "
    elif opportunity_real > 100000:
        insight += "Enough for a home down payment or full financial independence boost. "
    else:
        insight += "A meaningful step toward security and freedom. "

    counsel = "Counsel: "
    if has_debt and debt_apr > expected_return + 0.05:
        counsel += f"Attack that {debt_apr*100:.0f}% debt first — it's your highest 'guaranteed return'. "
    counsel += "Automate transfers. Track progress monthly. Small cuts compound!"

    st.markdown(f"### Insight\n{insight}\n\n### Advice\n{counsel}")

    # Charts (same as before)
    col1, col2 = st.columns(2)
    with col1:
        fig_bar, ax = plt.subplots()
        ax.bar(["Current", "Optimized"], [fv_current_real, fv_opt_real], color=["#ff6b6b", "#51cf66"])
        ax.set_ylabel("Future Value (Today's $)")
        ax.bar_label(ax.containers[0], fmt="$%,.0f")
        st.pyplot(fig_bar)
    with col2:
        fig_line, ax = plt.subplots()
        years_list = list(range(0, years + 1))
        current_line = [current_net_worth * (1 + expected_return)**y / (1 + inflation)**y for y in years_list]
        opt_line = [fv_opt_nominal / (1 + r_inf)**(y*12) / (current_net_worth if y == 0 else 1) + current_net_worth for y in years_list]  # simplified
        ax.plot(years_list, current_line, label="Current", color="red")
        ax.plot(years_list, [current_net_worth * (1 + expected_return)**y / (1 + inflation)**y + (fv_opt_nominal - current_net_worth * (1 + r_inv)**months) / (1 + inflation)**y if y > 0 else current_net_worth for y in years_list], label="Optimized", color="green")  # approximate
        ax.set_xlabel("Years")
        ax.set_ylabel("Real Wealth")
        ax.legend()
        st.pyplot(fig_line)

with tab3:
    st.header("🗂️ Your Optimized Monthly Budget")
    st.markdown("This budget prioritizes **wealth-building** while allowing joy.")

    # Auto-generated categories
    budget = {
        "Essentials (Housing, Food, Transport, Utilities, Insurance)": min(essentials, income * 0.60),
        "Debt Repayment": min_payment + surplus if has_debt and surplus > 0 else 0,
        "Emergency Fund / Investing": surplus if not (has_debt and payoff_months >= months) else max(0, surplus - min_payment),
        "Fun / Discretionary": max(0, income - essentials - (min_payment + surplus if has_debt else surplus))
    }

    # Adjust to fit income
    total_allocated = sum(budget.values())
    if total_allocated > income:
        scale = income / total_allocated
        budget = {k: v * scale for k, v in budget.items()}

    # Add remaining to investing
    remaining = income - sum(budget.values())
    if remaining > 0:
        budget["Emergency Fund / Investing"] += remaining

    df_budget = pd.DataFrame({
        "Category": budget.keys(),
        "Amount": [f"${v:,.0f}" for v in budget.values()],
        "Percentage": [f"{v/income*100:.0f}%" for v in budget.values()]
    })

    st.table(df_budget.style.set_properties(**{'text-align': 'left'}))

    # Pie Chart
    fig_pie, ax_pie = plt.subplots()
    ax_pie.pie(budget.values(), labels=budget.keys(), autopct="%1.0f%%", startangle=90)
    ax_pie.axis('equal')
    st.pyplot(fig_pie)

    st.info("This budget eliminates opportunity cost by directing surplus to high-ROI uses first (debt → invest). Adjust 'Essentials' down to increase gains!")

st.caption("Educational tool • Not financial advice • Built with care")
