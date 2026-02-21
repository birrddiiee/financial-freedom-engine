import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import uuid
from supabase import create_client, Client
import logic       
import calculator  

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Financial Freedom Engine", page_icon="🚀", layout="wide")

# ==========================================
# 🎨 CUSTOM CSS FOR MOBILE RESPONSIVENESS
# ==========================================
mobile_css = """
<style>
    /* This rule only activates on screens smaller than 768px (Mobile/Tablet) */
    @media (max-width: 768px) {
        /* Shrink main paragraphs, labels, and text */
        .stMarkdown p, .stText, label {
            font-size: 0.85rem !important;
        }
        /* Shrink the big Metric numbers (like Net Worth) */
        [data-testid="stMetricValue"] > div {
            font-size: 1.5rem !important;
        }
        /* Shrink the expander titles (1️⃣ Core Profile...) */
        .streamlit-expanderHeader {
            font-size: 0.9rem !important;
        }
        /* Shrink Headers */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.1rem !important; }
    }
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)
# ==========================================
# 📊 GOOGLE ANALYTICS (GA4) 
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
# ☁️ SUPABASE DATABASE CONNECTION
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

# ==========================================
# 🖥️ MAIN UI: TITLE & INSTANT GRATIFICATION
# ==========================================
st.title("🇮🇳 Financial Freedom Engine")
st.markdown("Adjust your parameters below. Your 100-year wealth projection will update **instantly**.")

# ==========================================
# 🎛️ MAIN PAGE INPUT PANEL (NO MORE SIDEBAR!)
# ==========================================

# --- STEP 1: USER PROFILE (Open by default) ---
with st.expander("1️⃣ Core Profile & Income", expanded=False):
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Current Age", value=30, min_value=18, max_value=100, step=1)
    default_retire = max(60, age)
    retire_age = c2.number_input("Retirement Age", value=default_retire, min_value=age, max_value=100, step=1)
    dependents = c3.number_input("Dependents", value=2, step=1)
    
    c4, c5, c6 = st.columns(3)
    income = c4.number_input("Monthly In-hand (₹)", value=100000, step=5000)
    basic_salary = c5.number_input("Monthly Basic (₹)", value=40000, step=1000)
    monthly_pf_inflow = basic_salary * 0.24 
    c6.info(f"✨ Auto-PF Inflow: ₹{monthly_pf_inflow:,.0f}/mo")

    c7, c8, c9 = st.columns(3)
    living_expense = c7.number_input("Living Exp. Excl. Rent (₹)", value=30000, step=1000)
    rent = c8.number_input("Monthly Rent (₹)", value=20000, step=1000)
    total_monthly_expense = living_expense + rent
    
    tax_options = [0.0, 0.10, 0.20, 0.30]
    tax_slab = c9.selectbox("Tax Slab", options=tax_options, index=3, format_func=lambda x: f"{int(x*100)}%")
    use_post_tax = st.toggle("Calculate Post-Tax Returns?", value=True)

# --- STEP 2: SAFETY & LIQUIDITY ---
with st.expander("2️⃣ Safety Net & Insurance", expanded=False):
    c1, c2, c3 = st.columns(3)
    cash = c1.number_input("Cash / Savings (₹)", value=100000, step=10000)
    fd = c2.number_input("Fixed Deposits (₹)", value=500000, step=10000)
    credit_limit = c3.number_input("Credit Card Limit (₹)", value=300000, step=10000)
    
    c4, c5, c6 = st.columns(3)
    emi = c4.number_input("Monthly EMIs (₹)", value=0, step=1000)
    term_insurance = c5.number_input("Term Cover (₹)", value=5000000, step=500000)
    health_insurance = c6.number_input("Health Cover (₹)", value=500000, step=100000)

# --- STEP 3: ASSETS ---
with st.expander("3️⃣ Current Investments", expanded=False):
    c1, c2, c3 = st.columns(3)
    epf = c1.number_input("EPF / PPF (₹)", value=200000, step=10000)
    mutual_funds = c2.number_input("Mutual Funds (₹)", value=150000, step=10000)
    stocks = c3.number_input("Direct Stocks (₹)", value=50000, step=10000)
    
    c4, c5, _ = st.columns(3)
    gold = c4.number_input("Gold (₹)", value=50000, step=10000)
    arbitrage = c5.number_input("Arbitrage Funds (₹)", value=50000, step=10000)

# --- STEP 4: STRATEGY & ASSUMPTIONS ---
with st.expander("4️⃣ Strategy & Growth Assumptions", expanded=False):
    c1, c2, c3 = st.columns(3)
    current_sip = c1.number_input("Current SIP (₹)", value=20000, step=1000)
    step_up_pct = c2.slider("Annual SIP Step-Up (%)", 0, 20, 10) 
    step_up = step_up_pct / 100
    swr = c3.number_input("Safe Withdrawal Rate (%)", value=4.0, step=0.1) / 100

    c4, c5, c6 = st.columns(3)
    h_options = ["Rent Forever", "Buy a Home", "Already Own"]
    housing_goal = c4.selectbox("Housing Plan", options=h_options, index=0)
    house_cost = c5.number_input("Future House Budget (₹)", value=5000000, step=500000)
    inflation = c6.number_input("General Inflation (%)", value=6.0, step=0.5) / 100
    
    st.markdown("**Expected Returns (%)**")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    rate_new_sip = r1.number_input("SIP", value=12.0) / 100
    rate_fd = r2.number_input("FD", value=7.0) / 100
    rate_epf = r3.number_input("EPF", value=8.1) / 100
    rate_equity = r4.number_input("Equity", value=12.0) / 100
    rate_gold = r5.number_input("Gold", value=8.0) / 100
    rate_arbitrage = r6.number_input("Arbitrage", value=7.5) / 100
    rent_inflation = 0.08 # Set statically to save space, or you can add it back

st.divider()

# ==========================================
# 🚀 LIVE DASHBOARD (Calculates Instantly)
# ==========================================

total_liq = cash + fd + credit_limit
net_worth = cash + fd + epf + mutual_funds + stocks + gold + arbitrage

# DATABASE AUTO-SAVE
data_payload = {
    "id": st.session_state['user_id'], "age": age, "retire_age": retire_age, "dependents": dependents,
    "income": income, "basic_salary": basic_salary, "living_expense": living_expense, "rent": rent,
    "tax_slab": tax_slab, "use_post_tax": use_post_tax, "cash": cash, "fd": fd, "credit_limit": credit_limit,
    "emi": emi, "term_insurance": term_insurance, "health_insurance": health_insurance, "epf": epf,
    "mutual_funds": mutual_funds, "stocks": stocks, "gold": gold, "arbitrage": arbitrage,
    "current_sip": current_sip, "step_up": step_up, "housing_goal": housing_goal, "house_cost": house_cost,
    "inflation": inflation, "rent_inflation": rent_inflation, "swr": swr, "rate_new_sip": rate_new_sip,
    "rate_fd": rate_fd, "rate_epf": rate_epf, "rate_equity": rate_equity, "rate_gold": rate_gold,
    "rate_arbitrage": rate_arbitrage, "total_liquidity": total_liq, "net_worth": net_worth
}
try:
    supabase.table("user_data").upsert(data_payload).execute()
except Exception as e:
    pass 

# RUN DIAGNOSTICS & SIMULATION
user_data_logic = {
    "income": income, "monthly_expense": total_monthly_expense, "cash": cash, "fd": fd, "credit_limit": credit_limit,
    "emi": emi, "dependents": dependents, "term_insurance": term_insurance, "health_insurance": health_insurance,
    "housing_goal": housing_goal, "house_cost": house_cost, "tax_slab": tax_slab, "use_post_tax": use_post_tax, 
    "rate_fd": rate_fd, "rate_arb": rate_arbitrage
}
diagnostics = logic.run_diagnostics(user_data_logic)
arbitrage_advice = logic.check_arbitrage_hack(user_data_logic)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Surplus", f"₹{income - total_monthly_expense - current_sip - emi:,}")
m2.metric("Liquid Safety", f"₹{cash + fd + credit_limit:,}")
m3.metric("Housing Plan", housing_goal)
m4.metric("PF Inflow (Auto)", f"₹{monthly_pf_inflow:,.0f}")

st.subheader("🚦 Financial Health Check")
def render_card(col, res, title):
    if res["status"] == "FAIL": col.error(f"**{title}**\n\n{res['msg']}")
    elif res["status"] == "ALERT": col.warning(f"**{title}**\n\n{res['msg']}")
    elif res["status"] == "WAIT": col.info(f"**{title}**\n\n{res['msg']}")
    else: col.success(f"**{title}**\n\n{res['msg']}")

col_l1, col_l2, col_l3 = st.columns(3)
render_card(col_l1, diagnostics['emergency'], "1. Liquidity")
render_card(col_l2, diagnostics['debt'], "2. Debt Health")
render_card(col_l3, diagnostics['life'], "3. Life Cover")

col_l4, col_l5, col_l6 = st.columns(3)
render_card(col_l4, diagnostics['health'], "4. Health Cover")
render_card(col_l5, diagnostics['house'], "5. House Goal")
render_card(col_l6, diagnostics['peace'], "6. Peace Fund")

st.divider()
st.subheader("📈 Wealth Projection")

eff_fd = logic.calculate_post_tax_rate(rate_fd, "FD", tax_slab, use_post_tax)
eff_arb = logic.calculate_post_tax_rate(rate_arbitrage, "Arbitrage", tax_slab, use_post_tax)
eff_eq = logic.calculate_post_tax_rate(rate_equity, "Equity", tax_slab, use_post_tax)
eff_gold = logic.calculate_post_tax_rate(rate_gold, "Gold", tax_slab, use_post_tax)
eff_epf = logic.calculate_post_tax_rate(rate_epf, "EPF", tax_slab, use_post_tax)
eff_sip = logic.calculate_post_tax_rate(rate_new_sip, "Equity", tax_slab, use_post_tax)

user_data_calc = {
    "age": age, "retire_age": retire_age, "living_expense": living_expense, "rent": rent,
    "current_sip": current_sip, "monthly_pf": monthly_pf_inflow, "step_up": step_up,
    "inflation": inflation, "rent_inflation": rent_inflation, "swr": swr, "house_cost": house_cost, "housing_goal": housing_goal,
    "cash": cash, "fd": fd, "epf": epf, "mutual_funds": mutual_funds, "stocks": stocks, "gold": gold, "arbitrage": arbitrage,
    "rate_savings": 0.03, "rate_epf": eff_epf, "rate_equity": eff_eq, "rate_gold": eff_gold, "rate_arbitrage": eff_arb, "rate_fd": eff_fd, "rate_new_sip": eff_sip
}

df = calculator.generate_forecast(user_data_calc)
freedom_row = df[df['Gap'] >= 0]
practical_age = freedom_row.iloc[0]['Age'] if not freedom_row.empty else 100

col_toggle, _ = st.columns([1, 3])
with col_toggle:
    zoom = st.toggle("🔍 Default Zoom", value=True)

if zoom and practical_age < 100:
    end_v = min(max(practical_age, retire_age) + 10, 100)
    view_x_domain = [age, end_v]
    temp_df = df[df['Age'] <= end_v]
    max_y = max(temp_df['Projected Wealth'].max(), temp_df['Required Corpus'].max()) * 1.1
    view_y_domain = [0, max_y]
else:
    view_x_domain = [age, 100]
    view_y_domain = [0, max(df['Projected Wealth'].max(), df['Required Corpus'].max()) * 1.1]

indian_fmt = "datum.value >= 10000000 ? format(datum.value / 10000000, '.2f') + ' Cr' : datum.value >= 100000 ? format(datum.value / 100000, '.2f') + ' L' : format(datum.value, ',.0f')"
base = alt.Chart(df).encode(x=alt.X('Age', scale=alt.Scale(domain=view_x_domain), axis=alt.Axis(format='d')))
nearest = alt.selection_point(nearest=True, on='mouseover', fields=['Age'], empty=False)

line_wealth = base.mark_line(color='#00FF00', strokeWidth=3).encode(
    y=alt.Y('Projected Wealth', scale=alt.Scale(domain=view_y_domain), axis=alt.Axis(labelExpr=indian_fmt, title='Amount (₹)'))
)
line_req = base.mark_line(color='#FF0000', strokeDash=[5, 5]).encode(y='Required Corpus')

selectors = base.mark_point().encode(
    opacity=alt.value(0),
    tooltip=[
        alt.Tooltip('Age', title='Age'),
        alt.Tooltip('Projected Wealth', format=',.0f', title='Wealth (₹)'),
        alt.Tooltip('Required Corpus', format=',.0f', title='Target (₹)'),
        alt.Tooltip('Gap', format=',.0f', title='Surplus/Gap (₹)')
    ]
).add_params(nearest)

rules = base.mark_rule(color='gray').encode(
    opacity=alt.condition(nearest, alt.value(0.5), alt.value(0))
).transform_filter(nearest)

st.altair_chart(alt.layer(line_wealth, line_req, selectors, rules).interactive(), width="stretch")

st.divider()
safe_retire_age = max(age, retire_age)
target_row = df[df['Age'] == safe_retire_age].iloc[0]
gap_val = target_row['Gap']

col_v1, col_v2 = st.columns(2)
with col_v1:
    st.markdown(f"### 🎯 Goal: Retire at {retire_age}")
    if gap_val >= 0:
        st.success(f"✅ **POSSIBLE**\nSurplus at {retire_age}: **₹{gap_val/10000000:.2f} Cr**")
    else:
        st.error(f"❌ **SHORTFALL**\nGap at {retire_age}: **₹{abs(gap_val)/10000000:.2f} Cr**")
        extra_sip_req = calculator.solve_extra_sip_needed(abs(gap_val), retire_age - age, eff_sip, step_up)
        st.info(f"💡 **The Fix:** Start an additional SIP of **₹{int(extra_sip_req):,}** / month.")

with col_v2:
    st.markdown("### 📅 Practical Reality")
    if practical_age <= age: 
        st.success("🎉 You are Financial Independent (FI) right now!")
    elif practical_age > 100: 
        st.error("⚠️ Financial Freedom not possible even by Age 100 with current settings.")
    else: 
        st.warning(f"⚠️ Practical Financial Freedom Age: **{practical_age}**")
    
    if arbitrage_advice['action'] == "SWITCH":
        st.info(f"💡 **Tax Tip:** {arbitrage_advice['msg']}")

feedback_text = st.text_area("Optional: Any feature requests or suggestions? Don't worry, it is anonymous.", max_chars=3000)