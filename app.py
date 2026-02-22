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
# 🎨 CUSTOM CSS FOR UI & MOBILE RESPONSIVENESS
# ==========================================
custom_css = """
<style>
    /* --- HIDE STREAMLIT NUMBER INPUT +/- BUTTONS --- */
    [data-testid="stNumberInputStepDown"] { display: none !important; }
    [data-testid="stNumberInputStepUp"] { display: none !important; }
    
    /* --- HIDE NATIVE BROWSER SPIN BUTTONS --- */
    input[type="number"]::-webkit-inner-spin-button, 
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    input[type="number"] {
        -moz-appearance: textfield !important;
    }

    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {
        .stMarkdown p, .stText, label {
            font-size: 0.85rem !important;
        }
        [data-testid="stMetricValue"] > div {
            font-size: 1.5rem !important;
        }
        .streamlit-expanderHeader {
            font-size: 0.9rem !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.1rem !important; }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

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

# Initialize Session State Variables
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())
if 'has_interacted' not in st.session_state:
    st.session_state['has_interacted'] = False

# ==========================================
# 🖥️ MAIN UI: TITLE & SETTINGS
# ==========================================
col_title, col_settings = st.columns([3, 1])

with col_settings:
    curr_choice = st.selectbox(
        "🌎 Currency & Region", 
        options=["🇮🇳 INR (₹)", "🇺🇸 USD ($)", "🇪🇺 EUR (€)", "🇬🇧 GBP (£)", "🇯🇵 JPY (¥)", "🇦🇺 AUD ($)", "🇨🇦 CAD ($)"],
        index=0
    )
    # Extract the flag and symbol from their choice
    flag = curr_choice.split(" ")[0]
    sym = curr_choice.split("(")[1].replace(")", "")
    is_inr = (sym == "₹")

with col_title:
    st.title(f"{flag} Financial Freedom Engine")
    st.markdown("Adjust your parameters below in four sections. Your wealth projection will update **instantly**.")

# ==========================================
# 👤 PERSONA TEMPLATES (INDIA ONLY)
# ==========================================
if is_inr:
    st.markdown("### ⚡ Quick Start: Choose a Profile")

    persona_options = [
        "⚙️ Custom (I will enter my own numbers)",
        "💻 The City Techie (High Income, High Rent)",
        "🏔️ The Family (Stability & Safe Assets Focus)",
        "🔥 The Aggressive FIRE Chaser (High Equity SIPs)"
    ]

    selected_persona = st.selectbox("Select a baseline profile to auto-fill the engine:", options=persona_options)

    # 🇮🇳 INDIAN NUMBERS (Rupees)
    personas_data = {
        "💻 The City Techie (High Income, High Rent)": {
            "age": 28, "retire_age": 55, "income": 150000, "rent": 35000, "living_expense": 40000,
            "cash": 100000, "fd": 0, "epf": 300000, "mf": 800000, "sip": 40000, "housing": "Rent Forever"
        },
        "🏔️ The Family (Stability & Safe Assets Focus)": {
            "age": 36, "retire_age": 60, "income": 90000, "rent": 15000, "living_expense": 35000,
            "cash": 150000, "fd": 500000, "epf": 1200000, "mf": 200000, "sip": 15000, "housing": "Buy a Home"
        },
        "🔥 The Aggressive FIRE Chaser (High Equity SIPs)": {
            "age": 32, "retire_age": 45, "income": 250000, "rent": 40000, "living_expense": 60000,
            "cash": 300000, "fd": 0, "epf": 800000, "mf": 2500000, "sip": 100000, "housing": "Rent Forever"
        }
    }
    default_custom = {
        "age": 30, "retire_age": 60, "income": 100000, "rent": 20000, "living_expense": 30000,
        "cash": 100000, "fd": 500000, "epf": 200000, "mf": 150000, "sip": 20000, "housing": "Rent Forever"
    }

    # Fetch the numbers based on the dropdown
    p_data = personas_data.get(selected_persona, default_custom)

else:
    # 🆕 THE FIX: Give the variable a clean name for your database so it doesn't crash
    selected_persona = "🌎 Global Default (No Persona)" 
    
    # 🌎 GLOBAL DEFAULT NUMBERS (Fallback for all other currencies)
    p_data = {
        "age": 30, "retire_age": 60, "income": 5000, "rent": 1500, "living_expense": 2000,
        "cash": 10000, "fd": 20000, "epf": 10000, "mf": 15000, "sip": 1000, "housing": "Rent Forever"
    }

st.divider()

# ==========================================
# 🎛️ MAIN PAGE INPUT PANEL
# ==========================================

# --- STEP 1: USER PROFILE ---
with st.expander("1️⃣ Core Profile & Income (Please Update)", expanded=False):
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Current Age", value=p_data["age"], min_value=18, max_value=100, step=None)
    default_retire = max(p_data["retire_age"], age)
    retire_age = c2.number_input("Retirement Age(Will default to current in calculation. If retirement , Current age)", value=default_retire, min_value=18, max_value=100, step=None)
    dependents = c3.number_input("Dependents", value=2, step=None)

    if retire_age < age:
        st.warning(f"⚠️ Retirement age should not be less than current age ({age}). Will default to current age in calculations.")
    safe_retire_age = max(age, retire_age)
    c4, c5, c6 = st.columns(3)
    income = c4.number_input(f"Monthly In-hand ({sym})", value=p_data["income"], step=None)
    basic_salary = c5.number_input(f"Monthly Basic ({sym})", value=int(p_data["income"]*0.4), step=None)
    monthly_pf_inflow = basic_salary * 0.24 
    c6.info(f"✨ Auto-PF Inflow: {sym}{monthly_pf_inflow:,.0f}/mo")

    c7, c8, c9 = st.columns(3)
    living_expense = c7.number_input(f"Living Exp. Excl. Rent ({sym})", value=p_data["living_expense"], step=None)
    rent = c8.number_input(f"Monthly Rent ({sym})", value=p_data["rent"], step=None)
    total_monthly_expense = living_expense + rent
    
    tax_options = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    tax_slab = c9.selectbox("Tax Slab", options=tax_options, index=6, format_func=lambda x: f"{int(x*100)}%")
    use_post_tax = st.toggle("Calculate Post-Tax Returns?", value=True)

# --- STEP 2: SAFETY & LIQUIDITY ---
with st.expander("2️⃣ Safety Net & Insurance (Please Update)", expanded=False):
    c1, c2, c3 = st.columns(3)
    cash = c1.number_input(f"Cash / Savings ({sym})", value=p_data["cash"], step=None)
    fd = c2.number_input(f"Fixed Deposits ({sym})", value=p_data["fd"], step=None)
    credit_limit = c3.number_input(f"Credit Card Limit ({sym})", value=int(p_data["income"]*3), step=None)
    
    c4, c5, c6 = st.columns(3)
    emi = c4.number_input(f"Monthly EMIs ({sym})", value=0, step=None)
    term_insurance = c5.number_input(f"Life/Term Insurance Cover ({sym})", value=int(p_data["income"]*12*10), step=None)
    health_insurance = c6.number_input(f"Health Insurance Cover ({sym})", value=int(p_data["income"]*12*2), step=None)

# --- STEP 3: ASSETS ---
with st.expander("3️⃣ Current Investments (Please Update)", expanded=False):
    c1, c2, c3 = st.columns(3)
    epf = c1.number_input(f"EPF / PPF ({sym})", value=p_data["epf"], step=None)
    mutual_funds = c2.number_input(f"Mutual Funds ({sym})", value=p_data["mf"], step=None)
    stocks = c3.number_input(f"Direct Stocks ({sym})", value=int(p_data["mf"]*0.3), step=None)
    
    c4, c5, _ = st.columns(3)
    gold = c4.number_input(f"Gold ({sym})", value=int(p_data["mf"]*0.1), step=None)
    arbitrage = c5.number_input(f"Arbitrage Funds ({sym})", value=0, step=None)

# --- STEP 4: STRATEGY & ASSUMPTIONS ---
with st.expander("4️⃣ Strategy & Growth Assumptions (Please Update)", expanded=False):
    c1, c2, c3 = st.columns(3)
    current_sip = c1.number_input(f"Current SIP ({sym})", value=p_data["sip"], step=None)
    step_up_pct = c2.slider("Annual SIP Step-Up (%)", 0, 20, 10) 
    step_up = step_up_pct / 100
    swr = c3.number_input("Safe Withdrawal Rate (%)", value=4.0, step=0.1) / 100

    c4, c5, c6 = st.columns(3)
    h_options = ["Rent Forever", "Buy a Home", "Already Own"]
    h_index = h_options.index(p_data["housing"])
    housing_goal = c4.selectbox("Housing Plan", options=h_options, index=h_index)
    house_cost_default = 5000000 if is_inr else 350000
    house_cost = c5.number_input(f"Future House Budget ({sym})", value=house_cost_default, step=None)
    inflation = c6.number_input("General Inflation (%)", value=6.0 if is_inr else 3.0, step=0.5) / 100
    
    st.markdown("**Expected Returns (%)**")
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    rate_new_sip = r1.number_input("SIP", value=12.0) / 100
    rate_fd = r2.number_input("FD", value=7.0 if is_inr else 4.0) / 100
    rate_epf = r3.number_input("EPF", value=8.1 if is_inr else 6.0) / 100
    rate_equity = r4.number_input("Equity", value=12.0) / 100
    rate_gold = r5.number_input("Gold", value=8.0 if is_inr else 5.0) / 100
    rate_arbitrage = r6.number_input("Arbitrage", value=7.5 if is_inr else 4.5) / 100
    rent_inflation = 0.08 if is_inr else 0.04

st.divider()

# ==========================================
# 🚀 LIVE DASHBOARD & CALCULATIONS
# ==========================================

total_liq = cash + fd + credit_limit
net_worth = cash + fd + epf + mutual_funds + stocks + gold + arbitrage

# ==========================================
# 💾 DATABASE AUTO-SAVE (GATEKEEPER)
# ==========================================
if st.session_state.get('has_interacted', False):
    data_payload = {
        "id": st.session_state['user_id'], 
        "currency": curr_choice,           # 🆕 Captures "🇮🇳 INR (₹)" or "🇺🇸 USD ($)"
        "persona": selected_persona,       # 🆕 Captures the exact dropdown text
        "age": age, "retire_age": retire_age, "dependents": dependents,
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
else:
    st.session_state['has_interacted'] = True


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
m1.metric("Monthly Surplus", f"{sym}{income - total_monthly_expense - current_sip - emi:,}")
m2.metric("Liquid Safety", f"{sym}{cash + fd + credit_limit:,}")
m3.metric("Housing Plan", housing_goal)
m4.metric("PF Inflow (Auto)", f"{sym}{monthly_pf_inflow:,.0f}")

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
    "age": age, "retire_age": safe_retire_age, "living_expense": living_expense, "rent": rent,
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

# Format chart labels based on Region
if is_inr:
    chart_fmt = "datum.value >= 10000000 ? format(datum.value / 10000000, '.2f') + ' Cr' : datum.value >= 100000 ? format(datum.value / 100000, '.2f') + ' L' : format(datum.value, ',.0f')"
else:
    chart_fmt = "datum.value >= 1000000 ? format(datum.value / 1000000, '.2f') + ' M' : datum.value >= 1000 ? format(datum.value / 1000, '.0f') + ' k' : format(datum.value, ',.0f')"

base = alt.Chart(df).encode(x=alt.X('Age', scale=alt.Scale(domain=view_x_domain), axis=alt.Axis(format='d')))
nearest = alt.selection_point(nearest=True, on='mouseover', fields=['Age'], empty=False)

line_wealth = base.mark_line(color='#00FF00', strokeWidth=3).encode(
    y=alt.Y('Projected Wealth', scale=alt.Scale(domain=view_y_domain), axis=alt.Axis(labelExpr=chart_fmt, title=f'Amount ({sym})'))
)
line_req = base.mark_line(color='#FF0000', strokeDash=[5, 5]).encode(y='Required Corpus')

selectors = base.mark_point().encode(
    opacity=alt.value(0),
    tooltip=[
        alt.Tooltip('Age', title='Age'),
        alt.Tooltip('Projected Wealth', format=',.0f', title=f'Wealth ({sym})'),
        alt.Tooltip('Required Corpus', format=',.0f', title=f'Target ({sym})'),
        alt.Tooltip('Gap', format=',.0f', title=f'Surplus/Gap ({sym})')
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
    
    if is_inr:
        formatted_gap = f"{sym}{abs(gap_val)/10000000:.2f} Cr"
    else:
        formatted_gap = f"{sym}{abs(gap_val)/1000000:.2f} M"

    if gap_val >= 0:
        st.success(f"✅ **POSSIBLE**\nSurplus at {retire_age}: **{formatted_gap}**")
    else:
        st.error(f"❌ **SHORTFALL**\nGap at {retire_age}: **{formatted_gap}**")
        extra_sip_req = calculator.solve_extra_sip_needed(abs(gap_val), retire_age - age, eff_sip, step_up)
        st.info(f"💡 **The Fix:** Start an additional SIP of **{sym}{int(extra_sip_req):,}** / month.")

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

# ==========================================
# 🗣️ USER FEEDBACK SUBMISSION
# ==========================================
st.divider()
st.subheader("💡 Help Improve the Engine")
feedback_text = st.text_area("Optional: Any feature requests, bugs, or suggestions? Don't worry, it is anonymous.", max_chars=3000)

if st.button("📤 Submit Feedback", type="primary"):
    if feedback_text.strip():
        try:
            supabase.table("user_data").update({"feedback": feedback_text}).eq("id", st.session_state['user_id']).execute()
            st.success("Thank you! Your feedback has been securely submitted. ✅")
        except Exception as e:
            st.error(f"🚨 Could not submit feedback: {e}")
    else:
        st.warning("Please type some feedback before clicking submit!")