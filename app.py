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
# 🎨 CUSTOM CSS
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

    /* iOS/WebKit MOBILE RESPONSIVENESS */
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
col_title, col_settings = st.columns([3, 1])

with col_settings:
    curr_choice = st.selectbox(
        "🌎 Currency & Region", 
        options=["🇮🇳 INR (₹)", "🇺🇸 USD ($)", "🇪🇺 EUR (€)", "🇬🇧 GBP (£)", "🇯🇵 JPY (¥)", "🇦🇺 AUD ($)", "🇨🇦 CAD ($)"],
        index=0
    )
    flag = curr_choice.split(" ")[0]
    sym = curr_choice.split("(")[1].replace(")", "")
    is_inr = (sym == "₹")

with col_title:
    st.title(f"{flag} Financial Freedom Engine")
    st.markdown("A tax-aware wealth simulator built for realistic planning.")

# ==========================================
# 👤 PERSONA SELECTOR
# ==========================================
if is_inr:
    cl_p, cd_p = st.columns([1, 2])
    cl_p.markdown("<p style='margin-top: 10px; font-weight: 700;'>⚡ Quick Start: Choose a Profile</p>", unsafe_allow_html=True)
    
    persona_options = [
        "⚙️ Custom (I will enter my own numbers)",
        "💻 The City Techie (High Income, High Rent)",
        "🏔️ The Family (Stability & Safe Assets Focus)",
        "🔥 The Aggressive FIRE Chaser (High Equity SIPs)"
    ]
    selected_persona = cd_p.selectbox("persona_select", persona_options, label_visibility="collapsed")
    
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
    p_data = personas_data.get(selected_persona, default_custom)

else:
    selected_persona = "🌎 Global Default (No Persona)" 
    p_data = {
        "age": 30, "retire_age": 60, "income": 5000, "rent": 1500, "living_expense": 2000,
        "cash": 10000, "fd": 20000, "epf": 10000, "mf": 15000, "sip": 1000, "housing": "Rent Forever"
    }

st.divider()

# ==========================================
# 🎛️ INPUT TABS
# ==========================================
tab_prof, tab_safe, tab_asset, tab_strat = st.tabs(["1️⃣ Profile", "2️⃣ Safety", "3️⃣ Assets", "4️⃣ Strategy"])

with tab_prof:
    r1c1, r1c2, r1c3 = st.columns(3)
    age = r1c1.number_input("Current Age", min_value=18, max_value=None, value=int(p_data["age"]))
    default_retire = max(p_data["retire_age"], age)
    retire_age = r1c2.number_input("Retire Age", min_value=18, max_value=None, value=int(default_retire))
    dependents = r1c3.number_input("Dependents", min_value=0, max_value=None, value=2)
    safe_retire_age = max(age, retire_age)
    
    r2c1, r2c2, r2c3 = st.columns(3)
    income = r2c1.number_input(f"Monthly In-hand ({sym})", min_value=0, max_value=None, value=int(p_data["income"]))
    r2c1.caption(f"**{fmt_curr(income, sym, is_inr)}**")
    
    if is_inr:
        basic_salary = r2c2.number_input("Monthly Basic (for EPF)", min_value=0, max_value=None, value=int(income*0.4))
        r2c2.caption(f"**{fmt_curr(basic_salary, sym, is_inr)}**")
        monthly_pf_inflow = basic_salary * 0.24
        r2c3.info(f"✨ Auto-EPF: {fmt_curr(monthly_pf_inflow, sym, is_inr)}/mo")
    else: 
        monthly_pf_inflow, basic_salary = 0, 0
        r2c2.empty(); r2c3.empty()

    r3c1, r3c2, r3c3 = st.columns(3)
    living_expense = r3c1.number_input("Monthly Expenses (Ex-Rent)", min_value=0, max_value=None, value=int(p_data["living_expense"]))
    r3c1.caption(f"**{fmt_curr(living_expense, sym, is_inr)}**")
    rent = r3c2.number_input("Monthly Rent", min_value=0, max_value=None, value=int(p_data["rent"]))
    r3c2.caption(f"**{fmt_curr(rent, sym, is_inr)}**")
    tax_options = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    tax_slab = r3c3.selectbox("Tax Slab", options=tax_options, index=6, format_func=lambda x: f"{int(x*100)}%")
    use_post_tax = r3c3.toggle("Calculate post tax returns", True)

with tab_safe:
    r1c1, r1c2, r1c3 = st.columns(3)
    cash = r1c1.number_input("Cash & Savings", min_value=0, max_value=None, value=int(p_data["cash"]))
    r1c1.caption(f"**{fmt_curr(cash, sym, is_inr)}**")
    fd = r1c2.number_input("Fixed Deposits", min_value=0, max_value=None, value=int(p_data["fd"]))
    r1c2.caption(f"**{fmt_curr(fd, sym, is_inr)}**")
    credit_limit = r1c3.number_input("Credit Card Limit", min_value=0, max_value=None, value=int(income*3))
    r1c3.caption(f"**{fmt_curr(credit_limit, sym, is_inr)}**")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    emi = r2c1.number_input("Current Monthly EMIs", min_value=0, max_value=None, value=0)
    r2c1.caption(f"**{fmt_curr(emi, sym, is_inr)}**")
    term_insurance = r2c2.number_input("Term Life Cover", min_value=0, max_value=None, value=int(income*120))
    r2c2.caption(f"**{fmt_curr(term_insurance, sym, is_inr)}**")
    health_insurance = r2c3.number_input("Health Insurance Cover", min_value=0, max_value=None, value=int(income*24))
    r2c3.caption(f"**{fmt_curr(health_insurance, sym, is_inr)}**")

with tab_asset:
    r1c1, r1c2, r1c3 = st.columns(3)
    epf = r1c1.number_input("EPF/PPF Balance", min_value=0, max_value=None, value=int(p_data.get("epf", 200000 if is_inr else 0)))
    r1c1.caption(f"**{fmt_curr(epf, sym, is_inr)}**")
    mutual_funds = r1c2.number_input("Mutual Funds", min_value=0, max_value=None, value=int(p_data["mf"]))
    r1c2.caption(f"**{fmt_curr(mutual_funds, sym, is_inr)}**")
    stocks = r1c3.number_input("Direct Stocks", min_value=0, max_value=None, value=int(p_data["mf"]*0.3))
    r1c3.caption(f"**{fmt_curr(stocks, sym, is_inr)}**")
    
    r2c1, r2c2, r2c3 = st.columns(3)
    gold = r2c1.number_input("Gold/SGBs", min_value=0, max_value=None, value=0)
    r2c1.caption(f"**{fmt_curr(gold, sym, is_inr)}**")
    arbitrage = r2c2.number_input("Arbitrage Funds", min_value=0, max_value=None, value=0)
    r2c2.caption(f"**{fmt_curr(arbitrage, sym, is_inr)}**")
    fixed_income = r2c3.number_input("Fixed Income (Bonds/T-Bills)", min_value=0, max_value=None, value=0)
    r2c3.caption(f"**{fmt_curr(fixed_income, sym, is_inr)}**")

with tab_strat:
    r1c1, r1c2, r1c3 = st.columns(3)
    current_sip = r1c1.number_input("Monthly SIP", min_value=0, max_value=None, value=int(p_data["sip"]))
    r1c1.caption(f"**{fmt_curr(current_sip, sym, is_inr)}**")
    step_up = r1c2.slider("Annual SIP Step-Up %", min_value=0, max_value=50, value=10) / 100
    inflation = r1c3.number_input("General Inflation %", min_value=0.0, max_value=None, value=6.0 if is_inr else 3.0) / 100
    
    r2c1, r2c2, r2c3 = st.columns(3)
    h_options = ["Rent Forever", "Buy a Home", "Already Own"]
    h_index = h_options.index(p_data.get("housing", "Rent Forever"))
    housing_goal = r2c1.selectbox("Housing Plan", options=h_options, index=h_index)
    
    house_cost_default = 5000000 if is_inr else 350000
    house_cost = r2c2.number_input("House Cost (Today's Value)", min_value=0, max_value=None, value=int(house_cost_default))
    r2c2.caption(f"**{fmt_curr(house_cost, sym, is_inr)}**")
    
    swr = r2c3.number_input("Safe Withdrawal Rate %", min_value=0.1, max_value=None, value=4.0) / 100
    
    r3c1, r3c2 = st.columns(2)
    rent_inflation = r3c1.number_input("Rent Inflation %", min_value=0.0, max_value=None, value=8.0 if is_inr else 4.0) / 100
    
    # 💀 DIE WITH ZERO MODE TOGGLE
    dwz_mode = r3c2.toggle("💀 Die With Zero Mode (Retire Early)", value=False, help="Instead of blindly saving 25x your expenses to preserve capital forever, this calculates the exact mathematical minimum needed to safely reach age 120. This usually shrinks your target drastically and allows you to retire earlier!")
    
    st.markdown("**Expected Returns (%)**")
    rr1, rr2, rr3, rr4 = st.columns(4)
    rate_sip = rr1.number_input("SIP", min_value=-50.0, max_value=None, value=12.0)/100
    rate_equity = rr2.number_input("Direct Equity", min_value=-50.0, max_value=None, value=12.0)/100
    rate_fd = rr3.number_input("FD", min_value=-50.0, max_value=None, value=7.0 if is_inr else 4.0)/100
    rate_epf = rr4.number_input("EPF", min_value=-50.0, max_value=None, value=8.1 if is_inr else 6.0)/100
    
    rr5, rr6, rr7, rr8 = st.columns(4)
    rate_gold = rr5.number_input("Gold", min_value=-50.0, max_value=None, value=8.0 if is_inr else 5.0)/100
    rate_arbitrage = rr6.number_input("Arbitrage", min_value=-50.0, max_value=None, value=7.5 if is_inr else 4.5)/100
    rate_fixed = rr7.number_input("Debt/ Bonds", min_value=-50.0, max_value=None, value=7.5 if is_inr else 4.5)/100

st.divider()

# ==========================================
# 🚀 CORE LOGIC & DASHBOARD
# ==========================================
total_monthly_expense = living_expense + rent
total_liq = cash + fd + credit_limit
net_worth = cash + fd + epf + mutual_funds + stocks + gold + arbitrage + fixed_income

user_data_logic = {
    "income": income, "monthly_expense": total_monthly_expense, "cash": cash, "fd": fd, "credit_limit": credit_limit,
    "emi": emi, "dependents": dependents, "term_insurance": term_insurance, "health_insurance": health_insurance,
    "housing_goal": housing_goal, "house_cost": house_cost, "tax_slab": tax_slab, "use_post_tax": use_post_tax, 
    "rate_fd": rate_fd, "rate_arb": rate_arbitrage, "sym": sym, "is_inr": is_inr
}

diagnostics = logic.run_diagnostics(user_data_logic)
arbitrage_advice = logic.check_arbitrage_hack(user_data_logic)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Surplus", fmt_curr(income - total_monthly_expense - current_sip - emi, sym, is_inr))
m2.metric("Liquid Safety", fmt_curr(total_liq, sym, is_inr))
m3.metric("Housing Plan", housing_goal)
m4.metric("PF Inflow (Auto)", fmt_curr(monthly_pf_inflow, sym, is_inr))

st.subheader("🚦 Financial Health Check")
def render_card(col, res, title):
    if res["status"] == "FAIL": col.error(f"**{title}**\n\n{res['msg']}")
    elif res["status"] == "ALERT": col.warning(f"**{title}**\n\n{res['msg']}")
    else: col.success(f"**{title}**\n\n{res['msg']}")

cl1, cl2, cl3 = st.columns(3)
render_card(cl1, diagnostics['emergency'], "Liquidity")
render_card(cl2, diagnostics['debt'], "Debt Health")
render_card(cl3, diagnostics['life'], "Life Cover")

col_l4, col_l5, col_l6 = st.columns(3)
render_card(col_l4, diagnostics['health'], "Health Cover")
render_card(col_l5, diagnostics['house'], "House Goal")
render_card(col_l6, diagnostics['peace'], "Peace Fund")

# ==========================================
# 📈 WEALTH PROJECTION & CHART
# ==========================================
eff_sip = logic.calculate_post_tax_rate(rate_sip, "Equity", tax_slab, use_post_tax)
eff_eq = logic.calculate_post_tax_rate(rate_equity, "Equity", tax_slab, use_post_tax)
eff_fd = logic.calculate_post_tax_rate(rate_fd, "FD", tax_slab, use_post_tax)
eff_epf = logic.calculate_post_tax_rate(rate_epf, "EPF", tax_slab, use_post_tax)
eff_gold = logic.calculate_post_tax_rate(rate_gold, "Gold", tax_slab, use_post_tax)
eff_arb = logic.calculate_post_tax_rate(rate_arbitrage, "Arbitrage", tax_slab, use_post_tax)
eff_bond = logic.calculate_post_tax_rate(rate_fixed, "Debt", tax_slab, use_post_tax)

calc_in = {
    "age": age, "retire_age": safe_retire_age, "living_expense": living_expense, "rent": rent, "current_sip": current_sip,
    "monthly_pf": monthly_pf_inflow, "step_up": step_up, "inflation": inflation, "rent_inflation": rent_inflation,
    "swr": swr, "house_cost": house_cost, "housing_goal": housing_goal, "cash": cash, "fd": fd, "epf": epf,
    "mutual_funds": mutual_funds, "stocks": stocks, "gold": gold, "arbitrage": arbitrage, "fixed_income": fixed_income,
    "rate_savings": 0.03, "rate_epf": eff_epf, "rate_equity": eff_eq, "rate_gold": eff_gold, "rate_arbitrage": eff_arb, 
    "rate_fd": eff_fd, "rate_new_sip": eff_sip, "rate_fixed": eff_bond, "dwz_mode": dwz_mode
}

df = calculator.generate_forecast(calc_in)

if not df.empty:
    df['Age'] = df['Age'].astype(int)
    df['Projected Wealth'] = df['Projected Wealth'].astype(float)
    df['Required Corpus'] = df['Required Corpus'].astype(float)
    df['Gap'] = df['Gap'].astype(float)
    if 'Annual Expense' in df.columns:
        df['Annual Expense'] = df['Annual Expense'].astype(float)

    practical_age = int(calculator.calculate_true_fi_age(calc_in))

    target_row = df[df['Age'] == safe_retire_age].iloc[0]
    gap_val = float(target_row['Gap'])
    extra_sip_req = float(calculator.solve_extra_sip_needed(abs(gap_val), safe_retire_age - age, eff_sip, step_up)) if gap_val < 0 else 0.0

    st.subheader("📊 Wealth Forecast")
    
    st.markdown("""
    <div style='display: flex; gap: 20px; margin-bottom: 10px; font-size: 0.90rem; flex-wrap: wrap;'>
        <div><span style='color: #00FF00; font-weight: 800;'>━ Solid Green Line:</span> Projected Wealth</div>
        <div><span style='color: #FF0000; font-weight: 800;'>╍ Dashed Red Line:</span> Required Target (Depletes to zero at age 120)</div>
        <div><span style='color: #FFA500; font-weight: 800;'>━ Solid Orange Line:</span> Annual Living Expenses</div>
    </div>
    """, unsafe_allow_html=True)

    zoom = st.toggle("🔍 Default Zoom", value=True)

    if zoom and practical_age < 120:
        end_v = int(min(max(practical_age, safe_retire_age) + 10, 120))
        plot_df = df[df['Age'] <= end_v].copy()
    else:
        plot_df = df.copy()

    def tooltip_fmt(val, is_inr):
        if is_inr:
            if val >= 10000000: return f"₹ {val/10000000:.2f} Cr"
            elif val >= 100000: return f"₹ {val/100000:.2f} L"
            else: return f"₹ {val:,.0f}"
        else:
            if val >= 1000000: return f"{sym} {val/1000000:.2f} M"
            elif val >= 1000: return f"{sym} {val/1000:.0f} k"
            else: return f"{sym} {val:,.0f}"

    plot_df['Wealth_Fmt'] = plot_df['Projected Wealth'].apply(lambda x: tooltip_fmt(x, is_inr))
    plot_df['Target_Fmt'] = plot_df['Required Corpus'].apply(lambda x: tooltip_fmt(x, is_inr))
    plot_df['Expense_Fmt'] = plot_df['Annual Expense'].apply(lambda x: tooltip_fmt(x, is_inr))
    plot_df['Gap_Fmt'] = plot_df['Gap'].apply(lambda x: tooltip_fmt(x, is_inr))

    if is_inr:
        chart_fmt = "datum.value >= 10000000 ? format(datum.value / 10000000, '.2f') + ' Cr' : datum.value >= 100000 ? format(datum.value / 100000, '.2f') + ' L' : format(datum.value, ',.0f')"
    else:
        chart_fmt = "datum.value >= 1000000 ? format(datum.value / 1000000, '.2f') + ' M' : datum.value >= 1000 ? format(datum.value / 1000, '.0f') + ' k' : format(datum.value, ',.0f')"

    base = alt.Chart(plot_df).encode(x=alt.X('Age:Q', axis=alt.Axis(format='d')))
    sel = alt.selection_point(nearest=True, on='mouseover', fields=['Age'], empty=False)
    
    c1 = base.mark_line(color='#00FF00', strokeWidth=3).encode(
        y=alt.Y('Projected Wealth:Q', axis=alt.Axis(labelExpr=chart_fmt, title=f"Amount ({sym})"))
    )
    c2 = base.mark_line(color='#FF0000', strokeDash=[5,5]).encode(
        y=alt.Y('Required Corpus:Q', axis=alt.Axis(labelExpr=chart_fmt, title=""))
    )
    
    if 'Annual Expense' in plot_df.columns:
        c3 = base.mark_line(color='#FFA500', strokeWidth=2).encode(
            y=alt.Y('Annual Expense:Q', axis=alt.Axis(labelExpr=chart_fmt, title=""))
        )
        layers = [c1, c2, c3]
    else:
        layers = [c1, c2]
    
    pt = base.mark_point().encode(
        opacity=alt.value(0), 
        tooltip=[
            alt.Tooltip('Age:Q', title='Age'), 
            alt.Tooltip('Wealth_Fmt:N', title='Wealth'), 
            alt.Tooltip('Target_Fmt:N', title='Target'), 
            alt.Tooltip('Expense_Fmt:N', title='Expenses'),
            alt.Tooltip('Gap_Fmt:N', title='Surplus/Gap')
        ]
    ).add_params(sel)
    
    rl = base.mark_rule(color='gray').encode(
        opacity=alt.condition(sel, alt.value(0.5), alt.value(0))
    ).transform_filter(sel)
    
    st.altair_chart(alt.layer(*layers, pt, rl), width="stretch")
    
    # 💡 EXPLAINING THE "SUDDEN DIP" AT RETIREMENT
    if housing_goal == "Buy a Home":
        st.info(f"💡 **Why the sudden drop near age {max(safe_retire_age, practical_age)}?** Because you selected 'Buy a Home', the calculator mathematically deducts the massive, inflation-adjusted cost of your dream house from your portfolio on the exact year you retire. The Red Target line also drops because you no longer need to save for it!")

    st.divider()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown(f"### 🎯 Goal: Retire at {safe_retire_age}")
        if gap_val >= 0: 
            st.success(f"✅ **POSSIBLE**\nSurplus at {safe_retire_age}: **{fmt_curr(gap_val, sym, is_inr)}**")
        else:
            st.error(f"❌ **SHORTFALL**\nGap at {safe_retire_age}: **{fmt_curr(abs(gap_val), sym, is_inr)}**")
            st.info(f"💡 **The Fix:** Start an additional SIP of **{fmt_curr(extra_sip_req, sym, is_inr)}** / month.")

    with col_v2:
        st.markdown("### 📅 Practical Reality")
        if practical_age <= age: 
            st.success("🎉 You are Financially Independent (FI) right now!")
        elif practical_age >= 120: 
            st.error("⚠️ Financial Freedom not possible even by Age 120 with current settings.")
        else: 
            st.warning(f"⚠️ Practical Financial Freedom Age: **{practical_age}**")
        
        if arbitrage_advice['action'] == "SWITCH":
            st.info(f"💡 **Tax Tip:** {arbitrage_advice['msg']}")

# ==========================================
# 💾 DB AUTO-SAVE 
# ==========================================
if st.session_state.get('has_interacted', False):
    payload = {
        "id": st.session_state['user_id'], "currency": curr_choice, "persona": selected_persona,
        "age": age, "retire_age": safe_retire_age, "dependents": dependents, "income": income, 
        "basic_salary": basic_salary, "living_expense": living_expense, "rent": rent, "tax_slab": tax_slab, 
        "use_post_tax": use_post_tax, "cash": cash, "fd": fd, "credit_limit": credit_limit, "emi": emi, 
        "term_insurance": term_insurance, "health_insurance": health_insurance, "epf": epf, "mutual_funds": mutual_funds, 
        "stocks": stocks, "gold": gold, "arbitrage": arbitrage, "fixed_income": fixed_income, "current_sip": current_sip, 
        "step_up": step_up, "housing_goal": housing_goal, "house_cost": house_cost, "inflation": inflation, 
        "swr": swr, "dwz_mode": dwz_mode, "rate_new_sip": rate_sip, "rate_fd": rate_fd, "rate_epf": rate_epf, 
        "rate_equity": rate_equity, "rate_gold": rate_gold, "rate_arbitrage": rate_arbitrage, "rate_fixed": rate_fixed, 
        "total_liquidity": total_liq, "net_worth": net_worth,
        "practical_age": practical_age if 'practical_age' in locals() else None,
        "gap_val": gap_val if 'gap_val' in locals() else None,
        "extra_sip_req": extra_sip_req if 'extra_sip_req' in locals() else None
    }
    if supabase:
        try: supabase.table("user_data").upsert(payload).execute()
        except Exception as e: st.sidebar.error(f"DB Error: {e}")
else:
    st.session_state['has_interacted'] = True

# ==========================================
# 🗣️ USER FEEDBACK SUBMISSION
# ==========================================
st.divider()
st.subheader("💡 Help Improve the Engine")
fb = st.text_area("Optional: Any feature requests, bugs, or suggestions? Don't worry, it is anonymous.", max_chars=3000)
if st.button("📤 Submit Feedback", type="primary"):
    if fb.strip() and supabase:
        try:
            supabase.table("user_data").update({"feedback": fb}).eq("id", st.session_state['user_id']).execute()
            st.success("Thank you! Your feedback has been securely submitted. ✅")
        except Exception as e: 
            st.error(f"🚨 Could not submit feedback: {e}")
    else:
        st.warning("Please type some feedback before clicking submit!")