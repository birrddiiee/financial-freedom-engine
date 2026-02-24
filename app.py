import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import uuid
import pandas as pd
from supabase import create_client, Client
import logic       
import calculator  

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Financial Freedom Engine", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 📈 CURRENCY FORMATTING LOGIC
# ==========================================
def fmt_curr(num, symbol, is_inr_mode):
    try:
        val = int(abs(num))
        sign = "-" if num < 0 else ""
        if is_inr_mode:
            s = str(val)
            if len(s) <= 3: res = s
            else:
                last_three = s[-3:]
                remaining = s[:-3]
                out = ""
                while len(remaining) > 2:
                    out = "," + remaining[-2:] + out
                    remaining = remaining[:-2]
                res = remaining + out + "," + last_three
            return f"{sign}₹{res}"
        else:
            return f"{sign}{symbol}{val:,}"
    except:
        return f"{symbol}{num}"

# ==========================================
# 🎨 CUSTOM CSS: MINIMALISM & iOS MOBILE GRID
# ==========================================
custom_css = """
<style>
    [data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { display: none !important; }
    input[type="number"]::-webkit-inner-spin-button, input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important; margin: 0 !important;
    }
    input[type="number"] { -moz-appearance: textfield !important; }

    div[data-baseweb="input"] > div { height: 42px !important; border-radius: 8px !important; border: 1px solid #333 !important; }
    div[data-baseweb="input"] input { padding: 4px 12px !important; font-size: 0.95rem !important; }
    .stNumberInput label { font-size: 0.85rem !important; font-weight: 600 !important; color: #888; padding-bottom: 4px !important; }
    .stTooltipIcon { display: none !important; }

    [data-testid="stCaptionContainer"] { margin-top: -12px !important; margin-bottom: 12px !important; color: #00FF00 !important; font-weight: 700 !important; font-size: 0.85rem !important; }
    div[data-testid="stTabs"] > div[data-baseweb="tab-list"] { display: flex !important; width: 100% !important; gap: 4px !important; }
    div[data-testid="stTabs"] button[data-baseweb="tab"] { flex: 1 !important; justify-content: center !important; background-color: #111 !important; border-radius: 4px 4px 0 0 !important; }
    div[data-testid="stTabs"] button[data-baseweb="tab"] p { font-size: 0.9rem !important; font-weight: 600 !important; }

    /* --- iOS/WebKit MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {
        .stMarkdown p, .stText, label { font-size: 0.8rem !important; }
        [data-testid="stMetricValue"] > div { font-size: 1.4rem !important; }
        h1 { font-size: 1.5rem !important; }
        div[data-testid="stTabs"] button[data-baseweb="tab"] p { font-size: 0.7rem !important; }

        [data-testid="stHorizontalBlock"] { display: flex !important; flex-wrap: wrap !important; width: 100% !important; gap: 0px !important; }
        [data-testid="stHorizontalBlock"] > div {
            width: 46% !important; min-width: 46% !important; flex: 1 1 46% !important; margin-bottom: 12px !important;
        }
        #vg-tooltip-element { pointer-events: none !important; z-index: 9999 !important; }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 📊 GOOGLE ANALYTICS
# ==========================================
GA_ID = "G-QB0270BY5S"
ga_script = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
    window.dataLayer = window.dataLayer || []; function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date()); gtag('config', '{GA_ID}');
</script>
"""
components.html(ga_script, height=0)

# ==========================================
# ☁️ SUPABASE CONNECTION
# ==========================================
@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()
if 'user_id' not in st.session_state: st.session_state['user_id'] = str(uuid.uuid4())
if 'has_interacted' not in st.session_state: st.session_state['has_interacted'] = False

# ==========================================
# 🖥️ HEADER & REGION
# ==========================================
c_title, c_settings = st.columns([3, 1])
with c_settings:
    curr_choice = st.selectbox("Region/Currency", options=["🇮🇳 INR (₹)", "🇺🇸 USD ($)", "🇪🇺 EUR (€)", "🇬🇧 GBP (£)"], index=0)
    sym = curr_choice.split("(")[1].replace(")", "")
    is_inr = (sym == "₹")
with c_title:
    st.title("Financial Freedom Engine 🚀")
    st.markdown("A tax-aware wealth simulator built for realistic planning.")

# ==========================================
# 👤 PERSONA SELECTOR
# ==========================================
if is_inr:
    cl_p, cd_p = st.columns([1, 2])
    cl_p.markdown("<p style='margin-top: 10px; font-weight: 700;'>⚡ Quick Load Profile:</p>", unsafe_allow_html=True)
    p_choice = cd_p.selectbox("persona", ["⚙️ Custom", "💻 Techie (28yo)", "🏔️ Family (36yo)", "🔥 FIRE (32yo)"], label_visibility="collapsed")
    p_map = {
        "💻 Techie (28yo)": {"age":28, "ret":50, "inc":180000, "rent":35000, "exp":40000, "mf":800000, "sip":60000},
        "🏔️ Family (36yo)": {"age":36, "ret":60, "inc":120000, "rent":15000, "exp":55000, "mf":200000, "sip":20000},
        "🔥 FIRE (32yo)": {"age":32, "ret":45, "inc":280000, "rent":45000, "exp":65000, "mf":3500000, "sip":140000}
    }
    p_defaults = p_map.get(p_choice, {"age":30, "ret":60, "inc":100000, "rent":20000, "exp":30000, "mf":200000, "sip":25000})
    selected_persona = p_choice
else:
    p_defaults = {"age":30, "ret":60, "inc":6000, "rent":1800, "exp":2200, "mf":25000, "sip":1500}
    selected_persona = "Global"

st.divider()

# ==========================================
# 🎛️ INPUT TABS
# ==========================================
tab_prof, tab_safe, tab_asset, tab_strat = st.tabs(["👤 Profile", "🛡️ Safety", "💰 Assets", "🎯 Strategy"])

with tab_prof:
    r1c1, r1c2, r1c3 = st.columns(3)
    age = r1c1.number_input("Current Age", 18, 100, p_defaults["age"])
    retire_age = r1c2.number_input("Retire Age", age, 100, p_defaults["ret"])
    dependents = r1c3.number_input("Dependents", 0, 10, 2)
    safe_retire_age = max(age, retire_age)
    
    r2c1, r2c2, r2c3 = st.columns(3)
    income = r2c1.number_input(f"Monthly In-hand ({sym})", 0, 10000000, p_defaults["inc"])
    r2c1.caption(fmt_curr(income, sym, is_inr))
    
    if is_inr:
        basic = r2c2.number_input("Monthly Basic (for EPF)", 0, income, int(income*0.4))
        r2c2.caption(fmt_curr(basic, sym, is_inr))
        epf_calc = basic * 0.24
        r2c3.info(f"✨ Auto-EPF: {fmt_curr(epf_calc, sym, is_inr)}/mo")
    else: 
        epf_calc, basic = 0, 0
        r2c2.empty(); r2c3.empty()

    r3c1, r3c2, r3c3 = st.columns(3)
    living = r3c1.number_input("Monthly Expenses (Ex-Rent)", 0, income, p_defaults["exp"])
    r3c1.caption(fmt_curr(living, sym, is_inr))
    rent = r3c2.number_input("Monthly Rent", 0, income, p_defaults["rent"])
    r3c2.caption(fmt_curr(rent, sym, is_inr))
    tax_slab = r3c3.selectbox("Tax Slab", [0.0, 0.1, 0.2, 0.3, 0.4], index=3, format_func=lambda x: f"{int(x*100)}%")

with tab_safe:
    r1c1, r1c2, r1c3 = st.columns(3)
    cash = r1c1.number_input("Cash & Savings", 0, 100000000, 100000)
    r1c1.caption(fmt_curr(cash, sym, is_inr))
    fd = r1c2.number_input("Fixed Deposits", 0, 100000000, 200000)
    r1c2.caption(fmt_curr(fd, sym, is_inr))
    limit = r1c3.number_input("Credit Card Limit", 0, 10000000, int(income*3))
    
    r2c1, r2c2, r2c3 = st.columns(3)
    emi = r2c1.number_input("Current Monthly EMIs", 0, income, 0)
    term = r2c2.number_input("Term Life Cover", 0, 1000000000, int(income*120))
    health = r2c3.number_input("Health Insurance Cover", 0, 50000000, int(income*24))

with tab_asset:
    r1c1, r1c2, r1c3 = st.columns(3)
    epf_total = r1c1.number_input("EPF/PPF Balance", 0, 100000000, 200000 if is_inr else 0)
    r1c1.caption(fmt_curr(epf_total, sym, is_inr))
    mf_total = r1c2.number_input("Mutual Funds", 0, 100000000, p_defaults["mf"])
    r1c2.caption(fmt_curr(mf_total, sym, is_inr))
    stock_total = r1c3.number_input("Direct Stocks", 0, 100000000, int(p_defaults["mf"]*0.3))
    
    r2c1, r2c2, r2c3 = st.columns(3)
    gold = r2c1.number_input("Gold/SGBs", 0, 100000000, 0)
    arb = r2c2.number_input("Arbitrage Funds", 0, 100000000, 0)
    bonds = r2c3.number_input("Bonds/Debt Assets", 0, 100000000, 0)

with tab_strat:
    r1c1, r1c2, r1c3 = st.columns(3)
    sip = r1c1.number_input("Monthly SIP", 0, income, p_defaults["sip"])
    r1c1.caption(fmt_curr(sip, sym, is_inr))
    step = r1c2.slider("Annual SIP Step-Up %", 0, 20, 10) / 100
    inf = r1c3.number_input("General Inflation %", 0.0, 15.0, 6.0 if is_inr else 3.0) / 100
    
    r2c1, r2c2, r2c3 = st.columns(3)
    housing = r2c1.selectbox("Housing Goal", ["Rent Forever", "Buy a Home", "Already Own"])
    house_cost = 5000000 if is_inr else 350000
    swr_rate = r2c2.number_input("Safe Withdrawal Rate %", 1.0, 10.0, 4.0) / 100
    use_post_tax = r2c3.toggle("Enable Tax-Adjusted Logic", True)
    
    st.markdown("**Expected Returns (%)**")
    rr1, rr2, rr3, rr4, rr5, rr6, rr7 = st.columns(7)
    rate_eq = rr1.number_input("SIP/Eq", value=12.0)/100
    rate_fd = rr2.number_input("FD", value=7.0 if is_inr else 4.0)/100
    rate_epf = rr3.number_input("EPF", value=8.1 if is_inr else 6.0)/100
    rate_gold = rr4.number_input("Gold", value=8.0 if is_inr else 5.0)/100
    rate_arb = rr5.number_input("Arb.", value=7.5 if is_inr else 4.5)/100
    rate_bond = rr6.number_input("Debt", value=7.5 if is_inr else 4.5)/100

st.divider()

# ==========================================
# 🚀 CORE LOGIC & DASHBOARD
# ==========================================
total_expense = living + rent
total_liq = cash + fd + limit
net_worth = cash + fd + epf_total + mf_total + stock_total + gold + arb + bonds

user_logic = {
    "income": income, "monthly_expense": total_expense, "cash": cash, "fd": fd, "credit_limit": limit,
    "emi": emi, "dependents": dependents, "term_insurance": term, "health_insurance": health,
    "housing_goal": housing, "house_cost": house_cost, "tax_slab": tax_slab, "use_post_tax": use_post_tax, 
    "rate_fd": rate_fd, "rate_arb": rate_arb, "sym": sym, "is_inr": is_inr
}

diag = logic.run_diagnostics(user_logic)
arb_tip = logic.check_arbitrage_hack(user_logic)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Surplus", fmt_curr(income - total_expense - sip - emi, sym, is_inr))
m2.metric("Liquid Safety", fmt_curr(total_liq, sym, is_inr))
m3.metric("Housing Plan", housing)
m4.metric("PF Inflow (Auto)", fmt_curr(epf_calc, sym, is_inr))

st.subheader("🚦 Financial Health Check")
def render_card(col, res, title):
    if res["status"] == "FAIL": col.error(f"**{title}**\n\n{res['msg']}")
    elif res["status"] == "ALERT": col.warning(f"**{title}**\n\n{res['msg']}")
    else: col.success(f"**{title}**\n\n{res['msg']}")

cl1, cl2, cl3 = st.columns(3)
render_card(cl1, diag['emergency'], "Liquidity")
render_card(cl2, diag['debt'], "Debt Health")
render_card(cl3, diag['life'], "Life Cover")

# ==========================================
# 📈 WEALTH PROJECTION & CHART
# ==========================================
eff_eq = logic.calculate_post_tax_rate(rate_eq, "Equity", tax_slab, use_post_tax)
eff_fd = logic.calculate_post_tax_rate(rate_fd, "FD", tax_slab, use_post_tax)
eff_epf = logic.calculate_post_tax_rate(rate_epf, "EPF", tax_slab, use_post_tax)
eff_gold = logic.calculate_post_tax_rate(rate_gold, "Gold", tax_slab, use_post_tax)
eff_arb = logic.calculate_post_tax_rate(rate_arb, "Arbitrage", tax_slab, use_post_tax)
eff_bond = logic.calculate_post_tax_rate(rate_bond, "Debt", tax_slab, use_post_tax)

calc_in = {
    "age": age, "retire_age": safe_retire_age, "living_expense": living, "rent": rent, "current_sip": sip,
    "monthly_pf": epf_calc, "step_up": step, "inflation": inf, "rent_inflation": 0.08 if is_inr else 0.04,
    "swr": swr_rate, "house_cost": house_cost, "housing_goal": housing, "cash": cash, "fd": fd, "epf": epf_total,
    "mutual_funds": mf_total, "stocks": stock_total, "gold": gold, "arbitrage": arb, "fixed_income": bonds,
    "rate_savings": 0.03, "rate_epf": eff_epf, "rate_equity": eff_eq, "rate_gold": eff_gold, "rate_arbitrage": eff_arb, 
    "rate_fd": eff_fd, "rate_new_sip": eff_eq, "rate_fixed": eff_bond
}

df = calculator.generate_forecast(calc_in)

if not df.empty:
    freedom = df[df['Gap'] >= 0]
    practical_age = int(freedom.iloc[0]['Age']) if not freedom.empty else 100

    target_row = df[df['Age'] == safe_retire_age].iloc[0]
    gap_val = float(target_row['Gap'])
    extra_sip = float(calculator.solve_extra_sip_needed(abs(gap_val), safe_retire_age - age, eff_eq, step)) if gap_val < 0 else 0.0

    st.subheader("📊 Wealth Forecast")
    c_tog, _ = st.columns([1, 3])
    zoom = c_tog.toggle("🔍 Default Zoom", value=True)

    if zoom and practical_age < 100:
        end_v = min(max(practical_age, safe_retire_age) + 10, 100)
        temp_df = df[df['Age'] <= end_v]
        view_x = [age, end_v]
        view_y = [0, float(max(temp_df['Projected Wealth'].max(), temp_df['Required Corpus'].max()) * 1.1)]
    else:
        view_x = [age, 100]
        view_y = [0, float(max(df['Projected Wealth'].max(), df['Required Corpus'].max()) * 1.1)]

    fmt = "datum.value >= 10000000 ? format(datum.value/10000000, '.2f') + ' Cr' : datum.value >= 100000 ? format(datum.value/100000, '.2f') + ' L' : format(datum.value, ',.0f')" if is_inr else "datum.value >= 1000000 ? format(datum.value/1000000, '.2f') + ' M' : datum.value >= 1000 ? format(datum.value/1000, '.0f') + ' k' : format(datum.value, ',.0f')"

    base = alt.Chart(df).encode(x=alt.X('Age', scale=alt.Scale(domain=view_x), axis=alt.Axis(format='d')))
    sel = alt.selection_point(nearest=True, on='mouseover', fields=['Age'], empty=False)
    
    c1 = base.mark_line(color='#00FF00', strokeWidth=3).encode(y=alt.Y('Projected Wealth', scale=alt.Scale(domain=view_y), axis=alt.Axis(labelExpr=fmt, title=f"Amount ({sym})")))
    c2 = base.mark_line(color='#FF0000', strokeDash=[5,5]).encode(y='Required Corpus')
    pt = base.mark_point().encode(opacity=alt.value(0), tooltip=['Age', alt.Tooltip('Projected Wealth', format=',.0f'), alt.Tooltip('Required Corpus', format=',.0f'), alt.Tooltip('Gap', format=',.0f')]).add_params(sel)
    rl = base.mark_rule(color='gray').encode(opacity=alt.condition(sel, alt.value(0.5), alt.value(0))).transform_filter(sel)
    
    st.altair_chart(alt.layer(c1, c2, pt, rl), use_container_width=True)

    st.divider()
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown(f"### 🎯 Goal: Retire at {safe_retire_age}")
        if gap_val >= 0: st.success(f"✅ **POSSIBLE**\nSurplus: **{fmt_curr(gap_val, sym, is_inr)}**")
        else:
            st.error(f"❌ **SHORTFALL**\nGap: **{fmt_curr(abs(gap_val), sym, is_inr)}**")
            st.info(f"💡 **Fix:** Add SIP of **{fmt_curr(extra_sip, sym, is_inr)}** / month.")

    with col_v2:
        st.markdown("### 📅 Practical Reality")
        if practical_age <= age: st.success("🎉 You are Financially Independent (FI) right now!")
        elif practical_age > 100: st.error("⚠️ Freedom not possible by Age 100.")
        else: st.warning(f"⚠️ Practical Financial Freedom Age: **{practical_age}**")
        if arb_tip['action'] == "SWITCH": st.info(f"💡 **Tax Tip:** {arb_tip['msg']}")

# ==========================================
# 💾 DB AUTO-SAVE (NOW CAPTURES EVERYTHING)
# ==========================================
if st.session_state.get('has_interacted', False):
    payload = {
        "id": st.session_state['user_id'], "currency": curr_choice, "persona": selected_persona,
        "age": age, "retire_age": safe_retire_age, "dependents": dependents, "income": income, 
        "basic_salary": basic, "living_expense": living, "rent": rent, "tax_slab": tax_slab, 
        "use_post_tax": use_post_tax, "cash": cash, "fd": fd, "credit_limit": limit, "emi": emi, 
        "term_insurance": term, "health_insurance": health, "epf": epf_total, "mutual_funds": mf_total, 
        "stocks": stock_total, "gold": gold, "arbitrage": arb, "fixed_income": bonds, "current_sip": sip, 
        "step_up": step, "housing_goal": housing, "house_cost": house_cost, "inflation": inf, 
        "swr": swr_rate, "rate_new_sip": rate_eq, "rate_fd": rate_fd, "rate_epf": rate_epf, 
        "rate_equity": rate_eq, "rate_gold": rate_gold, "rate_arbitrage": rate_arb, "rate_fixed": rate_bond, 
        "total_liquidity": total_liq, "net_worth": net_worth,
        
        # 🆕 Computed Metrics
        "practical_age": practical_age if 'practical_age' in locals() else None,
        "gap_val": gap_val if 'gap_val' in locals() else None,
        "extra_sip_req": extra_sip if 'extra_sip' in locals() else None
    }
    if supabase:
        try: supabase.table("user_data").upsert(payload).execute()
        except Exception as e: st.sidebar.error(f"DB Error: {e}")
else:
    st.session_state['has_interacted'] = True

# ==========================================
# 🗣️ FEEDBACK SUBMISSION
# ==========================================
st.divider()
st.subheader("💡 Help Improve the Engine")
fb = st.text_area("Any feature requests or bugs? (Anonymous)", max_chars=3000)
if st.button("📤 Submit Feedback", type="primary"):
    if fb.strip() and supabase:
        try:
            supabase.table("user_data").update({"feedback": fb}).eq("id", st.session_state['user_id']).execute()
            st.success("Feedback submitted! ✅")
        except: st.error("🚨 Error saving feedback.")