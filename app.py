import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import uuid
import pandas as pd
import math
from supabase import create_client, Client
import taxes       
import calculator  

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Financial Freedom Engine", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 📊 GOOGLE ANALYTICS (Native Injection)
# ==========================================
try:
    ga_id = st.secrets.get("GA_ID", None)
    if ga_id:
        ga_script = f"""
        <script>
            if (!window.parent.document.getElementById('ga-script')) {{
                var script1 = window.parent.document.createElement('script');
                script1.id = 'ga-script';
                script1.async = true;
                script1.src = 'https://www.googletagmanager.com/gtag/js?id={ga_id}';
                window.parent.document.head.appendChild(script1);

                var script2 = window.parent.document.createElement('script');
                script2.innerHTML = `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){{dataLayer.push(arguments);}}
                  gtag('js', new Date());
                  gtag('config', '{ga_id}');
                `;
                window.parent.document.head.appendChild(script2);
            }}
        </script>
        """
        components.html(ga_script, width=0, height=0)
except Exception as e:
    pass

# ==========================================
# 🎨 CUSTOM CSS FOR MOBILE UX
# ==========================================
custom_css = """
<style>
    [data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] { display: none !important; }
    input[type="number"]::-webkit-inner-spin-button, input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none !important; margin: 0 !important; }
    input[type="number"] { -moz-appearance: textfield !important; }
    
    div[data-baseweb="input"] > div { height: 42px !important; border-radius: 8px !important; border: 1px solid #333 !important; }
    div[data-baseweb="input"] input { padding: 4px 12px !important; font-size: 0.95rem !important; }
    .stNumberInput label, .stSelectbox label { font-size: 0.85rem !important; font-weight: 600 !important; color: #888; padding-bottom: 4px !important; }
    .stTooltipIcon { display: none !important; }
    
    /* Wizard Progress Bar Styling */
    .stProgress > div > div > div > div { background-color: #00FF00 !important; }
    
    /* Neon Green Captions */
    [data-testid="stCaptionContainer"] { margin-top: -12px !important; margin-bottom: 12px !important; color: #00FF00 !important; font-weight: 700 !important; font-size: 0.85rem !important; }
    
    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .stMarkdown p, .stText, label { font-size: 0.8rem !important; }
        [data-testid="stMetricValue"] > div { font-size: 1.4rem !important; }
        h1 { font-size: 1.5rem !important; }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# ☁️ SUPABASE & BULLETPROOF SESSION STATE
# ==========================================
@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

if 'user_id' not in st.session_state: st.session_state['user_id'] = str(uuid.uuid4())
if 'step' not in st.session_state: st.session_state['step'] = 0

# 🛡️ THE BULLETPROOF DATA VAULT
if 'db' not in st.session_state: st.session_state.db = {}

def sync(key):
    st.session_state.db[key] = st.session_state[key]

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
# 🧑‍💻 PERSONA DATA LIBRARY
# ==========================================
h_options = ["Rent Forever", "Buy a Home", "Already Own"]

personas_data = {
    "techie": {
        "age": 28, "retire_age": 55, "dependents": 2, "income": 150000, "living_expense": 40000, "rent": 35000,
        "tax_slab_idx": 6, "use_post_tax": True, "cash": 100000, "fd": 0, "credit_limit": 450000, "emi": 0,
        "term_insurance": 15000000, "health_insurance": 1000000, "epf": 300000, "mutual_funds": 800000, 
        "stocks": 200000, "gold": 0, "arbitrage": 0, "fixed_income": 0, "step_up": 10, "inflation": 6.0, 
        "housing_idx": 0, "house_cost": 15000000, "rent_inflation": 8.0, "rate_sip": 12.0, "rate_equity": 12.0, 
        "rate_fd_gross": 7.0, "rate_epf": 8.1, "rate_gold": 8.0, "rate_arbitrage": 7.5, "rate_fixed": 7.5,
        "current_sip": 40000, "monthly_pf": 14400
    },
    "family": {
        "age": 36, "retire_age": 60, "dependents": 3, "income": 90000, "living_expense": 35000, "rent": 15000,
        "tax_slab_idx": 4, "use_post_tax": True, "cash": 150000, "fd": 500000, "credit_limit": 200000, "emi": 15000,
        "term_insurance": 10000000, "health_insurance": 500000, "epf": 1200000, "mutual_funds": 200000, 
        "stocks": 50000, "gold": 100000, "arbitrage": 0, "fixed_income": 200000, "step_up": 5, "inflation": 6.0, 
        "housing_idx": 1, "house_cost": 8000000, "rent_inflation": 8.0, "rate_sip": 11.0, "rate_equity": 11.0, 
        "rate_fd_gross": 7.0, "rate_epf": 8.1, "rate_gold": 8.0, "rate_arbitrage": 7.5, "rate_fixed": 7.5,
        "current_sip": 15000, "monthly_pf": 9600
    },
    "fire": {
        "age": 32, "retire_age": 45, "dependents": 1, "income": 250000, "living_expense": 60000, "rent": 40000,
        "tax_slab_idx": 6, "use_post_tax": True, "cash": 300000, "fd": 0, "credit_limit": 500000, "emi": 0,
        "term_insurance": 20000000, "health_insurance": 2000000, "epf": 800000, "mutual_funds": 2500000, 
        "stocks": 1000000, "gold": 0, "arbitrage": 0, "fixed_income": 0, "step_up": 15, "inflation": 6.0, 
        "housing_idx": 0, "house_cost": 20000000, "rent_inflation": 8.0, "rate_sip": 13.0, "rate_equity": 13.0, 
        "rate_fd_gross": 7.0, "rate_epf": 8.1, "rate_gold": 8.0, "rate_arbitrage": 7.5, "rate_fixed": 7.5,
        "current_sip": 100000, "monthly_pf": 19200
    }
}

def load_persona_to_state(persona_key, curr_choice):
    st.session_state['curr_choice'] = curr_choice
    is_inr_mode = ("₹" in curr_choice)
    
    st.session_state.db = {} 
    st.session_state.db["persona"] = persona_key
    
    if persona_key == "blank":
        st.session_state.db.update({
            "age": 30, "retire_age": 60, "dependents": 2, "income": 0, "monthly_pf": 0, "living_expense": 0, "rent": 0,
            "tax_slab_idx": 6 if is_inr_mode else 4, "use_post_tax": True, "cash": 0, "fd": 0, "credit_limit": 0, "emi": 0,
            "term_insurance": 0, "health_insurance": 0, "epf": 0, "mutual_funds": 0, "stocks": 0, "gold": 0, "arbitrage": 0, "fixed_income": 0, 
            "step_up": 10 if is_inr_mode else 5, 
            "inflation": 6.0 if is_inr_mode else 3.0, 
            "housing_idx": 0, "house_cost": 5000000 if is_inr_mode else 350000, 
            "rent_inflation": 8.0 if is_inr_mode else 4.0, 
            "rate_sip": 12.0 if is_inr_mode else 8.0, 
            "rate_equity": 12.0 if is_inr_mode else 8.0, 
            "rate_fd_gross": 7.0 if is_inr_mode else 4.0, 
            "rate_epf": 8.1 if is_inr_mode else 6.0, 
            "rate_gold": 8.0 if is_inr_mode else 5.0, 
            "rate_arbitrage": 7.5 if is_inr_mode else 4.5, 
            "rate_fixed": 7.5 if is_inr_mode else 4.5,
            "current_sip": 0
        })
    else:
        for k, v in personas_data[persona_key].items():
            st.session_state.db[k] = v
            
    st.session_state.step = 1
    st.rerun()

if 'curr_choice' not in st.session_state:
    st.session_state['curr_choice'] = "🇮🇳 INR (₹)"

flag = st.session_state['curr_choice'].split(" ")[0]
sym = st.session_state['curr_choice'].split("(")[1].replace(")", "")
is_inr = (sym == "₹")

# ==========================================
# 🚀 GLOBAL APP HEADER
# ==========================================
st.title(f"🚀 Financial Freedom Engine")
st.markdown("A brutally honest retirement calculator built to ensure your money lasts until age 100.")
st.divider()

# ==========================================
# 🚀 THE WIZARD ENGINE
# ==========================================

# -----------------------------------
# STEP 0: THE WELCOME & PERSONA SCREEN
# -----------------------------------
if st.session_state.step == 0:
    st.markdown("### Step 0: Setup & Quick Start")
    st.markdown("Choose a starting point. If you wish please pre-fill the calculator with realistic numbers to save your time. **(Don't worry, you can easily edit it!)**")
    
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        curr = st.selectbox("🌎 Currency", ["🇮🇳 INR (₹)", "🇺🇸 USD ($)", "🇪🇺 EUR (€)", "🇬🇧 GBP (£)"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "₹" in curr:
        if st.button("💻 'The City Techie' (High Income, Renting, Aggressive)", width="stretch"):
            load_persona_to_state("techie", curr)
        if st.button("🏔️ 'The Family' (Stability & Safe Assets Focus)", width="stretch"):
            load_persona_to_state("family", curr)
        if st.button("🔥 'The FIRE Chaser' (Extreme Saving, Retiring at 45)", width="stretch"):
            load_persona_to_state("fire", curr)
            
    if st.button("🛠️ Start from a Blank Template", type="primary", width="stretch"):
        load_persona_to_state("blank", curr)

# -----------------------------------
# STEPS 1-4: THE GUIDED INPUT FLOW
# -----------------------------------
elif 1 <= st.session_state.step <= 4:
    
    st.markdown(f"#### Step {st.session_state.step} of 4")
    st.progress(st.session_state.step / 4)
    
    # --- STEP 1: PROFILE ---
    if st.session_state.step == 1:
        st.subheader("1️⃣ Personal Profile")
        
        c1, c2, c3 = st.columns(3)
        c1.number_input("Current Age", min_value=18, max_value=99, value=int(st.session_state.db.get("age", 30)), key="age", on_change=sync, args=("age",))
        c2.number_input("Desired Retirement Age", min_value=18, max_value=99, value=int(st.session_state.db.get("retire_age", 60)), key="retire_age", on_change=sync, args=("retire_age",))
        c3.number_input("Dependents", min_value=0, max_value=10, value=int(st.session_state.db.get("dependents", 2)), key="dependents", on_change=sync, args=("dependents",))
        
        c4, c5, c6 = st.columns(3)
        c4.number_input(f"Monthly In-hand Salary ({sym})", min_value=0, value=int(st.session_state.db.get("income", 0)), key="income", on_change=sync, args=("income",))
        c4.caption(f"**{fmt_curr(st.session_state.db.get('income', 0), sym, is_inr)}**")
        
        c5.number_input("Monthly EPFO/ Pension Contribution", min_value=0, value=int(st.session_state.db.get("monthly_pf", 0)), key="monthly_pf", on_change=sync, args=("monthly_pf",))
        c5.caption(f"**{fmt_curr(st.session_state.db.get('monthly_pf', 0), sym, is_inr)}**")

        c7, c8, c9 = st.columns(3)
        c7.number_input("Monthly Expenses (Excluding Rent)", min_value=0, value=int(st.session_state.db.get("living_expense", 0)), key="living_expense", on_change=sync, args=("living_expense",))
        c7.caption(f"**{fmt_curr(st.session_state.db.get('living_expense', 0), sym, is_inr)}**")
        
        c8.number_input("Monthly Rent", min_value=0, value=int(st.session_state.db.get("rent", 0)), key="rent", on_change=sync, args=("rent",))
        c8.caption(f"**{fmt_curr(st.session_state.db.get('rent', 0), sym, is_inr)}**")
        
        tax_options = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
        c9.selectbox("Tax Slab (Pre-Retirement)", options=range(len(tax_options)), format_func=lambda x: f"{int(tax_options[x]*100)}%", index=int(st.session_state.db.get("tax_slab_idx", 6)), key="tax_slab_idx", on_change=sync, args=("tax_slab_idx",))
        st.toggle("Calculate Post-Tax Returns automatically", value=bool(st.session_state.db.get("use_post_tax", True)), key="use_post_tax", on_change=sync, args=("use_post_tax",))

    # --- STEP 2: SAFETY ---
    elif st.session_state.step == 2:
        st.subheader("2️⃣ Safety & Debts")
        
        c1, c2, c3 = st.columns(3)
        c1.number_input("Cash & Savings in bank", min_value=0, value=int(st.session_state.db.get("cash", 0)), key="cash", on_change=sync, args=("cash",))
        c1.caption(f"**{fmt_curr(st.session_state.db.get('cash', 0), sym, is_inr)}**")
        
        c2.number_input("Fixed Deposits (FDs / CDs)", min_value=0, value=int(st.session_state.db.get("fd", 0)), key="fd", on_change=sync, args=("fd",))
        c2.caption(f"**{fmt_curr(st.session_state.db.get('fd', 0), sym, is_inr)}**")
        
        c3.number_input("Total Credit Card Limit", min_value=0, value=int(st.session_state.db.get("credit_limit", 0)), key="credit_limit", on_change=sync, args=("credit_limit",))
        c3.caption(f"**{fmt_curr(st.session_state.db.get('credit_limit', 0), sym, is_inr)}**")
        
        c4, c5, c6 = st.columns(3)
        c4.number_input("Total Monthly EMI(Debt) Payments", min_value=0, value=int(st.session_state.db.get("emi", 0)), key="emi", on_change=sync, args=("emi",))
        c4.caption(f"**{fmt_curr(st.session_state.db.get('emi', 0), sym, is_inr)}**")
        
        c5.number_input("Life/Term Insurance Cover", min_value=0, value=int(st.session_state.db.get("term_insurance", 0)), key="term_insurance", on_change=sync, args=("term_insurance",))
        c5.caption(f"**{fmt_curr(st.session_state.db.get('term_insurance', 0), sym, is_inr)}**")
        
        c6.number_input("Health Insurance Cover", min_value=0, value=int(st.session_state.db.get("health_insurance", 0)), key="health_insurance", on_change=sync, args=("health_insurance",))
        c6.caption(f"**{fmt_curr(st.session_state.db.get('health_insurance', 0), sym, is_inr)}**")

    # --- STEP 3: ASSETS ---
    elif st.session_state.step == 3:
        st.subheader("3️⃣ Invested Assets Corpus")
        
        c1, c2, c3 = st.columns(3)
        c1.number_input("Total Corpus in EPFO / 401k / Pensions", min_value=0, value=int(st.session_state.db.get("epf", 0)), key="epf", on_change=sync, args=("epf",))
        c1.caption(f"**{fmt_curr(st.session_state.db.get('epf', 0), sym, is_inr)}**")
        
        c2.number_input("Current Mutual Funds Value", min_value=0, value=int(st.session_state.db.get("mutual_funds", 0)), key="mutual_funds", on_change=sync, args=("mutual_funds",))
        c2.caption(f"**{fmt_curr(st.session_state.db.get('mutual_funds', 0), sym, is_inr)}**")
        
        c3.number_input("Money in Stocks", min_value=0, value=int(st.session_state.db.get("stocks", 0)), key="stocks", on_change=sync, args=("stocks",))
        c3.caption(f"**{fmt_curr(st.session_state.db.get('stocks', 0), sym, is_inr)}**")
        
        c4, c5, c6 = st.columns(3)
        c4.number_input("Gold (Physical/SGBs/ETF)", min_value=0, value=int(st.session_state.db.get("gold", 0)), key="gold", on_change=sync, args=("gold",))
        c4.caption(f"**{fmt_curr(st.session_state.db.get('gold', 0), sym, is_inr)}**")
        
        c5.number_input("Arbitrage Fund Value", min_value=0, value=int(st.session_state.db.get("arbitrage", 0)), key="arbitrage", on_change=sync, args=("arbitrage",))
        c5.caption(f"**{fmt_curr(st.session_state.db.get('arbitrage', 0), sym, is_inr)}**")
        
        c6.number_input("Fixed Income (Bonds)", min_value=0, value=int(st.session_state.db.get("fixed_income", 0)), key="fixed_income", on_change=sync, args=("fixed_income",))
        c6.caption(f"**{fmt_curr(st.session_state.db.get('fixed_income', 0), sym, is_inr)}**")

    # --- STEP 4: STRATEGY ---
    elif st.session_state.step == 4:
        st.subheader("4️⃣ Strategy & Returns")
        
        st.markdown("**Your Ongoing Investments**")
        c1, c2 = st.columns(2)
        c1.number_input("Monthly SIP ", min_value=0, value=int(st.session_state.db.get("current_sip", 0)), key="current_sip", on_change=sync, args=("current_sip",))
        c1.caption(f"**{fmt_curr(st.session_state.db.get('current_sip', 0), sym, is_inr)}**")
        
        c2.slider("Annual SIP Increase (Step-Up %)", min_value=0, max_value=50, value=int(st.session_state.db.get("step_up", 10)), key="step_up", on_change=sync, args=("step_up",))
        
        st.markdown("**Macro Economics & Housing**")
        c3, c4 = st.columns(2)
        c3.number_input("General Inflation %", min_value=0.0, max_value=20.0, value=float(st.session_state.db.get("inflation", 6.0)), key="inflation", on_change=sync, args=("inflation",))
        c4.number_input("Rent Inflation %", min_value=0.0, max_value=20.0, value=float(st.session_state.db.get("rent_inflation", 8.0)), key="rent_inflation", on_change=sync, args=("rent_inflation",))
        
        c5, c6 = st.columns(2)
        c5.selectbox("Housing Plan", options=range(len(h_options)), format_func=lambda x: h_options[x], index=int(st.session_state.db.get("housing_idx", 0)), key="housing_idx", on_change=sync, args=("housing_idx",))
        
        c6.number_input("House Cost in Today's Value", min_value=0, value=int(st.session_state.db.get("house_cost", 0)), key="house_cost", on_change=sync, args=("house_cost",))
        c6.caption(f"**{fmt_curr(st.session_state.db.get('house_cost', 0), sym, is_inr)}**")
        
        with st.expander("⚙️ Advanced: Expected Annual Return Rates (%)", expanded=False):
            rc1, rc2, rc3 = st.columns(3)
            rc1.number_input("Mutual Fund Return", value=float(st.session_state.db.get("rate_sip", 12.0)), key="rate_sip", on_change=sync, args=("rate_sip",))
            rc2.number_input("Stocks Return", value=float(st.session_state.db.get("rate_equity", 12.0)), key="rate_equity", on_change=sync, args=("rate_equity",))
            rc3.number_input("FD / CD Return (Gross)", value=float(st.session_state.db.get("rate_fd_gross", 7.0)), key="rate_fd_gross", on_change=sync, args=("rate_fd_gross",))
            
            rc4, rc5, rc6 = st.columns(3)
            rc4.number_input("Gold Return", value=float(st.session_state.db.get("rate_gold", 8.0)), key="rate_gold", on_change=sync, args=("rate_gold",))
            rc5.number_input("Arbitrage Fund Return", value=float(st.session_state.db.get("rate_arbitrage", 7.5)), key="rate_arbitrage", on_change=sync, args=("rate_arbitrage",))
            rc6.number_input("Debt/Bonds Return", value=float(st.session_state.db.get("rate_fixed", 7.5)), key="rate_fixed", on_change=sync, args=("rate_fixed",))
            
            st.number_input("EPFO/Pension Return", value=float(st.session_state.db.get("rate_epf", 8.1)), key="rate_epf", on_change=sync, args=("rate_epf",))

    # --- WIZARD NAVIGATION BUTTONS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
    
    with b_col1:
        if st.session_state.step == 1:
            if st.button("⬅️ Change Profile", width="stretch"):
                st.session_state.step = 0
                st.rerun()
        else:
            if st.button("⬅️ Back", width="stretch"):
                st.session_state.step -= 1
                st.rerun()
                
    with b_col3:
        if st.session_state.step == 1:
            if st.button("Next: Safety & Debts ⬆️", type="primary", width="stretch"):
                st.session_state.step = 2
                st.rerun()
        elif st.session_state.step == 2:
            if st.button("Next: Invested Assets ⬆️", type="primary", width="stretch"):
                st.session_state.step = 3
                st.rerun()
        elif st.session_state.step == 3:
            if st.button("Next: Strategy & Growth ⬆️", type="primary", width="stretch"):
                st.session_state.step = 4
                st.rerun()
        elif st.session_state.step == 4:
            if st.button("🚀 View Financial Reality ⬆️", type="primary", width="stretch"):
                st.session_state.step = 5
                st.rerun()

# -----------------------------------
# STEP 5: THE MAGIC REVEAL (RESULTS)
# -----------------------------------
elif st.session_state.step == 5:
    
    c_back, _, _ = st.columns([1, 3, 3])
    if c_back.button("⬅️ Edit Inputs", width="stretch"):
        st.session_state.step = 4
        st.rerun()
    
    # 🔒 Extract all values directly from our protected vault
    age = st.session_state.db.get("age", 30)
    safe_retire_age = max(age, st.session_state.db.get("retire_age", 60))
    living_expense = st.session_state.db.get("living_expense", 0)
    rent = st.session_state.db.get("rent", 0)
    tax_slab = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40][st.session_state.db.get("tax_slab_idx", 6)]
    use_post_tax = st.session_state.db.get("use_post_tax", True)
    inflation = st.session_state.db.get("inflation", 6.0) / 100.0
    rent_inflation = st.session_state.db.get("rent_inflation", 8.0) / 100.0
    house_cost = st.session_state.db.get("house_cost", 0)
    housing_goal = h_options[st.session_state.db.get("housing_idx", 0)]
    
    cash = st.session_state.db.get("cash", 0)
    fd = st.session_state.db.get("fd", 0)
    epf = st.session_state.db.get("epf", 0)
    mutual_funds = st.session_state.db.get("mutual_funds", 0)
    stocks = st.session_state.db.get("stocks", 0)
    gold = st.session_state.db.get("gold", 0)
    arbitrage = st.session_state.db.get("arbitrage", 0)
    fixed_income = st.session_state.db.get("fixed_income", 0)
    
    income = st.session_state.db.get("income", 0)
    emi = st.session_state.db.get("emi", 0)
    term_insurance = st.session_state.db.get("term_insurance", 0)
    
    current_sip = st.session_state.db.get("current_sip", 0)
    monthly_pf_inflow = st.session_state.db.get("monthly_pf", 0)
    step_up = st.session_state.db.get("step_up", 10) / 100.0
    
    rate_sip = st.session_state.db.get("rate_sip", 12.0) / 100.0
    rate_equity = st.session_state.db.get("rate_equity", 12.0) / 100.0
    rate_fd_gross = st.session_state.db.get("rate_fd_gross", 7.0) / 100.0
    rate_epf = st.session_state.db.get("rate_epf", 8.1) / 100.0
    rate_gold = st.session_state.db.get("rate_gold", 8.0) / 100.0
    rate_arbitrage = st.session_state.db.get("rate_arbitrage", 7.5) / 100.0
    rate_fixed = st.session_state.db.get("rate_fixed", 7.5) / 100.0

    eff_sip = taxes.calculate_post_tax_rate(rate_sip, "Equity", tax_slab, use_post_tax)
    eff_eq = taxes.calculate_post_tax_rate(rate_equity, "Equity", tax_slab, use_post_tax)
    eff_epf = taxes.calculate_post_tax_rate(rate_epf, "EPF", tax_slab, use_post_tax)
    eff_gold = taxes.calculate_post_tax_rate(rate_gold, "Gold", tax_slab, use_post_tax)
    eff_arb = taxes.calculate_post_tax_rate(rate_arbitrage, "Arbitrage", tax_slab, use_post_tax)
    eff_bond = taxes.calculate_post_tax_rate(rate_fixed, "Debt", tax_slab, use_post_tax)

    # --- BASE ENGINE: Calculates the immutable truth ---
    base_calc_in = {
        "age": age, "retire_age": safe_retire_age, "living_expense": living_expense, "rent": rent, "current_sip": current_sip,
        "monthly_pf": monthly_pf_inflow, "step_up": step_up, "inflation": inflation, "rent_inflation": rent_inflation,
        "house_cost": house_cost, "housing_goal": housing_goal, "cash": cash, "fd": fd, "epf": epf,
        "mutual_funds": mutual_funds, "stocks": stocks, "gold": gold, "arbitrage": arbitrage, "fixed_income": fixed_income,
        "rate_savings": 0.03, "rate_epf": eff_epf, "rate_equity": eff_eq, "rate_gold": eff_gold, "rate_arbitrage": eff_arb, 
        "rate_fd_gross": rate_fd_gross, "rate_new_sip": eff_sip, "rate_fixed": eff_bond, 
        "retire_mode": "off"
    }

    base_df = calculator.generate_forecast(base_calc_in)
    practical_age = int(calculator.calculate_true_fi_age(base_calc_in))
    target_row = base_df[base_df['Age'] == safe_retire_age].iloc[0] if safe_retire_age in base_df['Age'].values else base_df.iloc[-1]
    gap_val = float(target_row['Gap'])
    
    raw_extra_sip = float(calculator.solve_extra_sip_needed(base_calc_in))
    extra_sip_req = math.ceil(raw_extra_sip)
    
    if gap_val < -10 and extra_sip_req == 0:
        extra_sip_req = 1

    # --- 1. TOP DIAGNOSTICS (Line-Wise Report) ---
    st.header("Your Financial Reality 🔮")
    st.subheader("🎯 Retirement Goal Status")
    
    st.markdown("<ul style='font-size: 0.95rem; line-height: 1.6;'>", unsafe_allow_html=True)
    
    if extra_sip_req <= 0.0: 
        if gap_val >= 0:
            st.markdown(f"<li>🟢 <b>Goal (Retire at {safe_retire_age}):</b> ACHIEVABLE! You are projected to have a surplus of {fmt_curr(gap_val, sym, is_inr)}.</li>", unsafe_allow_html=True)
        else:
            st.markdown(f"<li>🟢 <b>Goal (Retire at {safe_retire_age}):</b> ACHIEVABLE! Simulator confirmed your wealth will safely last to age 100 regardless.</li>", unsafe_allow_html=True)
    else:
        st.markdown(f"<li>🔴 <b>Goal (Retire at {safe_retire_age}):</b> Shortfall Detected. You have a projected gap of {fmt_curr(abs(gap_val), sym, is_inr)}.</li>", unsafe_allow_html=True)
        st.markdown(f"<li>💡 <b>The Fix:</b> Add <b>{fmt_curr(extra_sip_req, sym, is_inr)} / month</b> to your current investments to retire on time.</li>", unsafe_allow_html=True)

    if practical_age <= age: 
        st.markdown(f"<li>🎉 <b>Practical Reality:</b> You are already Financially Independent (FI) right now!</li>", unsafe_allow_html=True)
    elif practical_age >= 100: 
        st.markdown(f"<li>🔴 <b>Practical Reality:</b> Financial Freedom is not possible even by age 100 with your current settings.</li>", unsafe_allow_html=True)
    else: 
        st.markdown(f"<li>📅 <b>Practical Reality:</b> If you cannot change anything, your true Financial Freedom Age is <b>{practical_age}</b> (when wealth naturally survives to 100).</li>", unsafe_allow_html=True)

    st.markdown("</ul>", unsafe_allow_html=True)
    st.divider()

    # --- 2. THE FINANCIAL HEALTH BULLET REPORT ---
    st.subheader("🩺 Financial Health Report")
    
    req_emergency = (living_expense + rent + emi) * 6
    curr_liquidity = cash + fd
    req_life = income * 120
    debt_ratio = (emi / income) if income > 0 else 0
    
    st.markdown("<ul style='font-size: 0.95rem; line-height: 1.6;'>", unsafe_allow_html=True)
    
    if curr_liquidity >= req_emergency:
        st.markdown(f"<li>🟢 <b>Emergency Fund:</b> You have {fmt_curr(curr_liquidity, sym, is_inr)}, safely covering your 6-month requirement of {fmt_curr(req_emergency, sym, is_inr)}.</li>", unsafe_allow_html=True)
    else:
        st.markdown(f"<li>🔴 <b>Emergency Fund:</b> You have {fmt_curr(curr_liquidity, sym, is_inr)}. To survive a 6-month crisis, you need {fmt_curr(req_emergency, sym, is_inr)}. <i>(Shortfall: {fmt_curr(req_emergency - curr_liquidity, sym, is_inr)})</i></li>", unsafe_allow_html=True)
        
    if term_insurance >= req_life:
        st.markdown(f"<li>🟢 <b>Life Cover:</b> Your family is fully protected with {fmt_curr(term_insurance, sym, is_inr)} in coverage.</li>", unsafe_allow_html=True)
    elif req_life > 0:
        st.markdown(f"<li>🔴 <b>Life Cover:</b> You only have {fmt_curr(term_insurance, sym, is_inr)}. Based on your income, your family needs {fmt_curr(req_life, sym, is_inr)} to be fully secure.</li>", unsafe_allow_html=True)
        
    if debt_ratio < 0.3:
        st.markdown(f"<li>🟢 <b>Debt Burden:</b> Your EMIs consume {int(debt_ratio*100)}% of your income. You are safely below the 30% danger zone.</li>", unsafe_allow_html=True)
    else:
        st.markdown(f"<li>🔴 <b>Debt Burden:</b> Your EMIs consume {int(debt_ratio*100)}% of your income. This exceeds the safe 30% limit and restricts wealth creation.</li>", unsafe_allow_html=True)
        
    if housing_goal == "Buy a Home":
        if (cash + fd + mutual_funds + stocks) < (house_cost * 0.2):
            st.markdown(f"<li>🔴 <b>House Goal:</b> You plan to buy a {fmt_curr(house_cost, sym, is_inr)} home, but your current liquid net worth is too low for a safe 20% down payment.</li>", unsafe_allow_html=True)
        else:
            st.markdown(f"<li>🟢 <b>House Goal:</b> You have sufficient liquid assets to make a 20% down payment on your future {fmt_curr(house_cost, sym, is_inr)} home.</li>", unsafe_allow_html=True)
            
    st.markdown("</ul>", unsafe_allow_html=True)
    st.divider()

    # --- 3. THE MAGIC PLACEHOLDERS FOR UI ORDERING ---
    scenario_container = st.container()
    chart_container = st.container()
    st.divider()
    strategy_container = st.container()

    # --- 4. INTERACTIVE STRATEGY CONTROLS (Rendered at the bottom) ---
    with strategy_container:
        st.markdown("### ⚡ Interactive Strategy Controls")
        qc1, qc2 = st.columns(2)
        
        fd_trap_toggled = qc1.toggle("🛡️ **Move your corpus 100% to Risk-Free (FD / CDs) at Retirement**", value=False)
        trap_banner_placeholder = st.empty()
        
        retire_mode = "off"
        blend_toggled = False
        
        base_eq = (100 - safe_retire_age) / 100.0  
        if extra_sip_req > 0:
            base_eq += 0.20 
        optimal_eq = max(0.20, min(0.80, base_eq))
        optimal_eq = round(optimal_eq * 20) / 20.0 
        
        if fd_trap_toggled:
            blend_toggled = qc2.toggle("✨ **Optimize My Retirement Portfolio (The Magic Fix)**", value=False)
            retire_mode = "dynamic" if blend_toggled else "100_fd"

        if fd_trap_toggled and not blend_toggled:
            target_corpus = target_row['Required Target']
            fd_gross_int = target_corpus * rate_fd_gross
            tax_amt = taxes.calculate_india_tax(fd_gross_int)
            net_int = fd_gross_int - tax_amt
            net_pct = (net_int / target_corpus) * 100 if target_corpus > 0 else 0
            
            with trap_banner_placeholder.container():
                st.error("#### 🚨 The Great Retirement Myth")
                st.markdown(f"""
                Let's look at the actual math of moving to a 100% Risk-Free portfolio at retirement. To safely survive until age 100 using only low-risk investments, you need a staggering **{fmt_curr(target_corpus, sym, is_inr)}**. Why is this number so terrifyingly high? 
                
                In Year 1 of retirement, your massive safe balance will generate **{fmt_curr(fd_gross_int, sym, is_inr)}** in interest. Because interests on FD is taxed on accrual, you will owe **{fmt_curr(tax_amt, sym, is_inr)}** in taxes, leaving a net of **{fmt_curr(net_int, sym, is_inr)}**.
                
                This means your true, in-hand return is only **{net_pct:.2f}%**. 
                
                With inflation at **{inflation*100:.1f}%**, your interest fails to cover your expenses. By trying to take zero risk, you mathematically guarantee that your savings bleed purchasing power every single day.
                """)
                
        elif fd_trap_toggled and blend_toggled:
            eq_pct_display = int(optimal_eq * 100)
            debt_pct_display = 100 - eq_pct_display
            with trap_banner_placeholder.container():
                st.success(f"✅ **Dynamic Bucket Strategy Active.** We analyzed your exact trajectory. To safely survive a massive {(100 - safe_retire_age)}-year retirement against {inflation*100:.1f}% inflation, your mathematically optimal portfolio split is **{debt_pct_display}% Safe Assets / {eq_pct_display}% Growth Assets**.")

    # --- 5. SCENARIO SWITCHER (Rendered above the graph) ---
    plot_calc_in = base_calc_in.copy()
    plot_calc_in['retire_mode'] = retire_mode
    if retire_mode == 'dynamic':
        plot_calc_in['equity_alloc'] = optimal_eq
    
    with scenario_container:
        if extra_sip_req > 0:
            st.markdown("#### 🕹️ Test the Fixes (Scenario Simulator)")
            
            sip_label = f"🟢 The 'Extra SIP' Fix (+{fmt_curr(extra_sip_req, sym, is_inr)}/mo)"
            age_label = f"🔵 The 'Practical Retirement Age' Fix ({practical_age} yrs)"
            traj_label = "🔴 My Current Trajectory"
            
            scenario = st.radio(
                "Choose a reality to plot:",
                [traj_label, sip_label, age_label],
                horizontal=True,
                label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            
            if scenario == sip_label:
                plot_calc_in['current_sip'] += extra_sip_req
            elif scenario == age_label:
                if practical_age >= 100:
                    st.warning("⚠️ Retiring at a later age won't solve this massive shortfall before age 100. Please use the 'Extra SIP' method.")
                    plot_calc_in['retire_age'] = 99
                else:
                    plot_calc_in['retire_age'] = practical_age

    # Generate Chart Data
    df = calculator.generate_forecast(plot_calc_in)

    # --- 6. RENDER THE CHART (Clean Altair Setup) ---
    with chart_container:
        st.subheader("📊 The 100-Year Wealth Trajectory")
        st.markdown("""
        <div style='display: flex; gap: 20px; margin-bottom: 10px; font-size: 0.85rem; flex-wrap: wrap;'>
            <div><span style='color: #00FF00; font-weight: 800;'>━ Solid Green Line:</span> Projected Wealth</div>
            <div><span style='color: #FF0000; font-weight: 800;'>╍ Dashed Red Line:</span> Required money to last till 100 years</div>
            <div><span style='color: #FFA500; font-weight: 800;'>━ Solid Orange Line:</span> Annual Living Expenses</div>
        </div>
        """, unsafe_allow_html=True)

        zoom = st.toggle("🔍 Default Zoom (Focus on early years)", value=True)

        if zoom and practical_age < 100:
            end_v = int(min(max(practical_age, plot_calc_in['retire_age']) + 10, 100))
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
        plot_df['Target_Fmt'] = plot_df['Required Target'].apply(lambda x: tooltip_fmt(x, is_inr))
        plot_df['Expense_Fmt'] = plot_df['Annual Expense'].apply(lambda x: tooltip_fmt(x, is_inr))
        plot_df['Gap_Fmt'] = plot_df['Gap'].apply(lambda x: tooltip_fmt(x, is_inr))

        if is_inr:
            chart_fmt = "datum.value >= 10000000 ? format(datum.value / 10000000, '.2f') + ' Cr' : datum.value >= 100000 ? format(datum.value / 100000, '.2f') + ' L' : format(datum.value, ',.0f')"
        else:
            chart_fmt = "datum.value >= 1000000 ? format(datum.value / 1000000, '.2f') + ' M' : datum.value >= 1000 ? format(datum.value / 1000, '.0f') + ' k' : format(datum.value, ',.0f')"

        base_chart = alt.Chart(plot_df).encode(
            x=alt.X('Age:Q', axis=alt.Axis(format='d', labelOverlap=True, tickCount=5))
        )
        
        sel = alt.selection_point(nearest=True, on='mouseover', fields=['Age'], empty=False)
        
        c1 = base_chart.mark_line(color='#00FF00', strokeWidth=3).encode(
            y=alt.Y('Projected Wealth:Q', axis=alt.Axis(labelExpr=chart_fmt, title=f"Amount ({sym})"))
        )
        c2 = base_chart.mark_line(color='#FF0000', strokeDash=[5,5]).encode(
            y=alt.Y('Required Target:Q', axis=alt.Axis(labelExpr=chart_fmt, title=""))
        )
        
        layers = [c1, c2]
        if 'Annual Expense' in plot_df.columns:
            c3 = base_chart.mark_line(color='#FFA500', strokeWidth=2).encode(
                y=alt.Y('Annual Expense:Q', axis=alt.Axis(labelExpr=chart_fmt, title=""))
            )
            layers.append(c3)
        
        pt = base_chart.mark_point().encode(
            opacity=alt.value(0), 
            tooltip=[
                alt.Tooltip('Age:Q', title='Age'), 
                alt.Tooltip('Wealth_Fmt:N', title='Wealth'), 
                alt.Tooltip('Target_Fmt:N', title='Req. Target'), 
                alt.Tooltip('Expense_Fmt:N', title='Expenses'),
                alt.Tooltip('Gap_Fmt:N', title='Surplus/Gap')
            ]
        ).add_params(sel)
        
        rl = base_chart.mark_rule(color='gray').encode(
            opacity=alt.condition(sel, alt.value(0.5), alt.value(0))
        ).transform_filter(sel)
        
        st.altair_chart(alt.layer(*layers, pt, rl), use_container_width=True)

    # --- 7. AUDIT THE MATH ---
    with st.expander("🔍 Audit the Math: Year-by-Year Raw Data", expanded=False):
        display_df = base_df.copy() 
        def format_currency_table(val):
            if is_inr:
                if val >= 10000000: return f"₹ {val/10000000:.2f} Cr"
                elif val >= 100000: return f"₹ {val/100000:.2f} L"
                else: return f"₹ {val:,.0f}"
            else:
                if val >= 1000000: return f"{sym} {val/1000000:.2f} M"
                else: return f"{sym} {val:,.0f}"

        display_df['Projected Wealth (Green)'] = display_df['Projected Wealth'].apply(format_currency_table)
        display_df['Required Money (Red)'] = display_df['Required Target'].apply(format_currency_table)
        display_df['Annual Expense (Orange)'] = display_df['Annual Expense'].apply(format_currency_table)
        display_df['Surplus / Gap'] = display_df['Gap'].apply(format_currency_table)
        st.dataframe(display_df[['Age', 'Projected Wealth (Green)', 'Required Money (Red)', 'Annual Expense (Orange)', 'Surplus / Gap']], width="stretch", hide_index=True)

    # --- 8. FEEDBACK BOX ---
    st.divider()
    st.subheader("💬 We value your feedback!")
    st.session_state.db["feedback_input"] = st.text_area("Tell us how we can improve your experience, or what features you'd like to see next:", value=st.session_state.db.get("feedback_input", ""), key="feedback_input", on_change=sync, args=("feedback_input",))
    
    if st.button("Submit Feedback", type="primary", width="stretch"):
        st.success("Thank you! Your feedback has been securely submitted.")

    # ==========================================
    # 💾 DB AUTO-SAVE 
    # ==========================================
    if supabase:
        try:
            payload = {
                "id": st.session_state['user_id'], 
                "currency": st.session_state['curr_choice'], 
                "age": age, 
                "retire_age": safe_retire_age, 
                "dependents": st.session_state.db.get("dependents", 0), 
                "income": st.session_state.db.get("income", 0), 
                "basic_salary": int(st.session_state.db.get("monthly_pf", 0)), 
                "living_expense": living_expense, 
                "rent": rent, 
                "tax_slab": float(st.session_state.db.get("tax_slab_idx", 6)), 
                "use_post_tax": use_post_tax, 
                "cash": cash, 
                "fd": fd, 
                "credit_limit": st.session_state.db.get("credit_limit", 0), 
                "emi": st.session_state.db.get("emi", 0), 
                "term_insurance": st.session_state.db.get("term_insurance", 0), 
                "health_insurance": st.session_state.db.get("health_insurance", 0), 
                "epf": epf, 
                "mutual_funds": mutual_funds, 
                "stocks": stocks, 
                "gold": gold, 
                "arbitrage": arbitrage, 
                "fixed_income": float(fixed_income), 
                "current_sip": current_sip, 
                "step_up": float(st.session_state.db.get("step_up", 10)), 
                "housing_goal": housing_goal, 
                "house_cost": house_cost, 
                "inflation": float(st.session_state.db.get("inflation", 6.0)), 
                "rent_inflation": float(st.session_state.db.get("rent_inflation", 8.0)), 
                "swr": 0.0,
                "rate_new_sip": float(st.session_state.db.get("rate_sip", 12.0)), 
                "rate_fd": float(st.session_state.db.get("rate_fd_gross", 7.0)), 
                "rate_epf": float(st.session_state.db.get("rate_epf", 8.1)), 
                "rate_equity": float(st.session_state.db.get("rate_equity", 12.0)), 
                "rate_gold": float(st.session_state.db.get("rate_gold", 8.0)), 
                "rate_arbitrage": float(st.session_state.db.get("rate_arbitrage", 7.5)), 
                "rate_fixed": float(st.session_state.db.get("rate_fixed", 7.5)), 
                "total_liquidity": (cash + fd + st.session_state.db.get("credit_limit", 0)), 
                "net_worth": (cash + fd + epf + mutual_funds + stocks + gold + arbitrage + fixed_income),
                "feedback": st.session_state.db.get("feedback_input", ""),
                "persona": st.session_state.db.get("persona", "blank"),
                "practical_age": int(practical_age),
                "gap_val": float(gap_val), 
                "extra_sip_req": float(extra_sip_req)
            }
            supabase.table("user_data").upsert(payload).execute()
        except Exception as e: 
            pass