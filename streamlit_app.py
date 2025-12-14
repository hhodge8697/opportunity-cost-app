import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine import fv_monthly, monthly_rate, months_to_payoff, total_interest_paid
import json

st.set_page_config(page_title="Opportunity Cost Calculator", layout="centered")
st.title("💰 Opportunity Cost Calculator")
st.markdown("**See exactly how much wealth you're leaving on the table** by not optimizing your money.")

# Load Profile if uploaded
uploaded_file = st.file_uploader("Load Profile (JSON)", type="json")
if uploaded_file:
    profile = json.load(uploaded_file)
    st.success("Profile loaded! Adjust as needed.")
else:
    profile = {}

tab1, tab2 = st.tabs(["📊 Your Numbers", "📈 Your Opportunity"])

with tab1:
    st.info("💡 Tip: Be honest — this only helps if your numbers are real!")

    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input("Monthly Take-Home Income", min_value=0, value=profile.get("income", 6000), step=100)
        essentials = st.number_input("Essential Expenses (rent, food, bills, etc.)", min_value=0, value=profile.get("essentials", 4000), step=100)
    with col2:
        current_net_worth = st.number_input("Current Savings + Investments", min_value=0, value=profile.get("current_net_worth", 10000), step=1000)
        expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, value=profile.get("expected_return", 7.0), step=0.5) / 100

    surplus = income - essentials
    if surplus < 0:
        st.error("You're spending more than you earn. Focus on increasing income or cutting essentials first.")
        surplus = 0
    else:
        st.success(f"**Monthly Surplus (Discretionary Money): ${surplus:,.0f}** 💸")

    st.divider()
    has_debt = st.checkbox("I have high-interest debt (credit cards, etc.)", value=profile.get("has_debt", False))
    if has_debt:
        col1, col2, col3 = st.columns(3)
        with col1:
            debt_balance = st.number_input("Total Debt Balance", min_value=0.0, value=profile.get("debt_balance", 15000.0))
        with col2:
            debt_apr = st.number_input("Average Interest Rate (%)", min_value=0.0, value=profile.get("debt_apr", 18.0)) / 100
        with col3:
            min_payment = st.number_input("Current Minimum Payment", min_value=0.0, value=profile.get("min_payment", 400.0))

    years = st.slider("Time Horizon (Years)", 5, 30, profile.get("years", 15))
    inflation = st.slider("Expected Annual Inflation (%)", 0.0, 10.0, profile.get("inflation", 3.0)) / 100

    # Save Profile
    profile_data = {
        "income": income,
        "essentials": essentials,
        "current_net_worth": current_net_worth,
        "expected_return": expected_return * 100,  # Store as %
        "has_debt": has_debt,
        "debt_balance": debt_balance if has_debt else 0,
        "debt_apr": debt_apr * 100 if has_debt else 0,
        "min_payment": min_payment if has_debt else 0,
        "years": years,
        "inflation": inflation * 100,
    }
    st.download_button("Save Profile (JSON)", data=json.dumps(profile_data), file_name="my_profile.json", mime="application/json")

with tab2:
    if surplus <= 0:
        st.warning("No surplus to optimize yet — that's your biggest opportunity!")
        st.stop()

    months = years * 12
    r_inv = monthly_rate(expected_return)
    r_inf = monthly_rate(inflation)

    # Current Path: Spend surplus → no extra growth
    fv_current_nominal = current_net_worth * (1 + r_inv)**months
    fv_current_real = fv_current_nominal / (1 + r_inf)**months

    # Optimized Path
    interest_saved = 0
    payoff_months = months
    if has_debt and debt_balance > 0:
        interest_saved = total_interest_paid(debt_balance, debt_apr, min_payment) - \
                         total_interest_paid(debt_balance, debt_apr, min_payment, surplus)
        payoff_months = months_to_payoff(debt_balance, debt_apr, min_payment, surplus)
        if payoff_months < months:
            invest_months = months - payoff_months
            fv_opt_nominal = current_net_worth * (1 + r_inv)**months + fv_monthly(surplus, r_inv, invest_months)
        else:
            fv_opt_nominal = current_net_worth * (1 + r_inv)**months
    else:
        fv_opt_nominal = current_net_worth * (1 + r_inv)**months + fv_monthly(surplus, r_inv, months)

    fv_opt_real = fv_opt_nominal / (1 + r_inf)**months
    opportunity_real = fv_opt_real - fv_current_real + (interest_saved / (1 + r_inf)**months)

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Path (Today's $)", f"${fv_current_real:,.0f}")
    col2.metric("Optimized Path (Today's $)", f"${fv_opt_real:,.0f}")
    col3.metric("**Missed Opportunity**", f"${opportunity_real:,.0f}", delta=f"+${opportunity_real:,.0f}")

    if interest_saved > 0:
        st.success(f"Plus: Save **${interest_saved:,.0f}** in interest by paying off debt in **{payoff_months // 12} years, {payoff_months % 12} months** (vs. slower payoff).")

    # Auto-Generated Insights + Counsel
    insight = f"By optimizing your **${surplus:,.0f}/month surplus** (redirect to debt/invest), "
    if opportunity_real > 500000:
        insight += "you could build a life-changing nest egg — enough for early retirement or a dream home. "
    elif opportunity_real > 100000:
        insight += "that's like gaining a house down payment or a luxury car you're currently missing. "
    elif opportunity_real > 20000:
        insight += "equivalent to a family vacation fund or emergency buffer you're forgoing. "
    else:
        insight += "a solid start toward financial security you're not capturing yet. "

    counsel = "Suggested Counsel: "
    if has_debt and debt_apr > expected_return:
        counsel += f"Prioritize that {debt_apr*100:.1f}% debt — it's costing you more than investments earn. Aim to pay extra ${surplus:,.0f}/month. "
    if surplus > 500:
        counsel += "Cut one non-essential (e.g., dining out $200/month) to boost gains. "
    counsel += "Start small: Automate transfers to high-yield savings or index funds. Review in 6 months!"

    st.markdown(f"### Personalized Insight\n{insight}\n\n### Suggested Counsel\n{counsel}")

    # Better Charts
    col1, col2 = st.columns(2)
    with col1:
        # Bar Chart: Nominal vs Real
        fig_bar, ax_bar = plt.subplots()
        scenarios = ["Current", "Optimized"]
        nominals = [fv_current_nominal, fv_opt_nominal]
        reals = [fv_current_real, fv_opt_real]
        x = range(len(scenarios))
        width = 0.35
        ax_bar.bar([p - width/2 for p in x], nominals, width, label="Nominal")
        ax_bar.bar([p + width/2 for p in x], reals, width, label="Inflation-Adjusted")
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(scenarios)
        ax_bar.set_ylabel("Future Value ($)")
        ax_bar.legend()
        ax_bar.bar_label(ax_bar.containers[0], fmt="$%,.0f", label_type="edge", fontsize=8)
        ax_bar.bar_label(ax_bar.containers[1], fmt="$%,.0f", label_type="edge", fontsize=8)
        st.pyplot(fig_bar)

    with col2:
        # Line Chart: Growth Over Time
        fig_line, ax_line = plt.subplots()
        time = list(range(0, months+1, 12))  # Yearly points
        current_growth = [current_net_worth * (1 + r_inv)**t for t in time]
        opt_growth = []
        for t in time:
            if has_debt:
                payoff_t = min(t, payoff_months)
                invest_t = max(0, t - payoff_months)
                opt_growth.append(current_net_worth * (1 + r_inv)**t + fv_monthly(surplus, r_inv, invest_t))
            else:
                opt_growth.append(current_net_worth * (1 + r_inv)**t + fv_monthly(surplus, r_inv, t))
        ax_line.plot([t/12 for t in time], current_growth, label="Current", color="red")
        ax_line.plot([t/12 for t in time], opt_growth, label="Optimized", color="green")
        ax_line.set_xlabel("Years")
        ax_line.set_ylabel("Wealth ($)")
        ax_line.legend()
        st.pyplot(fig_line)

    if surplus > 0:
        # Pie Chart
        fig_pie, ax_pie = plt.subplots()
        labels = ["Essentials", "Discretionary (Opportunity Lost)"]
        sizes = [essentials, surplus]
        ax_pie.pie(sizes, labels=labels, autopct="%1.0f%%", colors=["#999999", "#ff9999"])
        ax_pie.set_title("Monthly Income Breakdown")
        st.pyplot(fig_pie)

st.caption("Not financial advice • Educational tool • Assumptions: constant rates, no taxes or fees")
