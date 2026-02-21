import streamlit as st
import pandas as pd
import altair as alt
import uuid
import streamlit.components.v1 as components
from supabase import create_client, Client

# Import your custom logic files
import logic
import calculator

# ==========================================
# ⚙️ PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Financial Freedom Engine", page_icon="🇮🇳", layout="wide")

# ==========================================
# 📊 GOOGLE ANALYTICS (GA4) - PARENT INJECTION
# ==========================================
GA_ID = "G-QB0270BY5S"
ga_script = f"""
<script>
    if (!window.parent.document.getElementById('ga-script')) {{
        var script1 = window.parent.document.createElement('script');
        script1.id = 'ga-script';
        script1.async = true;
        script1.src = "https://www.googletagmanager.com/gtag/js?id={GA_ID}";
        window.parent.document.head.appendChild(script1);

        var script2 = window.parent.document.createElement('script');
        script2.innerHTML = `
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_ID}');
        `;
        window.parent.document.head.appendChild(script2);
    }}
</script>
"""
components.html(ga_script, height=0, width=0)

# ==========================================
# 🔌 SUPABASE DATABASE CONNECTION
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# ==========================================
# 🆔 SESSION STATE MANAGEMENT
# ==========================================
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

# ==========================================
# 🎛️ SIDEBAR INPUTS (All 37 Variables)
# ==========================================
st.sidebar.header("1️⃣ User Profile")
age = st.sidebar.number_input("Current Age", value=30, min_value=18, max_value=100, step=1)

# Dynamically set minimum retirement age to prevent the app from crashing
default_retire = max(60, age)
retire_age = st.sidebar.number_input("Retirement Age", value=default_retire, min_value=age, max_value=100, step=1)

dependents = st.sidebar.number_input("Dependents", value=0, min_value=0, step=1)
income = st.sidebar.number_input("Annual Income (₹)", value=1200000, step=50000)
basic_salary = st.sidebar.number_input("Basic Salary (₹)", value=600000, step=50000)
living_expense = st.sidebar.number_input("Annual Living Expense (₹)", value=400000, step=10000)
rent = st.sidebar.number_input("Annual Rent (₹)", value=200000, step=10000)
tax_slab = st.sidebar.number_input("Tax Slab (%)", value=30.0, step=5.0)
use_post_tax = st.sidebar.checkbox("Use Post-Tax Returns?", value=True)

st.sidebar.header("2️⃣ Current Assets")
cash = st.sidebar.number_input("Cash / Bank (₹)", value=50000, step=10000)
fd = st.sidebar.number_input("Fixed Deposits (₹)", value=100000, step=10000)
epf = st.sidebar.number_input("EPF / PPF Balance (₹)", value=300000, step=10000)
mutual_funds = st.sidebar.number_input("Mutual Funds (₹)", value=200000, step=10000)
stocks = st.sidebar.number_input("Direct Stocks (₹)", value=100000, step=10000)
gold = st.sidebar.number_input("Gold (₹)", value=50000, step=5000)
arbitrage = st.sidebar.number_input("Arbitrage Funds (₹)", value=0, step=5000)

st.sidebar.header("3️⃣ Liabilities & Insurance")
credit_limit = st.sidebar.number_input("Total Credit Limit (₹)", value=200000, step=10000)
emi = st.sidebar.number_input("Annual EMI (₹)", value=0, step=10000)
term_insurance = st.sidebar.number_input("Term Insurance Cover (₹)", value=10000000, step=1000000)
health_insurance = st.sidebar.number_input("Health Insurance Cover (₹)", value=500000, step=50000)

st.sidebar.header("4️⃣ Investments & Goals")
current_sip = st.sidebar.number_input("Monthly SIP (₹)", value=20000, step=1000)
step_up = st.sidebar.number_input("Annual SIP Step-Up (%)", value=10.0, step=1.0)
housing_goal = st.sidebar.selectbox("Housing Goal", ["Rent Forever", "Buy Later"])
house_cost = st.sidebar.number_input("Future House Cost (₹)", value=10000000, step=500000)

st.sidebar.header("5️⃣ Economic Assumptions")
inflation = st.sidebar.number_input("General Inflation (%)", value=6.0, step=0.5)
rent_inflation = st.sidebar.number_input("Rent Inflation (%)", value=8.0, step=0.5)
swr = st.sidebar.number_input("Safe Withdrawal Rate (%)", value=4.0, step=0.25)
rate_new_sip = st.sidebar.number_input("Return on New SIPs (%)", value=12.0, step=0.5)
rate_fd = st.sidebar.number_input("Return on FD (%)", value=7.0, step=0.5)
rate_epf = st.sidebar.number_input("Return on EPF (%)", value=8.1, step=0.1)
rate_equity = st.sidebar.number_input("Return on Equity (%)", value=12.0, step=0.5)
rate_gold = st.sidebar.number_input("Return on Gold (%)", value=8.0, step=0.5)
rate_arbitrage = st.sidebar.number_input("Return on Arbitrage (%)", value=6.5, step=0.5)

st.sidebar.divider()

# ==========================================
# 🚀 IGNITION BUTTON
# ==========================================
if st.sidebar.button("🚀 Calculate My Freedom Plan", type="primary"):
    st.session_state['submitted'] = True

# ==========================================
# 🖥️ MAIN SCREEN LOGIC
# ==========================================
if not st.session_state['submitted']:
    # --- WELCOME SCREEN ---
    st.title("🇮🇳 Financial Freedom Engine")
    st.info("👈 Please enter your details in the sidebar and click **'🚀 Calculate My Freedom Plan'** to view your personalized roadmap.")
    
    st.markdown("""
    ### Welcome to your Personal Wealth Architect
    By compiling your income, assets, and goals, this engine will run a 100-year simulation to determine your exact path to financial independence.
    
    **What you will discover:**
    * Your target Fi-Age (Financial Independence Age).
    * If you are on track to retire early.
    * Real-time optimization of your liquidity and debt.
    """)

else:
    # --- DASHBOARD SCREEN ---
    st.title("Your Financial Freedom Roadmap")
    
    # 1. Calculate the core metrics
    total_liq = cash + fd + mutual_funds + stocks + gold + arbitrage
    net_worth = total_liq + epf - emi  # Adjust logic here if needed based on your calculator.py
    
    # 2. Display Top Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Net Worth", f"₹{net_worth:,.0f}")
    col2.metric("Total Liquidity", f"₹{total_liq:,.0f}")
    col3.metric("Annual SIP", f"₹{(current_sip * 12):,.0f}")
    
    # 3. Optional: Add Feedback Input
    feedback_text = st.text_input("Any feedback on this tool? (Optional)")
    
    # 4. Run the Heavy Simulation (from your calculator.py)
    # NOTE: Ensure this matches the exact function name in your calculator.py!
    df = calculator.run_simulation(
        age=age, retire_age=retire_age, income=income, living_expense=living_expense,
        current_sip=current_sip, step_up=step_up, net_worth=net_worth, inflation=inflation
    )
    
    # 5. Extract target data safely to prevent crashes
    st.divider()
    safe_retire_age = max(age, retire_age)
    
    try:
        target_row = df[df['Age'] == safe_retire_age].iloc[0]
        gap_val = target_row['Gap'] if 'Gap' in df.columns else 0
        st.subheader(f"At Retirement (Age {safe_retire_age})")
        st.write(f"Estimated Gap: ₹{gap_val:,.0f}")
    except Exception as e:
        st.warning("Simulation data mapping required. Check calculator.py columns.")

    # 6. Render the Altair Chart (using the new Streamlit width format)
    if 'Age' in df.columns and 'Wealth' in df.columns:
        chart = alt.Chart(df).mark_line().encode(
            x='Age:Q',
            y='Wealth:Q',
            tooltip=['Age', 'Wealth']
        )
        st.altair_chart(chart, width="stretch")

    # ==========================================
    # 💾 SUPABASE DATA PAYLOAD & AUTO-SAVE
    # ==========================================
    data_payload = {
        "id": st.session_state['user_id'],
        "age": age,
        "retire_age": retire_age,
        "dependents": dependents,
        "income": income,
        "basic_salary": basic_salary,
        "living_expense": living_expense,
        "rent": rent,
        "tax_slab": tax_slab,
        "use_post_tax": use_post_tax,
        "cash": cash,
        "fd": fd,
        "credit_limit": credit_limit,
        "emi": emi,
        "term_insurance": term_insurance,
        "health_insurance": health_insurance,
        "epf": epf,
        "mutual_funds": mutual_funds,
        "stocks": stocks,
        "gold": gold,
        "arbitrage": arbitrage,
        "current_sip": current_sip,
        "step_up": step_up,
        "housing_goal": housing_goal,
        "house_cost": house_cost,
        "inflation": inflation,
        "rent_inflation": rent_inflation,
        "swr": swr,
        "rate_new_sip": rate_new_sip,
        "rate_fd": rate_fd,
        "rate_epf": rate_epf,
        "rate_equity": rate_equity,
        "rate_gold": rate_gold,
        "rate_arbitrage": rate_arbitrage,
        "total_liquidity": total_liq,
        "net_worth": net_worth,
        "feedback": feedback_text
    }

    # Unmasked error handling so it screams if there's a typo in the database
    try:
        supabase.table("user_data").insert(data_payload).execute()
    except Exception as e:
        st.error(f"🚨 ALERT - We caught the bug: {e}")