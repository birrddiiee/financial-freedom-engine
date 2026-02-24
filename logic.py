def calculate_post_tax_rate(rate, asset_type, tax_slab, use_post_tax):
    if not use_post_tax:
        return rate
        
    if asset_type == "Equity":
        return rate * 0.875 
    elif asset_type == "Arbitrage":
        return rate * 0.875 
    elif asset_type in ["FD", "Debt"]:
        return rate * (1 - tax_slab)
    elif asset_type == "Gold":
        return rate * 0.875
    elif asset_type == "EPF":
        return rate
    else:
        return rate

def run_diagnostics(data):
    res = {}
    monthly_exp = data['monthly_expense'] + data.get('emi', 0)
    liq = data['cash'] + data['fd']
    
    if liq >= monthly_exp * 6:
        res['emergency'] = {"status": "PASS", "msg": f"Great! You have {round(liq/monthly_exp, 1)} months of emergency funds."}
    elif liq >= monthly_exp * 3:
        res['emergency'] = {"status": "ALERT", "msg": f"You have {round(liq/monthly_exp, 1)} months of expenses. Target 6 months."}
    else:
        res['emergency'] = {"status": "FAIL", "msg": f"Low liquidity ({round(liq/monthly_exp, 1)} months). Build up cash/FD to cover 6 months."}
        
    if data['emi'] > data['income'] * 0.4:
        res['debt'] = {"status": "FAIL", "msg": "EMIs consume over 40% of income. High risk!"}
    elif data['emi'] > 0:
        res['debt'] = {"status": "ALERT", "msg": "Manageable debt, but aim to become debt-free before retirement."}
    else:
        res['debt'] = {"status": "PASS", "msg": "Zero EMI burden! Excellent."}
        
    if data['dependents'] > 0:
        if data['term_insurance'] >= data['income'] * 12 * 10:
            res['life'] = {"status": "PASS", "msg": "Adequate life cover for dependents."}
        else:
            res['life'] = {"status": "FAIL", "msg": "Increase term life insurance to at least 10x annual income."}
    else:
        res['life'] = {"status": "PASS", "msg": "No dependents, life cover is optional."}
        
    if data['health_insurance'] >= 1000000 or (data['health_insurance'] >= data['income']*3):
        res['health'] = {"status": "PASS", "msg": "Adequate health insurance cover."}
    else:
        res['health'] = {"status": "ALERT", "msg": "Consider increasing your health cover to at least 10-15 Lakhs."}
        
    if data['housing_goal'] == "Buy a Home" and liq < data['house_cost'] * 0.2:
         res['house'] = {"status": "ALERT", "msg": "If buying a house soon, your liquid down-payment (20%) is falling short."}
    else:
         res['house'] = {"status": "PASS", "msg": "Housing plan aligns with current assets."}
         
    if liq >= data['income'] * 12:
        res['peace'] = {"status": "PASS", "msg": "You have 1+ years of runway. True peace of mind!"}
    else:
        res['peace'] = {"status": "ALERT", "msg": "Keep investing to build a 1-year 'Peace Fund' for complete job flexibility."}
        
    return res

def check_arbitrage_hack(data):
    if data['tax_slab'] >= 0.3 and data['fd'] > 500000:
        return {"action": "SWITCH", "msg": "You are in the 30%+ tax slab with large FDs. Moving some FD money to Arbitrage Mutual Funds could reduce your tax from 30% to 12.5%."}
    return {"action": "NONE", "msg": "Asset allocation looks tax-efficient for your bracket."}