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
# 📊 GOOGLE ANALYTICS (GA4) - PARENT INJECTION
# ==========================================
GA_ID = "G-QB0270BY5S"
ga_script = f"""
<script>
    // Break out of the Streamlit iframe and inject into the main parent window
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

# Generate Anonymous User ID and Calculation State
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())
if 'is_calculated' not in st.session_state:
    st.session_state['is_calculated'] = False

# ==========================================
# SIDEBAR: THE INPUT WIZARD
# ==========================================
st.sidebar.header("⚙️ Configure Your Plan")

# --- STEP 1: USER PROFILE ---
with st.sidebar.expander("1️⃣ User Profile", expanded=True):
    # DYNAMIC AGE LOGIC FIX
    age = st.number_input("Current Age", value=30, min_value=18, max_value=100, step=1)
    default_retire = max(60, age)
    retire_age = st.number_input("Retirement Age", value=default_retire, min_value=age, max_value=100, step=1)
    
    dependents = st.number_input("Number of Dependents", value=2, step=1)
    income = st.number_input("Monthly In-hand Income (₹)", value=100000, step=5000)
    
    basic_salary = st.number_input("Monthly Basic Salary (₹)", value=40000, step=1000)
    monthly_pf_inflow = basic_salary * 0.24 
    st.caption(f"✨ Auto-PF Inflow: ₹{monthly_pf_inflow:,.0f} / month")

    living_expense = st.number_input("Living Expenses (Excl. Rent) (₹)", value=30000, step=1000)
    rent = st.number_input("Current Rent Paid (₹)", value=20000, step=1000)
    total_monthly_expense = living_expense + rent
    
    tax_options = [0.0, 0.10, 0.20, 0.30]
    tax_slab = st.selectbox("Your Tax Slab", options=tax_options, index=3, format_func=lambda x: f"{int(x*100)}%")
    use_post_tax = st.toggle("Calculate Post-Tax Returns?", value=True)

# --- STEP 2: SAFETY & LIQUIDITY ---
with st.sidebar.expander("2️⃣ Safety & Liquidity", expanded=False):
    cash = st.number_input("Cash / Savings Account (₹)", value=100000, step=10000)
    fd = st.number_input("Fixed Deposits (₹)", value=500000, step=10000)
    credit_limit = st.number_input("Credit Card Limit (₹)", value=300000, step=10000)
    emi = st.number_input("Total Monthly EMIs (₹)", value=0, step=1000)
    term_insurance = st.number_input("Term Insurance Cover (₹)", value=5000000, step=500000)
    health_insurance = st.number_input("Health Insurance Cover (₹)", value=500000, step=100000)

# --- STEP 3: ASSETS ---
with st.sidebar.expander("3️⃣ Current Assets", expanded=False):
    epf = st.number_input("EPF / PPF Balance (₹)", value=200000, step=10000)
    mutual_funds = st.number_input("Mutual Funds (₹)", value=150000, step=10000)
    stocks = st.number_input("Direct Stocks (₹)", value=50000, step=10000)
    gold = st.number_input("Gold (₹)", value=50000, step=10000)
    arbitrage = st.number_input("Arbitrage Funds (₹)", value=50000, step=10000)

# --- STEP 4: STRATEGY & ASSUMPTIONS ---
with st.sidebar.expander("4️⃣ Strategy & Assumptions", expanded=False):
    current_sip = st.number_input("Current Voluntary SIP (₹)", value=20000, step=1000)
    step_up_pct = st.slider("Annual SIP Step-Up (%)", 0, 20, 10) 
    step_up = step_up_pct / 100
    
    h_options = ["Rent Forever", "Buy a Home", "Already Own"]
    housing_goal = st.selectbox("Housing Plan", options=h_options, index=0)
    house_cost = st.number_input("Budget for House (Today's Value)", value=5000000, step=500000)
    
    inflation = st.number_input("General Inflation (%)", value=6.0, step=0.5) / 100
    rent_inflation = st.number_input("Rent Inflation (%)", value=8.0, step=0.5) / 100
    swr = st.number_input("Safe Withdrawal Rate (%)", value=4.0, step=0.1) / 100

    rate_new_sip = st.number_input("SIP Return Rate (%)", value=12.0) / 100
    rate_fd = st.number_input("FD Return Rate (%)", value=7.0) / 100
    rate_epf = st.number_input("EPF/PPF Return Rate (%)", value=8.1) / 100
    rate_equity = st.number_input("Equity Return Rate (%)", value=12.0) / 100
    rate_gold = st.number_input("Gold Return Rate (%)", value=8.0) / 100
    rate_arbitrage = st.number_input("Arbitrage Return Rate (%)", value=7.5) / 100

# ==========================================
# 📬 MANDATORY SUBMIT & OPTIONAL FEEDBACK
# ==========================================
st.sidebar.divider()
feedback_text = st.sidebar.text_area("Optional: Any feature requests or suggestions? Don't worry, it is anonymous. (Max 500 words)", max_chars=3000)

if not st.session_state['is_calculated']:
    # BUTTON WARNING FIX
    if st.sidebar.button("🚀 Calculate My Freedom Plan", type="primary", width="stretch"):
        st.session_state['is_calculated'] = True
        st.rerun() # Forces the app to reload instantly

# ==========================================
# MAIN DASHBOARD AREA
# ==========================================
st.title("🇮🇳 Financial Freedom Engine")

if not st.session_state['is_calculated']:
    # --- WELCOME SCREEN ---
    st.info("### ↖️ Tap the **>** icon in the top left corner to open the input panel.")
    st.warning("Please enter your details in the sidebar and click **'🚀 Calculate My Freedom Plan'** to view your personalized roadmap.")
    st.markdown("""
    ### Welcome to your Personal Wealth Architect
    By compiling your income, assets, and goals, this engine will run a 100-year simulation to determine your exact path to financial independence. 
    
    **What you will discover:**
    * Your target Fi-Age (Financial Independence Age).
    * If you are on track to retire early.
    * Real-time optimization of your liquidity and debt.
    """)
else:
    # --- UNLOCKED DASHBOARD & AUTO-SAVE MAGIC ---
    
    # 1. 🌟 LIVE-SYNC AUTO-SAVE 🌟
    total_liq = cash + fd + credit_limit
    net_worth = cash + fd + epf + mutual_funds + stocks + gold + arbitrage
    
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
    
    # DATABASE UNMASKING FIX
    try:
        supabase.table("user_data").upsert(data_payload).execute()
    except Exception as e:
        st.error(f"🚨 ALERT - Database Error: {e}")

    # 2. Run Diagnostics
    user_data_logic = {
        "income": income, "monthly_expense": total_monthly_expense, "cash": cash, "fd": fd, "credit_limit": credit_limit,
        "emi": emi, "dependents": dependents, "term_insurance": term_insurance, "health_insurance": health_insurance,
        "housing_goal": housing_goal, "house_cost": house_cost, "tax_slab": tax_slab, "use_post_tax": use_post_tax, 
        "rate_fd": rate_fd, "rate_arb": rate_arbitrage
    }
    diagnostics = logic.run_diagnostics(user_data_logic)
    arbitrage_advice = logic.check_arbitrage_hack(user_data_logic)

    st.divider()
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
    
    # INDEX ERROR CRASH FIX
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

    with st.expander("See Detailed Year-by-Year Data"):
        st.dataframe(df)