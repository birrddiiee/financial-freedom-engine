import pandas as pd

def generate_forecast(data):
    # Core variables
    age = data['age']
    retire_age = data['retire_age']
    living_expense = data['living_expense']
    rent = data['rent']
    sip = data['current_sip']
    step_up = data['step_up']
    inflation = data['inflation']
    rent_inflation = data['rent_inflation']
    swr = data['swr']
    house_cost = data['house_cost']
    housing_goal = data['housing_goal']
    monthly_pf = data['monthly_pf']
    
    # Initial Balances (Now includes all the new asset classes!)
    cash = data['cash']
    fd = data['fd']
    epf = data['epf']
    equity = data['mutual_funds'] + data['stocks']
    gold = data.get('gold', 0)
    arbitrage = data.get('arbitrage', 0)
    fixed_income = data.get('fixed_income', 0)
    
    # Expected Rates
    r_cash = data['rate_savings']
    r_fd = data['rate_fd']
    r_epf = data['rate_epf']
    r_eq = data['rate_equity']           # For existing equity
    r_sip = data.get('rate_new_sip', r_eq) # For new ongoing SIPs
    r_gold = data.get('rate_gold', 0.08)
    r_arb = data.get('rate_arbitrage', 0.07)
    r_fixed = data.get('rate_fixed', 0.07)
    
    forecast = []
    current_expense = living_expense * 12
    current_rent = rent * 12
    
    # We isolate the SIP corpus so it can grow at its own unique rate
    sip_corpus = 0.0
    annual_sip = sip * 12
    
    for yr in range(100 - age + 1):
        current_age = age + yr
        
        # Calculate Total Wealth for the current year
        total_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
        
        # Calculate Required Corpus
        req_corpus = 0
        if current_age >= retire_age:
            annual_need = current_expense
            if housing_goal == "Rent Forever":
                annual_need += current_rent
            req_corpus = annual_need / swr
            
            # Add house cost as a lump sum need at retirement age
            if housing_goal == "Buy a Home" and current_age == retire_age:
                req_corpus += house_cost
        
        # Log the current year's snapshot
        forecast.append({
            "Age": current_age,
            "Projected Wealth": total_wealth,
            "Required Corpus": req_corpus,
            "Gap": total_wealth - req_corpus
        })
        
        if current_age == 100: 
            break
        
        # 📈 COMPOUNDING FOR THE NEXT YEAR 
        if current_age < retire_age:
            # Still working: EPF and SIPs continue
            epf += (epf * r_epf) + (monthly_pf * 12)
            sip_corpus += (sip_corpus * r_sip) + annual_sip
            annual_sip *= (1 + step_up) # Step-up SIP for next year
        else:
            # Retired: Stop contributing, just compound existing EPF
            epf += epf * r_epf 
            
        # All other assets compound silently in the background
        equity += equity * r_eq
        gold += gold * r_gold
        arbitrage += arbitrage * r_arb
        fixed_income += fixed_income * r_fixed
        fd += fd * r_fd
        cash += cash * r_cash
        
        # Apply Inflation
        current_expense *= (1 + inflation)
        current_rent *= (1 + rent_inflation)
        if housing_goal == "Buy a Home" and current_age < retire_age:
            house_cost *= (1 + inflation)
            
    return pd.DataFrame(forecast)

def solve_extra_sip_needed(gap, years, rate, step_up):
    # Binary search to find the exact monthly SIP needed to close the wealth gap
    if gap <= 0 or years <= 0: return 0.0
    
    low, high = 0.0, gap
    best = high
    for _ in range(50): # 50 iterations is enough for penny-perfect precision
        mid = (low + high) / 2
        fv = 0
        annual_sip = mid * 12
        for y in range(years):
            fv = (fv + annual_sip) * (1 + rate)
            annual_sip *= (1 + step_up)
            
        if fv >= gap:
            best = mid
            high = mid
        else:
            low = mid
            
    return round(best / 12, 2)