import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from engine import Profile, Scenario, Debt, simulate

st.set_page_config(page_title="Opportunity Cost Optimizer", layout="wide")
st.title("🧮 Opportunity Cost Optimizer")

tab1, tab2, tab3 = st.tabs(["Profile & Expenses", "Debts & Scenarios", "Results"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Personal")
        current_age_years = st.number_input("Current Age (Years)", 18, 100, 40)
        life_expectancy = st.number_input("Life Expectancy", 70, 120, 90)
        retirement_age = st.number_input("Retirement Age", 60, 80, 67)
        birth_year = st.number_input("Birth Year", 1920, 2010, 1985)
        ss_pia = st.number_input("SS Monthly Benefit at Full Retirement Age", 0.0, 5000.0, 2800.0)

    with col2:
        st.subheader("Income")
        monthly_income = st.number_input("Monthly Take-Home Income", 0.0, 50000.0, 8500.0)
        post_retire_income = st.number_input("Monthly Income After Retirement", 0.0, 20000.0, 3000.0)
        income_growth = st.number_input("Annual Income Growth (%)", 0.0, 20.0, 3.0) / 100
        expense_inflation = st.number_input("Annual Expense Inflation (%)", 0.0, 10.0, 2.5) / 100

    st.subheader("Assets & Assumptions")
    col1, col2 = st.columns(2)
    with col1:
        cash = st.number_input("Current Cash Savings", 0.0, 1000000.0, 6000.0)
        investments = st.number_input("Current Investments", 0.0, 5000000.0, 25000.0)
    with col2:
        return_rate = st.number_input("Expected Annual Return (%)", 0.0, 20.0, 8.0) / 100
        discount_rate = st.number_input("Discount Rate (%)", 0.0, 15.0, 4.0) / 100
        ef_months = st.number_input("Emergency Fund Target (Months)", 1.0, 12.0, 4.0)

    st.subheader("Monthly Expenses")
    essential_cats = st.text_input("Essential Categories (comma-separated)", "rent,groceries,utilities,insurance,transport")
    essential_list = [c.strip() for c in essential_cats.split(",")] if essential_cats else None

    expenses = {}
    for i in range(10):
        col1, col2 = st.columns([3, 1])
        with col1:
            cat = st.text_input(f"Category {i+1}", f"{'rent' if i==0 else 'groceries' if i==1 else ''}")
        with col2:
            amt = st.number_input(f"Amount {i+1}", 0.0, 10000.0, step=50.0, key=f"amt{i}")
        if cat and amt > 0:
            expenses[cat] = amt
        if not cat:
            break

with tab2:
    st.subheader("Debts")
    debts = []
    for i in range(5):
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            name = st.text_input(f"Debt Name {i+1}", f"Credit Card {i+1}" if i==0 else "")
        with col2:
            balance = st.number_input(f"Balance {i+1}", 0.0, 100000.0, key=f"bal{i}")
        with col3:
            apr = st.number_input(f"APR % {i+1}", 0.0, 50.0, key=f"apr{i}") / 100
        with col4:
            min_pay = st.number_input(f"Min Payment {i+1}", 0.0, 2000.0, key=f"min{i}")
        if name and balance > 0:
            debts.append(Debt(name, balance, apr, min_pay))
        if not name:
            break

    st.subheader("Scenarios to Compare")
    num_scenarios = st.slider("Number of Scenarios", 1, 5, 2)
    scenarios = []
    for i in range(num_scenarios):
        with st.expander(f"Scenario {i+1}: {st.text_input(f'Name', f'Scenario {i+1}', key=f'name{i}')}", expanded=i<2):
            col1, col2 = st.columns(2)
            with col1:
                tithe = st.checkbox("Tithing Enabled", key=f"tithe{i}")
                if tithe:
                    rate = st.slider("Tithe Rate (%)", 0.0, 20.0, 10.0, key=f"rate{i}") / 100
                    start_rule = st.selectbox("Start Tithing", ["now", "after debt-free", "after emergency fund"], key=f"start{i}")
            with col2:
                claim_age = st.slider("SS Claim Age", 62, 70, 67, key=f"claim{i}")
            invest_rule = st.selectbox("Invest Surplus After", ["debt-free", "always"], key=f"invest{i}")
            scenarios.append(Scenario(
                name=st.session_state[f'name{i}'],
                tithe_enabled=tithe if tithe else False,
                tithe_rate=rate if tithe else 0.1,
                tithe_start_rule=start_rule if tithe else "now",
                ss_claim_age_years=claim_age,
                invest_after=invest_rule
            ))

with tab3:
    if st.button("🚀 Run Simulation", type="primary"):
        profile = Profile(
            current_age_years=current_age_years,
            life_expectancy_age_years=life_expectancy,
            retirement_age_years=retirement_age,
            monthly_income_after_tax=monthly_income,
            post_retirement_monthly_income=post_retire_income,
            annual_income_growth=income_growth,
            annual_expense_inflation=expense_inflation,
            cash_savings=cash,
            investment_balance=investments,
            debts=debts,
            invest_annual_return=return_rate,
            discount_rate=discount_rate,
            emergency_fund_target_months=ef_months,
            essential_expense_categories=essential_list,
            birth_year=birth_year,
            ss_pia_at_fra_monthly=ss_pia,
            base_expenses=expenses
        )

        results = {}
        for s in scenarios:
            results[s.name] = simulate(profile, s)

        df = pd.DataFrame(results).T
        st.dataframe(df.style.format({"final_net_worth": money, "ss_monthly_at_claim": money, "total_interest_paid": money}))

        if len(scenarios) > 1:
            st.subheader("Opportunity Cost (Differences)")
            base = scenarios[0].name
            deltas = df.sub(df.loc[base], axis=1).drop(index=base)
            st.dataframe(deltas.style.format(money))

        fig, ax = plt.subplots()
        df["final_net_worth"].plot(kind="bar", ax=ax)
        ax.set_ylabel("Final Net Worth")
        ax.tick_params(axis='x', rotation=30)
        st.pyplot(fig)

        csv = df.to_csv()
        st.download_button("Download Results CSV", csv, "results.csv", "text/csv")

st.caption("Not financial advice • For educational purposes only • Built with ❤️ using Grok + Streamlit")
