def calculate_post_tax_rate(rate, asset_type, tax_slab, use_post_tax):
    if not use_post_tax: return rate
    
    # India Tax Logic 2026
    if asset_type in ["Equity", "Arbitrage", "Gold"]:
        return rate * (1 - 0.125) # 12.5% LTCG
    elif asset_type in ["FD", "Savings"]:
        return rate * (1 - tax_slab) # Slab rate
    elif asset_type == "EPF":
        return rate # Exempt-Exempt-Exempt
    return rate

def run_diagnostics(data):
    # 1. Emergency Fund (Liquidity) - Including Strategic Credit Bridge
    cash_liq = data.get('cash', 0) + data.get('fd', 0)
    total_liq = cash_liq + data.get('credit_limit', 0)
    target_6mo = data.get('monthly_expense', 0) * 6
    
    if cash_liq >= target_6mo:
        emergency = {"status": "SUCCESS", "msg": "Pure cash covers 6 months. Very conservative!"}
    elif total_liq >= target_6mo:
        emergency = {"status": "SUCCESS", "msg": "Strategic Move: Credit Limit provides the bridge. High liquidity confirmed allowing more equity exposure."}
    else:
        emergency = {"status": "FAIL", "msg": f"Critical: Need ₹{target_6mo - total_liq:,.0f} more for safety."}

    # 2. Debt Health
    income = data.get('income', 1) # Prevent div by zero
    emi_ratio = data.get('emi', 0) / income
    if data.get('emi', 0) == 0:
        debt = {"status": "SUCCESS", "msg": "Debt-free! Your compounding will be massive."}
    elif emi_ratio > 0.40:
        debt = {"status": "FAIL", "msg": f"High Debt stress (>40%). Focus on clearing loans."}
    else:
        debt = {"status": "ALERT", "msg": f"EMI at {emi_ratio*100:.0f}%. Manageable."}

    # 3. Life Protection (12x Annual Income Rule)
    target_life = income * 12 * 12 
    if data.get('term_insurance', 0) < target_life:
        life = {"status": "FAIL", "msg": f"Term cover low. Target: ₹{target_life/10000000:.1f} Cr."}
    else:
        life = {"status": "SUCCESS", "msg": "Life cover is solid (12x+ income)."}

    # 4. Health Insurance Check (₹10L Benchmark)
    if data.get('health_insurance', 0) < 1000000:
        health = {"status": "ALERT", "msg": "Medical costs are rising. Aim for ₹10L+ cover."}
    else:
        health = {"status": "SUCCESS", "msg": "Health insurance is robust."}

    # 5. House Goal Check
    if data.get('housing_goal') == "Buy a Home":
        house = {"status": "WAIT", "msg": f"Tracking ₹{data.get('house_cost',0):,.0f} goal in projection."}
    else:
        house = {"status": "SUCCESS", "msg": "Asset-light rental strategy active."}

    # 6. Peace Fund (12 months of pure expenses)
    if cash_liq >= (data.get('monthly_expense', 0) * 12):
        peace = {"status": "SUCCESS", "msg": "1-Year Peace Fund achieved! You are bulletproof."}
    else:
        peace = {"status": "WAIT", "msg": "Aim for 12 months of cash for absolute peace of mind."}

    return {
        "emergency": emergency, "debt": debt, "life": life,
        "health": health, "house": house, "peace": peace
    }

def check_arbitrage_hack(data):
    if data.get('tax_slab', 0) >= 0.15:
        return {"action": "SWITCH", "msg": "Tax Tip: Move non-emergency FD to Arbitrage fund(12.5 % LTCG tax) since FD returns are taxed at income tax slab."}
    return {"action": "NONE", "msg": "Current structure is tax-efficient."}